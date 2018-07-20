// Copyright (c) 2018, AgriTheory and contributors
// For license information, please see license.txt

{% include 'erpnext/public/js/controllers/buying.js' %};

frappe.ui.form.on("Indirect Expense", {
	onload: (frm) => {
		frm.set_value("party_type", "Supplier");
		get_default_payables_account(frm);
		set_queries (frm);
	},
	onload_post_render: (frm) => {
		setup_set_route(frm);
		get_default_payables_account(frm);
	},
	party: (frm) => {
		if(frm.doc.party_type == "Supplier")
			get_payment_terms(frm);
	},
	payment_terms_template: (frm) => {
		if(frm.doc.party_type == "Supplier")
			get_due_date(frm);
	},
	invoice_date: (frm) => {
		get_due_date(frm);
	},
	refresh: (frm) => {
		if(frm.doc.docstatus==0){
			frm.add_custom_button("Convert to Purchase Invoice", () => {
				// frm = cur_frm;
				route_to_pi(frm);
			});
		} else {
			frm.add_custom_button("Payment Entry", (frm) => {
				console.log("yay!");}, "Make");
			frm.add_custom_button("Subscription", (frm) => {
				console.log("yay!");}, "Make");
			frm.page.set_inner_btn_group_as_primary("Make");
		}
	}
});

frappe.ui.form.on("Indirect Expense Entry", {
	amount: (frm) => {
		update_total_due(frm);
	},
	entries_remove: (frm) => {
		update_total_due(frm);
	},
	entries_add: (frm) => {
		update_total_due(frm);
	}
});

function set_queries (frm) {
	frm.set_query("accounts_payable_account", () => {
		return {"filters": [
			{"account_type": "Payable"},
			{"company": frm.doc.company},
			{"is_group": 0}, ]};
	});
	frm.set_query("party_type", () => {
		return{
			"filters": {
				"name": ["in",["Supplier", "Employee"]],
			}
		};
	});
	frm.fields_dict["entries"].grid.get_field("cost_center").get_query = () => {
		return{
			filters: [ {"company": frm.doc.company},
				{"is_group": 0}]};
	};
	frm.fields_dict["entries"].grid.get_field("account").get_query = () => {
		return{
			filters: [{"company": frm.doc.company},
				{"is_group": 0},
				{"account_type": ["not in", ["Accumulated Depreciation", "Bank", "Cash",
					"Depreciation", "Equity", "Fixed Asset", "Income Account"]]}, ]};
	};
}

function get_default_payables_account(frm){
	frappe.call({
		method: "get_default_payables_account",
		doc: frm.doc
	}).done((r) => {
		frm.set_value("accounts_payable_account", r.message)
	}).fail((r) => {
		console.log(r);
	});
}

function get_payment_terms(frm) {
	frappe.call({
		method: "get_payment_terms",
		doc: frm.doc
	}).done((r) => {
		frm.set_value("payment_terms_template", r.message);
	}).fail((r) => {
		console.log(r);
	});
}

frappe.ui.form.on("Indirect Expense Entry", {
	amount_due: (frm) => {
		frm.set_value("outstanding_amount", frm.doc.amount_due);
	}
});

function update_total_due(frm) {
	let running_total = 0;
	for(let i in frm.doc.entries) {
		if(frm.doc.entries[i].amount != undefined){
			running_total += frm.doc.entries[i].amount;
		}
	}
	frm.doc.amount_due = running_total;
	frm.doc.outstanding_amount = running_total;
	frm.doc.grand_total = running_total;
	frm.doc.net_total = running_total;
	frm.doc.base_grand_total = running_total;
	frm.refresh_field("amount_due");
}

function get_due_date(frm){
	if(frm.doc.payment_terms_template != undefined && frm.doc.invoice_date)
		frappe.call({
			method: "get_invoice_due_date",
			doc: frm.doc,
		}).done((r) => {
			frm.set_value("due_date", r.message);
		}).fail((r) => {
			console.log(r);
		});
}

function route_to_pi(frm){
	let new_purchase_invoice = frappe.model.make_new_doc_and_get_name("Purchase Invoice");
	frappe.route_options =
		{ "company": frm.doc.company,
			"supplier": frm.doc.party,
			"due_date": frm.doc.due_date,
			"bill_date": frm.doc.invoice_date,
			"bill_no": frm.doc.ref_number,
			"payment_terms_template": frm.doc.payment_terms_template,
			"credit_to": frm.doc.accounts_payable_account,
			"items": frm.doc.accounts
		};
	frappe.set_route("Form", "Purchase Invoice", new_purchase_invoice);
}

function setup_set_route(frm){
	if(frappe.route_options != undefined){
		frm.set_value("party_type", "Supplier");
		frm.set_value("company", frappe.route_options.company);
		frm.set_value("party", frappe.route_options.party);
		frm.set_value("due_date", frappe.route_options.due_date);
		frm.set_value("invoice_date", frappe.route_options.invoice_date);
		frm.set_value("ref_number", frappe.route_options.ref_number);
		frm.set_value("payment_terms_template", frappe.route_options.payment_terms);
		frm.set_value("accounts_payable_account", frappe.route_options.credit_to);
		frappe.route_options = {};
	}
}
