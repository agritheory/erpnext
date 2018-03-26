# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cint
from frappe.model.document import Document


class AssetCategory(Document):
    def validate(self):
        if self.depreciation_method == "Non-Depreciable Asset":
            frappe.msgprint(_("Are you sure this is a non-depreciable asset?", "Warning"))
        for field in ("total_number_of_depreciations", "frequency_of_depreciation"):
            if cint(self.get(field)) < 1 and self.depreciation_method != "Non-Depreciable Asset":
                frappe.throw(_("{0} must be greater than 0").format(self.meta.get_label(field)), frappe.MandatoryError)
