import frappe
from frappe.utils import get_datetime, today, now_datetime
from frappe import _


def get_permission_query_conditions(user):

    if not user:
        return ""

    roles = frappe.get_roles(user)

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

    return (
        "`tabProject`.name IN ("
        " SELECT parent FROM `tabProject User`"
        f" WHERE user = {frappe.db.escape(user)}"
        ")"
    )
