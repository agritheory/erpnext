// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Animal', {
	animal_origin: frm => {
		set_purchase_properties(frm);
	}
});

function set_purchase_properties(frm) {
	// Changes animal_origin section fields to required when 'Purchased'
	frm.set_df_property("purchase_date", "reqd", frm.doc.animal_origin == "Purchased");
	frm.set_df_property("purchased_from", "reqd", frm.doc.animal_origin == "Purchased");
	frm.set_df_property("purchase_price", "reqd", frm.doc.animal_origin == "Purchased");
}


// frm.set_df_property("purchase_price", "title", eval);
