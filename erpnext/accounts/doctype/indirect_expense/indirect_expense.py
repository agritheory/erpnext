# -*- coding: utf-8 -*-
# Copyright (c) 2018, AgriTheory and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe
from frappe import _
from six import iteritems
from frappe.model.document import Document
from erpnext.accounts.party import get_due_date, get_patry_tax_withholding_details
from erpnext.accounts.utils import get_account_currency
from erpnext import get_company_currency
from erpnext.accounts.general_ledger import make_gl_entries, delete_gl_entries
from erpnext.accounts.general_ledger import get_round_off_account_and_cost_center
from frappe.model.mapper import get_mapped_doc
from erpnext.setup.utils import get_exchange_rate
from erpnext.controllers import taxes_and_totals
from frappe.utils.data import nowdate
from frappe.utils import cint, flt, round_based_on_smallest_currency_fraction


class IndirectExpense(Document):
	def get_payment_terms(self):
		return frappe.db.get_value(self.party_type, self.party, "payment_terms")

	def validate(self):
		self.check_similar_invoice_number_and_amount()
		self.set_tax_withholding()
		# self.currency_conversion()

	def get_invoice_due_date(self):
		return get_due_date(self.payment_terms_template, self.posting_date, self.invoice_date)

	def get_default_payables_account(self):
		if self.company:
			return frappe.db.get_value("Company", self.company, "default_payable_account")
		else:
			frappe.throw("Please set company before payables account.")

	def on_submit(self):
		frappe.get_doc("Authorization Control").validate_approving_authority(self.doctype,
			self.company, self.base_grand_total)
		self.update_project()
		# make gl entries

	def currency_conversion(self):
		currencies = map(lambda x: x.invoice_currency if not self.company_currency else x.invoice_currency, self.entries)
		conversion_rate = map(lambda x: x.conversion_rate if not self.company_currency else x.conversion_rate, self.entries)
		if len(set(currencies)) > 1:
			frappe.throw(_("Only one Invoice Currency may be used per transaction"))
		elif len(set(conversion_rate)) > 1:
			frappe.throw(_("Currency Conversion rates are not consistient between accounts"))
		if self.check_conversion_rate(conversion_rate):
			round_off_account, round_off_cost_center = get_round_off_account_and_cost_center(self.company)
			self.rounding_adjustment = flt(self.total_due * conversion_rate, self.precision("total_due"))
			self.append("entries", {"account": round_off_account,
				"cost_center": round_off_cost_center,
				"amount": round_based_on_smallest_currency_fraction(self.rounding_adjustment, self.company_currency, self.precision("total_due")),
				"currency": self.company_currency})

	def check_conversion_rate(self, conversion_rate):
		default_currency = get_company_currency(self.company)
		if not default_currency:
			frappe.throw(_('Please enter default currency in Company Master'))
		elif (self.company_currency == default_currency and flt(conversion_rate) != 1.00) or not conversion_rate or (self.company_currency != default_currency and flt(conversion_rate) == 1.00):
				frappe.throw(_("Conversion rate cannot be 0 or 1"))
		else:
			return True

	def on_cancel(self):
		pass  # delete_gl_entries

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
				matches, "Warning Duplicate Entry", indicator="orange")

	def update_project(self):
		project_list = []
		for d in self.entries:
			if d.project and d.project not in project_list:
				project = frappe.get_doc("Project", d.project)
				project.flags.dont_sync_tasks = True
				# project.update_purchase_costing()  # requires change to project.py
				# total_purchase_cost = frappe.db.sql("""select sum(base_net_amount)
				# 		from `tabPurchase Invoice Item` as t1, `tabIndirect Expense` as t2,
				# 		where t1.project = %s and t1.docstatus=1
				# 		and t2.project = %s and t2.docstatus=1""", self.name)
				project.save()
				project_list.append(d.project)
				print(d.project + " updated")


################################################################################

	def set_tax_withholding(self):
		tax_withholding_details = get_patry_tax_withholding_details(self)
		for tax_details in tax_withholding_details:
			if flt(self.get("rounded_total") or self.grand_total) >= flt(tax_details['threshold']):
				if self.taxes:
					if tax_details['tax']['description'] not in [tax.description for tax in self.taxes]:
						self.append('taxes', tax_details['tax'])
				else:
					self.append('taxes', tax_details['tax'])

	def make_gl_entries(self, gl_entries=None, repost_future_gle=True, from_repost=False):
		if not self.amount_due:  # if there isn't a total, bail out
			return
		if not gl_entries:
			gl_entries = self.get_gl_entries()
		if gl_entries:
			make_gl_entries(gl_entries, cancel=(self.docstatus == 2), merge_entries=False)
		elif self.docstatus == 2:
			delete_gl_entries(voucher_type=self.doctype, voucher_no=self.name)

	def get_gl_entries(self):
		gl_entries = []
		self.make_supplier_gl_entry(gl_entries)
		self.make_payable_gl_entry(gl_entries)
		self.make_gle_for_rounding_adjustment(gl_entries)
		self.make_tax_gl_entries(gl_entries)
		return gl_entries

	def make_supplier_gl_entry(self, gl_entries):
		for row in self.entries:
			gl_entries.append(
				self.get_gl_dict({
					"account": row.account,
					"party_type": self.party,
					"party": self.party,
					"against": self.accounts_payable_account,
					"credit": self.total_due,
					"credit_in_account_currency": self.total_due,
				}, self.company_currency))

	def make_payable_gl_entry(self, gl_entries):
		gl_entries.append(
			self.get_gl_dict({
				"account": self.accounts_payable_account,
				"party_type": self.party,
				"party": self.party,
				"against": self.accounts_payable_account,
				"credit": self.total_due,
				"credit_in_account_currency": self.total_due,
			}, self.company_currency))

	def make_gle_for_rounding_adjustment(self, gl_entries):
		if self.rounding_adjustment:
			round_off_account, round_off_cost_center = get_round_off_account_and_cost_center(self.company)
			gl_entries.append(
				self.get_gl_dict({
					"account": round_off_account,
					"against": self.supplier,
					"debit_in_account_currency": self.rounding_adjustment,
					"debit": self.base_rounding_adjustment,
					"cost_center": round_off_cost_center,
				}))

	def make_tax_gl_entries(self, gl_entries):
		# tax table gl entries
		valuation_tax = {}
		for tax in self.get("taxes"):
			if tax.category in ("Total", "Valuation and Total") and flt(tax.base_tax_amount_after_discount_amount):
				account_currency = get_account_currency(tax.account_head)
				dr_or_cr = "debit" if tax.add_deduct_tax == "Add" else "credit"
				gl_entries.append(
					self.get_gl_dict({
						"account": tax.account_head,
						"against": self.supplier,
						dr_or_cr: tax.base_tax_amount_after_discount_amount,
						dr_or_cr + "_in_account_currency": tax.base_tax_amount_after_discount_amount if account_currency == self.company_currency else tax.tax_amount_after_discount_amount,
						"cost_center": tax.cost_center
					}, account_currency)
				)
			# accumulate valuation tax
			if self.is_opening == "No" and tax.category in ("Valuation", "Valuation and Total") and flt(tax.base_tax_amount_after_discount_amount):
				if self.auto_accounting_for_stock and not tax.cost_center:
					frappe.throw(_("Cost Center is required in row {0} in Taxes table for type {1}").format(tax.idx, _(tax.category)))
				valuation_tax.setdefault(tax.cost_center, 0)
				valuation_tax[tax.cost_center] += \
					(tax.add_deduct_tax == "Add" and 1 or -1) * flt(tax.base_tax_amount_after_discount_amount)

		if self.is_opening == "No" and self.negative_expense_to_be_booked and valuation_tax:
			# credit valuation tax amount in "Expenses Included In Valuation"
			# this will balance out valuation amount included in cost of goods sold

			total_valuation_amount = sum(valuation_tax.values())
			amount_including_divisional_loss = self.negative_expense_to_be_booked
			i = 1
			for cost_center, amount in iteritems(valuation_tax):
				if i == len(valuation_tax):
					applicable_amount = amount_including_divisional_loss
				else:
					applicable_amount = self.negative_expense_to_be_booked * (amount / total_valuation_amount)
					amount_including_divisional_loss -= applicable_amount

				gl_entries.append(
					self.get_gl_dict({
						"account": self.expenses_included_in_valuation,
						"cost_center": cost_center,
						"against": self.supplier,
						"credit": applicable_amount,
						"remarks": self.remarks or "Accounting Entry for Stock"
					})
				)

				i += 1

		if self.auto_accounting_for_stock and self.update_stock and valuation_tax:
			for cost_center, amount in iteritems(valuation_tax):
				gl_entries.append(
					self.get_gl_dict({
						"account": self.expenses_included_in_valuation,
						"cost_center": cost_center,
						"against": self.supplier,
						"credit": amount,
						"remarks": self.remarks or "Accounting Entry for Stock"
					})
				)

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
