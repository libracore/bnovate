# -*- coding: utf-8 -*-
# Copyright (c) bNovate (Douglas Watson)
# For license information, please see license.txt

import io
import frappe
from PyPDF2 import PdfFileReader, PdfFileWriter

from frappe.model.document import Document
from frappe.utils.pdf import get_file_data_from_writer
from erpnextswiss.erpnextswiss.doctype.label_printer.label_printer import create_pdf


@frappe.whitelist()
def download_label(label_reference, content):
    # Open PDF label, display in the browser instead of downloading.
    label = frappe.get_doc("Label Printer", label_reference)
    frappe.local.response.filename = "{name}.pdf".format(name=label_reference.replace(" ", "-").replace("/", "-"))
    frappe.local.response.filecontent = create_pdf(label, content)
    frappe.local.response.type = "pdf"
    # frappe.local.response.display_content_as = "inline" # Doesn't have any effect on our frappe version.

@frappe.whitelist()
def download_label_for_doc(doctype, docname, print_format, label_reference):
    """ Return PDF label based on an existing print format and label_printer size """
    doc = frappe.get_doc(doctype, docname)
    pf = frappe.get_doc("Print Format", print_format)

    template = """<style>{css}</style>{html}""".format(css=pf.css, html=pf.html)
    content = frappe.render_template(template, {"doc": doc})
    return download_label(label_reference, content)

@frappe.whitelist()
def download_label_for_docs(doctype, docnames, print_format, label_reference):
    """ Return PDF labels based on an existing print format and label_printer size.
     
        Expects a list of docnames.
    """
    docnames = docnames.split(',')
    output = PdfFileWriter()
    pf = frappe.get_doc("Print Format", print_format)
    label = frappe.get_doc("Label Printer", label_reference)

    template = """<style>{css}</style>{html}""".format(css=pf.css, html=pf.html)

    for docname in docnames:
        doc = frappe.get_doc(doctype, docname)
        content = frappe.render_template(template, {"doc": doc})
        filedata = create_pdf(label, content)
        reader = PdfFileReader(io.BytesIO(filedata))
        output.appendPagesFromReader(reader)

    frappe.local.response.filename = "{name}.pdf".format(name=doctype.replace(" ", "-").replace("/", "-"))
    frappe.local.response.filecontent = get_file_data_from_writer(output)
    frappe.local.response.type = "pdf"


# Example of how to use this from Javascript:
#
# const label_format = "Labels 50x30mm"
# const content = "Hello, world"
# window.open(
#          frappe.urllib.get_full_url("/api/method/bnovate.bnovate.utils.labels.download_label"  
# 		    + "?label_reference=" + encodeURIComponent(label_format)
# 		    + "&content=" + encodeURIComponent(content))
#     , "_blank"); // _blank opens in new tab.

# Other tips:
# use {{ frappe.get_url() }} in print formats to get base url for images and other files.
# All js scripts used in print formats (jsbarcode, qrcodejs...) should be imported from cdn.