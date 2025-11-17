import frappe
from frappe.utils import get_url_to_form

def send_mail_to_employee(employee_id, subject, message):
    """Utility to send email to employee's linked user"""
    emp_data = frappe.db.get_value("Employee", employee_id, "user_id")
    email = frappe.db.get_value("User", emp_data, "email")
    print("email ....", email)
    if email:
        frappe.sendmail(
            recipients=[email],
            subject=subject,
            message=message
        )

# -----------------------------
#  TASK CREATED
# -----------------------------
def task_created(doc, method):
    print("in create .....")
    if doc.is_group:
        return
    """Send email when task is created"""
    for row in doc.custom_assigned_to:
        emp_name = frappe.db.get_value("Employee", row.employee, "employee_name")
        link = get_url_to_form("Task", doc.name)

        msg = f"""
        <p>Hi {emp_name},</p>
        <p>A new task <b>{doc.subject}</b> has been assigned to you.</p>
        <p><a href="{link}">Click here</a> to view the task.</p>
        """
        print("msg ....",msg)

        send_mail_to_employee(
            row.employee,
            f"New Task Assigned: {doc.subject}",
            msg
        )

# -----------------------------
#  TASK UPDATED (but NOT when approved or returned)
# -----------------------------

def task_updated(doc, method):
    print("in update ..klamo .....")

    # ❌ Do NOT send update mail on creation
    if doc.flags.in_insert:
        return
    
    if doc.is_group:

        # Get logged-in user’s employee ID
        logged_user = frappe.session.user
        logged_employee = frappe.db.get_value("Employee", {"user_id": logged_user}, "name")

        # -------------------------------
        # CASE 1: Completed / Returned
        # -------------------------------

        if doc.workflow_state == "Pending":
            return

        # -------------------------------
        # CASE 2: Normal Update
        # -------------------------------

        for row in doc.custom_assigned_to:
            print('logged_employee ....',logged_employee,' .row.employee .....',row.employee)

            emp_name = frappe.db.get_value("Employee", row.employee, "employee_name")
            link = get_url_to_form("Task", doc.name)

            msg = f"""
            <p>Hi {emp_name},</p>
            <p>The task <b>{doc.subject}</b> has been updated.</p>
            <p><a href="{link}">Click here</a> to view changes.</p>
            """

            send_mail_to_employee(
                row.employee,
                f"Task Updated: {doc.subject}",
                msg
            )






import frappe
from frappe.utils import nowdate

def send_daily_task_summary():
    print("in task summary .....")
    """
    Sends daily open & overdue task count at 08:00 AM to each employee.
    Skips parent/group tasks.
    """

    today = nowdate()

    # Fetch all active employees
    employees = frappe.db.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "employee_name", "user_id"]
    )

    for emp in employees:

        if not emp.user_id:
            continue

        # Get user email
        email = frappe.db.get_value("User", emp.user_id, "email")
        if not email:
            continue

        # --------------------------------------
        # OPEN TASKS
        # --------------------------------------
        open_tasks = frappe.db.sql("""
            SELECT t.name
            FROM `tabTask` t
            JOIN `tabTask Employee` ta ON ta.parent = t.name
            WHERE ta.employee = %s
              AND t.status = 'Open'
              AND IFNULL(t.is_group, 0) = 0
        """, (emp.name,), as_dict=True)

        open_count = len(open_tasks)

        # --------------------------------------
        # OVERDUE TASKS (Open + End Date < Today)
        # --------------------------------------
        overdue_tasks = frappe.db.sql("""
            SELECT t.name
            FROM `tabTask` t
            JOIN `tabTask Employee` ta ON ta.parent = t.name
            WHERE ta.employee = %s
              AND t.status = 'Overdue'
              AND IFNULL(t.is_group, 0) = 0
        """, (emp.name), as_dict=True)

        overdue_count = len(overdue_tasks)

        # If no tasks at all – skip sending email
        if open_count == 0 and overdue_count == 0:
            continue

        # --------------------------------------
        # EMAIL CONTENT
        # --------------------------------------
        message = f"""
            <p>Hi <b>{emp.employee_name}</b>,</p>

            <p>Here is your daily task summary:</p>

            <ul>
                <li><b>{open_count}</b> Open Task(s)</li>
        """

        # Add overdue section ONLY if overdue tasks exist
        if overdue_count > 0:
            message += f"""
                <li><b>{overdue_count}</b> Overdue Task(s)</li>
            """

        # Close list
        message += """
            </ul>
            <p>Please check ERPNext for details.</p>
            <br>
            <p>Regards,<br>Reva Process Technologies</p>
        """

        subject = "Daily Task Summary — Open Tasks"

        # Send mail
        frappe.sendmail(
            recipients=[email],
            subject=subject,
            message=message,
        )
