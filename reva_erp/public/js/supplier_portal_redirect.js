
$(document).on('app_ready', function() {
    const current_user = frappe.session.user;
    const roles = frappe.boot.user && frappe.boot.user.roles || [];

    if (roles.includes("Supplier") || roles.includes("Pre Supplier")) {
        frappe.call({
            method: "reva_erp.api.supplier_creation_file.get_supplier_for_user",
            args: { user: current_user },
            callback: function (res) {
                if (res.message && res.message.length > 0) {
                    const supplier = res.message[0];

                    // Allow normal access if approved
                    if (supplier.workflow_state && supplier.workflow_state.toLowerCase() === "approved") {
                        return;
                    }

                    // Force open Supplier form if not approved
                    frappe.set_route("form", "Supplier", supplier.name);

                    // --- Restrict route navigation ---
                    const prevent_navigation = function() {
                        const route = frappe.get_route();

                        // Allowed routes:
                        const isSupplierForm = route[0] === "Form" && route[1] === "Supplier" && route[2] === supplier.name;
                        const isSupplierAddress = route[0] === "Form" && route[1] === "Address" && supplier.supplier_primary_address && route[2] === supplier.supplier_primary_address;

                        if (!isSupplierForm && !isSupplierAddress) {
                            frappe.show_alert({
                                message: __("Navigation is locked until your supplier profile is approved."),
                                indicator: "red"
                            });
                            frappe.set_route("form", "Supplier", supplier.name);
                        }
                    };

                    frappe.router.on('change', prevent_navigation);

                    // --- Block navigation except Logout and linked Address ---
                    setTimeout(() => {
                        $(document).on("click.blockNav", ".sidebar a, .navbar a", function (e) {
                            const href = $(this).attr("href") || "";
                            const text = $(this).text().trim().toLowerCase();

                            // Allow logout
                            if (href.includes("/?cmd=logout") || text === "logout") {
                                return true;
                            }

                            // Allow linked Address
                            if (supplier.supplier_primary_address && href.includes(`/app/address/${supplier.supplier_primary_address}`)) {
                                return true;
                            }

                            // Block everything else
                            e.preventDefault();
                            e.stopPropagation();
                            frappe.show_alert({
                                message: __("You cannot navigate away until your supplier profile is approved."),
                                indicator: "red"
                            });
                            frappe.set_route("form", "Supplier", supplier.name);
                            return false;
                        });
                    }, 1000);

                    

                    // --- Hide "Add Address" and "Add Contact" buttons on Supplier form ---
                    frappe.ui.form.on("Supplier", {
                        onload(frm) {
                            setTimeout(() => {
                                frm.$wrapper.find('.btn:contains("Add Address")').hide();
                                frm.$wrapper.find('.btn:contains("Add Contact")').hide();
                            }, 500);
                        }
                    });
                }
            }
        });
    }
});



