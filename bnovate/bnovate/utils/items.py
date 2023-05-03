# (C) 2023, bNovate
#
# General utility functions for working with items

import frappe

def get_highest_item_code(prefix=1):
    """ Return highest item code in a naming series """

    query = """
    --  --sql
SELECT MAX(item_code) as item_code
FROM `tabItem`
WHERE item_code LIKE "{prefix}%"
;
    """.format(prefix=prefix)
    data = frappe.db.sql(query, as_dict=True)
    if data:
        return data[0].item_code
    return None


@frappe.whitelist()
def get_next_item_code(prefix):
    """ Return next item code in naming series, with .02 suffix """

    last_code = get_highest_item_code(prefix)
    if not last_code:
        return None
    
    try:
        last_code = int(last_code[:6])
    except ValueError:
        frappe.throw("Highest existing item can't be converted into a number: ", last_code)
    
    return "{}.01".format(last_code + 1)

