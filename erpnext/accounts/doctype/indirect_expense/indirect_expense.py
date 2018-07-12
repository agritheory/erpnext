# -*- coding: utf-8 -*-
# Copyright (c) 2018, AgriTheory and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from erpnext.accounts import party
from frappe.utils.data import formatdate, nowdate
from frappe.model.mapper import get_mapped_doc
from erpnext.accounts.general_ledger import make_gl_entries, merge_similar_entries, delete_gl_entries

"""
from erpnext.controllers.buying_controller import BuyingController
from erpnext.accounts.utils import get_account_currency, get_fiscal_year
from erpnext.accounts.general_ledger import make_gl_entries, merge_similar_entries, delete_gl_entries
from erpnext.accounts.doctype.gl_entry.gl_entry import update_outstanding_amt
from erpnext.accounts.general_ledger import get_round_off_account_and_cost_center
"""


class IndirectExpense(Document):
	def autoname(self):
		prefix = "IE-" + self.invoice_date + "-" + self.party
		self.name = make_autoname(prefix + '-.###')

	def get_payment_terms(self):
		return frappe.db.get_value(self.party_type, self.party, "payment_terms")

	def validate(self):
		self.validate_invoice_number_and_amount()

	def get_due_date(self):
		return party.get_due_date_from_template(self.payment_terms, self.posting_date, self.invoice_date)

	def get_default_payables_account(self):
		if self.company:
			return frappe.db.get_value("Company", self.company, "default_payable_account")
		else:
			frappe.throw("Please set company before payables account.")

	def before_submit(self):
		self.linked_journal_entry = self.make_journal_entry()

	def on_cancel(self):
		doc = frappe.get_doc("Journal Entry", self.linked_journal_entry)
		doc.cancel()
		doc.delete()
		self.linked_journal_entry = ""

	def make_journal_entry(self):
		doc = frappe.new_doc("Journal Entry")
		doc.voucher_type = "Indirect Expense"
		doc.posting_date = self.invoice_date or nowdate()
		doc.payment_terms_template = self.payment_terms_template or ""
		doc.due_date = self.due_date or nowdate()
		doc.party = self.party
		doc.naming_series = "IE-"
		if self.company is not None:
			doc.company = self.company
		else:
			doc.company = frappe.db.get_value("Global Defaults", None, "default_company")
		doc.append("accounts", {
			"account": self.accounts_payable_account,
			"credit_in_account_currency": self.amount_due,
			"debit_in_account_currency": "0.00",
			"party_type": self.party_type,
			"party": self.party,
			"is_advance": "No"
		})
		for i, e in enumerate(self.entries):
			doc.append("accounts", {
				"account": e.account,
				"cost_center": e.cost_center,
				"project": e.project if e.project is not None else self.project,
				"debit_in_account_currency": e.amount,
				"credit_in_account_currency": "0.00",
				"party_type": self.party_type,
				"party": self.party
			})
		doc.cheque_no = self.party + " Indirect Expense - " + self.invoice_date + " - " + str(self.amount_due)
		doc.cheque_date = self.invoice_date
		doc.save()
		doc.submit()
		return doc.name

	def validate_invoice_number_and_amount(self):  # TODO: add purchase invoice to lookup
		matching_invoices = frappe.db.sql(
			"""select name from `tabIndirect Expense`
				where ref_number like %(invoice_no)s
				and party like %(party)s
				and docstatus = 1""",
			{"invoice_no": self.ref_number, "party": self.party}, as_dict=True)
		matches = ""
		for i in matching_invoices:
			matches += str(matching_invoices[0].name) + " "
		if matching_invoices:
			frappe.msgprint("This entry might be duplicate based on the Invoice Number and Party: " +
				matches,
				"Warning Duplicate Entry", indicator="orange")

################################################################################
	def make_gl_entries(self, gl_entries=None, repost_future_gle=True, from_repost=False):
		if not self.amount_due: # if there isn't a total, bail out
			return
		if not gl_entries:
			gl_entries = self.get_gl_entries()

		if gl_entries:
			update_outstanding = "No" if (cint(self.is_paid) or self.write_off_account) else "Yes" # where are self._is

			make_gl_entries(gl_entries,  cancel=(self.docstatus == 2),
				update_outstanding=update_outstanding, merge_entries=False)

			if update_outstanding == "No":
				update_outstanding_amt(self.credit_to, "Supplier", self.supplier,
					self.doctype, self.return_against if cint(self.is_return) else self.name)

			if repost_future_gle and cint(self.update_stock) and self.auto_accounting_for_stock:
				from erpnext.controllers.stock_controller import update_gl_entries_after
				items, warehouses = self.get_items_and_warehouses()
				update_gl_entries_after(self.posting_date, self.posting_time, warehouses, items)

		elif self.docstatus == 2 and cint(self.update_stock) and self.auto_accounting_for_stock:
			delete_gl_entries(voucher_type=self.doctype, voucher_no=self.name)



	def get_gl_entries(self, warehouse_account=None):
		self.expenses_included_in_valuation = self.get_company_default("expenses_included_in_valuation")
		self.negative_expense_to_be_booked = 0.0
		gl_entries = []

		self.make_supplier_gl_entry(gl_entries)
		self.make_item_gl_entries(gl_entries)
		self.make_tax_gl_entries(gl_entries)

		gl_entries = merge_similar_entries(gl_entries)

		self.make_payment_gl_entries(gl_entries)
		self.make_write_off_gl_entry(gl_entries)
		self.make_gle_for_rounding_adjustment(gl_entries)

		return gl_entries



@frappe.whitelist()
def convert_to_pi(source_name, target_doc=None, ignore_permissions=False):
	target_doc = get_mapped_doc("Indirect Expense", source_name,
		{"Indirect Expense": {
			"doctype": "Purchase Invoice",
			"field_map": {
				"company": "company",
				"supplier": "party",
				"due_date": "due_date",
				"invoice_date": "bill_date",
				"ref_number": "bill_no",
				"payment_terms_template": "payment_terms_template",
				"accounts_payable_account": "credit_to",
			}
		}}, target_doc)
	doc = frappe.get_doc("Indirect Expense", source_name)
	if doc.docstatus == 0 or doc.docstatus == 2:
		doc.delete()
	if doc.docstatus == 1:
		doc.cancel()
		doc.delete()
	return target_doc


@frappe.whitelist()
def make_payment_entry():
	pass


@frappe.whitelist()
def make_subscription():
	pass
