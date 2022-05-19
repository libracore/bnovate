frappe.provide("frappe.bnovate.work_order_execution")

frappe.pages['work-order-execution'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Work Order Execution',
		single_column: true,
	});
	frappe.bnovate.work_order_execution.page = page; // for easier debugging

	const state = {
		work_order_id: undefined,
		work_order_doc: undefined,
		docinfo: undefined, // docinfo[doctype][docname] -> {attachments: []}
	}
	frappe.bnovate.work_order_execution.state = state;

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
		}],
		body: page.body
	});
	form.make();

	const work_order = form.fields_dict.work_order.wrapper;
	const main_content = document.getElementById('main');

	function draw() {
		frappe.bnovate.work_order_execution.attachments = state.docinfo["Work Order"][state.work_order_id];

		main_content.innerHTML = frappe.render_template('work_order_execution', {
			doc: state.work_order_doc,
			docinfo: state.docinfo,
			attachments: state.docinfo["Work Order"][state.work_order_id].attachments,
		});

		if (state.remaining_qty) {
			page.set_primary_action('Finish', finish);
		}

		page.set_title(`Work Order Execution: ${state.work_order_doc.item_name}`);
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
		draw();
	}

	// LOGIC
	////////////////////////////
	async function finish() {
		let qty = await prompt_qty(state.remaining_qty);
		frappe.xcall('erpnext.manufacturing.doctype.work_order.work_order.make_stock_entry', {
			'work_order_id': state.work_order_id,
			'purpose': 'Manufacture',
			'qty': qty,
		}).then(ste => {
			ste.title = `Manufacture for ${ste.work_order}`;
			ste.docstatus = 1;
			console.log(ste)
			return frappe.db.insert(ste)
		}).finally(() => { state.load_work_order(state.work_order_id) });
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