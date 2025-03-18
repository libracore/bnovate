import random
import string
import requests

from bs4 import BeautifulSoup

import frappe
from frappe import _
from frappe.utils import get_datetime_str, nowdate, flt


def truncate(s, n):
    """ Return string with ellipsis in the middle if longer than n chars """
    if s is None:
        return ""
    return s[:n-1] + '…' if len(s) > n else s

def trim(s, token, n):
    """ Return string up to token. If token is missing, return ellipsized version """
    if s is None:
        return ""
    if token in s:
        return s[:s.index(token)]
    return truncate(s, n)

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

@frappe.whitelist()
def get_contact_display(contact_docname):
    contact_doc = frappe.get_doc("Contact", contact_docname)
    return ' '.join([n.strip() for n in [contact_doc.first_name, contact_doc.last_name] if n]).strip()

@frappe.whitelist()
def deepl_translate(texts, target_lang, source_lang="en"):
    """
    Return translated version of the strings, running through DeepL.

    Args:
        texts (str or list): The text or list of texts to be translated.
        target_lang (str): The target language code (e.g., 'de' for German).
        source_lang (str, optional): The source language code (default is 'en' for English). Set to None for auto-detect.

    Returns:
        str or list: The translated text(s).
    """
    api_url = "https://api-free.deepl.com/v2/translate"
    api_key = frappe.db.get_single_value('bNovate Settings', 'deepl_api_key')

    # Lists are passed as json strings through when called through FETCH...
    try:
        texts = frappe.parse_json(texts)
    except ValueError:
        pass

    return_string = False
    if not isinstance(texts, list):
        return_string = True
        texts = [texts]

    params = {
        "auth_key": api_key,
        "target_lang": target_lang,
        "text": texts,
    }

    if source_lang is not None:
        params["source_lang"] = source_lang

    response = requests.post(api_url, data=params)
    response_data = response.json()

    if response.status_code == 200 and "translations" in response_data:
        result = [translation["text"] for translation in response_data["translations"]]
        if return_string:
            return result[0]
        return result
    else:
        frappe.throw(_("Error in translation: {0}").format(response_data.get("message", "Unknown error")))


def validate_eu_eori(eori_number):
    """ Returns EORI details from the EU's EORI validation service.

    Success example:
    
        {'eori': 'FRxxxxxxxxxxxxxxxxx',
        'status': '0',
        'statusDescr': 'Valid',
        'name': 'Company Name',
        'address': 'Company Address Line 1',
        'street': "abc....",
        'postalCode': '1234',
        'city': 'ABCD',
        'country': 'Switzerland'}
    
    Failure example:
        
        {'eori': 'FRxxxxxxxxxxxxxxx',
        'status': '1',
        'statusDescr': 'Not valid',
        'name': None,
        'address': None,
        'street': None,
        'postalCode': None,
        'city': None,
        'country': None}

    Failure example:
    
    """

    url = "https://ec.europa.eu/taxation_customs/dds2/eos/validation/services/validation"
    headers = {
        "Content-Type": "text/xml",
        "User-Agent": "ERPNext",
    }
    
    # SOAP request body
    soap_request = """<?xml version="1.0" encoding="UTF-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:eori="http://eori.ws.eos.dds.s/">
        <soapenv:Header/>
        <soapenv:Body>
            <eori:validateEORI>
                <eori:eori>{eori_number}</eori:eori>
            </eori:validateEORI>
        </soapenv:Body>
    </soapenv:Envelope>""".format(eori_number=eori_number)
    
    response = requests.post(url, data=soap_request, headers=headers)
    
    if response.status_code != 200:
        return {"error": f"HTTP Error {response.status_code}", "details": response.text}
    
    soup = BeautifulSoup(response.text, "xml")
    result = {}

    eori_node = soup.find("result")
    if eori_node:
        result["eori"] = eori_node.find("eori").text if eori_node.find("eori") else None
        result["status"] = eori_node.find("status").text if eori_node.find("status") else None
        result["statusDescr"] = eori_node.find("statusDescr").text if eori_node.find("statusDescr") else None
        result["name"] = eori_node.find("name").text if eori_node.find("name") else None
        result["address"] = eori_node.find("address").text if eori_node.find("address") else None
        result["street"] = eori_node.find("street").text if eori_node.find("street") else None
        result["postalCode"] = eori_node.find("postalCode").text if eori_node.find("postalCode") else None
        result["city"] = eori_node.find("city").text if eori_node.find("city") else None
        result["country"] = eori_node.find("country").text if eori_node.find("country") else None
        result["address_display"] = "<br>\n".join([s or "" for s in [result["name"], result["street"], result["postalCode"], result["city"], result["country"]]])
        
        return result

    raise Exception("Invalid response", response.text)


@frappe.whitelist()
def check_eori(eori_number):
    """ Check EORI on public register. Raise frappe exception if invalid. 
    
    Only checks EU register, not UK.
    """

    if eori_number.startswith("GB"):
        frappe.throw(_('Please check UK EORI numbers on the <a target="_blank" href="https://www.tax.service.gov.uk/check-eori-number">UK government website</a>'))

    return validate_eu_eori(eori_number)