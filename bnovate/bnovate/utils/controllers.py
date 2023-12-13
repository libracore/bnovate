import frappe
from erpnext.selling.doctype.sales_order.sales_order import SalesOrder

class CustomSalesOrder(SalesOrder):
    """ Overrides sales order through hooks.py. Use custom shipping rule """
    pass

