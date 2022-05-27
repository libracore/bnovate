/*
Work Order Execution Page
-------------------------

* D. Watson, 2022

This page provides tools for operators to validate execution of work orders.

The workflow goes:

- Load this page, either from a button on WO or by scanning a QR code
- View key information (required items, links to work instructions, comments)
- When work is done, a couple steps:
	- Click "finish", indicate number of finished parts.
	- Adjust quantities of consumed items, add new ones if needed.
	- Submit -> Creates stock entry, redirects to "view" state


The main view switches between two tables: read and write (to adjust quantities, enter S/N....)

For serialized items, we force entry of components for one item at a time, so the "Submit" button becomes a "Next" button.
*/

// TODO: what if same info is submitted / sent twice? <-- From another tab open for example.
// Handle SNs.
// Handle expiry dates for fills and refills.
// Fix valuation - client side scripts are no longer called. Maybe fetch my own custom script?
//  Or move my script to a JS library function.
// Consider removing "view" mode for serialized items.
// Consider switching to serialized view if any serialized items are present. It shouldn't happen, but why not.

frappe.provide("frappe.bnovate.work_order_execution")

frappe.pages['work-order-execution'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Work Order Execution',
		single_column: true,
	});
	frappe.bnovate.work_order_execution.page = page; // for easier debugging
	window.page = page;

	const read = Symbol("read");
	const write = Symbol("write");

	const state = {
		work_order_id: null, 		// docname of the current workorder
		work_order_doc: null,  		// contents of the current workorder
		docinfo: null, 				// docinfo[doctype][docname] -> {attachments: []}
		view: read,					// state of the items display: read or write
		ste_doc: null, 				// will contain content of stock entry before submitting.
		produce_serial_no: false,	// true if produced item needs a serial number.
		serial_no_remaining: 0  	// when producing with S/N, loop this many more times
	}
	frappe.bnovate.work_order_execution.state = state;
	window.state = state;

	let form = new frappe.ui.FieldGroup({
		fields: [{
			label: 'Work Order',
			fieldname: 'work_order',
			fieldtype: 'Link',
			options: 'Work Order',
		}, {
			label: '',
			fieldtype: 'Column Break',
		}, {
			label: '',
			fieldtype: 'Column Break',
		}, {
			label: '',
			fieldtype: 'Section Break',
		}, {
			label: 'Main',
			fieldname: 'main',
			fieldtype: 'HTML',
			options: '<div id="main"></div>',
		}, {
			label: 'Items',
			fieldname: 'items',
			fieldtype: 'HTML',
			options: '<div id="items"></div>',
		}],
		body: page.body
	});
	form.make();

	const work_order = form.fields_dict.work_order.wrapper;
	const main_content = document.getElementById('main');
	const item_content = document.getElementById('items');

	function draw() {
		main_content.innerHTML = frappe.render_template('work_order_execution', {
			doc: state.work_order_doc,
			docinfo: state.docinfo,
			attachments: state.attachments,
		});

		page.clear_primary_action();
		if (state.view == read) {
			item_content.innerHTML = frappe.render_template('items_read', {
				doc: state.work_order_doc,
			});
			if (state.remaining_qty > 0 && state.work_order_doc.docstatus == 1 && state.work_order_doc.status != "Stopped") {
				page.set_primary_action('Finish', finish);
			}
		} else if (state.view == write) {
			item_content.innerHTML = frappe.render_template('items_write', {
				doc: state.ste_doc,
			});
			if (state.serial_no_remaining > 0) {
				page.set_primary_action('Next', validate);
			} else {
				page.set_primary_action('Submit', validate);
			}
			attach_validator();
		}

		let doc = state.work_order_doc;
		page.set_title(`Work Order Execution: ${doc.item_name}`);
		page.set_indicator(
			state.work_order_doc.status,
			// use frappe's built-in indicator colour logic.
			frappe.listview_settings['Work Order'].get_indicator(state.work_order_doc)?.[1]
		);
	}

	// DATA STRUCTURE
	////////////////////////////

	// TODO: Refactor to load_work_order: downloads the docs, sets the ID in the state etc.
	state.load_work_order = async (wo_id) => {
		state.view = read; 				// reset view
		state.work_order_id = wo_id;
		state.ste_doc = null;
		state.produce_serial_no = false;
		state.serial_no_remaining = 0;

		// with_doctype loads default for the doctype, populates listview_settings,
		// giving us status indicators
		await frappe.model.with_doctype('Work Order');

		// with_doc returns the doc and populates docinfo, giving us attachments. Force refresh
		frappe.model.clear_doc('Work Order', wo_id);
		state.work_order_doc = await frappe.model.with_doc('Work Order', wo_id);
		state.docinfo = frappe.model.docinfo;
		state.remaining_qty = state.work_order_doc.qty - state.work_order_doc.produced_qty;

		// should we switch to serialized behaviour?
		await fetch_item_details([state.work_order_doc.production_item]);
		state.produce_serial_no = locals["Item"][state.work_order_doc.production_item].has_serial_no;

		// BOMs can't change after submit, no need to clear cache
		state.bom_doc = await frappe.model.with_doc('BOM', state.work_order_doc.bom_no);

		state.attachments = [];
		state.attachments.push(
			...state.docinfo['Work Order'][wo_id].attachments || [],
			...state.docinfo['BOM'][state.work_order_doc.bom_no].attachments || []
		);
		draw();
	}

	// LOGIC
	////////////////////////////
	async function finish() {
		// Prompts user for finished qty.
		page.clear_primary_action();

		let qty = await prompt_qty(state.remaining_qty);

		if (qty == 0) {
			return;
		}
		if (state.produce_serial_no) {
			state.serial_no_remaining = qty - 1;
			return await build_ste(1)
		}
		return await build_ste(qty);
	}

	async function build_ste(qty) {
		// Build stock entry and switch items table from read to write view to allow adjusting qties
		let ste = await frappe.xcall('erpnext.manufacturing.doctype.work_order.work_order.make_stock_entry', {
			'work_order_id': state.work_order_id,
			'purpose': 'Manufacture',
			'qty': qty,
		})
		ste.title = `Manufacture for ${ste.work_order}`;

		// Attach batch and sn requirements.
		await fetch_item_details(ste.items.map(sti => sti.item_code));
		for (let item of ste.items) {
			item.has_batch_no = locals["Item"][item.item_code].has_batch_no;
			item.has_serial_no = locals["Item"][item.item_code].has_serial_no;
		}
		ste.production_item_entry = ste.items.find(it => it.item_code == state.work_order_doc.production_item);

		// Prepare doc for final editing in "write" view
		ste.docstatus = 1;
		ste.required_items = ste.items.filter(i => i.s_warehouse);
		state.ste_doc = ste;
		state.view = write;
		draw();
	}

	function validate_inputs() {
		// Enable Submit button only if all required fields have values.
		const required_inputs = [...document.querySelectorAll("[data-required]")];
		let valid = true;
		for (let input of required_inputs) {
			if (!input.value) {
				input.classList.add('required')
				valid = false;
			} else {
				input.classList.remove('required')
			}
		}
		return valid;
	}

	function validate() {
		// Calls submit() if form is valid. Else shows alert.
		page.btn_primary.prop("disabled", true);

		if (!validate_inputs()) {
			page.btn_primary.prop("disabled", false);
			frappe.msgprint({
				title: 'Missing Fields',
				indicator: 'red',
				message: 'Please complete required fields',
			});
			return;
		}

		submit();
	}

	async function submit() {
		// Submits STE with adjusted qties to db.
		page.clear_primary_action();

		// Get adjusted quantities, apply to STE items
		[...document.querySelectorAll("input.qty-delta")]
			.map(el => [el.dataset.idx, parseFloat(el.value) || 0])
			.map(([idx, delta]) => {
				state.ste_doc.items.find(i => i.idx == idx).qty += delta;
			});
		// Same for batches, only on select items.
		[...document.querySelectorAll("input.batch")]
			.map(el => [el.dataset.idx, el.value || 0])
			.map(([idx, batch_no]) => {
				state.ste_doc.items.find(i => i.idx == idx).batch_no = batch_no;
			}); // BTW, this also modifies the same object pointed to from production_item_entry.
		// And for serial no
		[...document.querySelectorAll("input.serial")]
			.map(el => [el.dataset.idx, el.value || 0])
			.map(([idx, serial_no]) => {
				state.ste_doc.items.find(i => i.idx == idx).serial_no = serial_no;
			});

		if (state.ste_doc.production_item_entry.has_batch_no) {
			// Create target batch if it doesn't exist
			await create_batch_if_undefined(state.work_order_doc.production_item,
				state.ste_doc.production_item_entry.batch_no);
		}

		handle_scrap(state.ste_doc, state.work_order_doc.production_item);
		handle_fills(state.ste_doc, state.work_order_doc.production_item);

		// Submit, post comment. Submitted doc now has a docname.
		let submitted_doc = await frappe.db.insert(state.ste_doc);
		let comment = document.getElementById("comment").value;
		if (comment) {
			post_comment(submitted_doc.doctype, submitted_doc.name, comment);
			post_comment(state.work_order_doc.doctype, state.work_order_doc.name, comment);
		}
		frappe.show_alert(`<a href="#Form/Stock Entry/${submitted_doc.name}">${submitted_doc.name} created</a>`)

		if (state.serial_no_remaining > 0) {
			state.serial_no_remaining -= 1;
			return await build_ste(state.serial_no_remaining);
		}
		// Reload, flash new produced qty
		await state.load_work_order(state.work_order_id)
		document.getElementById("produced-qty").classList.add("pulse-info");
	}

	function handle_scrap(ste_doc, bom_item) {
		// Cleans up exceptions related to scrap items.
		// Finds scrap items with matching SNs in 'input' items and copies SN over

		let scrap_items = ste_doc.items.filter(it => !it.s_warehouse && it.item_code !== bom_item);
		let input_items = ste_doc.items.filter(it => !!it.s_warehouse);

		for (let scrap_item of scrap_items) {
			scrap_item.serial_no = input_items
				.filter(it => it.item_code == scrap_item.item_code)
				.map(it => it.serial_no)
				.join("\n");
		}
	}

	function handle_fills(ste_doc, bom_item) {
		// Handles special workflows related to fills refills
		// - builds "fill associations" table.
		// Assumes all serial numbers are filled in ste_doc.items.

		if (!bom_item.startsWith("FIL")) {
			return;
		}

		let enc_sn = ste_doc.items.find(it => !it.s_warehouse && it.item_code == "100146")?.serial_no;
		let fill_sn = ste_doc.items.find(it => !it.s_warehouse && it.item_code == bom_item)?.serial_no;

		if (enc_sn && fill_sn) {
			ste_doc.fill_associations = [{
				enclosure_serial: enc_sn,
				fill_serial: fill_sn,
			}];
		}

	}

	async function prompt_qty(default_qty) {
		return new Promise((resolve, reject) => {
			let d = new frappe.ui.Dialog({
				title: "Enter number of produced items",
				fields: [{
					'fieldname': 'qty',
					'fieldtype': 'Float',
					'label': 'Quantity',
					'default': default_qty,
					// 'options': 'Serial No',
					'reqd': 1,
				}],
				primary_action_label: 'OK',
				primary_action: function (values) {
					resolve(values.qty);
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

	// SERVER CALLS
	////////////////////////////

	async function post_comment(doctype, docname, comment) {
		await frappe.call({
			"method": "frappe.desk.form.utils.add_comment",
			"args": {
				reference_doctype: doctype,
				reference_name: docname,
				content: comment,
				comment_email: frappe.session.user,
				comment_by: frappe.session.user_fullname,
			}
		});
	}

	async function fetch_item_details(item_codes) {
		// Fetch item detail docs, store in locals["Items"].
		let promises = [];
		for (let item_code of item_codes) {
			promises.push(frappe.model.with_doc("Item", item_code));
		}

		return Promise.all(promises);
	}

	async function create_batch_if_undefined(item_code, batch_no) {
		// Creates batch if it doesn't exist yet
		let batch_doc = await frappe.model.with_doc("Batch", batch_no);
		if (batch_doc) {
			return batch_doc
		}
		return await frappe.db.insert({
			doctype: "Batch",
			title: `${batch_no} for item ${item_code}`,
			batch_id: batch_no,
			item: item_code,
		})
	}

	// LISTENERS
	////////////////////////////

	function attach_validator() {
		[...document.querySelectorAll("[data-required]")]
			.map(el => el.addEventListener("change", validate_inputs))
	}

	work_order.addEventListener("change", (e) => {
		state.load_work_order(e.target.value);
	})

	page.wrapper.on('show', (e) => {
		if (frappe.route_options.work_order) {
			form.set_value('work_order', frappe.route_options.work_order);
			state.load_work_order(frappe.route_options.work_order)
		}
	});

}