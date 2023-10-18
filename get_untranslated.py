# Run with bench console:
# $ bench console < get_untranslated.py

import frappe

from csv import writer


messages = frappe.translate.get_server_messages('bnovate')
messages.extend(frappe.translate.get_all_messages_from_js_files('bnovate'))

messages = frappe.translate.deduplicate_messages(messages)

for lang in ('fr', 'de'):
    full_dict = frappe.translate.get_full_dict(lang)
    untranslated = [ m for m in messages if not full_dict.get(m[1]) ]

    with open('untranslated_{0}.csv'.format(lang), 'wb') as fo:
        w = writer(fo, lineterminator='\n')
        for p, m in untranslated:
            w.writerow([p.encode('utf-8') if p else '', m.encode('utf-8'), "".encode('utf-8')])
