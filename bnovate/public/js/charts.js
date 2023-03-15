/* Modals.js. (c) 2023, bNovate.
 *
 * Custom chart creation for bNovate app
 * 
 *  * Timeline: google Timeline chart
 * 
 * 
 ****************************************************/

frappe.provide('bnovate.charts');

/* Add a Google Timeline chart to the chart area of a report. 

Tooltips are replaced by Bootstrap popovers and can contain any HTML.

    report: frappe.query_report object
    build_dt: function that takes report and returns a google table formatted for a timeline

        Column spec: row, label, tooltip, [style,] start_date, end_date
*/
bnovate.charts.draw_timeline_chart = function (report, build_dt) {
    report.$chart.html(`
            <div class="chart-container">
                <div id="timeline" class="report-chart">Timeline</div>
            </div>
    `);

    // Track mouse position in chart to draw popover at correct location
    report.mousePos = { x: 0, y: 0 };
    let container = document.getElementById("timeline");
    document.addEventListener("mousemove", (e) => {
        report.mousePos.x = e.pageX;
        report.mousePos.y = e.pageY;
    });

    // Popover is the popup shown when clicking a bar on the timeline chart.
    // #sacrificial is a little 0x0 px square created at the location clicked.
    function dismiss_popover() {
        $('#sacrificial').popover('hide');
        $('#sacrificial').remove();
    }

    google.charts.load('current', { 'packages': ['timeline'] });
    google.charts.setOnLoadCallback(drawChart);
    function drawChart() {
        let chart = new google.visualization.Timeline(container);
        report.chart = chart;

        report.chart_dt = build_dt(report);

        // Show a popover when a timeline element is clicked. Popovers in bootstrap 3 don't
        // delete nicely, so I made a workaround where I create a sacrificial div centered on the
        // click and bind the popover to this div.
        google.visualization.events.addListener(chart, 'select', () => {

            dismiss_popover();


            $(document.body).append(
                `<div id="sacrificial" style="left: ${report.mousePos.x}px; top: ${report.mousePos.y}px"></div>`
            )
            console.log("reached here")

            let row = chart.getSelection()[0].row;
            let contents = report.chart_dt.getValue(row, 2);

            $("#sacrificial").popover({
                container: "body",
                title: "My fancy popover",
                html: true,
                content: contents,
                placement: "bottom",
            }).popover('show');

        });

        // Any click outside the popover dismisses it. May interfere with other popovers...
        document.addEventListener("click", (event) => {
            const popover = $(".popover");
            if (popover.is(event.target) || popover.has(event.target).length) {
                // Ignore if click target is inside a popover
                return;
            }
            dismiss_popover();
        });
        frappe.route.on('change', () => { dismiss_popover() });

        chart.draw(report.chart_dt, {
            height: 250,
            fontName: "Open Sans",
            tooltip: {
                // isHtml: true,
                trigger: 'both', // disable it

            },
        });
    }
}