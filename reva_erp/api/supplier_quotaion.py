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



# import frappe
# from frappe.utils import nowdate

# @frappe.whitelist(allow_guest=False)
# def add_attachments_to_quotation(docname, attachments=None, data=None):
#     print("in function .......",attachments)
#     print()
#     print("data ....",data)
#     """
#     Add attachments to existing Supplier Quotation's child table `custom_addendum`.
#     attachments: list of dicts with keys:
#         attachment_type, remark, file_url
#     """
    
#     if not attachments:
#         return

#     # Convert string to list if passed from JS
#     import json
#     if isinstance(attachments, str):
#         attachments = json.loads(attachments)

#     # Fetch Supplier Quotation
#     sq = frappe.get_doc("Supplier Quotation", docname)

#     for att in attachments:
#         print("att .....",attachments)
#         # Add row to child table
#         sq.append("custom_addendum", {
#             "attachment_type": att.get("attachment_type"),
#             "remark": att.get("remark"),
#             "attachment": att.get("file_url"),
#             "date": nowdate()
#         })

#     sq.save(ignore_permissions=True)
#     frappe.db.commit()
#     return True




import frappe
from frappe.utils import nowdate

@frappe.whitelist(allow_guest=False)
def add_attachments_to_quotation():
    """Handle file uploads and add them to Supplier Quotation's custom_addendum child table"""
    from werkzeug.utils import secure_filename

    docname = frappe.form_dict.get("docname")
    if not docname:
        frappe.throw("Missing quotation name")

    sq = frappe.get_doc("Supplier Quotation", docname)

    idx = 0
    while True:
        file_key = f"file_{idx}"
        if file_key not in frappe.request.files:
            break

        file = frappe.request.files[file_key]
        print("file ....",file)
        attachment_type = frappe.form_dict.get(f"attachment_type_{idx}")
        remark = frappe.form_dict.get(f"remark_{idx}")

        # Save the file to the File DocType
        _file = frappe.get_doc({
            "doctype": "File",
            "file_name": secure_filename(file.filename),
            "attached_to_doctype": "Supplier Quotation",
            "attached_to_name": docname,
            "content": file.read(),
            "is_private": 1
        })
        _file.save(ignore_permissions=True)

        # Add record in child table
        sq.append("custom_addendum", {
            "attachment_type": attachment_type,
            "remark": remark,
            "attachment": _file.file_url,
            "date": nowdate()
        })

        idx += 1

    sq.save(ignore_permissions=True)
    frappe.db.commit()

    return {"message": "Attachments added successfully"}

