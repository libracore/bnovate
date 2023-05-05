import frappe

from bnovate.bnovate.doctype.storage_location.storage_location import find_serial_no

def get_context(context):
    # secret key
    context.key = frappe.form_dict.key
    context.contents = get_contents(frappe.form_dict.key)
    context.title = "Storage"

    context.no_header = 1
    context.show_sidebar = 0
    return context

def get_contents(secret_key):
    matches = frappe.db.sql("""
        SELECT name FROM `tabStorage Location` WHERE `key` LIKE "{secret_key}";
    """.format(secret_key=secret_key), as_dict=True)
    if not matches:
        return
    
    docname = matches[0].name
    return frappe.get_doc("Storage Location", docname)
