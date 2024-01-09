import frappe
from erpnext.selling.doctype.sales_order.sales_order import SalesOrder


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
    
    