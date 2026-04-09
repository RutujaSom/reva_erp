import frappe

@frappe.whitelist()
def unlock_rfq(rfq_name):
    rfq = frappe.get_doc("Request for Quotation", rfq_name)
    if rfq.docstatus != 1:
        frappe.throw("Only submitted RFQs can be unlocked.")

    # Instead of a new field → downgrade docstatus temporarily
    rfq.db_set("docstatus", 0)
    return True





@frappe.whitelist()
def get_suppliers_by_group(supplier_group):
    suppliers = frappe.get_all(
        "Supplier",
        filters={"supplier_group": supplier_group},
        fields=["name", "supplier_name"]
    )
    return suppliers



@frappe.whitelist()
def get_suppliers_by_item(item):
    """
    Get all suppliers linked to a given Item.
    """
    suppliers = frappe.db.sql("""
        SELECT supplier 
        FROM `tabItem Supplier`
        WHERE parent = %s
    """, item, as_dict=True)

    return suppliers


@frappe.whitelist()
def get_item_suppliers(item):
    """Return list of suppliers linked to an Item."""
    suppliers = frappe.db.get_all(
        "Item Supplier",
        filters={"parent": item},
        fields=["supplier"]
    )
    return [s["supplier"] for s in suppliers]




import frappe
from frappe import _

ALLOWED_EXTENSIONS = (".pdf", ".jpg", ".jpeg", ".png")

def validate_rfq_addendum_attachments(doc, method=None):
    """
    Validate RFQ attachments from custom_addendum child table
    """

    for row in doc.custom_addendum:

        if not row.attachment:
            frappe.throw(
                _("Attachment missing in row #{0}.").format(row.idx),
                frappe.ValidationError
            )

        # --------------------------------------------------
        # File extension validation
        # --------------------------------------------------
        file_name = row.attachment.lower()

        if not file_name.endswith(ALLOWED_EXTENSIONS):
            frappe.throw(
                _(
                    "Invalid file type in row #{0}. "
                    "Only PDF and image files are allowed."
                ).format(row.idx),
                frappe.ValidationError
            )
