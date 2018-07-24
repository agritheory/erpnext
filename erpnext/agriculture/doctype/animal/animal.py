# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class Animal(Document):
	def animal_name(self):
		print("animal name running")
		if not self.name:

			if self.animal_identifier and self.animal_id_number:
				self.name = self.animal_identifier + " - " + self.animal_id_number
			elif not self.animal_identifier and self.animal_id_number:
				self.name, self.animal_identifier = self.animal_id_number, self.animal_id_number
			elif self.animal_identifier:
				self.name = make_autoname(self.animal_identifier + " - ", ".#####")
			else:
				frappe.msgprint(_("Please enter either a Common Name or ID number for this animal"), raise_exception=1,
					title=_("Name or ID Required"), indicator='red')

	def validate(self):
		self.validate_purchased_animal()
		self.animal_name()

	def validate_purchased_animal(self):
		# if purchased, fields are mandatory
		if self.animal_origin == 'Purchased':
			if self.purchase_date is None:
				frappe.throw("Purchase Date is required for purchased animals.")
			if self.purchase_price == 0.00:
				frappe.throw("Purchase Price is required for purchased animals.")
			if self.purchase_price <= -0.01:
				frappe.throw("Purchase Price cannot be a negative number.")
		else:
			pass
