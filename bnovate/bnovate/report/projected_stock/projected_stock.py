# Copyright (c) 2013-2022, bnovate, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import textwrap
import itertools
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    
    return columns, data, None, chart
    
def get_columns():
    return [
        {'fieldname': 'date', 'fieldtype': 'Date', 'label': _('Date'), 'width': 80},
        {'fieldname': 'doctype', 'fieldtype': 'Data', 'label': _('Doctype'), 'width': 100},
        {'fieldname': 'docname', 'fieldtype': 'Data', 'label': _('Docname'), 'width': 100},
        {'fieldname': 'item_code', 'fieldtype': 'Link', 'label': _('Item code'), 'options': 'Item', 'width': 300},
        {'fieldname': 'warehouse', 'fieldtype': 'Link', 'label': _('Warehouse'), 'options': 'Warehouse', 'width': 300},
        {'fieldname': 'qty', 'fieldtype': 'Int', 'label': _('Qty'), 'width': 100}, 
        {'fieldname': 'balance', 'fieldtype': 'Int', 'label': _('Stock balance'), 'width': 100}, 
    ]
    
def get_data(filters):
    
    if not filters.item_code or not filters.warehouse:
        return None
        
    sql_query = """
SELECT 
    e.date,
    e.doctype,
    e.docname,
    e.item_code,
    i.item_name,
    e.warehouse,
    e.qty,
    @running_total := @running_total + qty AS balance
FROM (
  (SELECT
	CURDATE() as date,
    'Stock Balance' as `doctype`,
    null as `docname`,
	b.item_code,
    b.warehouse,
    b.actual_qty as qty
  FROM `tabBin` as b
) UNION ALL (
  SELECT
	soi.delivery_date as `date`,
    'Sales Order' as `doctype`,
    soi.parent as `docname`,
	soi.item_code,
    soi.warehouse,
    -(soi.qty - soi.delivered_qty) as qty
  FROM `tabSales Order Item` as soi
  WHERE soi.delivered_qty < soi.qty
    AND soi.docstatus = 1
) UNION ALL (
  SELECT
	IFNULL(poi.expected_delivery_date, poi.schedule_date) as `date`,
    'Purchase Order' as `doctype`,
    poi.parent as `docname`,
	poi.item_code,
    poi.warehouse,
    (poi.qty - poi.received_qty) as qty
  FROM `tabPurchase Order Item` as poi
  WHERE poi.received_qty < poi.qty
    AND poi.docstatus = 1
)) as e -- "entries"
JOIN (SELECT @running_total := 0) r
JOIN `tabItem` as i on e.item_code = i.name
WHERE e.item_code = '{item_code}' AND e.warehouse = '{warehouse}'
ORDER BY date ASC
    """.format(item_code=filters.item_code, warehouse=filters.warehouse)
    
    data = frappe.db.sql(sql_query, as_dict=True)

    return data


def get_chart(data):
    
    if data is None:
        return None
    
    dates = [it['date'] for it in data]
    balance = [it['balance'] for it in data]
    
    purchases = [ it['qty'] if it['doctype'] == 'Purchase Order' else 0 for it in data ]
    sales = [ it['qty'] if it['doctype'] == 'Sales Order' else 0 for it in data ]
    
    chart = {
        "data": {
            "labels": dates,
            "datasets": [{
                "name": "Purchased",
                "values": purchases,
                "chartType": "bar",
            }, {
                "name": "Sold",
                "values": sales,
                "chartType": "bar",
            }, {
                "name": "Balance",
                "values": balance,
                "chartType": "line",
            }],
            "yMarkers": [{
                "label": "Stockout",
                "value": 0,
                "options": { "labelPos": 'left' }
            }],
        },
        "type": 'axis-mixed',
        "barOptions": {
            "stacked": True,
            "spaceRatio": 0.1,
        },

        "title": "Projected stock balance",
    }
    return chart
            
    
        
    
