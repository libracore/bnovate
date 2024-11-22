// Hacky way to redirect to the last viewed page after a login.

// Everytime a visitor loads a page that requires login, we save the last visited
// page to localStorage (see message.py and message.hml)
//
// Social auth redirects to /me after login, and regular auth redirects to /. 
// If we land on one of those two pages, check if localStorage has a last visited
// page and redirect if so. The HTML templates for those pages call redirect_if_needed()


function redirect_if_needed() {
    dest_path = localStorage.getItem("return_to_path");
    if (!dest_path) {
        return;
    }

    localStorage.removeItem("return_to_path");
    if (location.pathname === dest_path) {
        return;
    }

    frappe.show_progress("Redirecting...", 1, 10);
    setTimeout(() => frappe.show_progress("Redirecting...", 2, 10), 1000);
    setTimeout(() => frappe.show_progress("Redirecting...", 3, 10), 2000);
    setTimeout(() => frappe.show_progress("Redirecting...", 4, 10), 3000);
    setTimeout(() => frappe.show_progress("Redirecting...", 5, 10), 4000);
    setTimeout(() => frappe.show_progress("Redirecting...", 6, 10), 5000);
    setTimeout(() => frappe.show_progress("Redirecting...", 7, 10), 6000);
    setTimeout(() => frappe.show_progress("Redirecting...", 8, 10), 7000);
    setTimeout(() => frappe.show_progress("Redirecting...", 9, 10), 8000);

    window.location.pathname = dest_path;

}
