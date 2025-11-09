import frappe

@frappe.whitelist()
def get_employee_for_user(user=None):
    print("in if ....")
    user = user or frappe.session.user
    emp = frappe.db.get_value("Employee", {"user_id": user}, "name")
    print("emp ....",emp)
    return emp
