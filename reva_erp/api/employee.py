import json
import frappe

@frappe.whitelist()
def get_employee_for_user(user=None):
    user = user or frappe.session.user
    emp = frappe.db.get_value("Employee", {"user_id": user}, "name")
    return emp



@frappe.whitelist()
def get_assigned_employee_users(employee_ids):
    if isinstance(employee_ids, str):
        employee_ids = json.loads(employee_ids)

    print(f"Employee IDs: {employee_ids}")

    emp_list = frappe.get_all(
        "Employee",
        filters={"name": ["in", employee_ids]},
        fields=["name", "user_id"],
        ignore_permissions=True
    )

    print(f"Employee List: {emp_list}")
    return emp_list



import frappe

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_project_employees(doctype, txt, searchfield, start, page_len, filters):
    project = filters.get("project")

    if not project:
        return []

    # Get users who are members of the project
    project_users = frappe.get_all(
        "Project User",                  # Child table in Project doctype
        filters={"parent": project},
        pluck="user"
    )

    if not project_users:
        return []

    # Get employees linked to those users
    employees = frappe.get_all(
        "Employee",
        filters={
            "user_id": ["in", project_users],
            "status": "Active",
            searchfield: ["like", f"%{txt}%"]
        },
        fields=["name", "employee_name"],
        limit_start=start,
        limit_page_length=page_len
    )

    return [[e.name, e.employee_name] for e in employees]