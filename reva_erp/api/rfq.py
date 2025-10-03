import frappe

@frappe.whitelist()
def unlock_rfq(rfq_name):
    print(rfq_name,'...////')
    rfq = frappe.get_doc("Request for Quotation", rfq_name)
    if rfq.docstatus != 1:
        frappe.throw("Only submitted RFQs can be unlocked.")

    # Instead of a new field → downgrade docstatus temporarily
    rfq.db_set("docstatus", 0)
    return True





@frappe.whitelist()
def get_suppliers_by_group(supplier_group):
    print("supplier_group .....",supplier_group)
    suppliers = frappe.get_all(
        "Supplier",
        filters={"supplier_group": supplier_group},
        fields=["name", "supplier_name"]
    )
    return suppliers



@frappe.whitelist()
def get_suppliers_by_item(item):
    print("item .....")
    """
    Get all suppliers linked to a given Item.
    """
    suppliers = frappe.db.sql("""
        SELECT supplier 
        FROM `tabItem Supplier`
        WHERE parent = %s
    """, item, as_dict=True)
    print("suppliers .....",suppliers)

    return suppliers


@frappe.whitelist()
def get_item_suppliers(item):
    print(">>>>>>>>")
    """Return list of suppliers linked to an Item."""
    suppliers = frappe.db.get_all(
        "Item Supplier",
        filters={"parent": item},
        fields=["supplier"]
    )
    return [s["supplier"] for s in suppliers]