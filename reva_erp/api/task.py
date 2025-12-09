import frappe
from frappe.utils import get_datetime, today, now_datetime
from frappe import _

def get_permission_query_conditions(user):
    """Restrict Task visibility based on user role and assigned_to child table"""
    if not user:
        return ""

    roles = frappe.get_roles(user)

    # Administrator → see all tasks
    if "Administrator" in roles or "System Manager" in roles:
        return ""
  
    # HR Manager → see tasks assigned to their team + themselves
    if "HR Manager" in roles:
        manager_emp = frappe.db.get_value("Employee", {"user_id": user}, "name")
        if manager_emp:
            # Get all team members
            employee_list = frappe.db.get_all(
                "Employee",
                filters={"reports_to": manager_emp},
                pluck="name"
            )
            employee_list.append(manager_emp)  # include manager
        else:
            employee_list = []

        if employee_list:
            employees_sql = ", ".join([frappe.db.escape(emp) for emp in employee_list])
            # Use EXISTS subquery to check in child table
            return f"""
                EXISTS (
                    SELECT 1 FROM `tabTask Employee`
                    WHERE `tabTask Employee`.parent = `tabTask`.name
                    AND `tabTask Employee`.employee IN ({employees_sql})
                )
            """
        # fallback → only tasks assigned to themselves
        emp = frappe.db.get_value("Employee", {"user_id": user}, "name")
        if emp:
            return f"""
                EXISTS (
                    SELECT 1 FROM `tabTask Employee`
                    WHERE `tabTask Employee`.parent = `tabTask`.name
                    AND `tabTask Employee`.employee = {frappe.db.escape(emp)}
                )
            """
        return "1=0"

    # Employee → only tasks assigned to themselves
    if "Employee" in roles:
        emp = frappe.db.get_value("Employee", {"user_id": user}, "name")
        if emp:
            return f"""
                EXISTS (
                    SELECT 1 FROM `tabTask Employee`
                    WHERE `tabTask Employee`.parent = `tabTask`.name
                    AND `tabTask Employee`.employee = {frappe.db.escape(emp)}
                )
            """
        return "1=0"

    # Default deny
    return "1=0"


def has_permission(doc, user=None):
    """Extra safeguard for direct access to a Task"""
    if not user:
        return False

    roles = frappe.get_roles(user)

    if "Administrator" in roles:
        return True

    # Get logged-in employee
    emp = frappe.db.get_value("Employee", {"user_id": user}, "name")
    if not emp:
        return False

    # Get all employees assigned to this task
    assigned_employees = [row.employee for row in frappe.get_all(
        "Task Employee",
        filters={"parent": doc.name},
        fields=["employee"]
    )]

    if "HR Manager" in roles:
        manager_emp = frappe.db.get_value("Employee", {"user_id": user}, "name")
        if manager_emp:
            team = frappe.get_all(
                "Employee",
                filters={"reports_to": manager_emp},
                pluck="name"
            )
            team.append(manager_emp)
            # Check if any assigned employee is in manager's team
            return any(e in team for e in assigned_employees)

    if "Employee" in roles:
        return emp in assigned_employees

    return False






@frappe.whitelist(allow_guest=True)
def auto_close_incomplete_working_tasks():

    from frappe.utils import today, now_datetime, get_datetime

    # Fetch all Tasks in Working status
    working_tasks = frappe.get_all(
        "Task",
        filters={"status": "Working"},
        fields=["name"]
    )

    for task in working_tasks:
        task_doc = frappe.get_doc("Task", task.name)

        for emp_row in task_doc.custom_assigned_to:
            emp = emp_row.employee
            if not emp:
                continue

            # Update Timesheets linked to this task for this employee
            timesheets = frappe.get_all(
                "Timesheet",
                filters={"employee": emp},
                fields=["name"]
            )

            for ts in timesheets:
                ts_doc = frappe.get_doc("Timesheet", ts.name)
                updated = False

                for log in ts_doc.time_logs:
                    if log.task == task_doc.name and not log.completed:

                        # Close log at time of scheduler run (8 PM)
                        end_dt = now_datetime()

                        log.to_time = end_dt
                        log.completed = True

                        # Calculate hours
                        if log.from_time:
                            from_dt = get_datetime(log.from_time)
                            diff_hours = (end_dt - from_dt).total_seconds() / 3600
                            log.hours = round(diff_hours, 2)

                        updated = True

                if updated:
                    ts_doc.save(ignore_permissions=True)

            # Stop the task
            task_doc.status = "Stopped"
            task_doc.save(ignore_permissions=True)

            frappe.db.commit()

            frappe.log_error(
                f"Task {task_doc.name} auto-closed at 8 PM for employee {emp}",
                "Auto Task Close"
            )


def execute():
    task_status_field = frappe.get_doc("DocField", {
        "parent": "Task",
        "fieldname": "status"
    })

    # Current options
    options = task_status_field.options.split("\n") if task_status_field.options else []

    # Add new options safely
    new_options = ["Stopped","On Hold"]
    for opt in new_options:
        if opt not in options:
            options.append(opt)

    # Save back
    task_status_field.options = "\n".join(options)
    task_status_field.save(ignore_permissions=True)
