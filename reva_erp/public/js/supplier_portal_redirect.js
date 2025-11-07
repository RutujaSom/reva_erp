
$(document).on('app_ready', function() {
    const current_user = frappe.session.user;
    const roles = frappe.boot.user && frappe.boot.user.roles || [];

    console.log("Logged in user:", current_user);

    // Proceed only if user is Supplier or Pre Supplier
    if (roles.includes("Supplier") || roles.includes("Pre Supplier")) {

        frappe.call({
            method: "reva_erp.api.supplier_creation_file.get_supplier_for_user",
            args: { user: current_user },
            callback: function (res) {
                if (res.message && res.message.length > 0) {
                    const supplier = res.message[0];
                    console.log("Supplier data:", supplier, '.....supplier.workflow_state ..',supplier.workflow_state);

                    // Check if supplier has an approval status field
                    // (assuming fieldname = "approval_status")
                    if (supplier.workflow_state && supplier.workflow_state.toLowerCase() === "approved") {
                        // If approved, show message or redirect elsewhere
                        frappe.msgprint({
                            title: "Access Restricted",
                            message: "Your supplier profile is already approved. You cannot edit the form.",
                            indicator: "green"
                        });

                        // Example: redirect to desk or home page instead of opening Supplier form
                        window.location.href = "/me";
                    } 
                    else {
                        // Not approved — open Supplier form for update
                        frappe.set_route("form", "Supplier", supplier.name);

                        // Lock navigation — prevent going anywhere else
                        const prevent_navigation = function () {
                            const route = frappe.get_route();
                            // If not on Supplier form, force redirect back
                            if (!(route[0] === "Form" && route[1] === "Supplier" && route[2] === supplier.name)) {
                                frappe.set_route("form", "Supplier", supplier.name);
                                frappe.show_alert({
                                    message: __("You cannot navigate away until your supplier profile is approved."),
                                    indicator: "red"
                                });
                            }
                        };

                        // Recheck route on every route change
                        frappe.router.on('change', prevent_navigation);

                        // Also disable sidebar and topbar navigation visually
                        setTimeout(() => {
                            $(".navbar, .sidebar").css({
                                "pointer-events": "none",
                                "opacity": "0.4"
                            });
                        }, 1000);
                    
                    }
                }
            }
        });
    }
});


