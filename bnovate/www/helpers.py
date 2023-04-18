# Copyright (c) 2013-2023, bnovate, libracore and contributors
# For license information, please see license.txt

import frappe

from frappe import _

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