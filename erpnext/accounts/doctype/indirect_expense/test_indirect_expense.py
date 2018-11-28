# -*- coding: utf-8 -*-
# Copyright (c) 2018, WHO Agency and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest
# from erpnext.accounts.doctype.doctype.indirect_expense import calc_exchange_rate


test_records = frappe.get_test_records('Indirect Expense')


class TestIndirectExpense(unittest.TestCase):
	def test_indirect_expense_split_account(self):
		ie = frappe.copy_doc(test_records[0])
		ie.save()
		ie.submit()
		submitted_ie = frappe.get_doc("Indirect Expense", ie.name)
		self.assertEqual(submitted_ie.amount_due, ie.amount_due)

	def test_indirect_expense_split_cost_center(self):
		ie = frappe.copy_doc(test_records[0])
		ie.entries[0].cost_center = "_Test Cost Center 2"
		ie.save()
		ie.submit()
		submitted_ie = frappe.get_doc("Indirect Expense", ie.name)
		self.assertEqual(submitted_ie.entries[0].cost_center, ie.ie.entries[0].cost_center)
		self.assertEqual(submitted_ie.entries[1].cost_center, ie.ie.entries[1].cost_center)

	def test_foreign_AP_account_curency(self):
		ie = frappe.copy_doc(test_records[0])
		ie.payables_account_currency = "USD"
		ie.save()
		ie.submit()
		submitted_ie = frappe.get_doc("Indirect Expense", ie.name)
		self.assertEqual(submitted_ie.rounding_adjustment, ie.rounding_adjustment)

	def test_rounding(self):
		self.create_foreign_currency_account()
		ie = frappe.copy_doc(test_records[1])
		ie.payables_account_currency = "CHF"
		ie.entries[0].amount_in_payables_account_currency = 100
		ie.entries[0].exchange_rate = 1.032
		ie.save()
		ie.submit()
		submitted_ie = frappe.get_doc("Indirect Expense", ie.name)
		self.assertEqual(submitted_ie.entries[0].cost_center, ie.ie.entries[0].cost_center)
		# assert on rounding_adjustment


def create_foreign_currency_account(self):
	if not frappe.db.exists("Account", "1299 - USA Payables - _TC"):
		acc = frappe.new_doc("Account")
		acc.account_name = "USA Payables"
		acc.parent_account = "Accounts Payable - _TC"
		acc.account_number = "1299"
		acc.company = "_Test Company"
		acc.insert()





# TODO: update Payment Entry Discount code to include Indirect Expense
# TODO: update project cost code (inline)
# TODO: update landed cost voucher
# TODO: update campaign costing report
