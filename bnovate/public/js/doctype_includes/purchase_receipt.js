/* Customisations for Purchase Receipt 
 * 
 * Included by hooks.py to add client-side code
 * (same effect as writing a custom script)
 */

frappe.require("/assets/bnovate/js/iot.js")  // provides bnovate.iot

frappe.ui.form.on("Purchase Receipt", {
    scan(frm) {
        scan_serialized_items(frm);
    }
})
async function get_item_masters(frm) {
    let item_codes = [
        ...frm.doc.items?.map(i => i.item_code) || [],
    ];

    if (!item_codes) {
        return;
    }

    let item_masters = await frappe.db.get_list("Item", {
        fields: ['name', 'has_serial_no', 'item_name'],
        filters: { name: ['in', item_codes] }
    })

    return item_masters.reduce((c, n) => ({ ...c, [n.name]: n }), {});
}

async function prompt_serial_no(title, description) {
    const values = await bnovate.utils.prompt(title,
        [{
            fieldname: 'serial_no',
            fieldtype: 'Data',
            label: 'Serial No',
            // 'options': 'Serial No',
            reqd: 1,
        }, {
            fieldname: 'description',
            fieldtype: 'HTML',
            options: description || '',
        }], "Scan Next", "Cancel");
    return values.serial_no;
}

async function scan_serialized_items(frm) {
    let masters = await get_item_masters(frm);
    console.log(masters);
    for (let item of frm.doc.items) {
        // Items with serial numbers directly on the item (as opposed to packed item)
        if (item.item_code && masters[item.item_code].has_serial_no) {
            console.log(item);
            let accumulator = [];
            for (let i = 0; i < item.qty; i++) {
                let serial_no = await prompt_serial_no(
                    `Scan item ${masters[item.item_code].item_name} - no ${i + 1}/${item.qty}`,
                    `
                    <table class="table">
                    <thead>
                        <tr>
                            <th>Sr</th>
                            <th>Item Code</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>${item.idx}</td>
                            <td>${item.item_code}</td>
                            <td>
                                <b>${masters[item.item_code].item_name}</b><br /> 
                                ${item.description}
                                <br /><br />
                                <div style="background-color: #fffdf4;">
                                    <b>Serial numbers:</b> ${accumulator.join(" ")}
                                </div>
                            </td>
                        </tr>
                    </tbody>
                    </table>
                    `
                );

                if (!serial_no) {
                    break;
                }

                if (serial_no.indexOf(';') >= 0) {
                    // Looks like a Teltonika SN
                    const values = bnovate.iot.decode_teltonika_qr(serial_no);
                    serial_no = values.teltonika_serial;
                }
                accumulator.push(serial_no.trim());
                frappe.model.set_value(item.doctype, item.name, "serial_no", accumulator.join("\n"));
                frm.refresh_field("items");
            }
        }
    }
}