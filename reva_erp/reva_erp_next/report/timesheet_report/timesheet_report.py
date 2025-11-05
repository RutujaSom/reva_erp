import frappe
from frappe.utils import now_datetime

def execute(filters=None):
    columns = [
        {"label": "Employee ID", "fieldname": "employee", "fieldtype": "Data", "width": 180},  # changed to Data
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 200},
        {"label": "Project Name", "fieldname": "project_name", "fieldtype": "Data", "width": 200},
        {"label": "Task ID", "fieldname": "task", "fieldtype": "Link", "options": "Task", "width": 180},
        {"label": "Task Subject", "fieldname": "subject", "fieldtype": "Data", "width": 250},
        {"label": "Total Hours", "fieldname": "total_hours", "fieldtype": "Float", "width": 120},
    ]

    conditions = ""
    values = {}

    if filters.get("employee"):
        conditions += " AND t.employee = %(employee)s"
        values["employee"] = filters.get("employee")

    if filters.get("project"):
        conditions += " AND d.project = %(project)s"
        values["project"] = filters.get("project")

    if filters.get("task"):
        conditions += " AND d.task = %(task)s"
        values["task"] = filters.get("task")

    query = f"""
        SELECT
            e.name AS employee,
            e.employee_name AS employee_name,
            p.project_name AS project_name,
            d.task,
            ts.subject,
            SUM(d.hours) AS total_hours
        FROM
            `tabTimesheet` t
        INNER JOIN
            `tabTimesheet Detail` d ON d.parent = t.name
        LEFT JOIN
            `tabEmployee` e ON e.name = t.employee
        LEFT JOIN
            `tabProject` p ON p.name = d.project
        LEFT JOIN
            `tabTask` ts ON ts.name = d.task
        WHERE
            t.docstatus = 1
            AND (d.hours IS NOT NULL AND d.hours > 0.0)
            {conditions}
        GROUP BY
            e.name, e.employee_name, p.project_name, d.task, ts.subject
        ORDER BY
            e.employee_name, p.project_name, ts.subject
    """

    data = frappe.db.sql(query, values, as_dict=True)
    return columns, data
