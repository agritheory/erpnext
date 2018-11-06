# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import datetime
from frappe.utils import get_datetime, formatdate
from erpnext.accounts.utils import get_fiscal_year
from copy import deepcopy

# TODO: rows are not being initialized correctly
# TODO: add additional periodicity options
# TODO: sort item'd forecasts by item group
# TODO: add indent formatting



def execute(filters=None):
	columns, data = [], []
	period_list = get_periodicity(filters.from_date, filters.to_date, filters.periodicity)
	if filters.based_on == "Item":
		columns.append({"label": "Item", "fieldname": "item",
		"fieldtype": "Link", "width": 200, "options": "Item"})
	else:
		columns.append({"label": "Customer", "fieldname": "customer",
		"fieldtype": "Link", "width": 200})
	for period in period_list[:-1]:
		columns.append({"label": formatdate(period), "fieldname": formatdate(period),
		"fieldtype": "Currency", "width": 75})
	data = get_data(columns, period_list, filters)
	return columns, data


def get_periodicity(start_date, end_date, periodicity):
	start_date = get_datetime(start_date)
	end_date = get_datetime(end_date)
	if periodicity == "Weekly":
		return get_weeks(start_date, end_date)
	elif periodicity == "Monthly":
		return get_months(start_date, end_date)
	elif periodicity == "Quarterly":
		return get_quarters(start_date, end_date)
	elif periodicity == "Fiscal Year":
		# time comparison for greater than one year
		return get_fiscal_year(start_date, end_date)


def get_weeks(start_date, end_date):
	period = datetime.timedelta(days=7)
	weeks = []
	weeks.append(start_date.date())
	d = start_date + datetime.timedelta(days=(7 - start_date.weekday()))
	weeks.append(d.date())
	while d < end_date - period:
		weeks.append((d + period).date())
		d += period
	weeks.append(end_date.date())
	return weeks


def get_months(start_date, end_date):
	months = []
	months.append(start_date.date())
	d = start_date
	while d < end_date:
		if d.day == 1 and d != start_date:
			months.append(d.date())
		d += datetime.timedelta(days=1)
	months.append(end_date.date())
	return months


def get_quarters(start_date, end_date):
	quarters = []
	quarters.append(start_date.date())
	fiscal_year_start = get_fiscal_year(start_date)[1]
	# print(type(fiscal_year_start), type(start_date))
	next_quarter_start = fiscal_year_start
	while next_quarter_start < start_date.date():
		next_quarter_start = next_quarter_start.replace(month=(next_quarter_start.month + 3) % 12)
	d = next_quarter_start
	while d < end_date.date():
		d = d.replace(month=(d.month + 3) % 12)
		quarters.append(d.date())
	quarters.append(end_date.date())
	print(quarters)
	return quarters


def in_date_range(period_list, target_date):
	for i in range(0, len(period_list) - 1):
		if target_date >= period_list[i] and target_date <= period_list[i + 1]:
			return period_list[i]


def get_data(columns, period_list, filters):
	data = []
	row_schema = dict.fromkeys(map(lambda x: x["fieldname"], columns), 0)
	row_schema["indent"] = 0
	row_schema["parent"] = ""
	item_groups(data, row_schema)
	format_forecast(period_list, itemless_forecasts(period_list, filters), data, row_schema)
	format_forecast(period_list, item_forecasts(period_list, filters), data,
		row_schema, root="All Item Groups")
	return data


def itemless_forecasts(period_list, filters):
	return frappe.db.sql("""
		select name, item, start_date, weighted_total
		from `tabForecast`
		where start_date between %(period_start)s and %(period_end)s
		and company = %(company)s
		order by item asc
		""",
		{"period_start": period_list[0], "period_end": period_list[-1],
		"company": filters.company},
		as_dict=True)


def item_groups(data, row_schema):
	item_groups = frappe.db.sql("""
		select name, parent_item_group as parent
		from `tabItem Group`
		""", as_dict=True)
	for item_group in item_groups:
		row = deepcopy(row_schema)
		if item_group["name"] != "All Item Groups":
			row["item"] = item_group["name"]
		else:
			continue
		# indent("All Item Groups", row)
		data.append(row)


def item_forecasts(period_list, filters):
	return frappe.db.sql("""
		select t1.parent, t1.item_name as item, t1.item_group, t2.start_date,
		t1.weighted_amount as weighted_total
		from `tabForecast Item` t1 inner join `tabForecast` t2
		where t2.start_date between %(period_start)s and %(period_end)s
		and t2.company = %(company)s
		and t1.parent = t2.name
		order by item asc
		""",
		{"period_start": period_list[0], "period_end": period_list[-1],
		"company": filters.company},
		as_dict=True)


def forecast_auto_repeat(period_list, filters):
	weighting = frappe.db.get_value("Selling Settings", "forecast_auto_repeat")
	# get auto repeats in period


def forecast_subscriptions(period_list, filters):
	weighting = frappe.db.get_value("Selling Settings", "forecast_subscriptions")
	# get subscriptions in period


def format_forecast(period_list, forecast, data, row_schema, root=None):
	for i in forecast:
		period = in_date_range(period_list, i["start_date"])
		row = next((row for row in data if row["item"] == i["item"]), None)
		if row:
			row[formatdate(period)] =+ i["weighted_total"]
		else:
			row = deepcopy(row_schema)
			row["item"] = i["item"]
			row[formatdate(period)] = i["weighted_total"]
			data.append(row)
	# if not root:
	# 	return
	# else:
	# 	indent(root, forecast)


# def subtotal_item_groups():
# 	while item_group is not "All Item Groups":
# 		if accounts_obj[account].get(cost_center) is not None:
# 			accounts_obj[account][cost_center] += gle[amount_key]
# 			accounts_obj[account]["total"] += gle[amount_key]
# 		account = accounts_obj[account]["parent_account"]


# def trim_zerod_rows():



"""
Recursively formats indentation based on layers below "root".
Requires a field called "parent" to be present; this is mapped to
item_group from Forecast Item if items are present
"""


def indent(root, rows, indent=0):
	res = []
	for row in rows:
		if row["parent"] == root:
			row["indent"] = float(indent)
			res.append(row)
			res.extend(indent(row["name"], rows, indent + 1))
	return res
