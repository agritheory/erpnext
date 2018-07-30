# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
# from frappe.agriculture.ag_utils import get_animal_weight_and_uom

class AnimalGroup(Document):
	# def load_member_weight_and_uom(self, member_type, member):
	# 	doc = frappe.get_doc(member_type, member)
	# 	if doc.doctype == "Animal":
	#
	# 		weight = doc
	# 		w_uom = doc.
	pass

	def get_animal_member_info(self, member_type, member):
		pass
		# if member_type not in ["Animal", "Animal Group"]:
		# 	return
		# else:
		# 	m = frappe.get_doc(member_type, member)
		# 	if m.doctype == "Animal":
		# 		return {"":}
