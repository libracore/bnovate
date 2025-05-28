/*
Material Request Custom Script
------------------------------

- Show suppliers


*/
frappe.ui.form.on('Material Request', {
    async refresh(frm) {

        frm.get_item_masters = async () => get_item_masters(frm);
        frm.get_suppliers = async () => get_suppliers(frm);

        if (frm.doc.material_request_type === "Purchase") {


            let suppliers = await get_suppliers(frm);
            console.log(suppliers);
            for (let item of frm.doc.items) {
                const tooltip = frappe.render_template(`
                <ul>
                    {% for item in supplier_items %}
                    <li>{{ item.supplier_name }} - ref. {{ item.supplier_part_no }}</li>
                    {% endfor %}
                </ul>
                `, suppliers[item.item_code]);

                let field = document.querySelector(`[data-name="${item.name}"] [data-fieldname="default_supplier"]`)
                field.innerHTML = `
                <span data-html="true" data-toggle="tooltip" title="${tooltip}" style="max-width: 400px; white-space: normal; display: inline-block;">
                    ${suppliers[item.item_code].default_supplier_name || "[Undefined]"}
                <i class="fa fa-info-circle"></i></span >
            `;
            }

            // Activate tooltips
            $(function () {
                $('[data-toggle="tooltip"]').tooltip()
            })
        } else if (frm.doc.material_request_type === "Manufacture") {
            frm.add_custom_button(__("Work Order (select items)"),
                () => frm.events.select_items_for_work_orders(frm), __('Create'));
        }
    },


    async select_items_for_work_orders(frm) {
        // Adapted from ERPNext's purchase_order.js
        let values = await bnovate.utils.prompt(
            "Select Items", [{
                fieldname: 'items_for_wo',
                fieldtype: 'Table',
                label: 'Select Items',
                fields: [
                    {
                        fieldtype: 'Data',
                        fieldname: 'item_code',
                        label: __('Item'),
                        read_only: 1,
                        in_list_view: 1
                    },
                    {
                        fieldtype: 'Data',
                        fieldname: 'item_name',
                        label: __('Item name'),
                        read_only: 1,
                        in_list_view: 1
                    },
                ],
                data: cur_frm.doc.items,
                read_only: 1,
            }],
            'Create Work Order',
            'Cancel'
        );
        let selected = values.items_for_wo.filter(v => v.__checked);
        let resp = await frappe.call({
            method: "bnovate.bnovate.utils.controllers.raise_work_orders_for_material_request",
            args: {
                "material_request": frm.doc.name,
                selected,
            },
        });

        if (resp.message.length) {
            frm.reload_doc();
        }

    },
})

async function get_suppliers(frm) {
    let item_masters = await get_item_masters(frm);

    let suppliers = {};
    for (let [item_code, item] of Object.entries(item_masters)) {

        // thanks to https://github.com/frappe/erpnext/issues/19535
        let { default_supplier } = item.item_defaults.find(({ company }) => company === frappe.defaults.get_user_default('company')) || {};

        let default_supplier_name = ""
        if (default_supplier) {
            const supplier = await frappe.model.with_doc("Supplier", default_supplier);
            default_supplier_name = supplier.supplier_name || default_supplier;
        }

        item.supplier_items.forEach(async supplier_item => {
            const supplier_doc = await frappe.model.with_doc("Supplier", supplier_item.supplier);
            supplier_item.supplier_name = supplier_doc?.supplier_name;
        })

        suppliers[item_code] = {
            default_supplier,
            default_supplier_name,
            supplier_items: item.supplier_items,
        };
    }

    return suppliers;
}

async function get_item_masters(frm) {
    let item_codes = [
        ...frm.doc.items?.map(i => i.item_code) || [],
        ...frm.doc.packed_items?.map(i => i.item_code) || [],
    ];

    if (!item_codes) {
        return;
    }

    // let item_masters = {};
    let item_masters = await Promise.all(item_codes.map(it => frappe.db.get_doc("Item", it)));
    return item_masters.reduce((c, n) => ({ ...c, [n.name]: n }), {});
}