# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe import _
from frappe.utils import nowdate
from erpnext.accounts.utils import get_fiscal_year
from PyPDF2 import PdfFileWriter
from frappe.utils.print_format import read_multi_pdf


def execute(filters=None):
	if not filters:
		filters.setdefault('fiscal_year', get_fiscal_year(nowdate())[0])
		filters.setdefault('company', frappe.db.get_default("company"))
	data = []
	columns = get_columns()
	data = frappe.db.sql("""
		SELECT
			s.supplier_group as "supplier_group",
			gl.party AS "supplier",
			s.tax_id as "tax_id",
			SUM(gl.debit) AS "payments"
		FROM
			`tabGL Entry` gl INNER JOIN `tabSupplier` s
		WHERE
			s.name = gl.party
		AND	s.irs_1099 = 1
		AND gl.fiscal_year = %(fiscal_year)s
		AND gl.party_type = "Supplier"

		GROUP BY
			gl.party

		ORDER BY
			gl.party DESC""", {"fiscal_year": filters.fiscal_year,
				"supplier_group": filters.supplier_group,
				"company": filters.company}, as_dict=True)
	return columns, data


def get_columns():
	return [
		{
			"fieldname": "supplier_group",
			"label": _("Supplier Group"),
			"fieldtype": "Link",
			"options": "Supplier Group",
			"width": 160
		},
		{
			"fieldname": "supplier",
			"label": _("Supplier"),
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 160
		},
		{
			"fieldname": "tax_id",
			"label": _("Tax ID"),
			"fieldtype": "Data",
			"width": 80
		},
		{

			"fieldname": "payments",
			"label": _("Total Payments"),
			"fieldtype": "Currency",
			"options": "Supplier",
			"width": 80
		}
	]

@frappe.whitelist()
def irs_1099_print_format(filters):
	filters = json.loads(filters)
	columns, data = execute(filters)
	output = PdfFileWriter()
	for row in data:
		output = frappe.get_print("Supplier", row.name, print_format='IRS 1099', as_pdf=True, output=output)
	filecontent = read_multi_pdf(output)
