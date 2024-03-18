frappe.provide("bnovate.translations");

bnovate.translations.get_messages = async function () {
    let resp = await frappe.call("frappe.desk.page.setup_wizard.setup_wizard.load_languages")

    const default_language = resp.message.default_language;
    resp = await frappe.call("frappe.desk.page.setup_wizard.setup_wizard.load_messages", { language: default_language })

    Object.assign(frappe._messages, resp.__messages);
}
