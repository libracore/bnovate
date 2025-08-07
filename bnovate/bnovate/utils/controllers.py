import json
import frappe
from six import string_types
from frappe import msgprint, _
from frappe.utils import new_line_sep
from erpnext.selling.doctype.sales_order.sales_order import SalesOrder
from erpnext.manufacturing.doctype.work_order.work_order import get_item_details


def check_blanket_order_currency(doc, method=None):
    """ Make sure document currency matches blanket order currency"""

    if method != 'before_submit':
        return

    blanket_orders = set( it.blanket_order for it in doc.items if it.blanket_order)

    for bko in blanket_orders:
        bko_doc = frappe.get_doc("Blanket Order", bko)

        if bko_doc.currency and bko_doc.currency != doc.currency:
            frappe.throw("Blanket order {0} currency ({1}) does not match document currency ({2}). Please manually adjust pricing and Blanket Order links.".format(
                bko_doc.name, bko_doc.currency, doc.currency
            ))

def check_delivery_date_updates(doc, method=None):
    """ Check if delivery date is changed. If applicable, set benchmark delivery date to customer's request """

    if method != 'before_update_after_submit':
        return

    old_doc = doc.get_doc_before_save()

    for new_item in doc.items:
        old_item = next((i for i in old_doc.items if i.name == new_item.name), None)
        if not old_item:
            continue

        if str(new_item.delivery_date) != str(old_item.delivery_date):
            if not doc.date_change_origin:
                frappe.throw(_("Ship date has been changed. Please set 'Date Change Origin' field to indicate the reason for the change."))

            if doc.date_change_origin == "Customer":
                new_item.benchmark_delivery_date = new_item.delivery_date 
                print("Set new item benchmark delivery date to new delivery date")
            else:
                new_item.benchmark_delivery_date = old_item.delivery_date 
                print("Set new item benchmark delivery date to old delivery date")

    doc.date_change_origin = None

    return doc


    
@frappe.whitelist()
def raise_work_orders_for_material_request(material_request, selected=[]):
    """ Create WO for a MR, only for the subset of selected items 

    Adapted from erpnext/stock/doctype/material_request/material_request.py
    """

    if isinstance(selected, string_types):
        selected = json.loads(selected)

    mr = frappe.get_doc("Material Request", material_request)
    errors =[]
    work_orders = []
    default_wip_warehouse = frappe.db.get_single_value("Manufacturing Settings", "default_wip_warehouse")

    selected_docnames = [ s['name'] for s in selected ]
    selected_items = [ i for i in mr.items if i.name in selected_docnames]


    for d in selected_items:
        if (d.qty - d.ordered_qty) >0:
            if frappe.db.exists("BOM", {"item": d.item_code, "is_default": 1}):
                wo_order = frappe.new_doc("Work Order")
                wo_order.update({
                    "production_item": d.item_code,
                    "qty": d.qty - d.ordered_qty,
                    "fg_warehouse": d.warehouse,
                    "wip_warehouse": default_wip_warehouse,
                    "description": d.description,
                    "stock_uom": d.stock_uom,
                    "expected_delivery_date": d.schedule_date,
                    "sales_order": d.sales_order,
                    "bom_no": get_item_details(d.item_code).bom_no,
                    "material_request": mr.name,
                    "material_request_item": d.name,
                    "planned_start_date": mr.transaction_date,
                    "company": mr.company
                })

                wo_order.set_work_order_operations()
                wo_order.save()

                work_orders.append(wo_order.name)
            else:
                errors.append(_("Row {0}: Bill of Materials not found for the Item {1}").format(d.idx, d.item_code))

    if work_orders:
        message = ["""<a href="#Form/Work Order/%s" target="_blank">%s</a>""" % \
            (p, p) for p in work_orders]
        msgprint(_("The following Work Orders were created:") + '\n' + new_line_sep(message))

    if errors:
        frappe.throw(_("Productions Orders cannot be raised for:") + '\n' + new_line_sep(errors))

    return work_orders