
import frappe
import os
import PyPDF2
from PIL import Image
from frappe.utils.file_manager import get_file_path


@frappe.whitelist(allow_guest=True)
def download_rfq_pdf(rfq_name):
    print("in  ......")
    doc = frappe.get_doc("Request for Quotation", rfq_name)
    temp_dir = frappe.get_site_path("public", "files")

    merged_pdf_path = os.path.join(temp_dir, f"{rfq_name}_merged.pdf")
    merger = PyPDF2.PdfMerger()

    # --------------------------------------------------
    # 1️⃣ MAIN RFQ FORM (PRINT FORMAT PDF)
    # --------------------------------------------------
    pdf_bytes = frappe.get_print(
        "Request for Quotation",
        rfq_name,
        print_format=None,   # use default form print
        as_pdf=True
    )

    main_pdf_path = os.path.join(temp_dir, f"{rfq_name}_form.pdf")
    with open(main_pdf_path, "wb") as f:
        f.write(pdf_bytes)

    merger.append(main_pdf_path)

    # --------------------------------------------------
    # 2️⃣ FETCH ATTACHMENT INDEX ORDER
    # --------------------------------------------------
    index_records = frappe.get_all(
        "File Attachment Index",
        filters={"module": "Request for Quotation"},
        fields=["attachment_type", "idx"],
        order_by="idx asc"
    )

    index_map = {d["attachment_type"]: d["idx"] for d in index_records}
    # --------------------------------------------------
    # 3️⃣ SORT RFQ ATTACHMENTS USING INDEX
    # --------------------------------------------------
    attachments = []

    for row in doc.custom_addendum:
        if not row.attachment:
            continue

        att_type = row.attachment_type or ""
        att_index = index_map.get(att_type, 999)

        attachments.append({
            "path": get_file_path(row.attachment),
            "type": att_type,
            "idx": att_index
        })

    attachments.sort(key=lambda x: x["idx"])
    # --------------------------------------------------
    # 4️⃣ MERGE ATTACHMENTS
    # --------------------------------------------------
    for att in attachments:
        file_path = att["path"].lower()

        if file_path.endswith(".pdf"):
            merger.append(att["path"])

        elif file_path.endswith((".jpg", ".jpeg", ".png")):
            img_pdf = convert_image_to_pdf(att["path"], temp_dir)
            if img_pdf:
                merger.append(img_pdf)

    # --------------------------------------------------
    # 5️⃣ SAVE FINAL MERGED PDF
    # --------------------------------------------------
    with open(merged_pdf_path, "wb") as f:
        merger.write(f)

    merger.close()

    return f"/files/{rfq_name}_merged.pdf"


# -----------------------------------------------
# 🔹 Convert image to PDF
# -----------------------------------------------
def convert_image_to_pdf(image_path, output_folder):
    try:
        img = Image.open(image_path).convert("RGB")

        pdf_path = os.path.join(
            output_folder,
            os.path.basename(image_path).split('.')[0] + "_img.pdf"
        )

        img.save(pdf_path, "PDF", resolution=100.0)

        return pdf_path

    except Exception as e:
        frappe.log_error(f"Image → PDF failed: {e}")
        return None
