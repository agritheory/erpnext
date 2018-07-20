// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Animal Group', {
	refresh: (frm) => {

	}
});

frappe.ui.form.on("Animal Group Member", {
	refresh: (frm) => {
		frm.set_query("member_type", () => {
			return {
				"filters":
					["DocType", "name", "in", ["Animal", "Animal Group"]],
			};
		});
		frm.set_query("member", () => {
			return {
				"filters":
					[], // not a parent/ nested set?
			};
		});
	}
});
