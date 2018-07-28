# -*- coding: utf-8 -*-
# Copyright (c) 2018, AgriTheory and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe
from frappe import _
import json
from erpnext.controllers.accounts_controller import AccountsController
from erpnext.accounts.party import get_due_date_from_template
from erpnext.accounts.utils import get_account_currency
from erpnext.accounts.general_ledger import make_gl_entries, get_round_off_account_and_cost_center
from frappe.model.mapper import get_mapped_doc
from erpnext.setup.utils import get_exchange_rate
from frappe.utils import flt, round_based_on_smallest_currency_fraction
from frappe.utils.data import fmt_money
from erpnext.accounts.utils import get_currency_precision


class IndirectExpense(AccountsController):
	def __init__(self, *args, **kwargs):
		super(IndirectExpense, self).__init__(*args, **kwargs)

	def validate(self):
		self.check_similar_invoice_number_and_amount()
		self.validate_multi_currency()
		self.set_amounts_in_company_currency()
		self.get_rounding()

	def on_submit(self):
		frappe.get_doc("Authorization Control").validate_approving_authority(self.doctype,
			self.company, self.amount_due)
		self.update_project()
		self.make_entries_to_gl()

	def on_cancel(self):
		self.make_entries_to_gl(cancel=True)
		self.update_project()

	def get_invoice_due_date(self):
		return get_due_date_from_template(template_name=self.payment_terms_template,
			posting_date=self.posting_date, bill_date=self.invoice_date)

	def get_payment_terms(self):
		ptt = frappe.db.get_value(self.party_type, self.party, "payment_terms")
		return ptt if ptt else ""

	def get_default_payables_account(self):
		if self.company:
			payables = frappe.db.get_value("Company", self.company, "default_payable_account")
			payables_account_currency = get_account_currency(payables)
			return {"payables": payables, "payables_account_currency": payables_account_currency}
		else:
			frappe.throw("Please set company before payables account.")

	def calc_exchange_rate(self):
		for row in self.entries:
			if row.account and row.amount and row.invoice_currency:
				if row.invoice_currency == self.payables_account_currency:
					row.exchange_rate = 1
					row.amount_in_payables_account_currency = row.amount
				elif row.invoice_currency != self.payables_account_currency:
					row.exchange_rate = get_exchange_rate(from_currency=row.invoice_currency,
						to_currency=self.payables_account_currency, transaction_date=self.posting_date)
					row.amount_in_payables_account_currency = row.amount * row.exchange_rate
					# fmt_money(row.amount, currency=row.invoice_currency)
				if not row.exchange_rate:
					frappe.throw(_("Row {0}: Exchange Rate is mandatory").format(row["idx"]))
		return "Done"

	def set_amounts_in_company_currency(self):
		for row in self.entries:
			row.amount_in_payables_account_currency = row.amount * row.exchange_rate

	def validate_multi_currency(self):
		alternate_currency = []
		for row in self.entries:
			account = frappe.db.get_value("Account", row.account, ["account_currency", "account_type"], as_dict=1)
			if account:
				row.account_currency = account.account_currency
				row.account_type = account.account_type
			if not row.account_currency:
				row.account_currency = self.payables_account_currency
			if row.account_currency != self.payables_account_currency and row.account_currency not in alternate_currency:
				alternate_currency.append(row.account_currency)
			self.calc_exchange_rate()

	def check_similar_invoice_number_and_amount(self):
		matching_invoices = frappe.db.sql(
			"""select name from `tabIndirect Expense` as t1
				where ref_number like %(invoice_no)s
				and party like %(party)s
				and docstatus = 1""",
			{"invoice_no": self.ref_number, "party": self.party}, as_dict=True)
		matching_pis = frappe.db.sql(
			"""select name from `tabPurchase Invoice` as t1
				where bill_no like %(invoice_no)s
				and supplier like %(party)s
				and docstatus = 1""",
			{"invoice_no": self.ref_number, "party": self.party}, as_dict=True)
		matches = ""
		for i in (matching_invoices + matching_pis):
			matches += str(matching_invoices[0].name) + " "
		if matching_invoices:
			frappe.msgprint("This entry might be duplicate based on the Invoice Number and Party: " +
				matches, "Duplicate Entry Warning", indicator="orange")

	def update_project(self):
		project_list = []
		if self.project:
			project_list.append(self.project)
		for row in self.entries:
			if row.project and row.project not in project_list:
				project = frappe.get_doc("Project", row.project)
				project.flags.dont_sync_tasks = True
				# project.update_purchase_costing()  # requires change to project.py
				# total_purchase_cost = frappe.db.sql("""select sum(base_net_amount)
				# 		from `tabPurchase Invoice Item` as t1, `tabIndirect Expense` as t2,
				# 		where t1.project = %s and t1.docstatus=1
				# 		and t2.project = %s and t2.docstatus=1""", self.name)
				project.save()
				project_list.append(row.project)

	def get_rounding(self):
		pass


################################################################################
	def make_entries_to_gl(self, cancel=False):
		gl_entries = []
		self.make_payable_gl_entry(gl_entries, cancel)
		self.make_expense_entries(gl_entries, cancel)
		self.make_gle_for_rounding_adjustment(gl_entries, cancel)
		if gl_entries:
			print(gl_entries)
			make_gl_entries(gl_entries, cancel=cancel, merge_entries=False)

	def make_expense_entries(self, gl_entries, cancel):
		for row in self.entries:
			gl_entries.append(
				self.get_gl_dict({
					"account": row.account,
					"debit": flt(row.amount, row.precision("amount")),
					"account_currency": self.payables_account_currency,
					"debit_in_account_currency": flt(row.amount_in_payables_account_currency,
						row.precision("amount_in_payables_account_currency")),
					"remarks": row.remark,
					"cost_center": row.cost_center,
					"project": row.project,
					"finance_book": self.finance_book,
				}, self.payables_account_currency))
		# if gl_entries:
		# 	print(gl_entries)
		# 	make_gl_entries(gl_entries, cancel=cancel, merge_entries=False)

	def make_payable_gl_entry(self, gl_entries, cancel):
		gl_entries.append(
			self.get_gl_dict({
				"account": self.accounts_payable_account,
				"party_type": self.party_type,
				"party": self.party,
				# "against": self.against_expense_account,
				"credit": self.amount_due,
				"credit_in_account_currency": self.amount_due,
			}, self.payables_account_currency))
		# if gl_entries:
		# 	print(gl_entries)
		# 	make_gl_entries(gl_entries, cancel=cancel, merge_entries=False)

	def make_gle_for_rounding_adjustment(self, gl_entries, cancel):
		if self.rounding_adjustment:
			round_off_account, round_off_cost_center = get_round_off_account_and_cost_center(self.company)
			gl_entries.append(
				self.get_gl_dict({
					"account": round_off_account,
					"against": self.supplier,
					"debit_in_account_currency": self.rounding_adjustment,
					"debit": self.base_rounding_adjustment,
					"cost_center": round_off_cost_center,
				}, self.payables_account_currency))
			# if gl_entries:
			# 	print(gl_entries)
			# 	make_gl_entries(gl_entries, cancel=cancel, merge_entries=False)

##################################################################################################


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
def map_to_payment_entry(source_name, target_doc=None, ignore_permissions=False):
	target_doc = get_mapped_doc("Indirect Expense", source_name,
		{"Indirect Expense": {
			"doctype": "Payment Entry",
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
	return target_doc


@frappe.whitelist()
def map_to_auto_repeat(source_name, target_doc=None, ignore_permissions=False):
	target_doc = get_mapped_doc("Indirect Expense", source_name,
		{"Indirect Expense": {
			"doctype": "Auto Repeat",
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
	return target_doc
