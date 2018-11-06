# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document


class Forecast(Document):
	def validate(self):
		# validate dates
		# create or modify repeats
		self.validate_items()
		self.make_weighted_total()

	def validate_items(self):
		if not self.items:
			self.omit_items = 1
		else:
			running_total = 0
			self.omit_items = 0
			for item in self.items:
				item.weighting = self.weighting
				item.weighted_amount = item.amount * self.calc_weighting()
				running_total = running_total + item.amount

	def make_weighted_total(self):
		self.weighted_total = self.total_amount * self.calc_weighting()

	def calc_weighting(self):
		if self.weighting == "90%":
			return .9
		elif self.weighting == "80%":
			return .8
		elif self.weighting == "70%":
			return .7
		elif self.weighting == "60%":
			return .6
		elif self.weighting == "50% or lower":
			return .5
		else:
			return .5

	def get_item_details(self, item):
		item = frappe.get_doc("Item", {"item_code": item})
		price_list = None
		for item_default in item.item_defaults:
			if item_default.company == self.company:
				price_list = item_default.default_price_list
				continue
		if not price_list:
			price_list = frappe.defaults.get_defaults()["selling_price_list"]
		price = frappe.db.sql(""" select price_list_rate
			from `tabItem Price`
			where item_code=%(item_code)s
			and price_list=%(price_list)s
			order by price_list_rate desc
			""",
			{"item_code": item.item_code, "price_list": price_list},
			as_dict=True)
		item_details = {"item_code": item.item_code, "item_name": item.item_name,
		"description": item.description, "item_group": item.item_group,
		"stock_uom": item.stock_uom, "uom": item.stock_uom,
		"rate": price[0]["price_list_rate"]}
		return item_details
