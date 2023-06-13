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

    chart = None
    if filters.item_code and filters.warehouse:
        chart = get_chart(data)
    
    return columns, data, None, chart
    
def get_columns():
    return [
        {'fieldname': 'date', 'fieldtype': 'Date', 'label': _('Date'), 'width': 80},
        {'fieldname': 'doctype', 'fieldtype': 'Data', 'label': _('Doctype'), 'width': 100},
        {'fieldname': 'docname', 'fieldtype': 'Dynamic Link', 'label': _('Docname'), 'options': 'doctype', 'width': 100, 'align': 'left'},
        {'fieldname': 'item_code', 'fieldtype': 'Link', 'label': _('Item code'), 'options': 'Item', 'width': 250, 'align': 'left'},
        {'fieldname': 'warehouse', 'fieldtype': 'Link', 'label': _('Warehouse'), 'options': 'Warehouse', 'width': 100},
        {'fieldname': 'qty', 'fieldtype': 'Number', 'label': _('Qty'), 'width': 80}, 
        {'fieldname': 'projected_qty', 'fieldtype': 'Number', 'label': _('Projected Quantity'), 'width': 80}, 
        {'fieldname': 'guaranteed_qty', 'fieldtype': 'Number', 'label': _('Guaranteed Quantity'), 'width': 80}, 
        {'fieldname': 'stock_uom', 'fieldtype': 'Data', 'label': _('Unit'), 'width': 100}, 
    ]
    
def get_data(filters):
    sql_query = build_query(filters.so_drafts, filters.wo_drafts, filters.item_code, filters.warehouse)
    data = frappe.db.sql(sql_query, as_dict=True)

    return data

def build_query(so_drafts=False, wo_drafts=False, item_code=None, warehouse=None):
    item_filter = "true"
    warehouse_filter = "true"
    if item_code:
        item_filter = "e.item_code = '{}'".format(item_code)
    if warehouse:
        warehouse_filter = "e.warehouse = '{}'".format(warehouse)

    so_status = " = 1 " # Only submitted
    if so_drafts:
        so_status = " <= 1" # include drafts and submitted. 

    wo_status = " = 1 " # Only submitted
    if wo_drafts:
        wo_status = " <= 1" # include drafts and submitted. 

    return """
SELECT 
    e.date,
    e.doctype,
    e.docname,
    e.detail_doctype,
    e.detail_docname,
    e.item_code,
    i.item_name,
    i.stock_uom,
    e.warehouse,
    e.qty,
    ROUND(SUM(e.qty) OVER (
      PARTITION BY e.item_code, e.warehouse ORDER BY e.order_prio, e.date ASC, e.docname, e.idx
    ), 3) AS projected_qty,
    ROUND(SUM(IF(e.detail_doctype in ("Purchase Order Item", "Work Order"), 0, e.qty)) 
        OVER ( PARTITION BY e.item_code, e.warehouse ORDER BY e.order_prio, e.date ASC, e.docname, e.idx 
    ), 3) AS guaranteed_qty
FROM (
  (SELECT
    0 as order_prio, -- to keep stock balance as first item in list
    0 as idx,
    CURDATE() as date,
    'Stock Balance' as `doctype`,
    null as `docname`,
    null as `detail_docname`,
    null as `detail_doctype`,
    b.item_code,
    b.warehouse,
    b.actual_qty as qty
  FROM `tabBin` as b
) UNION ALL (
-- Sales Order: items to sell
  SELECT
    1 as order_prio,
    soi.idx as idx,
    soi.delivery_date as `date`,
    'Sales Order' as `doctype`,
    soi.parent as `docname`,
    soi.name as `detail_docname`,
    'Sales Order Item' as `detail_doctype`,
    soi.item_code,
    soi.warehouse,
    -(soi.qty - soi.delivered_qty) * soi.conversion_factor as qty
  FROM `tabSales Order Item` as soi
  JOIN `tabSales Order` as so ON so.name = soi.parent
  WHERE soi.delivered_qty < soi.qty
    AND soi.docstatus {so_status}
    AND so.status != 'Closed'
    AND (so._user_tags NOT LIKE "%template%" OR so._user_tags IS NULL)
) UNION ALL (
-- Packed items: items to sell inside bundles
  SELECT
    1 as order_prio,
    soi.idx as idx,  -- order according to parent item, so first item in SO 'reserves' its packed items as well
    soi.delivery_date as `date`,
    'Sales Order' as `doctype`,
    soi.parent as `docname`,
    pi.name as `detail_docname`,
    'Packed Item' as `detail_doctype`,
    pi.item_code,
    pi.warehouse,
  	ROUND(-(soi.qty - soi.delivered_qty) / soi.qty * pi.qty, 3) as qty -- soi conversion factor already calculated in packed item qty!
  FROM `tabPacked Item` as pi
  JOIN `tabSales Order` as so ON so.name = pi.parent
  JOIN `tabSales Order Item` as soi on soi.name = pi.parent_detail_docname
  WHERE soi.delivered_qty < soi.qty
    AND soi.docstatus {so_status}
    AND so.status != 'Closed'
    AND (so._user_tags NOT LIKE "%template%" OR so._user_tags IS NULL)
) UNION ALL (
-- Purchase Order: items to receive
  SELECT    
    1 as order_prio,
    poi.idx as idx,
    IFNULL(poi.expected_delivery_date, poi.schedule_date) as `date`,
    'Purchase Order' as `doctype`,
    poi.parent as `docname`,
    poi.name as `detail_docname`,
    'Purchase Order Item' as `detail_doctype`,
    poi.item_code,
    poi.warehouse,
    (poi.qty - poi.received_qty) * poi.conversion_factor as qty
  FROM `tabPurchase Order Item` as poi
  JOIN `tabPurchase Order` as po ON po.name = poi.parent
  WHERE poi.received_qty < poi.qty
    AND poi.docstatus = 1
    AND po.status != 'Closed'
) UNION ALL (
-- Work Orders: produced items
SELECT
    1 as order_prio,
    1 as idx,
    IFNULL(wo.expected_delivery_date, CAST(wo.planned_start_date AS date)) as `date`,
    "Work Order" as `doctype`,
    wo.name as `docname`,
    wo.name as `detail_docname`,
    'Work Order' as `detail_doctype`,
    wo.production_item as `item_code`,
    wo.fg_warehouse,
    wo.qty - wo.produced_qty as `qty`
FROM `tabWork Order` as wo
WHERE wo.docstatus {wo_status}
    AND wo.qty > wo.produced_qty
    AND wo.status != 'Stopped'
) UNION ALL (
-- Work Order Items: consumed items
SELECT
    1 as order_prio,
    woi.idx as idx,
    CAST(wo.planned_start_date AS date) as `date`,
    "Work Order" as `doctype`,
    wo.name as `docname`,
    woi.name as `detail_docname`,
    'Work Order Item' as `detail_doctype`,
    woi.item_code as `item_code`,
    woi.source_warehouse as `warehouse`,
    -(woi.required_qty - woi.consumed_qty) as `qty`
FROM `tabWork Order Item` as woi
JOIN `tabWork Order` as wo ON woi.parent = wo.name
WHERE wo.docstatus {wo_status} 
    AND wo.qty > wo.produced_qty
    AND wo.status != 'Stopped'
)) as e -- "entries"
JOIN `tabItem` as i on e.item_code = i.name
WHERE {item_filter} AND {warehouse_filter}
ORDER BY item_code, warehouse, order_prio, date ASC, docname, e.idx

    """.format(item_filter=item_filter, warehouse_filter=warehouse_filter, so_status=so_status, wo_status=wo_status)

def get_chart(data):
    
    if data is None:
        return None
    
    dates = [it['date'] for it in data]
    balance = [it['projected_qty'] for it in data]
    
    initial_stock = [ it['qty'] if it['doctype'] == 'Stock Balance' else 0 for it in data ]
    purchases = [ it['qty'] if it['doctype'] == 'Purchase Order' else 0 for it in data ]
    sales = [ it['qty'] if it['doctype'] == 'Sales Order' else 0 for it in data ]
    produced = [ it['qty'] if it['doctype'] == 'Work Order' else 0 for it in data ]
    
    chart = {
        "data": {
            "labels": dates,
            "datasets": [{
                "name": "Initial Stock",
                "values": initial_stock,
                "chartType": "bar",
            }, {
                "name": "Purchases",
                "values": purchases,
                "chartType": "bar",
            }, {
                "name": "Sales",
                "values": sales,
                "chartType": "bar",
            }, {
                "name": "Production",
                "values": produced,
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
            
    
        
    
