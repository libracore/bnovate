// Copyright (c) 2023, bNovate, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.require("/assets/bnovate/js/lib/gcharts/loader.js")
frappe.require("/assets/bnovate/js/charts.js")

frappe.query_reports["Subscription Timeline"] = {
    filters: [
        {
            "fieldname": "customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer"
        },

    ],
    onload(report) {
        this.report = report;
    },
    after_datatable_render(datatable) {
        bnovate.charts.draw_timeline_chart(this.report, build_subscription_dt);
    },
};

function build_subscription_dt(report) {
    var dataTable = new google.visualization.DataTable();

    dataTable.addColumn({ type: 'string', id: 'Customer Name' });
    dataTable.addColumn({ type: 'string', id: 'Subscription' });
    dataTable.addColumn({ type: 'string', id: 'tooltip', role: 'tooltip' });
    // dataTable.addColumn({ type: 'string', id: 'style', role: 'style' });
    dataTable.addColumn({ type: 'date', id: 'Start' });
    dataTable.addColumn({ type: 'date', id: 'End' });

    let rows = report.data.map(row => [
        row.customer_name,
        `${row.subscription}: ${row.title}`,
        frappe.render_template(popover_template, row),
        frappe.datetime.str_to_obj(row.start_date),
        frappe.datetime.str_to_obj(row.computed_end_date),
    ]);

    dataTable.addRows(rows);

    return dataTable;
}

const popover_template = `
    <div class="preview-popover-header">
        <div class="preview-header">
        </div>

        <div class="preview-header">
            <div class="preview-main">
                {{ subscription }}: {{ title }}
                <span class="small preview-value">
                </span>
                <br>
                <span class="small text-muted">{{ start_date }} {% if end_date %} - {{ end_date }}{% endif %}</span>
            </div>
        </div>
    </div>
    <hr>
    <div class="popover-body">
        <div class="preview-table" style="max-width: none">
            <div class="preview-field">
                <div class="small preview-label text-muted bold">Planned End Date</div>
                <div class="small preview-value">{{ planned_end_date || "TBD" }}</div>
            </div>
            <div class="preview-field">
                <div class="small preview-label text-muted bold">Actual End Date</div>
                <div class="small preview-value">{{ end_date || "TBD" }}</div>
            </div>

        </div>
    </div>
`