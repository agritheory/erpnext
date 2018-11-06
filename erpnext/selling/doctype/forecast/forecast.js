// Copyright (c) 2018, AgriTheory and contributors
// For license information, please see license.txt

frappe.ui.form.on("Forecast", {
	based_on: frm => {
		change_inline_help(frm, "based_on", based_on_help[frm.doc.based_on]);
		change_fieldname_title(frm, "item", frm.doc.based_on);
	},
	qty: frm => {
		calculate_total(frm);
	},
	price: frm => {
		calculate_total(frm);
	},
	repeat: frm => {
		change_inline_help(frm, "repeat", repeat_help[frm.doc.repeat]);
	},
});

frappe.ui.form.on("Forecast Item", {
	item_code: (frm, cdt, cdn) => {
		get_item_details(frm, cdt, cdn);
	},
	rate: (frm, cdt, cdn) => {
		calculate_row_amount(frm, cdt, cdn);
		calculate_total(frm);
	},
	qty: (frm, cdt, cdn) => {
		calculate_row_amount(frm, cdt, cdn);
		calculate_total(frm);
	},
	items_remove: frm => {
		calculate_total(frm);
		frm.set_df_property("total_amount", "read_only", frm.doc.items.length > 0);
	},
	items_add: frm => {
		calculate_total(frm);
		frm.set_df_property("total_amount", "read_only", frm.doc.items.length > 0);
	}
});

function calculate_total(frm) {
	let running_total = 0;
	for(let i in frm.doc.items) {
		if(frm.doc.items[i].rate != undefined && frm.doc.items[i].qty != undefined){
			running_total += frm.doc.items[i].amount;
		}
	}
	frm.set_value("total_amount",  running_total);
}

function calculate_row_amount(frm, cdt, cdn){
	if(locals[cdt][cdn].rate != undefined && locals[cdt][cdn].qty != undefined){
		frappe.model.set_value(cdt, cdn, "amount", locals[cdt][cdn].rate * locals[cdt][cdn].qty);
	}
}

let based_on_help = {
	"Item": __("Specify the quantity of Items in the table below"),
	"Item Group": __("Specify the quantity of Items from this Item Group in their selling unit of measure"),
	"Product Bundle": __("Specify the quantity of Product Bundles in their selling unit of measure"),
	"Customer": __("Specify the amount in " + frappe.defaults.get_default("Currency") + " to this Customer"),
	"Sales Partner": __("Specify the amount in " + frappe.defaults.get_default("Currency") + " by this Sales Partner"),
	"Sales Person": __("Specify the amount in " + frappe.defaults.get_default("Currency") + " by this Sales Person")
};

let repeat_help = {
	"Single Instance": __("When saved, a single instance of this forecast will be created"),
	"Repeat": __("When saved, forecasts will be created in the date range"),
	"Distribute": __("When saved, forecasts will be created in the date range with the distribution percentage"),
};

function change_fieldname_title(frm, fieldname, new_title){
	frm.fields_dict[fieldname].set_label(new_title);
}

function change_inline_help(frm, fieldname, help){
	frm.fields_dict[fieldname].set_new_description(help);
}

function map_fields(frm, cdt, cdn, field_map){
	Object.entries(field_map).map(([field, value]) =>
		field_map.hasOwnProperty(field) ? frappe.model.set_value(cdt, cdn, field, value) : null);
}

function get_item_details(frm, cdt, cdn) {
	if(locals[cdt][cdn].item_code != undefined){
		frappe.call({
			method: "get_item_details",
			doc: frm.doc,
			args: {"item": locals[cdt][cdn].item_code}
		}).done((r) => {
			map_fields(frm, cdt, cdn, r.message);
		}).fail((f) => {
			console.log("Failed on get_item_price", f);
		});
	}
}
