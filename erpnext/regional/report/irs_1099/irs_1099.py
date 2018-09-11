# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import nowdate
from erpnext.accounts.utils import get_fiscal_year


def execute(filters=None):
	if not filters:
		filters.setdefault('fiscal_year', get_fiscal_year(nowdate())[0])
		filters.setdefault('company', frappe.db.get_default("company"))
	columns, data = [], []
	columns.append({"label": "Supplier", "fieldname": "supplier",
		"fieldtype": "Link", "width": 200, "options": "Supplier"},
		{"label": "Tax ID", "fieldname": "tax_id",
			"fieldtype": "Data", "width": 100},
		{"label": "Total Payments", "fieldname": "payments",
			"fieldtype": "Currency", "width": 100, "options": "Supplier"})

	data = frappe.db.sql("""
		SELECT
			gl.party AS "Supplier:Link/Supplier:100",
			SUM(gl.debit) AS "Total Payments:Currency:100"
		FROM
			`tabGL Entry` gl
		JOIN `tabSupplier` s ON s.name = gl.party
		WHERE
			s.irs_1099 = 1
		AND gl.fiscal_year = %(fiscal_year)s
		AND s.supplier_group = %(supplier_group)s
		AND gl.party_type = "Supplier"

		GROUP BY
			gl.party

		ORDER BY
			gl.party DESC""", {"fiscal_year": filters.fiscal_year,
				"supplier_group": filters.supplier_group,
				"company": filters.company}, as_dict=True)

	return columns, data
