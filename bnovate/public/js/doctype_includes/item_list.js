frappe.listview_settings['Item'] = {
    ...frappe.listview_settings['Item'],
    onload() {
    },
    async primary_action() {
        const values = await prompt_new_item();
        frappe.route_options = values;
        frappe.set_route("Form", "Item", "New Item");
    },
}


function prompt_new_item() {

    return new Promise((resolve, reject) => {
        let d = new frappe.ui.Dialog({
            title: 'Create New Item',
            fields: [{
                label: 'Naming Series',
                fieldname: 'series',
                fieldtype: 'Select',
                options: ['', '1xxxxx', '2xxxxx', '3xxxxx', '4xxxxx'],
                async change(e) {
                    const series = e.currentTarget.value;
                    const prev_code = await bnovate.utils.get_next_item_code(series.substring(0, 1));
                    d.set_value('item_code', prev_code);
                }
            }, {
                label: 'Item Code',
                fieldname: 'item_code',
                fieldtype: 'Data',
                reqd: true,
            }, {
                label: 'Item Name',
                fieldname: 'item_name',
                fieldtype: 'Data',
                reqd: true,
            }, {
                label: 'Item Group',
                fieldname: 'item_group',
                fieldtype: 'Link',
                options: 'Item Group',
                default: 'R&D',
                reqd: true,
            }],
            primary_action_label: 'Create',
            primary_action() {
                resolve(d.get_values());
                d.hide();
            },
        })

        window.d = d;
        d.show();

    })
}