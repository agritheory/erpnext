// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Crop Cycle', {
	refresh: (frm) => {
		frm.add_custom_button(__("Harvest"), () => {
			harvestDialog.show()
			setTimeout()
			console.log(cur_dialog)
		})
		if (!frm.doc.__islocal){
			frm.add_custom_button(__('Reload Linked Analysis'), () => frm.call("reload_linked_analysis"));
		}

		frappe.realtime.on("List of Linked Docs", (output) => {
			let analysis_doctypes = ['Soil Texture', 'Plant Analysis', 'Soil Analysis'];
			let analysis_doctypes_docs = ['soil_texture', 'plant_analysis', 'soil_analysis'];
			let obj_to_append = {soil_analysis: [], soil_texture: [], plant_analysis: []};
			output['Land Unit'].forEach( (land_doc) => {
				analysis_doctypes.forEach( (doctype) => {
					output[doctype].forEach( (analysis_doc) => {
						let point_to_be_tested = JSON.parse(analysis_doc.location).features[0].geometry.coordinates;
						let poly_of_land = JSON.parse(land_doc.location).features[0].geometry.coordinates[0];
						if (is_in_land_unit(point_to_be_tested, poly_of_land)){
							obj_to_append[analysis_doctypes_docs[analysis_doctypes.indexOf(doctype)]].push(analysis_doc.name);
						}
					});
				});
			});
			frm.call('append_to_child', {
				obj_to_append: obj_to_append
			});
		});
	}
});

function is_in_land_unit(point, vs) {
	// ray-casting algorithm based on
	// http://www.ecse.rpi.edu/Homepages/wrf/Research/Short_Notes/pnpoly.html
	var x = point[0], y = point[1];
	var inside = false;
	for (var i = 0, j = vs.length - 1; i < vs.length; j = i++) {
		var xi = vs[i][0], yi = vs[i][1];
		var xj = vs[j][0], yj = vs[j][1];
		var intersect = ((yi > y) != (yj > y))
			&& (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
		if (intersect) inside = !inside;
	}
	return inside;
}


var harvestDialog = new frappe.ui.Dialog({
	'title': 'Harvest ' + cur_frm.doc.name +'?',
	'fields': [
		{'label': 'Harvest Item', 'fieldname': 'harvest_item', 'fieldtype': 'Link', 'options': 'Item'},
		{'label': 'Harvest Date','fieldname': 'harvest_date', 'fieldtype': 'Date', 'default': moment().date()},
		{'label': 'Estimate Remainder by','fieldname': 'estimate', 'fieldtype': 'Select', 'options': 'Estimate remainder by percent\nEstimate remainder by remaining yield'},
		{'fieldtype': 'Column Break'},
		{'label': 'Quantity','fieldname': 'qty', 'fieldtype': 'Float'},
		{'label': 'Estimated Percent Remaining','fieldname': 'est_remaining', 'fieldtype': 'Percent'},
		{'label': 'Estimated Yield Remaining','fieldname': 'est_remaining', 'fieldtype': 'Float'}
	],
	primary_action: function(frm){
		harvestDialog.hide();
		show_alert(harvestDialog.get_values());
	}
});

function harvest_items(values){
	frappe.call({
		method: "harvest_items",
		doc: frm.doc,
		args: values,
	}).done(() => {
		// success message
		console.log(r.message)
	}).fail((r) => {
		console.log(r);
	});
}
