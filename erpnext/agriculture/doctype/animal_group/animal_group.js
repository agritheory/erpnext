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
	},
	member: (frm,cdt, cdn) => {
		if(locals[cdt][cdn].member_type == "Animal" || locals[cdt][cdn].member_type == "Animal"){
			get_animal_member_info(frm, cdt, cdn);
		}
	}
});

function get_animal_member_info(frm, cdt, cdn){
	frappe.call({
		method: "get_animal_member_info",
		doc: frm.doc,
		args: {"member_type": locals[cdt][cdn].member_type, "member": locals[cdt][cdn].member}
	}).done((r) => {
		console.log(r.message);
		if(Array.isArray(r.message) || r.message.length){
			// frm.set
		}
	}).fail((f) => {
		console.log("Failed on get_animal_member_info callback", f);
	});



}
