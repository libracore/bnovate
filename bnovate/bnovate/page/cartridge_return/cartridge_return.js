frappe.pages['cartridge-return'].on_page_load = function (wrapper) {

	// LAYOUT STUFF
	///////////////////

	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Cartridge Return',
		single_column: false
	});


	let state = {
		encs: [
		], // will contain list of objects with attributes: serial_no [str], warehouse [str], transferred [bool]
	};
	window.state = state;

	let form = new frappe.ui.FieldGroup({
		fields: [{
			label: 'Instructions',
			fieldname: 'instructions',
			fieldtype: 'HTML',
			options: '<p><b>Scan</b> cartridge enclosure barcodes.</p><p><b>Confirm return</b> will create a stock entry only for cartridges, and only if they are not in "To Refill".`</p>',
		}, {
			label: '',
			fieldtype: 'Column Break',
		}, {
			label: 'statusTable',
			fieldname: 'status_table',
			fieldtype: 'HTML',
			options: '<div id="status_table"></div>',
		}],
		scan_button: scan,
		body: page.body
	});
	form.make();

	const status_table = document.getElementById("status_table");

	const table_template = `
	<table class="table">
		<thead>
		<tr>
			<th>Serial No</th>
			<th>Warehouse</th>
			<th>Customer</th>
			<th>Open Order</th>
			<th>Repair?</th>
			<th></th>
		</tr>
		</thead>
		<tbody>
		{% for enc in encs %}
		<tr>
			<td><a href="/desk#Form/Serial No/{{ enc.serial_no }}" target="_blank">{{ enc.serial_no }}</a></td>
			<td>{{ enc.warehouse }}</td>
			<td>{{ enc.customer_name }}</td>
			<td>
				{% if enc.open_sales_order %}
					<a href="{{ frappe.utils.get_form_link("Sales Order", enc.open_sales_order) }}" target="_blank">{{ enc.open_sales_order }}</a>
				{% endif %}
			</td>
			<td>
				{% if not enc.transferred %}
					<input type="checkbox" class="repair-needed" id="repair-{{ enc.serial_no }}">
				{% endif %}
			</td>
			<td>
				{% if enc.transferred %}
					<i class="octicon octicon-check" style="color: #4bc240"></i>
					<a href="/desk#Form/Stock%20Entry/{{ enc.docname }}" target="_blank">{{ enc.docname }}</a>
				{% else %}
					<button class="btn btn-xs btn-danger remove-rows" data-serial-no="{{ enc.serial_no }}"><i class="octicon octicon-x"></i></button>
				{% endif %}

				<span style="color: #db4242">{{ enc.error }}</span>
			</td>
		</tr>
		{% endfor %}
	</tbody>
	</table>
	`;


	function draw_table() {
		status_table.innerHTML = frappe.render_template(table_template, { encs: Object.values(state.encs) });

		document.querySelectorAll(".remove-rows").forEach((el) => {
			el.addEventListener('click', (e) => {
				state.remove_serial_no(e.currentTarget.dataset.serialNo);
				console.log(e)
			})
		})
	}
	draw_table();

	page.set_primary_action("Confirm return", create_all_entries);
	page.set_secondary_action("Scan", scan);
	// page.add_inner_button("Refresh", () => {
	// 	state.refresh_warehouses().then(draw_table);
	// })

	// DATA STRUCTURE
	////////////////////////

	state.add_serial_no = async function (serial_no) {
		// Ignore if the serial_no already exists
		if (state.encs.findIndex(enc => enc.serial_no == serial_no) < 0) {
			let location = await lookup_location(serial_no);
			state.encs.push({
				serial_no,
				...location,
			})
		}
		draw_table();
	};

	state.remove_serial_no = function (serial_no) {

		let index = state.encs.findIndex(enc => enc.serial_no == serial_no);
		if (index >= 0) {
			state.encs.splice(index, 1);
			draw_table();
		}
	}


	// LOGIC
	////////////////////////

	async function scan() {

		while (true) {
			let serial_no;
			try {
				serial_no = await prompt_serial_no("Scan enclosure S/N");
			} catch (err) {
				// User clicked cancel
				break;
			}
			state.add_serial_no(serial_no);
		}
	}

	async function lookup_location(serial_no) {
		try {
			let sn_doc = await frappe.db.get_doc('Serial No', serial_no);
			let customer = sn_doc.customer; // This never happens with cartridges
			let customer_name = sn_doc.customer_name;
			let item_code = sn_doc.item_code;
			let error = '';

			if (item_code != '100146') {
				error = 'Not a cartridge';
			}
			console.log(sn_doc)
			if ((!customer) && sn_doc.purchase_document_type == "Delivery Note") {
				// Typical configuration of Serial No doc for cartridges after delivery.
				let dn_doc = await frappe.db.get_doc('Delivery Note', sn_doc.purchase_document_no);
				console.log(dn_doc)
				customer = dn_doc.customer;
				customer_name = dn_doc.customer_name;
			}
			return {
				warehouse: sn_doc.warehouse,
				customer: customer,
				customer_name: customer_name,
				open_sales_order: sn_doc.open_sales_order,
				error: error,
			}
		} catch (err) {
			console.log(err);
			return {
				warehouse: 'Not found',
				error: err.statusText,
			}
		}
	}

	async function prompt_serial_no(title) {
		return new Promise((resolve, reject) => {
			let d = new frappe.ui.Dialog({
				title: title,
				fields: [{
					'fieldname': 'serial_no',
					'fieldtype': 'Data',
					'label': 'Serial No',
					// 'options': 'Serial No',
					'reqd': 1,
				}],
				primary_action_label: 'Scan next',
				primary_action: function (values) {
					resolve(values.serial_no.trim());
					this.hide();
				},
				secondary_action_label: 'Cancel',
				secondary_action: function () {
					reject();
				}
			});
			d.show();
		})
	}

	async function create_repack_entry(enc) {
		const needs_repair = document.getElementById(`repair-${enc.serial_no}`).checked;
		const warehouse = needs_repair ? "Repairs - bN" : "To Refill - bN";
		doc = await frappe.db.insert({
			doctype: "Stock Entry",
			title: `Cartridge Return for ${enc.serial_no}`,
			stock_entry_type: "Repack",
			docstatus: 1,
			from_customer: enc.customer,
			items: [{
				item_code: '100146',
				qty: 1,
				s_warehouse: enc.warehouse,
				t_warehouse: warehouse,
				serial_no: enc.serial_no,
			}, {
				item_code: '101011.02', // Tubing pouch 200 mm, needs cleaning
				qty: 3,
				t_warehouse: "Stores - bN",
			}, {
				item_code: '101012.02', // Tubing pouch 120 mm, needs cleaning
				qty: 1,
				t_warehouse: "Stores - bN",
			}, {
				item_code: '100799', // Barrel plug for pouches
				qty: 4,
				s_warehouse: "Stores - bN",
			}]

		});
		return doc;
	}

	async function create_all_entries() {
		for (enc of Object.values(state.encs)) {
			if (enc.warehouse !== "To Refill - bN" && enc.warehouse !== "Repairs - bN" && !enc.error) {
				let doc = await create_repack_entry(enc);
				console.log(doc);
				if (doc) {
					enc.transferred = true;
					enc.warehouse = doc.items[0].t_warehouse;
					enc.url = "/" + doc.name;
					enc.docname = doc.name;
					draw_table();
				}
			}
		}
	}

}