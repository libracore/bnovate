# Copyright (c) 2013-2023, bnovate, libracore and contributors
# For license information, please see license.txt

import frappe

from frappe import _

from frappe.contacts.doctype.address.address import get_address_display

def auth():
    # check login, throw exception if not logged in
    if frappe.session.user=='Guest':
        frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)
    if not "@" in frappe.session.user:
        frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)

def is_guest():
    if frappe.session.user=='Guest' or not "@" in frappe.session.user:
        return True
    return False

def update_context(context):
    """ Called by hooks.py as a 'middleware' on all pages, including Desk pages. """
    build_sidebar(context, context.show_sidebar)
    return context

def get_settings():
    return frappe.get_single("bNovate Settings")

def get_session_customers():
    # fetch customers for this user, ordered the same as in Desk.
    customers = frappe.db.sql("""
        SELECT 
            `tC1`.`link_name` AS `docname`,
            `tCus`.`enable_cartridge_portal`
        FROM `tabContact`
        JOIN `tabDynamic Link` AS `tC1` ON `tC1`.`parenttype` = "Contact" 
                                       AND `tC1`.`link_doctype` = "Customer" 
                                       AND `tC1`.`parent` = `tabContact`.`name`
        JOIN `tabCustomer` as `tCus` ON `tCus`.`name` = `tC1`.`link_name`
        WHERE `tabContact`.`user` = "{user}"
        ORDER BY `tC1`.`idx`;
    """.format(user=frappe.session.user), as_dict=True)

    return customers

def get_session_primary_customer():
    """ Return ID of primary customer, i.e. first in list of linked customers """
    customers = get_session_customers()
    if customers:
        return customers[0]
    else:
        return None

def get_session_contact():
    """ Return names of contacts associated to this user id """

    # Note: I prevent a user from owning several contacts by setting User ID to unique in Contact doctype

    users = frappe.db.sql("""
    SELECT
        name
    FROM tabContact tc
    WHERE tc.user = "{user}"
    """.format(user=frappe.session.user), as_dict=True)

    return users[0].name

def has_cartridge_portal():
    """ True if user is allowed to use cartridge management features """
    customer = get_session_primary_customer()
    if customer is not None and customer.enable_cartridge_portal:
        return True
    return False


def build_sidebar(context, show=True):
    context.show_sidebar = show
    context.sidebar_items = [{
            'route': '/',
            'title': 'Dashboard',
        }, {
            'route': '/quotations',
            'title': 'Quotations',
        }, {
            'route': '/instruments',
            'title': 'My Instruments',
        }]

    if has_cartridge_portal():
        context.sidebar_items.extend([{
                'route': '/cartridges',
                'title': 'My Cartridges',
            }, {
                'route': '/requests',
                'title': 'Refill Requests',
            }, {
                'route': '/my_addresses',
                'title': 'My Addresses',
            }])

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
            `tC1`.`link_name` AS `customer_docname`
        FROM `tabContact`
        JOIN `tabDynamic Link` AS `tC1` ON `tC1`.`parenttype` = "Contact" 
                                       AND `tC1`.`link_doctype` = "Customer" 
                                       AND `tC1`.`parent` = `tabContact`.`name`
        JOIN `tabDynamic Link` AS `tA1` ON `tA1`.`parenttype` = "Address" 
                                       AND `tA1`.`link_doctype` = "Customer" 
                                       AND `tA1`.`link_name` = `tC1`.`link_name`
        LEFT JOIN `tabAddress` ON `tabAddress`.`name` = `tA1`.`parent`
        WHERE `tabContact`.`user` = "{user}"
        ORDER BY `tabAddress`.`company_name`, `tabAddress`.`address_line1`
    """.format(user=frappe.session.user), as_dict=True)

    for addr in addresses:
        addr.display = get_address_display(addr)

    
    return addresses


@frappe.whitelist()
def create_address(address_line1, pincode, city, address_type="Shipping", company_name=None, address_line2=None, country="Switzerland"):
    """ Add address on primary customer associated to this user """
    # fetch customers for this user
    customer = get_session_primary_customer()
    customer_links = [{'link_doctype': 'Customer', 'link_name': customer.docname}]
    # create new address
    pure_name = "{0}-{1}-{2}-{3}".format(customer.docname, company_name, address_line1, city).replace(" ", "_").replace("&", "and").replace("+", "and").replace("?", "-").replace("=", "-")
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
def delete_address(name):
    """ Unlink all customers from this address """
    # fetch customers for this user
    customers = get_session_customers()
    address = frappe.get_doc("Address", name)
    permitted = False
    for l in address.links:
        for c in customers:
            if l.link_name == c.customer_docname:
                permitted = True
    if permitted:
        # delete address: drop links
        for l in address.links:
            address.remove(l)
        # FIXME: current hack is to associate to a dummy customer to override a validation which automatically re-links
        address.append('links', {'link_doctype': 'Customer', 'link_name': frappe.get_single('bNovate Settings').dummy_customer})
        address.save(ignore_permissions=True)
        frappe.db.commit()
    else:
        raise frappe.PermissionError


@frappe.whitelist()
def get_countries():
    return [c.name for c in frappe.get_all("Country")]