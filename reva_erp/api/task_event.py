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
    print("in create .....", doc, doc.is_group)
    if doc.is_group:
        return
    """Send email when task is created"""
    print("doc.custom_assigned_to ....",len(doc.custom_assigned_to))
    if len(doc.custom_assigned_to) == 1:
        for row in doc.custom_assigned_to:
            print("row .....",row)
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

    today = nowdate()
    subject = f"Daily Task Summary – {today}"

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

        # --------- OPEN TASKS ----------
        open_tasks = frappe.db.sql("""
            SELECT t.name, t.subject, t.project, t.priority, t.status, t.exp_end_date AS due_date
            FROM `tabTask` t
            JOIN `tabTask Employee` ta ON ta.parent = t.name
            WHERE ta.employee = %s
            AND t.status = 'Open'
            AND t.exp_start_date <= %s
            AND IFNULL(t.is_group, 0) = 0
        """, (emp.name, today), as_dict=True)

        open_count = len(open_tasks)

        # --------- OVERDUE TASKS ----------
        overdue_tasks = frappe.db.sql("""
            SELECT t.name, t.subject, t.project, t.priority, t.status, t.exp_end_date AS due_date
            FROM `tabTask` t
            JOIN `tabTask Employee` ta ON ta.parent = t.name
            WHERE ta.employee = %s
              AND t.status = 'Overdue'
              AND IFNULL(t.is_group, 0) = 0
        """, (emp.name,), as_dict=True)

        overdue_count = len(overdue_tasks)

        print("open_count", open_count, "overdue_count", overdue_count)

        # Skip sending if no tasks
        if open_count == 0 and overdue_count == 0:
            continue

        # -------------------------------------------------
        # BUILD CLEAN HTML EMAIL
        # -------------------------------------------------

        message = f"""
        <div style="font-family: Arial, sans-serif; font-size: 14px; color: #333;">
        
            <h3>Daily Task Summary — {today}</h3>

            <p>Hi <strong>{emp.employee_name}</strong>,</p>

            <p>Here is your task summary for today:</p>

            <hr>

            <!-- OPEN TASKS -->
            <h4>Open Tasks ({open_count})</h4>
        """

        # Add OPEN tasks:
        if open_count > 0:
            message += "<ul>"
            for t in open_tasks:
                task_link = frappe.utils.get_url_to_form("Task", t.name)
                message += f"""
                <li>
                    <strong>{t.subject}</strong> <br>
                    Project: {t.project or '-'} <br>
                    Priority: {t.priority or '-'} <br>
                    Task ID: <a href="{task_link}">{t.name}</a>
                </li><br>
                """
            message += "</ul>"
        else:
            message += "<p>No open tasks.</p>"

        message += "<hr>"

        # Add OVERDUE tasks:
        message += f"<h4 style='color:red;'>Overdue Tasks ({overdue_count})</h4>"

        if overdue_count > 0:
            message += "<ul>"
            for t in overdue_tasks:
                task_link = frappe.utils.get_url_to_form("Task", t.name)
                message += f"""
                <li>
                    <strong>{t.subject}</strong> 
                    Project: {t.project or '-'} <br>
                    Priority: {t.priority or '-'} <br>
                    Task ID: <a href="{task_link}">{t.name}</a><br>
                </li><br>
                """
            message += "</ul>"
        else:
            message += "<p>No overdue tasks. Great job! 🎉</p>"

        # Suggested Section
        message += """
            <hr> <br><br>

            <p>Regards,<br>
            <strong>Reva Process Technologies</strong></p>
        </div>
        """

        # Send email
        frappe.sendmail(
            recipients=[email],
            subject=subject,
            message=message,
        )
