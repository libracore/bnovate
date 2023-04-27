const modal_style = `
/* Style needs to be defined outside of shadow DOM. */


.wizard-page textarea {
}
</style >
`

customElements.define('address-modal', class extends HTMLElement {
    constructor() {
        super();

        window.theModal = this;

        // Data used to build the refill request doc:
        this.address = {};
    }

    draw(contents) {
        // Attach template. Only draw when modal is summoned, makes it more likely that translations are loaded.
        this.attachShadow({ mode: "open" });
        // this.shadowRoot.innerHTML = frappe.render_template(modal_template, {});
        this.shadowRoot.appendChild(contents)

        const style = document.createElement("style");
        style.textContent = modal_style;
        document.head.appendChild(style);

        this.modal = this.shadowRoot.getElementById("myModal");
        this.cancel = this.shadowRoot.getElementById("cancel-button");
        this.save = this.shadowRoot.getElementById("save-button");

        $(this.modal).on('show.bs.modal', (e) => {
            this.bind_listeners(e.target);
        })

        $(this.modal).on('hide.bs.modal', (e) => {
            // e.target.querySelector('.modal-body #page1').innerHTML = '';
        })

        $(this.cancel).click(() => {
            // Close the modal or redirect to another page
            $(this.modal).modal("hide");
        });

        $(this.save).click(() => {
            this.confirm();
        });
    }

    async show(contents, callback) {
        if (!this.shadowRoot) {
            this.draw(contents);
        }
        this.callback = callback;
        $(this.modal).modal({ backdrop: 'static', keyboard: false });
    }

    hide() {
        $(this.modal).modal('hide');
    }


    // Enable or disable buttons based on form completion
    enable_buttons() {
        const doc = this.build_doc()
    }

    // Set all blank variant selects when the first one is modified
    bind_listeners(el) {
    }

    build_doc() {
        const frm = document.querySelector("#address-form");
        const data = new FormData(frm);
        return Object.fromEntries(data);
    }

    confirm() {
        this.callback(this.build_doc());
        this.hide();
    }
})