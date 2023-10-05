const wizard_template = `
`;

const template_page4 = `
`

class WizardPage {
    constructor(elementId, validate, callback) {
        this.element = document.getElementById(elementId);
        this.validate = validate;
        this.callback = callback;

        // Initialize the wizard
        this.currentPage = 1;
        this.numPages = 4; // $(".wizard-page").length;

        this.next = document.getElementById("next-button");
        this.prev = document.getElementById("prev-button");
        this.done = document.getElementById("confirm-button");

        // Add event listeners to the navigation buttons
        $(this.prev).click(() => {
            this.prev_page();
        });

        $(this.next).click(() => {
            this.next_page();
        });

        $(this.cancel).click(() => {
            // Close the modal or redirect to another page
            $(this.modal).modal("hide");
        });

        $(this.done).click(() => {
            this.confirm();
        });

        this.bind_listeners();
        this.show_page(1);
    }

    prev_page() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.show_page(this.currentPage);
        }
    }

    next_page() {
        if (this.currentPage < this.numPages) {
            this.currentPage++;
            this.show_page(this.currentPage);
        }
    }

    update_buttons() {
        if (this.currentPage == 1) {
            this.prev.disabled = true;
        } else {
            this.prev.disabled = false;
        }


        if (this.currentPage == this.numPages) {
            this.next.hidden = true;
            this.done.hidden = true;
        } else if (this.currentPage == 3) {
            this.next.hidden = true;
            this.done.hidden = false;
        } else {
            this.next.hidden = false;
            this.done.hidden = true;
        }

        $(".wizard-step").removeClass("current");
        $(`.wizard-step[data-step='${this.currentPage}']`).addClass("current");
    }

    bind_listeners() {
        [...document.querySelectorAll("input")].map(el => el.addEventListener('change', () => {
            this.enable_buttons();
        }));
    }

    // Enable or disable buttons based on form completion
    enable_buttons() {
        if (this.currentPage == 1) {
            this.next.disabled = false;
        } else if (this.currentPage == 2) {
            this.next.disabled = false;
        } else if (this.currentPage == 3) {
            if (this.validate()) {
                this.done.disabled = false;
            } else {
                this.done.disabled = true;
            }
        }
    }

    // Show the specified page and update the navigation buttons
    show_page(page) {
        // if (page == this.numPages) {
        //     this.element.querySelector('#page' + page).innerHTML = frappe.render_template(
        //         template_page4,
        //         { doc: {} }
        //     );
        // }

        $(".wizard-page").hide();
        $("#page" + page).show();

        this.update_buttons();
        this.enable_buttons();
    }

    async confirm() {
        this.done.disabled = true;
        this.next_page();
        await this.callback();
    }
}