# Copyright (c) 2013, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import textwrap
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    message = "Test message"
    chart = get_chart(filters)
    
    return columns, data, message, chart

def get_columns():
    return [
        {'fieldname': 'weeknum', 'fieldtype': 'Int', 'label': _('Week'), 'width': 80},
        {'fieldname': 'parent', 'fieldtype': 'Link', 'label': _('Parent'), 'options': 'Sales Order', 'width': 100},
        {'fieldname': 'customer_name', 'fieldtype': 'Link', 'label': _('Customer'), 'options': 'Customer', 'width': 150},
        {'fieldname': 'delivery_date', 'fieldtype': 'Date', 'label': _('Ship date'), 'width': 80},
        # {'fieldname': 'qty', 'fieldtype': 'Int', 'label': _('Qty Ordered'), 'width': 100}, 
        {'fieldname': 'remaining_qty', 'fieldtype': 'Int', 'label': _('Qty to Deliver'), 'width': 100}, 
        {'fieldname': 'item_code', 'fieldtype': 'Link', 'label': _('Item code'), 'options': 'Item', 'width': 300},
        # {'fieldname': 'item_name', 'fieldtype': 'Data', 'label': _('Item name'), 'width': 300},
        {'fieldname': 'item_group', 'fieldtype': 'Link', 'label': _('Item group'), 'options': 'Item Group', 'width': 150},
        # {'fieldname': 'item_group', 'fieldtype': 'Data', 'label': _('Item group'), 'width': 300},
        # {'fieldname': 'status', 'fieldtype': 'Data', 'label': _('Status'), 'width': 100}
    ]
    
def get_data(filters):
    
    extra_filters = ""
    if filters.only_manufacturing:
        extra_filters += "AND it.include_item_in_manufacturing = 1"
    
    sql_query = """
SELECT 
	WEEK(soi.delivery_date) as weeknum,
    soi.parent as parent,
    so.customer_name as customer_name,
    soi.qty as qty,
    (soi.qty - soi.delivered_qty) AS remaining_qty,
    soi.delivery_date as delivery_date,
    soi.item_code as item_code,
    it.item_name as item_name,
    it.item_group as item_group
FROM `tabSales Order Item` as soi
JOIN `tabSales Order` as so ON soi.parent = so.name
JOIN `tabItem` as it on soi.item_code = it.name
WHERE
	so.docstatus = 1 AND 
    so.per_delivered < 100 AND
    soi.qty > soi.delivered_qty AND
    so.status != 'Closed'
    {extra_filters}
ORDER BY soi.delivery_date ASC
    """.format(extra_filters=extra_filters)

    data = frappe.db.sql(sql_query, as_dict=True)
    
    return data


def get_chart(filters):
    
    extra_filters = ""
    if filters.only_manufacturing:
        extra_filters += "AND it.include_item_in_manufacturing = TRUE"
        
    sql_query = """
SELECT
    WEEK(soi.delivery_date) as weeknum,
    SUBDATE(soi.delivery_date, WEEKDAY(soi.delivery_date)) as week,
    soi.qty - soi.delivered_qty AS remaining_qty,
    it.item_group as item_group
FROM `tabSales Order Item` as soi
JOIN `tabSales Order` as so ON soi.parent = so.name
JOIN `tabItem` as it on soi.item_code = it.name
WHERE
	so.docstatus = 1 AND 
    so.status != 'Closed' AND
    soi.qty > soi.delivered_qty
    {extra_filters}
GROUP BY week, item_group
ORDER BY week ASC
    """.format(extra_filters=extra_filters)
    
    data = frappe.db.sql(sql_query, as_dict=True)
    
    # Build dict of dict, that store the sum of items in each group, each week.
    weeks = sorted(set([it['week'] for it in data]))
    groups = sorted(set([it['item_group'] for it in data]))
    plotdata = {}

    for g in groups:
        plotdata[g] = {}
        for w in weeks:
            plotdata[g][w] = 0

    for item in data:
        week, group, qty = item['week'], item['item_group'], item['remaining_qty']
        plotdata[group][week] += qty

    # Convert to format expected by Frappe charts
    datasets = []
    for group in plotdata.keys():
        datasets.append({
            "name": ellipsis(group, 12),
            "values": plotdata[group].values(),
        })
    
    chart = {
        "data": {
            "labels": [w.strftime("%Y-%m-%e (week %V)") for w in weeks],
            "datasets": datasets,
        },
        "type": 'bar',
        "barOptions": {"stacked": True},
        "title": "Total items per week",
    }
    return chart
    
    
### Helpers

def ellipsis(text, length=10):
    if len(text) <= length:
        return text
    return text[:int(length/2)-1] + "…" + text[-int(length/2):]
