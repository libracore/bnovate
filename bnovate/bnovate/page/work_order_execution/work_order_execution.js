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
// Add field for operator to add comments.


frappe.provide("frappe.bnovate.work_order_execution")

frappe.pages['work-order-execution'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Work Order Execution',
		single_column: true,
	});
	frappe.bnovate.work_order_execution.page = page; // for easier debugging

	const read = Symbol("read");
	const write = Symbol("write");

	const state = {
		work_order_id: undefined, 	// docname of the current workorder
		work_order_doc: undefined,  // contents of the current workorder
		docinfo: undefined, 		// docinfo[doctype][docname] -> {attachments: []}
		view: read,					// state of the items display: read or write
		ste_doc: undefined, 		// will contain content of stock entry before submitting.
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
		if (state.view == read) {
			item_content.innerHTML = frappe.render_template('items_read', {
				doc: state.work_order_doc,
			})
		} else if (state.view == write) {
			item_content.innerHTML = frappe.render_template('items_write', {
				doc: state.ste_doc,
			})
		}

		page.clear_primary_action();
		if (state.remaining_qty > 0) {
			if (state.view == read) {
				page.set_primary_action('Finish', finish);
			} else {
				page.set_primary_action('Submit', submit);
			}
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
		state.work_order_id = wo_id;

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
		ste.docstatus = 1;
		ste.required_items = ste.items.filter(i => i.s_warehouse);
		state.ste_doc = ste;
		state.view = write;
		draw();
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

		// Submit and refresh
		await frappe.db.insert(state.ste_doc);
		state.view = read;

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
	frappe.bnovate.work_order_execution.post_comment = post_comment;

	// LISTENERS
	////////////////////////////

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