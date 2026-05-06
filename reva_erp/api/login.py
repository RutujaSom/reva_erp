import json

import frappe


PROJECT_HOME_PAGE = "/app/projects"


def on_login_redirect(login_manager):
    frappe.local.response["home_page"] = PROJECT_HOME_PAGE


def force_project_home_page(response=None, request=None):
    if not _is_login_request(request):
        return

    if frappe.local.response.get("message") in ("Logged In", "No App"):
        frappe.local.response["home_page"] = PROJECT_HOME_PAGE

    if not response or response.mimetype != "application/json":
        return

    try:
        data = json.loads(response.get_data(as_text=True) or "{}")
    except json.JSONDecodeError:
        return

    if data.get("message") in ("Logged In", "No App"):
        data["home_page"] = PROJECT_HOME_PAGE
        response.set_data(json.dumps(data, separators=(",", ":")))


def _is_login_request(request):
    if not request:
        return False

    return request.form.get("cmd") == "login" or request.path == "/api/method/login"
