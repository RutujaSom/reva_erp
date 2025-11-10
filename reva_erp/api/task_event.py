import frappe
from frappe.utils import get_url_to_form

def send_mail_to_employee(employee_id, subject, message):
    """Utility to send email to employee's linked user"""
    email = frappe.db.get_value("Employee", employee_id, "prefered_email")
    if email:
        frappe.sendmail(
            recipients=[email],
            subject=subject,
            message=message
        )

def task_created(doc, method):
    """When Task is created, notify all assigned employees"""
    for row in doc.assigned_to:
        emp_name = frappe.db.get_value("Employee", row.employee, "employee_name")
        link = get_url_to_form("Task", doc.name)
        msg = f"""
        <p>Hi {emp_name},</p>
        <p>A new task <b>{doc.subject}</b> has been assigned to you.</p>
        <p><a href="{link}">Click here</a> to view the task.</p>
        """
        send_mail_to_employee(row.employee, f"New Task Assigned: {doc.subject}", msg)

def task_updated(doc, method):
    """When Task is updated, notify assigned employees"""
    for row in doc.assigned_to:
        emp_name = frappe.db.get_value("Employee", row.employee, "employee_name")
        link = get_url_to_form("Task", doc.name)
        msg = f"""
        <p>Hi {emp_name},</p>
        <p>The task <b>{doc.subject}</b> has been updated.</p>
        <p><a href="{link}">Click here</a> to view changes.</p>
        """
        send_mail_to_employee(row.employee, f"Task Updated: {doc.subject}", msg)

def task_approval_created(doc, method):
    """When Task Approval record is created"""
    if doc.approver:
        emp_name = frappe.db.get_value("Employee", doc.approver, "employee_name")
        link = get_url_to_form("Task Approval", doc.name)
        msg = f"""
        <p>Hi {emp_name},</p>
        <p>A task is awaiting your approval.</p>
        <p><a href="{link}">Click here</a> to review.</p>
        """
        send_mail_to_employee(doc.approver, f"Task Approval Pending", msg)

def task_approval_updated(doc, method):
    """When Task Approval is approved or rejected"""
    task = frappe.get_doc("Task", doc.task)
    for row in task.assigned_to:
        emp_name = frappe.db.get_value("Employee", row.employee, "employee_name")
        link = get_url_to_form("Task", task.name)
        msg = f"""
        <p>Hi {emp_name},</p>
        <p>Your task <b>{task.subject}</b> has been <b>{doc.workflow_state}</b> by the approver.</p>
        <p><a href="{link}">Click here</a> to view the task.</p>
        """
        send_mail_to_employee(row.employee, f"Task {doc.workflow_state}: {task.subject}", msg)
