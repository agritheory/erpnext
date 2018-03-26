// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt
/* try {
	frappe.require("/assets/erpnext/css/frappe-datatable.css");
	console.log("datatable css success");
} catch(err) {console.log("datatable css", err)}
try {
frappe.provide("/assets/erpnext/js/lodash.js");
console.log("datatable lodash success");
} catch(err) {console.log("lodash", err)}
try {
frappe.provide("/assets/erpnext/js/Sortable.min.js");
console.log("datatable Sortable success");
} catch(err) {console.log("Sortable", err)}
try {
frappe.provide("/assets/erpnext/js/clusterize.min.js");
console.log("datatable clusterize success");
} catch(err) {console.log("clusterize", err)}
try {
frappe.provide("/assets/erpnext/js/frappe-datatable.js");
console.log("datatable datatable success");
} catch(err) {console.log("datatable js", err)}


frappe.require("/assets/erpnext/css/frappe-datatable.css");
frappe.provide("/assets/erpnext/js/lodash.js");
frappe.provide("/assets/erpnext/js/Sortable.min.js");
frappe.provide("/assets/erpnext/js/clusterize.min.js");
frappe.provide("/assets/erpnext/js/frappe-datatable.js");
*/

/* Custom Datatables*/
frappe.require("/assets/swimventory/css/frappe-datatable.css");
frappe.require("/assets/swimventory/js/lodash.js");
frappe.require("/assets/swimventory/js/Sortable.min.js");
frappe.require("/assets/swimventory/js/clusterize.min.js");
frappe.require("/assets/swimventory/js/frappe-datatable.js");

frappe.ui.form.on("Bank Reconciliation Datatable", {
	setup: function(frm) {
		frm.add_fetch("bank_account", "account_currency", "account_currency");
	},
	onload: function(frm) {
		let default_bank_account =  frappe.defaults.get_user_default("Company")?
			locals[":Company"][frappe.defaults.get_user_default("Company")]["default_bank_account"]: "";
		frm.set_value("bank_account", default_bank_account);
		frm.set_query("bank_account", function() {
			return {
				"filters": {
					"account_type": ["in",["Bank","Cash"]],
					"is_group": 0
				}
			};
		});
		frm.set_value("from_date", frappe.datetime.month_start());
		frm.set_value("to_date", frappe.datetime.month_end());
	},
	refresh: function(frm) {
		frm.disable_save();
		render_datatable(frm);
	},
	beginning_bank_balance: function(frm) {
		calculate_difference(frm);
	},
	ending_bank_balance: function(frm) {
		calculate_difference(frm);
	},
	update_clearance_date: function(frm) {
		return frappe.call({
			method: "update_clearance_date",
			doc: frm.doc,
			callback: function(r, rt) {
				frm.refresh_field("payment_entries");
				frm.refresh_fields();
			}
		});
	},
	get_payment_entries: function(frm) {
		return frappe.call({
			method: "get_payment_entries",
			doc: frm.doc,
			callback: function(r, rt) {
				frm.refresh_field("payment_entries");
				$(frm.fields_dict.payment_entries.wrapper).find("[data-fieldname=amount]").each(function(i,v){
					if (i !=0){
						$(v).addClass("text-right");
					}
				});
			}
		});
	},
	onload_post_render: function(frm) {
		get_account_currency(frm);
		get_oldest_uncleared(frm);
		get_book_balance(frm);
	}, from_date: function(frm) {
		get_book_balance(frm);
	}, to_date: function(frm) {
		get_book_balance(frm);
	}
});

function get_account_currency(frm) {
	frappe.call({
		method: "get_account_currency",
		doc: frm.doc,
	}).done(() => {
		frm.refresh_field("account_currency");
	}).fail((r) => {
		console.log(r);
	});
}

function get_book_balance(frm) {
	frappe.call({
		method: "get_balances",
		doc: frm.doc,
	}).done(() => {
		frm.refresh_field("beginning_book_balance");
		frm.refresh_field("ending_book_balance");
	}).fail((r) => {
		console.log(r);
	});
}

function get_oldest_uncleared(frm) {
	frappe.call({
		method: "get_oldest_uncleared",
		doc: frm.doc,
	}).done(() => {
		frm.refresh_field("oldest_uncleared");
	}).fail((r) => {
		console.log(r);
	});
}

function render_datatable(frm) {
	console.log("render_datatable");
	let data = [];
	let columns = [];
	let largeData = false;

	function buildData() {
		console.log("buildData");

		data = [[ "Tiger Nixon", {content: "System Architect", editable: false}, "Edinburgh", "5421", "2011/04/25", "$320,800", "" ], [ "Garrett Winters", "Accountant", "Tokyo", "8422", "2011/07/25", "$170,750", "" ], [ "Ashton Cox", "Junior Technical Author", "San Francisco", "1562", "2009/01/12", "$86,000", "" ], [ "Cedric Kelly", "Senior Javascript Developer", "Edinburgh", "6224", "2012/03/29", "$433,060", "" ], [ "Airi Satou", "Accountant", "Tokyo", "5407", "2008/11/28", "$162,700", "" ], [ "Brielle Williamson", "Integration Specialist", "New York", "4804", "2012/12/02", "$372,000", "" ], [ "Herrod Chandler", "Sales Assistant", "San Francisco", "9608", "2012/08/06", "$137,500", "" ], [ "Rhona Davidson", "Integration Specialist", "Tokyo", "6200", "2010/10/14", "$327,900", "" ], [ "Colleen Hurst", "Javascript Developer", "San Francisco", "2360", "2009/09/15", "$205,500", "" ], [ "Sonya Frost", "Software Engineer", "Edinburgh", "1667", "2008/12/13", "$103,600", "" ], [ "Jena Gaines", "Office Manager", "London", "3814", "2008/12/19", "$90,560", "" ], [ "Quinn Flynn", "Support Lead", "Edinburgh", "9497", "2013/03/03", "$342,000", "" ], [ "Charde Marshall", "Regional Director", "San Francisco", "6741", "2008/10/16", "$470,600", "" ], [ "Haley Kennedy", "Senior Marketing Designer", "London", "3597", "2012/12/18", "$313,500", "" ], [ "Tatyana Fitzpatrick", "Regional Director", "London", "1965", "2010/03/17", "$385,750", "" ], [ "Michael Silva", "Marketing Designer", "London", "1581", "2012/11/27", "$198,500", "" ], [ "Paul Byrd", "Chief Financial Officer (CFO)", "New York", "3059", "2010/06/09", "$725,000", "" ], [ "Gloria Little", "Systems Administrator", "New York", "1721", "2009/04/10", "$237,500", "" ], [ "Bradley Greer", "Software Engineer", "London", "2558", "2012/10/13", "$132,000", "" ], [ "Dai Rios", "Personnel Lead", "Edinburgh", "2290", "2012/09/26", "$217,500", "" ], [ "Jenette Caldwell", "Development Lead", "New York", "1937", "2011/09/03", "$345,000", "" ], [ "Yuri Berry", "Chief Marketing Officer (CMO)", "New York", "6154", "2009/06/25", "$675,000", "" ], [ "Caesar Vance", "Pre-Sales Support", "New York", "8330", "2011/12/12", "$106,450", "" ], [ "Doris Wilder", "Sales Assistant", "Sidney", "3023", "2010/09/20", "$85,600", "" ], [ "Angelica Ramos", "Chief Executive Officer (CEO)", "London", "5797", "2009/10/09", "$1,200,000", "" ], [ "Gavin Joyce", "Developer", "Edinburgh", "8822", "2010/12/22", "$92,575", "" ], [ "Jennifer Chang", "Regional Director", "Singapore", "9239", "2010/11/14", "$357,650", "" ], [ "Brenden Wagner", "Software Engineer", "San Francisco", "1314", "2011/06/07", "$206,850", "" ], [ "Fiona Green", "Chief Operating Officer (COO)", "San Francisco", "2947", "2010/03/11", "$850,000", "" ], [ "Shou Itou", "Regional Marketing", "Tokyo", "8899", "2011/08/14", "$163,000", "" ], [ "Michelle House", "Integration Specialist", "Sidney", "2769", "2011/06/02", "$95,400", "" ], [ "Suki Burks", "Developer", "London", "6832", "2009/10/22", "$114,500", "" ], [ "Prescott Bartlett", "Technical Author", "London", "3606", "2011/05/07", "$145,000", "" ], [ "Gavin Cortez", "Team Leader", "San Francisco", "2860", "2008/10/26", "$235,500", "" ], [ "Martena Mccray", "Post-Sales support", "Edinburgh", "8240", "2011/03/09", "$324,050", "" ], [ "Unity Butler", "Marketing Designer", "San Francisco", "5384", "2009/12/09", "$85,675", "" ], [ "Howard Hatfield", "Office Manager", "San Francisco", "7031", "2008/12/16", "$164,500", "" ], [ "Hope Fuentes", "Secretary", "San Francisco", "6318", "2010/02/12", "$109,850", "" ], [ "Vivian Harrell", "Financial Controller", "San Francisco", "9422", "2009/02/14", "$452,500", "" ], [ "Timothy Mooney", "Office Manager", "London", "7580", "2008/12/11", "$136,200", "" ], [ "Jackson Bradshaw", "Director", "New York", "1042", "2008/09/26", "$645,750", "" ], [ "Olivia Liang", "Support Engineer", "Singapore", "2120", "2011/02/03", "$234,500", "" ], [ "Bruno Nash", "Software Engineer", "London", "6222", "2011/05/03", "$163,500", "" ], [ "Sakura Yamamoto", "Support Engineer", "Tokyo", "9383", "2009/08/19", "$139,575", "" ], [ "Thor Walton", "Developer", "New York", "8327", "2013/08/11", "$98,540", "" ], [ "Finn Camacho", "Support Engineer", "San Francisco", "2927", "2009/07/07", "$87,500", "" ], [ "Serge Baldwin", "Data Coordinator", "Singapore", "8352", "2012/04/09", "$138,575", "" ], [ "Zenaida Frank", "Software Engineer", "New York", "7439", "2010/01/04", "$125,250", "" ], [ "Zorita Serrano", "Software Engineer", "San Francisco", "4389", "2012/06/01", "$115,000", "" ], [ "Jennifer Acosta", "Junior Javascript Developer", "Edinburgh", "3431", "2013/02/01", "$75,650", "" ], [ "Cara Stevens", "Sales Assistant", "New York", "3990", "2011/12/06", "$145,600", "" ], [ "Hermione Butler", "Regional Director", "London", "1016", "2011/03/21", "$356,250", "" ], [ "Lael Greer", "Systems Administrator", "London", "6733", "2009/02/27", "$103,500", "" ], [ "Jonas Alexander", "Developer", "San Francisco", "8196", "2010/07/14", "$86,500", "" ], [ "Shad Decker", "Regional Director", "Edinburgh", "6373", "2008/11/13", "$183,000", "" ], [ "Michael Bruce", "Javascript Developer", "Singapore", "5384", "2011/06/27", "$183,000", "" ], [ "Donna Snider", "Customer Support", "New York", "4226", "2011/01/25", "$112,000", "" ]];
		return data
	}

	function makeDatatable() {
		console.log('No of Rows:', data.length)

		const start = performance.now();
		var datatable = new DataTable(document.querySelector('#datatable'), {
			addCheckboxColumn: true,
			addSerialNoColumn: true,
			enableClusterize: true,
			layout: 'fluid',
			data: buildData(),
			columns: ["Name", {content: "Position", width: 120}, "Office", "Extn.", "Start Date", "Salary", { content: "Blank", focusable: false, resizable: false }],
			enableInlineFilters: true,
			getEditor(colIndex, rowIndex, value, parent) {
				// editing obj only for date field
				if (colIndex != 6) return;

				const $input = document.createElement('input');
				$input.type = 'date';
				parent.appendChild($input);

				const parse = value => value.replace(/\//g, '-');
				const format = value => value.replace(/\-/g, '/');

				return {
					initValue(value) {
						$input.focus();
						$input.value = parse(value);
					},
					setValue(value) {
						$input.value = parse(value);
					},
					getValue() {
						return format($input.value);
					}
				}
			}
		});
		console.log("window");
		window.datatable = datatable;
	}
	makeDatatable();

}

function calculate_difference(frm) {
	frm.doc.difference = (frm.doc.beginning_book_balance - frm.doc.ending_book_balance) - (frm.doc.beginning_bank_balance - frm.doc.ending_bank_balance)
	frm.refresh_field("difference");
}
