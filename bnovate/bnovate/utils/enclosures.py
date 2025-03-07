# (C) 2023, bNovate
#
# General utility functions for enclosures

import frappe
from frappe.utils import getdate, get_link_to_form
from frappe.exceptions import DoesNotExistError
from erpnext.stock.doctype.serial_no.serial_no import get_serial_nos

def is_enclosure(item_code):
    return str(item_code) in ("100146", "101083") or str(item_code).startswith("ENC")

def is_instrument(item_code):
    docs = frappe.get_all("Item", filters={'item_group': 'Instruments', 'has_serial_no': 1})
    item_codes = [d['name'] for d in docs]
    return item_code in item_codes

def check_so_serial_no(so, method=None):
    """ Check that SNs are specified for refills. Called through hooks.py """
    if method not in ('before_submit', 'on_update_after_submit'):
        return

    refills = [it for it in so.items if it.item_group == 'Cartridge Refills']

    for it in refills:
        serial_nos = get_serial_nos(it.serial_nos)

        deets = {"item_code": it.item_code, "row": it.idx}
        if len(serial_nos) != it.qty:
            frappe.throw("For item {item_code}, row {row}: {count} Serial Nos entered. Please enter {qty}.".format(
                qty=int(it.qty),
                count = len(serial_nos),
                **deets
            ))

        if len(serial_nos) != len(set(serial_nos)):
            frappe.throw("For item {item_code}, row {row}: duplicate serial number entered.".format(*deets))

        for serial_no in serial_nos:
            try:
                sn_doc = frappe.get_doc("Serial No", serial_no)
            except DoesNotExistError:
                frappe.throw("For item {item_code}, row {row}: unknown serial number {serial_no}".format(
                    serial_no=serial_no,
                    **deets
                ))
            else:
                if not is_enclosure(sn_doc.item_code):
                    frappe.throw("For item {item_code}, row {row}: {serial_no} is not a cartridge enclosure".format(
                        serial_no=serial_no,
                        **deets
                ))

def associate_so_serial_no(so, method=None):
    """ Set 'open_sales_order' field on Serial No. Called through hooks.py.
    
    We need this because db lookups in text field are super slow.
    """

    # The state of the doc displayed here is the 'target' state intented if all checks 
    # go through.
    # I haven't found how to access the "old" version of the document for comparisons.

    new_serials = set()

    refills = [it for it in so.items if it.item_group == 'Cartridge Refills']
    for it in refills:
        serial_nos = get_serial_nos(it.serial_nos)
        for serial_no in serial_nos:
            new_serials.add(serial_no)
            sn_doc = frappe.get_doc("Serial No", serial_no) # raises an error with helpful message if SN doesn't exist.
            
            if so.docstatus == 2 or it.delivered_qty >= it.qty:
                # Trying to cancel the document OR to fully deliver line item
                # Remove association on SN
                if sn_doc.open_sales_order == so.name:
                    sn_doc.db_set("open_sales_order", None)
                    sn_doc.db_set("open_sales_order_item", None)
                    # print("Removed association")

            else:
                # Creating or saving the SO. 
                # check that there is no conflict:
                if not sn_doc.open_sales_order:
                    sn_doc.db_set("open_sales_order", so.name)
                    sn_doc.db_set("open_sales_order_item", it.name)
                    # print("Set", serial_no, "to SO", so.name)
                else:
                    if sn_doc.open_sales_order != so.name:
                        frappe.throw("{so} already exists for {sn}".format(
                            so=frappe.utils.get_link_to_form("Sales Order", sn_doc.open_sales_order), 
                            sn=frappe.utils.get_link_to_form("Serial No", serial_no)
                        ))
                    # else:
                    #     print("Nothing to change")
    
    # Find dangling references: Serial No that point to this SO because they were
    # previously included, but are no longer included in this SO.
    docs = frappe.db.get_list("Serial No", filters={"open_sales_order": ["=", so.name]})
    all_serials = set(d['name'] for d in docs)
    dangling = all_serials.difference(new_serials)
    for serial_no in dangling:
        print("Removing dangling associationg from", serial_no, "to", so.name)
        sn_doc = frappe.get_doc("Serial No", serial_no)
        sn_doc.db_set("open_sales_order", None)
        sn_doc.db_set("open_sales_order_item", None)


def set_wo_serial_no(wo, method=None):
    """ Set Serial No for a refill work order based on SO.

    Called from hooks.py 
    """

    if method not in ['before_save', 'on_update_after_submit']:
        return

    if not wo.sales_order_item:
        return

    # Only overwrite serial no if it is empty
    if wo.serial_no:
        return

    print(wo.sales_order_item)
    try:
        # Reference to a SOI actually points to a packed item
        pi = frappe.get_doc("Packed Item", wo.sales_order_item)
        soi = frappe.get_doc("Sales Order Item", pi.parent_detail_docname)
    except DoesNotExistError:
        frappe.msgprint("This WO is associated with a Sales Order Item that no longer exists. Please manually enter Serial Nos.")
        return
    
    serial_nos = get_serial_nos(soi.serial_nos) # cleanup
    wo.db_set("serial_no", "\n".join(serial_nos))


def set_owner_from_dn(dn, method=None):
    """ Set Serial No owner (custom field) from a DN.

    Owner is set by the first delivery note submitted.
     
    Called by hooks.py
    """

    if not method in ('on_submit', 'on_cancel'):
        return

    for item in dn.packed_items:
        if not is_enclosure(item.item_code) and not is_instrument(item.item_code):
            continue

        print("Enclosure found.", item.qty, item.serial_no)
        serial_nos = get_serial_nos(item.serial_no)

        for serial in serial_nos:
            if serial.startswith("BNO"):
                # Owned by bNovate
                continue 
            sn_doc = frappe.get_doc("Serial No", serial)
            if (method == "on_submit" and item.qty > 0):
                if not sn_doc.owned_by:
                    sn_doc.db_set("owned_by", dn.customer)
                    sn_doc.db_set("owned_by_name", dn.customer_name)
                    sn_doc.db_set("owner_set_by", dn.name)

            # In case of a return or a cancelled DN:
            elif (method == "on_submit" and item.qty < 0) or method == "on_cancel":
                # Cancel ownership only if this document set the ownership and it hasn't changed.
                # If not we assume an older document set it, or that is was manually set.
                if sn_doc.owner_set_by in [dn.name, dn.return_against] and sn_doc.owned_by == dn.customer:
                    sn_doc.db_set("owned_by", None)
                    sn_doc.db_set("owned_by_name", None)
                    sn_doc.db_set("owner_set_by", None)


def check_serial_no_in_dn(dn, method=None):
    """ Check that Serial No of packed item in DN corresponds to that specified in SO. 
    
    Only checks if: 
    - Packed item master is marked "Check Serial No on Delivery"
    - There is a linked SO
    - SO has Serial Nos specified

    """

    if not method in ('before_save', 'before_submit'):
        return
    
    # Allow save in case of errors, but block Submit.
    raise_exception = method == 'before_submit'

    dni_lookup = {dni.name: dni for dni in dn.items}

    for pi in dn.packed_items:
        item_master = frappe.get_doc("Item", pi.item_code)
        if not pi.serial_no or not item_master.check_serial_no_on_delivery:
            continue
        
        dni = dni_lookup[pi.parent_detail_docname]
        if not dni.so_detail:
            continue

        soi = frappe.get_doc("Sales Order Item", dni.so_detail)
        if soi.serial_nos is None or not soi.serial_nos.strip():
            continue
            

        dn_serial_nos = get_serial_nos(pi.serial_no)
        so_serial_nos = get_serial_nos(soi.serial_nos)
        print(dn_serial_nos)
        print(so_serial_nos)

        deets = {"item_code": pi.item_code, "idx": pi.idx}
        if len(dn_serial_nos) != len(so_serial_nos):
            frappe.msgprint("For item {item_code}, packed items row {idx}: {count} Serial Nos entered. Please enter {qty}.".format(
                qty=len(so_serial_nos),
                count = len(dn_serial_nos),
                **deets
            ), raise_exception=raise_exception)
            continue

        if len(dn_serial_nos) != len(set(dn_serial_nos)):
            frappe.msgprint(
                "For item {item_code}, packed items row {idx}: duplicate serial number entered.".format(**deets), 
                raise_exception=raise_exception)
            continue

        for serial_no in dn_serial_nos:
            if serial_no not in so_serial_nos:
                frappe.msgprint(
                    "For item {item_code}, row {idx}: Serial no {serial_no} does not match Sales Order. "
                    "Expected: <br>- {serial_nos}".format(serial_no=serial_no, serial_nos="<br>- ".join(so_serial_nos), **deets),
                    raise_exception=raise_exception)