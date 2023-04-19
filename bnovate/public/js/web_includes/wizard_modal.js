const modal_style = `
/* Style needs to be defined outside of shadow DOM. */
:root {
    --number-of-steps: 4;
    --line-width: 2px;
    --bullet-size: 2em;
    
    --line-color: #ffa632;
    --label-color: #575757;
    --completed-background-color: #ffecd4;
    --uncompleted-background-color: #ffffffff;
    
}

.wizard-ribbon {
    display: flex;
    /* justify-content: space-between; */
    align-items: center;
    margin-bottom: 1rem;
}

ol.wizard-ribbon {
    position: relative;
    overflow: hidden;
    counter-reset: wizard 0;
    list-style-type: none;
}

.wizard-ribbon li {
    position: relative;
    float: left;
    width: calc(100% / var(--number-of-steps));
    text-align: center;
    /* color: var(--active-background-color); */
}

.wizard-ribbon .current ~ li {
    color: var(--label-color);
}

.wizard-ribbon li:before {
    counter-increment: wizard;
    content: ""; /* counter(wizard); */
    display: block;
    color: var(--line-color);
    background-color: var(--completed-background-color);
    border: var(--line-width) solid var(--line-color);
    text-align: center;
    width: var(--bullet-size);
    height: var(--bullet-size);
    line-height: var(--bullet-size);
    border-radius: var(--bullet-size);
    position: relative;
    left: 50%;
    margin-bottom: calc(var(--bullet-size) / 2);
    margin-left: calc(var(--bullet-size) * -0.5);
    z-index: 1;
}

.wizard-ribbon .current ~ li:before {
    background-color: var(--uncompleted-background-color);
    color: var(--line-color);
    border-color: var(--line-color);
}

.wizard-ribbon li + li:after {
    content: "";
    display: block;
    width: 100%;
    background-color: var(--line-color);
    height: var(--line-width);
    position: absolute;
    left: -50%;
    top: calc(var(--bullet-size) / 2);
    z-index: 0;
}

.wizard-ribbon .current ~ li:after {
    background-color: var(--line-color);
}

.modal-header {
    background-color: var(--completed-background-color);
}

.wizard-page {
    text-align: center;
}
`
const modal_template = `
<div class="modal" tabindex="-1" role="dialog" id="myModal" style="display:none">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Request Refill</h5>
                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <div class="modal-body">
                
                <ol class="wizard-ribbon">
                    <li class="wizard-step current" data-step="1">Cartridges</li>
                    <li class="wizard-step" data-step="2">Shipping</li>
                    <li class="wizard-step" data-step="3">Billing</li>
                </ol>
                
                <div class="wizard-page" id="page1">
                    <i class="fa fa-cog fa-spin" style="font-size: 20px"></i>
                </div>
                
                <div class="wizard-page" id="page2" style="display: none;">
                </div>
                
                <div class="wizard-page" id="page3" style="display: none;">
                </div>
                <div class="modal-footer">
                    <div class="wizard-buttons">
                        <!-- <button type="button" class="btn btn-danger" id="cancelButton">Cancel</button> -->
                        <button type="button" class="btn btn-secondary" id="prev-button">Previous</button>
                        <button type="button" class="btn btn-primary" id="next-button">Next</button>
                        <button type="button" class="btn btn-primary" id="done-button">Done</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
`

const template_page1 = `
        <table class="table">
            <thead>
                <th>Serial No</th>
                <th>Variant</th>
            </thead>
            <tbody>
                {% for sn in serial_nos %}
                <tr>
                    <td>{{ sn.serial_no }}</td>
                    <td>ICC</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    `
customElements.define('wizard-modal', class extends HTMLElement {
    constructor() {
        super();

        // Data used to build the refill request doc:
        this.serial_nos = [];
        this.doc = {};

        // Initialize the wizard
        this.currentPage = 1;
        this.numPages = 3; // $(".wizard-page").length;

        // Attach template.
        // const template = document.getElementById("wizard-modal-template").content;
        // this.shadowRoot.appendChild(template.cloneNode(true));
        this.attachShadow({ mode: "open" });
        this.shadowRoot.innerHTML = modal_template;

        // Create some CSS to apply to the shadow DOM
        const style = document.createElement("style");
        style.textContent = modal_style;
        document.head.appendChild(style)

        this.modal = this.shadowRoot.getElementById("myModal");
        this.next = this.shadowRoot.getElementById("next-button");
        this.prev = this.shadowRoot.getElementById("prev-button");
        this.done = this.shadowRoot.getElementById("done-button");

        $(this.modal).on('show.bs.modal', (e) => {
            this.currentPage = 1;
            this.showPage(this.currentPage);

            console.log(this.serial_nos);
            console.log(frappe.render_template(template_page1, {
                serial_nos: this.serial_nos,
            }))

            e.target.querySelector('.modal-body #page1').innerHTML = frappe.render_template(template_page1, {
                serial_nos: this.serial_nos,
            });
        })

        $(this.modal).on('hide.bs.modal', (e) => {
            // e.target.querySelector('.modal-body #page1').innerHTML = '';
        })

        // Add event listeners to the navigation buttons
        $(this.prev).click(() => {
            if (this.currentPage > 1) {
                this.currentPage--;
                this.showPage(this.currentPage);
            }
        });

        $(this.next).click(() => {
            console.log("next", this.currentPage, this.numPages)
            if (this.currentPage < this.numPages) {
                this.currentPage++;
                this.showPage(this.currentPage);
            }
        });

        $(this.cancel).click(() => {
            // Close the modal or redirect to another page
            $(this.modal).modal("hide");
        });
    }

    show(serial_nos) {
        this.serial_nos = serial_nos;
        $(this.modal).modal({ backdrop: 'static', keyboard: false });
        console.log(this.serial_nos);
    }

    // Show or hide the navigation buttons based on the current page
    updateButtons() {
        if (this.currentPage == 1) {
            this.prev.disabled = true;
        } else {
            this.prev.disabled = false;
        }

        if (this.currentPage == this.numPages) {
            this.next.hidden = true;
            this.done.hidden = false;
        } else {
            this.next.hidden = false;
            this.done.hidden = true;
        }

        $(".wizard-step").removeClass("current");
        $(`.wizard-step[data-step='${this.currentPage}']`).addClass("current");
    }

    // Show the specified page and update the navigation buttons
    showPage(page) {
        $(".wizard-page").hide();
        $("#page" + page).show();
        this.updateButtons();
    }
})