// frappe.ready(function() {
// 	// bind events here
// })

frappe.ready(function() {
    $(".btn-primary").on("click", function(e) {
        e.preventDefault();

        let data = frappe.web_form.get_values();

        frappe.call({
            // method: "your_app.your_app.web_form.supplier_registration.supplier_registration.register_supplier",
			method: "reva_erp.reva_erp_next.web_form.supplier_registration.supplier_registration.register_supplier",
            args: { data: JSON.stringify(data) },
            callback: function(r) {
                if (r.message && r.message.status === "success") {
                    frappe.msgprint("Supplier registered successfully!");
                    frappe.web_form.clear();
                }
            }
        });
    });
});
