# Copyright (c) 2025, Excellminds and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate


class TaskApproval(Document):

    def on_update(doc, method=None):
        """
        When a Task Approval is approved, activate the next approval level.
        """
        if doc.workflow_state == "Approved":
            next_level = doc.approval_level + 1

            next_approval = frappe.db.get_value(
                "Task Approval",
                {"task": doc.task, "approval_level": next_level},
                "name",
            )

            if next_approval:
                frappe.db.set_value("Task Approval", next_approval, "workflow_state", "Pending")
                frappe.msgprint(f"Next approval level ({next_level}) is now set to Pending.")
            else:
                frappe.msgprint("✅ All approvals completed — no next level.")

            approvals = frappe.get_all(
                "Task Approval",
                filters={
                    "task": doc.task,
                    "workflow_state": ["!=", "Discard"]
                },
                fields=["workflow_state"]
            )
            states = [a.workflow_state for a in approvals]

            if approvals and all(s == "Approved" for s in states):
                frappe.db.set_value("Task", doc.task, "workflow_state", "Approved")
                on_update_task_approval(doc, method=None)


        if doc.workflow_state == "Rejected":
            # The employee who rejected
            rejecting_employee = doc.employee
            # Find all other Task Approval records for the same task
            other_approvals = frappe.get_all(
                "Task Approval",
                filters={
                    "task": doc.task,
                    "workflow_state": ["not in", ["Discard"]]
                },
                fields=["name"]
            )

            for approval in other_approvals:
                frappe.db.set_value("Task Approval", approval.name, "workflow_state", "Discard")
                frappe.db.set_value("Task Approval", approval.name, "discarded_by", rejecting_employee)

            frappe.db.set_value("Task", doc.task, "workflow_state", "Returned")
            frappe.db.set_value("Task", doc.status, "workflow_state", "Open")

            frappe.msgprint(f"All other pending approvals for this task have been discarded.")






def on_update_task_approval(doc, method=None):
   
    # Update parent task if applicable
    task_doc = frappe.get_doc("Task", doc.task)
    if task_doc.parent_task:
        parent_task = frappe.get_doc("Task", task_doc.parent_task)

        if parent_task.is_group:
            # Get all child tasks
            child_tasks = frappe.get_all(
                "Task",
                filters={"parent_task": parent_task.name},
                fields=["name"]
            )

            all_approved = True
            for child in child_tasks:
                approvals = frappe.get_all(
                    "Task Approval",
                    filters={"task": child.name},
                    fields=["workflow_state"]
                )
                states = [a.workflow_state for a in approvals]
                if not states or any(s != "Approved" for s in states):
                    all_approved = False
                    break

            if all_approved:
                parent_task.status = "Completed"
                parent_task.completed_on = nowdate()
                parent_task.save(ignore_permissions=True)




def get_permission_query_conditions(user):
    if not user or user == "Administrator":
        return ""

    # Apply restriction only for Task Approver doctype
    return f"`tabTask Approval`.`approver` = '{user}'"


def has_permission(doc, user):
    # Allow access if Administrator
    if user == "Administrator":
        return True

    # Allow access if the logged-in user is the approver
    if doc.approver == user:
        return True

    return False
