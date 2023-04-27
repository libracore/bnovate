
frappe.call("frappe.desk.page.setup_wizard.setup_wizard.load_languages")
    .then((res) => {
        const default_language = res.message.default_language;
        return frappe.call("frappe.desk.page.setup_wizard.setup_wizard.load_messages", { language: default_language })
    })
    .then((res) => {
        console.log("Got the messages", res.__messages)
        Object.assign(frappe._messages, res.__messages);
    });