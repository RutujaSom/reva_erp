import frappe
from frappe.model.document import Document
import string
import random

"""Send mail o supplier for at the time od creatiion"""
def after_supplier_insert(self):
    print('after_supplier_insert .....',self.workflow_state)
    # Get supplier email (assuming you have an email field)
    supplier_email = self.email_id  # replace with your actual fieldname
    if supplier_email:
        subject = "Welcome to Our System"
        message = f"""
            <p>Dear {self.supplier_name},</p>
            <p>Thank you for registering as a supplier with us.</p>
            <p>We look forward to working with you.</p>
        """

        # Send email
        frappe.sendmail(
            recipients=[supplier_email],
            subject=subject,
            message=message
        )



def after_supplier_approved(self):
    print('after_supplier_approved .....',self.workflow_state)
    """
        Trigger custom logic after Supplier document is updated post submission.
        Handles creation of User accounts and notification emails based on workflow state.
    """
    # APPROVED SUPPLIER
    if self.workflow_state == "Approved":
        
        # Email message to notifiy supplier
        message = f"""
        <p>Dear <b>{self.supplier_name}</b>,</p>
        <p>Congratulations! Your supplier registration has been <b>approved</b>.</p>
        
        <p style="margin-top:20px;">Best regards,<br>
        """

        frappe.sendmail(
            recipients=[self.email_id],
            subject="Supplier Registration Approved",
            message=message
        )

    # REJECTED SUPPLIER
    elif self.workflow_state == "Rejected":
        message = f"""
        <p>Dear <b>{self.supplier_name}</b>,</p>
        <p>We regret to inform you that your supplier registration has been <b>rejected</b>.</p>
        <p>For further details, please contact us.</p>
        <p style="margin-top:20px;">Best regards,<br>
        """
        frappe.sendmail(
            recipients=[self.email_id],
            subject="Supplier Registration Rejected",
            message=message
        )



@frappe.whitelist()
def get_supplier_for_user(user):
    return frappe.db.sql("""
        SELECT s.name, s.workflow_state
        FROM `tabSupplier` s
        INNER JOIN `tabPortal User` p ON p.parent = s.name
        WHERE p.user = %s
        LIMIT 1
    """, user, as_dict=True)





import frappe

@frappe.whitelist()
def create_user_for_supplier(doc, method):
    """
    Automatically create a User for the Supplier when a new Supplier is saved,
    and send a confirmation email like the web registration process.
    """
    supplier_name = doc.supplier_name
    email_id =  doc.email_id or None  # Adjust fieldname if different
    mobile_no =  doc.mobile_no or None  # Adjust if needed

    if not email_id:
        frappe.logger().warning(f"Supplier {supplier_name} has no email; skipping user creation.")
        return

    frappe.set_user("Administrator")

    # --- Step 1: Create User if not exists ---
    if not frappe.db.exists("User", email_id):
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
    else:
        user = frappe.get_doc("User", email_id)

    # --- Step 2: Link User in Supplier portal_users child table ---
    if not any(u.user == user.name for u in doc.portal_users):
        doc.append("portal_users", {"user": user.name})
        doc.save(ignore_permissions=True)

    frappe.set_user("Guest")

    reset_link = user.reset_password()
    # Derive login link from the same base as reset link
    from urllib.parse import urlparse
    parsed = urlparse(reset_link)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    login_link = f"{base_url}/login"



    # --- Step 3: Send Confirmation Email ---
    subject = f"Welcome {supplier_name}!"
    message = f"""
        <p>Dear {supplier_name},</p>
        <p>Thank you for registering as a supplier on our portal.</p>
        <p>Your Supplier ID: <b>{doc.name}</b></p>
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
