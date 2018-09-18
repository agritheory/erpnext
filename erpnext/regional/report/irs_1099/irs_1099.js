// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.query_reports["IRS 1099"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1,
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname":"fiscal_year",
			"label": __("Fiscal Year"),
			"fieldtype": "Link",
			"options": "Fiscal Year",
			"default": frappe.defaults.get_user_default("fiscal_year"),
			"width": "80",
			"reqd": 1,
		},
		{
			"fieldname":"supplier_group",
			"label": __("Supplier Group"),
			"fieldtype": "Link",
			"options": "Supplier Group",
			"default": "",
			"width": "80"
		},
	],

	onload: function(query_report) {
		query_report.page.add_inner_button(__("IRS 1099 Form PDF Bulk"), () => {
			build_1099_print(query_report);


		})
	}
};

function build_1099_print(query_report){
	frappe.call({
		method: "erpnext.regional.report.irs_1099.irs_1099.irs_1099_print_format",
		args: {"filters": query_report.get_values()}
	}).done(() => {
	}).fail((f) => {
		console.log(f);
	});
}
