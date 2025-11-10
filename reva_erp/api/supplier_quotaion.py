import frappe

def supplier_quotation_status_update(doc, method):
    
    # 🟡 1. When supplier updates from portal and quotation is still Draft → mark as Pending
    if (
        frappe.session.user != "Administrator"
        and "Supplier" in frappe.get_roles(frappe.session.user)
        and doc.workflow_state == "Draft"
    ):
        frappe.db.set_value("Supplier Quotation", doc.name, "workflow_state", "Pending")


    # When Approved → submit if not already submitted
    elif doc.workflow_state == "Approved" and doc.docstatus == 0:
        try:
            frappe.db.set_value("Supplier Quotation", doc.name, "status", "Submitted")
            doc.submit()
            frappe.msgprint("Supplier Quotation submitted (Approved).")
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Error while submitting Supplier Quotation")
            frappe.msgprint(f"Error while submitting: {str(e)}")

    # When Rejected → mark as cancelled without recursion
    elif doc.workflow_state == "Rejected" and doc.docstatus == 0:
        try:
            frappe.db.set_value("Supplier Quotation", doc.name, "status", "Cancelled")
            frappe.db.set_value("Supplier Quotation", doc.name, "docstatus", 2)
            frappe.msgprint("Supplier Quotation cancelled (Rejected).")
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Error while cancelling Supplier Quotation")
            frappe.msgprint(f"Error while cancelling: {str(e)}")
