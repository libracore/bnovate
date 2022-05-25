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


The main view switches between two tables: read -> write (to adjust quantities, enter S/N....)
*/

// TODO: what if same info is submitted / sent twice? <-- disable submit button. Can still have another tab open.
// More visual feedback when STE is submitted.
// Avoid double clicks on Finish?
// Handle batches
// Handle SNs.
// TODO: auto-populate expiry date based on shelf-life when creating batch.


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
		work_order_id: null, 	// docname of the current workorder
		work_order_doc: null,  	// contents of the current workorder
		docinfo: null, 			// docinfo[doctype][docname] -> {attachments: []}
		view: read,				// state of the items display: read or write
		ste_doc: null, 			// will contain content of stock entry before submitting.
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
			page.set_primary_action('Submit', validate);
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

		// with_doctype loads default for the doctype, populates listview_settings,
		// giving us status indicators
		await frappe.model.with_doctype('Work Order');

		// with_doc returns the doc and populates docinfo, giving us attachments. Force refresh
		frappe.model.clear_doc('Work Order', wo_id);
		state.work_order_doc = await frappe.model.with_doc('Work Order', wo_id);
		state.docinfo = frappe.model.docinfo;
		state.remaining_qty = state.work_order_doc.qty - state.work_order_doc.produced_qty;

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
		// Prompts user for finished qty. Generates stock entry content without submitting to DB,
		// switched view from 'read' to 'write', to allow adjusting qties.
		page.clear_primary_action();
		let qty = await prompt_qty(state.remaining_qty);
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
		for (let input of required_inputs) {
			if (!input.value) {
				input.classList.add('required')
				return false;
			} else {
				input.classList.remove('required')
			}
		}
		return true;
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
	window.validate = validate;

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

		// Create target batch if it doesn't exist
		await create_batch_if_undefined(state.work_order_doc.production_item,
			state.ste_doc.production_item_entry.batch_no);

		// Submit, post comment. Submitted doc now has a docname.
		let submitted_doc = await frappe.db.insert(state.ste_doc);
		let comment = document.getElementById("comment").value;
		if (comment) {
			post_comment(submitted_doc.doctype, submitted_doc.name, comment);
			post_comment(state.work_order_doc.doctype, state.work_order_doc.name, comment);
		}
		frappe.show_alert(`<a href="#Form/Stock Entry/${submitted_doc.name}">${submitted_doc.name} created</a>`)

		// Reload, flash new produced qty
		await state.load_work_order(state.work_order_id)
		document.getElementById("produced-qty").classList.add("pulse-info");
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
		[...document.querySelectorAll("[data-required")]
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