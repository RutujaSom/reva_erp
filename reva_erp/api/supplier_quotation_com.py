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
















import frappe

@frappe.whitelist()
def get_supplier_quotation_comparison(filters=None):
    print("in func ...............////////////////")
    import json
    filters = json.loads(filters) if isinstance(filters, str) else (filters or {})

    conditions = []
    values = {}

    # Optional filters
    if filters.get("company"):
        conditions.append("sq.company = %(company)s")
        values["company"] = filters["company"]

    if filters.get("from_date"):
        conditions.append("sq.transaction_date >= %(from_date)s")
        values["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions.append("sq.transaction_date <= %(to_date)s")
        values["to_date"] = filters["to_date"]

    if filters.get("supplier"):
        conditions.append("sq.supplier IN %(supplier)s")
        values["supplier"] = tuple(filters["supplier"])

    if filters.get("item_code"):
        conditions.append("sq_item.item_code = %(item_code)s")
        values["item_code"] = filters["item_code"]

    if filters.get("supplier_quotation"):
        conditions.append("sq.name IN %(supplier_quotation)s")
        values["supplier_quotation"] = tuple(filters["supplier_quotation"])

    if filters.get("request_for_quotation"):
        conditions.append("sq.request_for_quotation = %(request_for_quotation)s")
        values["request_for_quotation"] = filters["request_for_quotation"]

    if filters.get("workflow_state"):
        conditions.append("sq.workflow_state = %(workflow_state)s")
        values["workflow_state"] = filters["workflow_state"]

    if not conditions:
        conditions_sql = ""
    else:
        conditions_sql = "WHERE " + " AND ".join(conditions)
    print("conditions_sql ......",conditions_sql)
    query = f"""
        SELECT
            sq.name AS quotation,
            sq.transaction_date,
            sq.supplier,
            sq.company,
            sq_item.item_code,
            item.item_name,
            sq_item.qty,
            sq_item.rate,
            sq_item.amount,
            sq.workflow_state
        FROM
            `tabSupplier Quotation` sq
        JOIN
            `tabSupplier Quotation Item` sq_item ON sq.name = sq_item.parent
        LEFT JOIN
            `tabItem` item ON sq_item.item_code = item.name
        {conditions_sql}
        ORDER BY sq.transaction_date DESC
    """


#     query = f"""
#     SELECT
#         sq_item.item_code AS item_code,
#         item.item_name AS item_name,
#         sq.supplier AS supplier_name,
#         sq.name AS quotation,
#         sq_item.qty AS qty,
#         sq_item.rate AS price,
#         sq_item.uom AS uom,
#         sq.price_list_currency AS price_list_currency,
#         sq.currency AS currency,
#         sq_item.stock_uom AS stock_uom,
#         (sq_item.qty * sq_item.rate) AS base_amount,
#         sq_item.base_rate AS base_rate,
#         sq.request_for_quotation AS request_for_quotation,
#         sq.valid_till AS valid_till,
#         COALESCE(sq_item.lead_time_days, 0) AS lead_time_days,
#         (sq_item.rate / NULLIF(sq_item.conversion_factor, 0)) AS price_per_unit
#     FROM
#         `tabSupplier Quotation` sq
#     JOIN
#         `tabSupplier Quotation Item` sq_item ON sq.name = sq_item.parent
#     LEFT JOIN
#         `tabItem` item ON sq_item.item_code = item.name
#     {conditions_sql}
#     ORDER BY
#         sq.transaction_date DESC
# """


    data = frappe.db.sql(query, values, as_dict=True)
    print("data .....",data)
    return data
