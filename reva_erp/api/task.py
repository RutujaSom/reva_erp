import frappe

def get_permission_query_conditions(user):
    """Restrict Task visibility based on user role"""
    if not user:
        return ""

    roles = frappe.get_roles(user)

    # Administrator → see all records
    if "Administrator" in roles:
        return ""

    # HR Manager → See tasks assigned to their team + themselves
    if "HR Manager" in roles:
        manager_emp = frappe.db.get_value("Employee", {"user_id": user}, "name")
        if manager_emp:
            employee_list = frappe.db.get_all(
                "Employee",
                filters={"reports_to": manager_emp},
                pluck="user_id"
            )
            employee_list.append(user)  # include manager
            employees = ",".join([frappe.db.escape(e) for e in employee_list])

            # Filter using your custom field
            return f"`tabTask`.`assigned_to` in ({employees})"

        # If no team, fallback → only own tasks
        return f"`tabTask`.`assigned_to` = {frappe.db.escape(user)}"

    # Employee → only their tasks
    if "Employee" in roles:
        return f"`tabTask`.`assigned_to` = {frappe.db.escape(user)}"

    # Default deny
    return "1=0"


def has_permission(doc, user=None):
    """Extra safeguard for direct access"""
    if not user:
        return False

    roles = frappe.get_roles(user)

    if "Administrator" in roles:
        return True

    # Check ToDo assignments instead of non-existent field
    assigned_users = frappe.get_all(
        "ToDo",
        filters={"reference_type": "Task", "reference_name": doc.name},
        pluck="allocated_to"
    )

    if "HR Manager" in roles:
        manager_emp = frappe.db.get_value("Employee", {"user_id": user}, "name")
        if manager_emp:
            team = frappe.get_all(
                "Employee", filters={"reports_to": manager_emp}, pluck="user_id"
            )
            team.append(user)
            return any(u in team for u in assigned_users)

    if "Employee" in roles:
        return user in assigned_users

    return False



