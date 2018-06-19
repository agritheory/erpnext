# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.document import Document


class Work(Document):
	def validate(self):
		self.validate_dates()

	def validate_dates(self):
		if self.start_date and self.end_date:
			if self.start_date > self.end_date:
				frappe.throw(_("End Date cannot be before Start Date."))
