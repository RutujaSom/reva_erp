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

