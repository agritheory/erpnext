# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

# import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def setup(patch=True):
	make_custom_fields()


def make_custom_fields():
	custom_fields = {
		'Supplier': [
			dict(fieldname='irs_1099', fieldtype='Check', insert_after='tax_id',
				label='Is IRS 1099 reporting required for supplier?')
		]
	}
	create_custom_fields(custom_fields)

# method to add print format for IRS 1099 report
