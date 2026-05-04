# your_app/utils/auth.py
import frappe

def on_login_redirect(login_manager):
    frappe.local.response["home_page"] = "/app/product"