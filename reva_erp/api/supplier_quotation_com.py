import frappe
from frappe import _

@frappe.whitelist()
def process_supplier_quotations(approve=None, reject=None):
    """
    Approve or reject Supplier Quotation records.
    :param approve: list of Supplier Quotation names to approve
    :param reject: list of Supplier Quotation names to reject
    """
    if isinstance(approve, str):
        import json
        approve = json.loads(approve)
    if isinstance(reject, str):
        import json
        reject = json.loads(reject)

    success_approved = []
    success_rejected = []

    # --- Approve quotations ---
    for name in approve or []:
        try:
            doc = frappe.get_doc("Supplier Quotation", name)
            # Update workflow state to Approved
            doc.workflow_state = "Approved"
            doc.save(ignore_permissions=True)
            # Submit if needed
            # if doc.docstatus == 0:
            #     doc.submit()
            success_approved.append(name)
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), f"Error approving Supplier Quotation {name}")

    # --- Reject quotations ---
    for name in reject or []:
        try:
            doc = frappe.get_doc("Supplier Quotation", name)
            # Update workflow state to Rejected
            doc.workflow_state = "Rejected"
            doc.save(ignore_permissions=True)
            # Optionally cancel if submitted
            # if doc.docstatus == 1:
            #     doc.cancel()
            success_rejected.append(name)
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), f"Error rejecting Supplier Quotation {name}")

    return {
        "approved": success_approved,
        "rejected": success_rejected,
        "message": _("Processed Supplier Quotations successfully")
    }
