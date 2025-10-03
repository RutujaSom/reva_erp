
import frappe

def send_email_on_workflow_state(self, method=None):
    """
    Send email to supplier automatically based on workflow_state
    Uses contact_email field of the PO
    """

    supplier_email = self.contact_email
    supplier_name = self.supplier

    if not supplier_email:
        return

    if self.workflow_state == "Approved":
        message = f"""
        <p>Dear <b>{supplier_name}</b>,</p>
        <p>Your Purchase Order <b>{self.name}</b> has been <b>approved</b>.</p>
        <p>Thank you for your support.</p>
        <p>Best regards,<br>[Your Company Name]</p>
        """
        frappe.sendmail(
            recipients=[supplier_email],
            subject=f"Purchase Order {self.name} Approved",
            message=message,
            reference_doctype="Purchase Order",
            reference_name=self.name
        )

    elif self.workflow_state == "Rejected":
        message = f"""
        <p>Dear <b>{supplier_name}</b>,</p>
        <p>We regret to inform you that your Purchase Order <b>{self.name}</b> has been <b>rejected</b>.</p>
        <p>For queries, please contact us.</p>
        <p>Best regards,<br>[Your Company Name]</p>
        """
        frappe.sendmail(
            recipients=[supplier_email],
            subject=f"Purchase Order {self.name} Rejected",
            message=message,
            reference_doctype="Purchase Order",
            reference_name=self.name
        )
