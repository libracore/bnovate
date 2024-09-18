import random
import string

import frappe
from frappe.utils import get_datetime_str, nowdate, flt

@frappe.whitelist()
def get_random_id():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(32))


@frappe.whitelist()
def get_fixed_exchange_rate(from_currency, to_currency, transaction_date=None, args=None):
    """ Return long-term exchange rate value, used for shipping rules for example """
    if not (from_currency and to_currency):
        # manqala 19/09/2016: Should this be an empty return or should it throw and exception?
        return
    if from_currency == to_currency:
        return 1

    if not transaction_date:
        transaction_date = nowdate()

    filters = [
        ["date", "<=", get_datetime_str(transaction_date)],
        ["from_currency", "=", from_currency],
        ["to_currency", "=", to_currency]
    ]

    if args == "for_buying":
        filters.append(["for_buying", "=", "1"])
    elif args == "for_selling":
        filters.append(["for_selling", "=", "1"])

    # cksgb 19/09/2016: get last entry in Currency Exchange with from_currency and to_currency.
    entries = frappe.get_all(
        "Fixed Currency Exchange", fields=["exchange_rate"], filters=filters, order_by="date desc",
        limit=1)
    if entries:
        return flt(entries[0].exchange_rate)

    return


@frappe.whitelist()
def upload_file():
    """ Uploads file to a specific field in a doc, if specified 

    This is a wrapper around Frappe's built-in upload_file, that fixes file attachments.
    
    """ 

    doc = frappe.handler.upload_file()
    if doc.attached_to_doctype and doc.attached_to_name and doc.attached_to_field:
        target_doc = frappe.get_doc(doc.attached_to_doctype, doc.attached_to_name)
        target_doc.set(doc.attached_to_field, doc.file_url)
        target_doc.save()

    return doc
