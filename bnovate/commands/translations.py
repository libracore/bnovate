# (c) 2023, bNovate
# Translation utils that are more useful for my workflow

from __future__ import unicode_literals, absolute_import, print_function
import sys
import click
import frappe
from csv import writer

from frappe.commands import pass_context, get_site

@click.command('bn-untranslated')
@click.argument('lang')
@pass_context
def get_untranslated(context, lang):
    """ Dump untranslated strings to stdout - pipe into a csv file to then import into spreadsheet """
    site = get_site(context)
    try:
        frappe.init(site=site)
        frappe.connect()
        _get_untranslated(lang)
    finally:
        frappe.destroy()

def _get_untranslated(lang):
    messages = frappe.translate.get_server_messages('bnovate')
    messages.extend(frappe.translate.get_all_messages_from_js_files('bnovate'))

    messages = frappe.translate.deduplicate_messages(messages)
    messages.sort(key=lambda x: x[0])

    full_dict = frappe.translate.get_full_dict(lang)
    untranslated = [ m for m in messages if not full_dict.get(m[1]) ]

    with open('untranslated_{0}.csv'.format(lang), 'wb') as fo:
        # w = writer(fo, lineterminator='\n')
        w = writer(sys.stdout, lineterminator='\n')
        for p, m in untranslated:
            # w.writerow([p.encode('utf-8') if p else '', m.encode('utf-8'), "".encode('utf-8')])
            w.writerow([p if p else '', m, ''])