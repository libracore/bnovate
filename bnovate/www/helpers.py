# Copyright (c) 2013-2023, bnovate, libracore and contributors
# For license information, please see license.txt

import frappe

from frappe import _

from frappe.contacts.doctype.address.address import get_address_display

def auth():
    # check login
    if frappe.session.user=='Guest':
        frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)
    if not "@" in frappe.session.user:
        frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)

def get_session_customers():
    # fetch customers for this user, ordered the same as in Desk.
    customers = frappe.db.sql("""
        SELECT 
            `tC1`.`link_name` AS `customer`
        FROM `tabContact`
        JOIN `tabDynamic Link` AS `tC1` ON `tC1`.`parenttype` = "Contact" 
                                       AND `tC1`.`link_doctype` = "Customer" 
                                       AND `tC1`.`parent` = `tabContact`.`name`
        WHERE `tabContact`.`user` = "{user}"
        ORDER BY `tC1`.`idx`;
    """.format(user=frappe.session.user), as_dict=True)

    return [ c['customer'] for c in customers]

def get_session_primary_customer():
    return get_session_customers()[0]


def get_session_contact():
    """ Return names of contacts associated to this user id """

    # TODO: prevent a user from owning several contacts.

    users = frappe.db.sql("""
    SELECT
        name
    FROM tabContact tc
    WHERE tc.user = "{user}"
    """.format(user=frappe.session.user), as_dict=True)

    return users[0].name

@frappe.whitelist()
def get_addresses():
    """ Return addresses for the current contact """
    addresses = frappe.db.sql("""
        SELECT 
            `tabAddress`.`name`,
            `tabAddress`.`company_name`,
            `tabAddress`.`address_type`,
            `tabAddress`.`address_line1`,
            `tabAddress`.`address_line2`,
            `tabAddress`.`pincode`,
            `tabAddress`.`city`,
            `tabAddress`.`country`,
            `tabAddress`.`is_primary_address`,
            `tabAddress`.`is_shipping_address`,
            `tC1`.`link_name` AS `customer_name`
        FROM `tabContact`
        JOIN `tabDynamic Link` AS `tC1` ON `tC1`.`parenttype` = "Contact" 
                                       AND `tC1`.`link_doctype` = "Customer" 
                                       AND `tC1`.`parent` = `tabContact`.`name`
        JOIN `tabDynamic Link` AS `tA1` ON `tA1`.`parenttype` = "Address" 
                                       AND `tA1`.`link_doctype` = "Customer" 
                                       AND `tA1`.`link_name` = `tC1`.`link_name`
        LEFT JOIN `tabAddress` ON `tabAddress`.`name` = `tA1`.`parent`
        WHERE `tabContact`.`user` = "{user}";
    """.format(user=frappe.session.user), as_dict=True)

    for addr in addresses:
        addr.display = get_address_display(addr)

    
    return addresses


@frappe.whitelist()
def create_address(address_line1, pincode, city, address_type="Shipping", company_name=None, address_line2=None, country="Switzerland"):
    error = None
    # fetch customers for this user
    customer = get_session_primary_customer()
    customer_links = [{'link_doctype': 'Customer', 'link_name': customer}]
    # create new address
    pure_name = "{0}-{1}-{2}".format(customer, address_line1, city).replace(" ", "_").replace("&", "and").replace("+", "and").replace("?", "-").replace("=", "-")
    new_address = frappe.get_doc({
        'doctype': 'Address',
        'address_title': pure_name,
        'company_name': company_name,
        'address_type': address_type,
        'address_line1': address_line1,
        'address_line2': address_line2,
        'pincode': pincode,
        'city': city,
        'country': country,
        'links': customer_links
    })
    
    new_address.insert(ignore_permissions=True)
    frappe.db.commit()

@frappe.whitelist()
def update_address(name, address_line1, pincode, city, address_line2=None, country="Switzerland", is_primary=0):
    error = None
    # fetch customers for this user
    customers = get_session_customers()
    address = frappe.get_doc("Address", name)
    permitted = False
    for l in address.links:
        for c in customers:
            if l.link_name == c['customer']:
                permitted = True
    if permitted:
        # update address
        address.address_line1 = address_line1
        address.address_line2 = address_line2
        address.pincode = pincode
        address.city = city
        address.country = country
        if is_primary:
            address.is_primary_address = 1
        else:
            address.is_primary_address = 0
        try:
            address.save(ignore_permissions=True)
            frappe.db.commit()
        except Exception as err:
            error = err
    else:
        error = "Permission error"
    return {'error': error, 'name': address.name or None}

@frappe.whitelist()
def delete_address(name):
    error = None
    # fetch customers for this user
    customers = get_session_customers()
    address = frappe.get_doc("Address", name)
    permitted = False
    for l in address.links:
        for c in customers:
            if l.link_name == c['customer']:
                permitted = True
    if permitted:
        # delete address: drop links
        address.links = []
        try:
            address.save(ignore_permissions=True)
            frappe.db.commit()
        except Exception as err:
            error = err
    else:
        error = "Permission error"
    return {'error': error}


@frappe.whitelist()
def get_countries():
    return [c.name for c in frappe.get_all("Country")]