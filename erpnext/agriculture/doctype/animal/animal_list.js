frappe.listview_settings["Animal"] = {
	add_fields: ["animal_status"],
	get_indicator: function(doc) {
		return [__(doc.animal_status), indicate_animal_status(doc.animal_status), "status,=," + doc.status];
	}
};

function indicate_animal_status(status){
	switch(status) {
		case "Deceased":
			return "black";
		case "Processed":
			return "purple";
		case "Sold":
			return "yellow";
		default:
			return "green";
	}
}
