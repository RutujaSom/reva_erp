import frappe
import json
import socket
# from frappe.utils import get_url
# from frappe.utils.password import reset_password

def get_context(context):
    """Add context data for Web Form"""
    context.countries = frappe.get_all("Country", fields=["name"])
    return context


@frappe.whitelist(allow_guest=True)
def register_supplier(data):
    """Called from Supplier Registration Web Form"""
    data = json.loads(data)

    supplier_name = data.get("supplier_name")
    email_id = data.get("email_id")
    mobile_no = data.get("mobile_no")
    address_line1 = data.get("address_line_1")
    city = data.get("city")
    state = data.get("state")
    country = data.get("country")
    pincode = data.get("pincode")
    data["country"] = "India"

    # ----------- Step 1: Create User -----------
    frappe.set_user("Administrator")

    if email_id and not frappe.db.exists("User", email_id):
        user = frappe.get_doc({
            "doctype": "User",
            "email": email_id,
            "first_name": supplier_name,
            "mobile_no": mobile_no,
            "send_welcome_email": 0,
            "roles": [
                {"role": "Pre Supplier"}   # ✅ Add role directly before insert
            ]
        })
        user.insert(ignore_permissions=True)
        user.add_roles("Pre Supplier")
        
        # Remove Allow Modules if any default entries got added
        # frappe.db.delete("Has Role", {"parent": user.name})
    else:
        user = frappe.get_doc("User", email_id)

    # ----------- Step 2: Create Supplier -----------
    supplier = frappe.get_doc({
        "doctype": "Supplier",
        "supplier_name": supplier_name,
        "supplier_group": data.get("supplier_group"),
        "supplier_type": data.get("supplier_type"),
        "supplier_details": data.get("supplier_details"),
        "website": data.get("website"),
    })
    supplier.insert(ignore_permissions=True)

    # Add portal user link (child table entry)
    supplier.append("portal_users", {
        "user": user.name
    })

    # ----------- Step 3: Create Address -----------
    address = frappe.get_doc({
        "doctype": "Address",
        "address_title": supplier_name,
        "address_type": "Billing",
        "address_line1": address_line1,
        "city": city,
        "state": state,
        "country": country,
        "pincode": str(pincode) if pincode else "",
        "custom_gstin__uin": data.get("gst"),
        "custom_gst_state": data.get("gst_state"),
        "custom_gst_category": data.get("gst_category"),
        "custom_gst_state_number": data.get("gst_state_number"),
        "links": [{
            "link_doctype": "Supplier",
            "link_name": supplier.name
        }]
    })
    address.insert(ignore_permissions=True)

    # ----------- Step 4: Create Contact -----------
    contact = frappe.get_doc({
        "doctype": "Contact",
        "first_name": supplier_name,
        "email_ids": [{"email_id": email_id, "is_primary": 1}] if email_id else [],
        "phone_nos": [{"phone": mobile_no, "is_primary_phone": 1}] if mobile_no else [],
        "links": [{
            "link_doctype": "Supplier",
            "link_name": supplier.name
        }]
    })
    contact.insert(ignore_permissions=True)

    # ----------- Step 5: Update Supplier with Address & Contact -----------
    supplier.supplier_primary_address = address.name
    supplier.supplier_primary_contact = contact.name
    supplier.save(ignore_permissions=True)

    frappe.set_user("Guest")

    # ----------- Step 6: Send Confirmation Email -----------
    subject = f"Welcome {supplier_name}!"
    reset_link = user.reset_password()


    # Derive login link from the same base as reset link
    from urllib.parse import urlparse
    parsed = urlparse(reset_link)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    login_link = f"{base_url}/login"


    message = f"""
        <p>Dear {supplier_name},</p>
        <p>Thank you for registering as a supplier on our portal.</p>
        <p>Your Supplier ID: <b>{supplier.name}</b></p>
        <p>You can log in using your email: <b>{email_id}</b></p>
        
        <p>🔑 <b>Set Your Password:</b> 
        <a href="{reset_link}" style="color:#1a73e8;">Click here to set your password</a></p>

        <p>🌐 <b>Login to Portal:</b> 
        <a href="{login_link}" style="color:#1a73e8;">Go to Login Page</a></p>
        
        <p>Our team will review and approve your supplier account shortly.</p>
        <p>Best regards,<br>Supplier Management Team</p>
    """

    frappe.sendmail(
        recipients=[email_id],
        subject=subject,
        message=message
    )

    return {"status": "success", "supplier": supplier.name}
