import frappe
from frappe.utils import get_datetime, today, now_datetime
from frappe import _

# def get_permission_query_conditions(user):
#     """Restrict Task visibility based on user role and assigned_to child table"""
#     if not user:
#         return ""

#     roles = frappe.get_roles(user)

#     # Administrator → see all tasks
#     if "Administrator" in roles or "System Manager" in roles:
#         return ""
  
#     # HR Manager → see tasks assigned to their team + themselves
#     if "HR Manager" in roles:
#         manager_emp = frappe.db.get_value("Employee", {"user_id": user}, "name")
#         if manager_emp:
#             # Get all team members
#             employee_list = frappe.db.get_all(
#                 "Employee",
#                 filters={"reports_to": manager_emp},
#                 pluck="name"
#             )
#             employee_list.append(manager_emp)  # include manager
#         else:
#             employee_list = []

#         if employee_list:
#             employees_sql = ", ".join([frappe.db.escape(emp) for emp in employee_list])
#             # Use EXISTS subquery to check in child table
#             return f"""
#                 EXISTS (
#                     SELECT 1 FROM `tabTask Employee`
#                     WHERE `tabTask Employee`.parent = `tabTask`.name
#                     AND `tabTask Employee`.employee IN ({employees_sql})
#                 )
#             """
#         # fallback → only tasks assigned to themselves
#         emp = frappe.db.get_value("Employee", {"user_id": user}, "name")
#         if emp:
#             return f"""
#                 EXISTS (
#                     SELECT 1 FROM `tabTask Employee`
#                     WHERE `tabTask Employee`.parent = `tabTask`.name
#                     AND `tabTask Employee`.employee = {frappe.db.escape(emp)}
#                 )
#             """
#         return "1=0"

#     # Employee → only tasks assigned to themselves
#     if "Employee" in roles:
#         emp = frappe.db.get_value("Employee", {"user_id": user}, "name")
#         if emp:
#             return f"""
#                 EXISTS (
#                     SELECT 1 FROM `tabTask Employee`
#                     WHERE `tabTask Employee`.parent = `tabTask`.name
#                     AND `tabTask Employee`.employee = {frappe.db.escape(emp)}
#                 )
#             """
#         return "1=0"

#     # Default deny
#     return "1=0"




def get_permission_query_conditions(user):
    """
    Generate SQL query conditions to restrict Task document visibility based on the user's roles and assignments.

    Args:
        user (str): The user ID for whom to generate permission conditions.

    Returns:
        str: SQL WHERE clause conditions as a string. Returns an empty string for users with full access roles or if no conditions apply.

    Logic:
        - Users with roles in the full_access_roles set (e.g., Administrator, System Manager, CEO, etc.) have unrestricted access (returns "").
        - The task creator (owner) can always see their own tasks.
        - Users with "Employee", "Project User", or "Projects Manager" roles can view tasks assigned to them via the "Task Employee" child table.
        - "Projects Manager" role users can also view all tasks belonging to projects they are assigned to via the "Project User" table.
        - If no conditions are met, returns an empty string (no restriction).
    """
    if not user:
        return ""

    roles = frappe.get_roles(user)
    print("Roles:", roles)

    # 🔹 Roles with full access
    full_access_roles = {
        "Administrator",
        "System Manager",
        "CEO",
        "HR",
        "HR Manager",
        "HR User",
        "Account",
        "Accounts Manager",
        "Accounts User",
        "General Manager",
    }

    if full_access_roles.intersection(set(roles)):
        return ""

    conditions = []

    # 🔹 Always allow creator to see their tasks
    conditions.append(f"`tabTask`.owner = '{user}'")

    # 🔹 Employee / Project User / Projects Manager assignment logic
    emp = None
    if {"Employee", "Project User", "Projects Manager"}.intersection(set(roles)):
        emp = frappe.db.get_value("Employee", {"user_id": user}, "name")

        if emp:
            conditions.append(f"""
                (
                    IFNULL(`tabTask`.is_group, 0) = 0
                    AND
                    EXISTS (
                        SELECT 1
                        FROM `tabTask Employee`
                        WHERE
                            `tabTask Employee`.parent = `tabTask`.name
                            AND `tabTask Employee`.employee = {frappe.db.escape(emp)}
                    )
                )
            """)

    # 🔹 Projects Manager: all tasks of assigned projects
    if "Projects Manager" in roles:
        print("in Projects Manager role .....")
        conditions.append(f"""
            `tabTask`.project IN (
                SELECT parent
                FROM `tabProject User`
                WHERE user = '{user}'
            )
        """)

    # 🔹 Safety fallback
    if not conditions:
        return ""

    return "(" + " OR ".join(conditions) + ")"


# def has_permission(doc, user=None):
#     """Extra safeguard for direct access to a Task"""
#     if not user:
#         return False

#     roles = frappe.get_roles(user)

#     if "Administrator" in roles:
#         return True

#     # Get logged-in employee
#     emp = frappe.db.get_value("Employee", {"user_id": user}, "name")
#     if not emp:
#         return False

#     # Get all employees assigned to this task
#     assigned_employees = [row.employee for row in frappe.get_all(
#         "Task Employee",
#         filters={"parent": doc.name},
#         fields=["employee"]
#     )]

#     if "HR Manager" in roles:
#         manager_emp = frappe.db.get_value("Employee", {"user_id": user}, "name")
#         if manager_emp:
#             team = frappe.get_all(
#                 "Employee",
#                 filters={"reports_to": manager_emp},
#                 pluck="name"
#             )
#             team.append(manager_emp)
#             # Check if any assigned employee is in manager's team
#             return any(e in team for e in assigned_employees)

#     if "Employee" in roles:
#         return emp in assigned_employees

#     return False






@frappe.whitelist(allow_guest=True)
def auto_close_incomplete_working_tasks():
    """
    Automatically closes all tasks with status "Working" and their associated incomplete time logs at the time of scheduler run (e.g., 8 PM).

    For each "Working" task:
        - Iterates through all assigned employees.
        - For each employee, finds all related Timesheets.
        - For each Timesheet, updates incomplete time logs linked to the task:
            - Sets the end time to the current time.
            - Marks the log as completed.
            - Calculates and updates the hours worked.
        - Changes the task status to "Stopped".
        - Saves changes and commits the transaction.
        - Logs the auto-closure event for auditing.

    Intended to be run as a scheduled job to ensure no "Working" tasks or time logs remain incomplete at the end of the workday.
    """

    from frappe.utils import today, now_datetime, get_datetime

    # Fetch all Tasks in Working status
    working_tasks = frappe.get_all(
        "Task",
        filters={"status": "Working"},
        fields=["name"]
    )
    print("working_tasks .......",working_tasks)

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
    """
    Updates the 'status' field options of the 'Task' DocType by adding new status options if they do not already exist.

    This function retrieves the 'status' field from the 'Task' DocType, checks its current options, and appends "Stopped" and "On Hold" to the list of options if they are not already present. The updated options are then saved back to the field.

    Raises:
        frappe.DoesNotExistError: If the 'status' field in the 'Task' DocType does not exist.
    """
    
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
