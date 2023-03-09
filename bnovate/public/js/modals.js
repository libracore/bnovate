/* Modals.js. (c) 2023, bNovate.
 *
 * Custom modal creation for bNovate app
 * 
 * report_modal: modal that shows the chart and datatable from a report with specific filters.
 *      It can't use report filters named `target`, `report_name`, or `toggle...`.
 * 
 * 
 ****************************************************/

frappe.provide('bnovate.modals');

// Call this once on the page, specify an id of your choice.
// element, if specified, should be a jquery element (like most of frappe's elements). 
// Typically this would be the $page element
bnovate.modals.attach_report_modal = function (modal_id, element) {
    if (element == undefined) {
        element = cur_page.page.page.wrapper;
    }

    // Add a modal in which we can render other reports
    element.append(`
        <div class="modal fade bn-modal" id="${modal_id}" tabindex="-1" aria-labelledby="${modal_id}Label" aria-hidden="true">
        <div class="modal-dialog modal-xl">
            <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="${modal_id}Label">Loading...</h5>
            </div>
            <div class="modal-body">
                <div class="message-wrapper">
                    <!-- Placeholder for chart -->
                </div>
                <div class="chart-wrapper">
                    <!-- Placeholder for chart -->
                </div>
                <div class="report-wrapper" align="center" style="display: block">
                    <i class="fa fa-cog fa-spin" style="font-size: 20px"></i>
                </div>
                </div>
            </div>
            </div>
        </div>
        </div>
    `)
    console.log("modal bound to page")
    $('#' + modal_id).on('hide.bs.modal', (e) => {
        // reset contents when modal is hidden
        e.target.querySelector('.chart-wrapper').innerHTML = '';
        e.target.querySelector('.report-wrapper').innerHTML = '<i class="fa fa-cog fa-spin" style="font-size: 20px"></i>';
    });
    $('#' + modal_id).on('show.bs.modal', (e) => {
        console.log(e);
        // relatedTarget is the link that was clicked, should be created by
        // report_link() below.
        let report_name = e.relatedTarget.dataset.report_name;
        let title = e.relatedTarget.dataset.title;

        // remove attributes that we know for sure are not used filters but to launch the modal
        let filters = Object.fromEntries(
            Object.entries(e.relatedTarget.dataset)
                .filter(([k, v]) => ["report_name", "title", "target", "toggle"].indexOf(k) < 0)
        )
        console.log(filters);
        _draw_report($(e.target), report_name, title, filters);
    });
};

async function _draw_report(target, report_name, title, filters) {
    target.find(".modal-title").html(title);
    const resp = await frappe.call({
        method: "frappe.desk.query_report.run",
        args: {
            report_name,
            filters
        }
    });

    const report_data = resp.message;

    const report = new frappe.views.QueryReport({
        parent: target,
        report_name: "Projected Stock",
        $report: target.find('.report-wrapper'),
        $chart: target.find('.chart-wrapper'),
        $message: target.find('.message-wrapper'),
    });
    await report.get_report_doc();
    await report.get_report_settings();
    report.prepare_report_data(report_data);

    setTimeout(() => {
        report.render_datatable();
        report.render_chart(report_data.chart);
    }, 500)
}

bnovate.modals.report_link = function (text, modal_id, report_name, title, filters) {
    // Create a link that pops up the report modal
    // returns an HTML string like `<a data-toggle="modal" ...>Text</a>`
    let linky = document.createElement("a");
    linky.innerHTML = text;
    Object.assign(linky.dataset, {
        toggle: "modal",
        target: '#' + modal_id,
        report_name,
        title,
        ...filters,
    })
    return linky.outerHTML;
}