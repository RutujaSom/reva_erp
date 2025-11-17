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

        # ❌ Skip email to the user performing update
        if row.employee == logged_employee:
            continue

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

