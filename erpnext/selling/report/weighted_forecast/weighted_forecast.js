// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Weighted Forecast"] = {
	"filters": [
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1,
			"width": "60px"
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), 12),
			"reqd": 1,
			"width": "60px"
		},
		{
			"fieldname": "periodicity",
			"label": __("Periodicity"),
			"fieldtype": "Select",
			"options": [
				{ "value": "Weekly", "label": __("Weekly") },
				{ "value": "Monthly", "label": __("Monthly") },
				{ "value": "Quarterly", "label": __("Quarterly") },
				{ "value": "Fiscal Year", "label": __("Fiscal Year") }
			],
			"default": "Monthly",
			"reqd": 1
		},
		{
			"fieldname": "based_on",
			"label": __("Forecast Based On"),
			"fieldtype": "Select",
			"options": [
				{ "value": "Item", "label": __("Item Groups and Bundles") },
				{ "value": "Customer", "label": __("Customer, Sales Partner and Sales Person") }
			],
			"default": "Item",
			"reqd": 1
		},
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1
		},
		// {
		// 	"fieldname": "accumulated_values",
		// 	"label": __("Accumulated Values"),
		// 	"fieldtype": "Check"
		// }
	]
}
