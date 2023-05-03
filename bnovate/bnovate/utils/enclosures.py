# (C) 2023, bNovate
#
# General utility functions for enclosures

import frappe
from erpnext.stock.doctype.serial_no.serial_no import get_serial_nos

def is_enclosure(item_code):
    return item_code == "100146" or item_code.startswith("ENC")

def set_owner_from_dn(dn, method=None):
    """ Set Serial No owner (custom field) from a DN.

    Owner is set by the first delivery note submitted.
     
    Called by hooks.py
    """

    if not method in ('on_submit', 'on_cancel'):
        return

    for item in dn.packed_items:
        if not is_enclosure(item.item_code):
            continue

        print("Enclosure found.", item.qty, item.serial_no)
        serial_nos = get_serial_nos(item.serial_no)

        for serial in serial_nos:
            if serial.startswith("BNO"):
                # Owned by bNovate
                continue 
            sn_doc = frappe.get_doc("Serial No", serial)
            if method == "on_submit":
                if not sn_doc.owned_by:
                    sn_doc.db_set("owned_by", dn.customer)
                    sn_doc.db_set("owned_by_name", dn.customer_name)
                    sn_doc.db_set("owner_set_by", dn.name)
            elif method == "on_cancel":
                # Cancel ownership only if this document set the ownership and it hasn't changed.
                # If not we assume an older document set it, or that is was manually set.
                if sn_doc.owner_set_by == dn.name and sn_doc.owned_by == dn.customer:
                    sn_doc.db_set("owned_by", None)
                    sn_doc.db_set("owned_by_name", None)
                    sn_doc.db_set("owner_set_by", None)

