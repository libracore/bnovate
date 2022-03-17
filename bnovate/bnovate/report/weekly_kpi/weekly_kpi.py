# Copyright (c) 2022, libracore, bNovate and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from datetime import date, datetime, timedelta
from frappe import _
from erpnextswiss.erpnextswiss.common_functions import get_recursive_item_groups

def execute(filters=None):
    columns, data = [], []

    columns = get_columns()

    first_date = find_first_kw_start_date(filters.year)

    data = []
    year, week_num, day_of_week = date.today().isocalendar()
    if year != filters.year:
        week_num = 52
    totals = {'orders_confirmed': 0, 'instruments_qty': 0}
    for kw in range(0, (week_num + 1), 1):
        c_year, c_week, c_day = first_date.isocalendar()
        _data = get_values(first_date, first_date + timedelta(days=6))
        _data['week'] = "CW {0}".format(c_week)
        _data['start_date'] = first_date.date()
        totals['orders_confirmed'] += _data['orders_confirmed']
        _data['cum_orders_confirmed'] = totals['orders_confirmed']
        totals['instruments_qty'] += _data['instruments_qty']
        _data['cum_instruments_qty'] = totals['instruments_qty']
        data.append(_data)
        first_date = first_date + timedelta(days=7)

    # revert output
    output = []
    for d in range((len(data) - 1), -1, -1):
        output.append(data[d])
    return columns, output

def get_columns():
    return [
        {"label": _("Week"), "fieldname": "week", "fieldtype": "Data", "width": 50},
        {"label": _("Start"), "fieldname": "start_date", "fieldtype": "Date", "width": 80},
        {"label": _("Orders confirmed"), "fieldname": "orders_confirmed", "fieldtype": "Currency", "width": 120},
        {"label": _("Cum. orders"), "fieldname": "cum_orders_confirmed", "fieldtype": "Currency", "width": 120},
        {"label": _("Instruments"), "fieldname": "instruments_qty", "fieldtype": "Int", "width": 120},
        {"label": _("Cum. instruments"), "fieldname": "cum_instruments_qty", "fieldtype": "Int", "width": 120},
        {"label": "", "fieldname": "blank", "fieldtype": "Data", "width": 20}
    ]

def find_first_kw_start_date(year):
    sql_query="""SELECT DATE_ADD("{year}-01-01", INTERVAL (-WEEKDAY("{year}-01-01")) DAY) AS `date`;""".format(year=year)
    start_date = frappe.db.sql(sql_query, as_dict=True)[0]['date']
    return datetime.strptime(start_date, '%Y-%m-%d')

def get_values(from_date, to_date):
    # sales order volume KPI: only "Products and Services"
    orders_confirmed_item_groups = get_recursive_item_groups("Products and Services")
    
    sql_query = """SELECT
       IFNULL(SUM(`tabSales Order Item`.`amount`), 0) AS `orders_confirmed`
     FROM `tabSales Order Item`
     LEFT JOIN `tabSales Order` ON `tabSales Order`.`name` = `tabSales Order Item`.`parent`
     WHERE
       `tabSales Order`.`docstatus` = 1
       AND `tabSales Order`.`transaction_date` >= '{from_date}'
       AND `tabSales Order`.`transaction_date` <= '{to_date}'
       AND `tabSales Order Item`.`item_group` IN ({item_groups})""".format(
        from_date=from_date, to_date=to_date, 
        item_groups=", ".join("\"{0}\"".format(w) for w in orders_confirmed_item_groups))
    orders_confirmed = frappe.db.sql(sql_query, as_dict=True)[0]

    # instrument quantity KPI: only "Instruments"
    instruments_item_groups = get_recursive_item_groups("Instruments")
    
    sql_query = """SELECT
       IFNULL(SUM(`tabSales Order Item`.`qty`), 0) AS `instruments_qty`
     FROM `tabSales Order Item`
     LEFT JOIN `tabSales Order` ON `tabSales Order`.`name` = `tabSales Order Item`.`parent`
     WHERE
       `tabSales Order`.`docstatus` = 1
       AND `tabSales Order`.`transaction_date` >= '{from_date}'
       AND `tabSales Order`.`transaction_date` <= '{to_date}'
       AND `tabSales Order Item`.`item_group` IN ({item_groups})""".format(
        from_date=from_date, to_date=to_date, 
        item_groups=", ".join("\"{0}\"".format(w) for w in instruments_item_groups))
    instruments = frappe.db.sql(sql_query, as_dict=True)[0]
    
    # wrap into data row
    data = {
        'orders_confirmed': orders_confirmed['orders_confirmed'],
        'instruments_qty': instruments['instruments_qty']
    }
    
    return data
    

