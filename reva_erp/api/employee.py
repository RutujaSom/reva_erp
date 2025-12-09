import frappe

@frappe.whitelist()
def get_employee_for_user(user=None):
    user = user or frappe.session.user
    emp = frappe.db.get_value("Employee", {"user_id": user}, "name")
    return emp
