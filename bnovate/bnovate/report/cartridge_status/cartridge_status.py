# Copyright (c) 2013, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

from erpnext.stock.doctype.serial_no.serial_no import get_serial_nos

from operator import attrgetter

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    
    return columns, data

def get_columns():
    return [
        {'fieldname': 'serial_no', 'fieldtype': 'Link', 'label': _('Serial No'), 'options': 'Serial No', 'width': 100},
        {'fieldname': 'compatibility', 'fieldtype': 'Data', 'label': _('Compatibility'), 'width': 150, 'align': 'left'}, 
        {'fieldname': 'type', 'fieldtype': 'Data', 'label': _('Type'), 'width': 150}, 
        {'fieldname': 'status', 'fieldtype': 'Data', 'label': _('Status'), 'width': 150}, 
        {'fieldname': 'storage_location', 'fieldtype': 'Link', 'label': _('Shelf'), 'options': 'Storage Location', 'width': 80, 'align': 'left'},
        {'fieldname': 'storage_slot', 'fieldtype': 'Link', 'label': _('Slot'), 'options': 'Storage Slot', 'width': 70, 'align': 'left'},

        {'fieldname': 'warehouse', 'fieldtype': 'Link', 'label': _('Warehouse'), 'options': 'Warehouse', 'width': 100},
        {'fieldname': 'posting_date', 'fieldtype': 'Date', 'label': _('Since date'), 'width': 80},
        {'fieldname': 'owned_by', 'fieldtype': 'Link', 'label': _('Owned by Customer'), 'options': 'Customer', 'width': 120},
        {'fieldname': 'customer_name', 'fieldtype': 'Data', 'label': _('Customer Name'), 'width': 300, 'align': 'left'}, 

        {'fieldname': 'refill_request', 'fieldtype': 'Link', 'label': _('Refill Request'), 'options': 'Refill Request', 'width': 100, 'align': 'left'}, 
        {'fieldname': 'open_sales_order', 'fieldtype': 'Link', 'label': _('Sales Order'), 'options': 'Sales Order', 'width': 220, 'align': 'left'}, 
        {'fieldname': 'work_order', 'fieldtype': 'Link', 'label': _('Work Order'), 'options': 'Work Order', 'width': 200, 'align': 'left'}, 
        {'fieldname': 'woe', 'fieldtype': 'Link', 'label': _('Manufacturing Stock Entry'), 'options': 'Work Order', 'width': 200, 'align': 'left'}, 

        {'fieldname': 'shipping_address', 'fieldtype': 'Text', 'label': _('Shipping Address'), 'width': 150, 'align': 'left'}, 
        {'fieldname': 'tracking_link', 'fieldtype': 'Data', 'label': _('Tracking No'), 'width': 100, 'align': 'left'}, 

        {'fieldname': 'location', 'fieldtype': 'Data', 'label': _('Location'), 'width': 150}, 
        # {'fieldname': 'item_code', 'fieldtype': 'Link', 'label': _('Item'), 'options': 'Item', 'width': 100},
        {'fieldname': 'docname', 'fieldtype': 'Dynamic Link', 'label': _('Transfer doc'), 'options': 'doctype', 'width': 100}, 
        {'fieldname': 'order_status', 'fieldtype': 'Data', 'label': _('Order Status'), 'width': 150, 'align': 'left'}, 
    ]

def get_data(filters):
    extra_filters = ""
    if filters.customer:
        if type(filters.customer) == str:
            filters.customer = [filters.customer]
        customers = '("' + '", "'.join(filters.customer) + '")'
        extra_filters += '\nAND sn.owned_by IN {}'.format(customers)
    
    if filters.only_stored:
        extra_filters += '\nAND sn.warehouse IN ("Repairs - bN", "To Refill - bN", "Finished Goods - bN")'

    if filters.serial_no:
        if type(filters.serial_no) == str:
            if "," in filters.serial_no or "\n" in filters.serial_no:  # Then it came from a data- tag.
                filters.serial_no = get_serial_nos(filters.serial_no)
            else:
                filters.serial_no = [filters.serial_no.strip()]
        serial_nos = '("' + '", "'.join(filters.serial_no) + '")'
        extra_filters += '\nAND sn.serial_no IN {0}'.format(serial_nos)

    # Like this the strings are picked up:
    translations_hack = [_("Shipped to Customer")]

    sql_query = """
        WITH items AS (
            SELECT
                it.name,
                it.item_name,
                it.short_name,
                it.item_group,
                GROUP_CONCAT(itc.label) as compatibility
            FROM `tabItem` as it
            LEFT JOIN `tabItem Compatibility` itc ON it.name = itc.parent
            WHERE it.item_group = "Cartridge Enclosures"
            GROUP BY it.name
        )
        SELECT 
            sn.serial_no, 
            IF(sn.serial_no LIKE "%BNO%", "Rental", "Customer-owned") as type,
            NULL as status,
            sn.item_code, 
            it.compatibility,
            sn.warehouse, 
            IF(sn.warehouse = "Customer Locations - bN", "Shipped to Customer", "bNovate") as location,
            sn.purchase_document_type AS doctype,
            sn.purchase_document_no AS docname,
            sn.purchase_date AS posting_date,
            sn.owned_by,
            cr.customer_name,
            dn.carrier,
            dn.tracking_no,
            dn.shipping_address,
            (SELECT rri.parent 
                FROM `tabRefill Request Item` rri 
                JOIN `tabRefill Request` rr ON rri.parent = rr.name
                WHERE rri.serial_no = sn.serial_no AND rri.docstatus = 1 AND rr.status IN ("Requested", "Confirmed")
                ORDER BY rr.transaction_date DESC 
                LIMIT 1
            ) as refill_request,
            sn.open_sales_order,
            so.docstatus AS so_docstatus,
            so.status AS so_status,
            wo.name AS work_order,
            wo.status AS wo_status,
            woe.woe_name AS woe, -- Work Order Entry, i.e. stock entry associated with that cartridge 
            woe.woe_docstatus AS woe_docstatus,
            loc.name as storage_location_docname,
            loc.title as storage_location,
            sl.label as storage_slot

        FROM `tabSerial No` sn
        LEFT JOIN `tabStock Entry` ste ON sn.purchase_document_no = ste.name
        LEFT JOIN `tabCustomer` cr ON sn.owned_by = cr.name
        LEFT JOIN `tabDelivery Note` dn ON sn.purchase_document_no = dn.name
        LEFT JOIN `tabSales Order` so ON sn.open_sales_order = so.name
        LEFT JOIN items it ON sn.item_code = it.name
        -- Join on a subquery that lists only packed items with matching work orders
        LEFT JOIN ( SELECT spi.name as name, spi.parent_detail_docname, spi.parent, swo.name AS wo_name
                    FROM `tabPacked Item` spi
                    JOIN `tabWork Order` swo ON spi.name = swo.sales_order_item ) AS pi ON pi.parent_detail_docname = sn.open_sales_order_item
        LEFT JOIN `tabWork Order` wo on pi.wo_name = wo.name

        -- Production status: 'Work Order Entries' make subtable of stock entries that match the work order, then filter to keep only matching serial no
        LEFT JOIN ( SELECT ste2.name AS woe_name, ste2.docstatus as woe_docstatus, ste2.work_order, fai.enclosure_serial_data
                    FROM `tabFill Association Item` fai
                    JOIN `tabStock Entry` ste2 on fai.parent = ste2.name) AS woe 
                    ON woe.work_order = wo.name AND woe.enclosure_serial_data = sn.serial_no
        -- Storage Slot
        LEFT JOIN `tabStorage Slot` sl on sl.serial_no = sn.serial_no
        LEFT JOIN `tabStorage Location` loc on sl.parent = loc.name

        WHERE sn.item_code IN ("100146", "101083")
            AND sn.warehouse IS NOT NULL
            {extra_filters}
        ORDER BY sn.serial_no
    """.format(extra_filters=extra_filters)

    data = frappe.db.sql(sql_query, as_dict=True)

    for row in data:

        row.order_status = None
        if row.so_docstatus == 1:
            # SO is submitted. Note, open SO disappears when cartridge is shipped
            row.order_status = "Confirmed"
        elif row.refill_request or row.so_docstatus == 0:
            # Refill Request or Draft SO exist
            row.order_status = "Requested"

        if row.location == "bNovate":
            if row.refill_request or row.open_sales_order:
                if row.woe_docstatus == 0:
                    row.status = "Filling"
                    row.sort_index = 3
                elif row.woe_docstatus == 1:
                    row.status = "Ready to Ship"
                    row.sort_index = 4
                else:
                    row.status = "Refill Pending"
                    row.sort_index = 2
            else:
                row.status = "In Storage"  # Includes 'cartridges scheduled for repair'
                row.sort_index = 1

        else:
            if row.refill_request or row.open_sales_order:
                row.status = "Awaiting Return"
                row.sort_index = 5
            else:
                row.status = "Shipped"
                row.sort_index = 6

        if row.carrier and row.carrier.strip() == "DHL":
            row.tracking_link = '''<a href="https://www.dhl.com/ch-en/home/tracking/tracking-express.html?submit=1&tracking-id={0}" target="_blank">{0}</a>'''.format(row.tracking_no)
        else:
            row.tracking_link = row.tracking_no

        if row['type'] == 'Rental' and row['customer_name']:
            row['type'] = '<span style="color: orangered">{}</span>'.format(row['type'])
            row['customer_name'] = '<span style="color: orangered">{}</span>'.format(row['customer_name'])

    
    data.sort(key=attrgetter('sort_index'))
    
    return data


def translations_trick():
    [
        _("Confirmed"),
        _("Requested"),
        _("Filling"),
        _("Ready to Ship"),
        _("Refill Pending"),
        _("In Storage"),
        _("Awaiting Return"),
        _("Shipped"),
    ]