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
        }, {
            "fieldname": "reminders_only",
            "label": __("Show only reminders"),
            "fieldtype": "Check",
        }, {
            "fieldname": "include_drafts",
            "label": __("Include Drafts"),
            "fieldtype": "Check",
            "default": 0
        }
    ],
    onload(report) {
        this.report = report;

        // Copied from listview get_indicator
        this.status_color = {
            "Draft": "red",
            "Active": "green",
            "Finished": "darkgrey",
            "Stopped": "darkgrey",
            "Cancelled": "darkgrey",
        };
    },
    after_datatable_render(datatable) {
        bnovate.charts.draw_timeline_chart(this.report, build_subscription_dt);
    },
    formatter(value, row, col, data, default_formatter) {
        if (col.fieldname === "status") {
            let color = this.status_color[data.status] ? this.status_color[data.status] : "grey";
            return `<span class="indicator ${color}">${default_formatter(value, row, col, data)}</span>`
        }
        return default_formatter(value, row, col, data);
    },
};

function build_subscription_dt(report) {
    var dataTable = new google.visualization.DataTable();

    dataTable.addColumn({ type: 'string', id: 'Customer Name' });
    dataTable.addColumn({ type: 'string', id: 'Subscription' });
    dataTable.addColumn({ type: 'string', id: 'tooltip', role: 'tooltip' });
    dataTable.addColumn({ type: 'string', id: 'style', role: 'style' });
    dataTable.addColumn({ type: 'date', id: 'Start' });
    dataTable.addColumn({ type: 'date', id: 'End' });

    const colorMap = {
        "Draft": "#ff5858",
        "Active": "#98d85b",
        "Finished": "#b8c2cc",
        "Stopped": "#b8c2cc",
        "Cancelled": "#b8c2cc",
    }

    let rows = report.data.map(row => [
        row.customer_name,
        `${row.subscription}: ${row.title}`,
        frappe.render_template(popover_template, row),
        `color: ${colorMap[row.status]}`,
        frappe.datetime.str_to_obj(row.start_date),
        frappe.datetime.str_to_obj(row.computed_end_date),
    ]);

    console.log(rows)

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