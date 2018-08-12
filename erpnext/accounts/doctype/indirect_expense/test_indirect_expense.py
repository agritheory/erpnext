# -*- coding: utf-8 -*-
# Copyright (c) 2018, WHO Agency and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest
# from erpnext.accounts.doctype.doctype.indirect_expense import 

test_records = frappe.get_test_records('Indirect Expense')

class TestIndirectExpense(unittest.TestCase):
	def test_indirect_expense_split_account(self):
		ie = frappe.copy_doc(test_records[0])

		self.jv_against_voucher_testcase(base_jv, jv_invoice)


# test non-default AP account curency and conversion from default currency expense
# opposite of this
# split expense
# split cost center with same expense account
# induce rounding

# update Payment Entry Discount code to include Indirect Expense
# update project cost code (inline)
# update landed cost voucher
# update campaign costing report
