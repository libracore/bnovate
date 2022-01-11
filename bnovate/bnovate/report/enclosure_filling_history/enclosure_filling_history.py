# Copyright (c) 2022, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    
    return columns, data

def get_columns():
    return [
        {'fieldname': 'name', 'fieldtype': 'Link', 'label': _('STE'), 'options': 'Stock Entry', 'width': 80},
        {'fieldname': 'posting_date', 'fieldtype': 'Date', 'label': _('Production date'), 'width': 100},
        {'fieldname': 'expiry_date', 'fieldtype': 'Date', 'label': _('Expiry date'), 'width': 100},
        {'fieldname': 'fill_serial', 'fieldtype': 'Link', 'label': _('Fill Serial'), 'options': 'Serial No', 'width': 150},
        {'fieldname': 'enclosure_serial', 'fieldtype': 'Link', 'label': _('Enclosure Serial'), 'options': 'Serial No', 'width': 150},
        {'fieldname': 'fill_type', 'fieldtype': 'Link', 'label': _('Fill Type'), 'options': 'Item', 'width': 200},
    ]
    
    
    
def get_data(filters):
    
    sn_filter = ""
    if filters.serial_no:
        sn_filter = """ AND (`fa`.`enclosure_serial` LIKE "%{serial_no}%" OR `fa`.`fill_serial` LIKE "%{serial_no}%") """.format(serial_no=filters.serial_no)
    sql_query = """
    SELECT
        `ste`.`name`,
        `ste`.`posting_date`,
        `ste`.`expiry_date`,
        `fa`.`fill_serial`,
        `fa`.`enclosure_serial`,
        `fa`.`fill_type`
    FROM `tabStock Entry` AS `ste`
    JOIN `tabFill Association Item` AS `fa` ON `fa`.`parent` = `ste`.`name`
    WHERE `ste`.`purpose` = "Manufacture"
        {sn_filter}
        AND ste.docstatus = 1
    ORDER BY `ste`.`posting_date` DESC
    """.format(sn_filter=sn_filter)

    data = frappe.db.sql(sql_query, as_dict=True)
    return data
