import frappe
import os
import PyPDF2
from PIL import Image
from frappe.utils.file_manager import get_file_path
from datetime import datetime

# @frappe.whitelist()
# def download_po_pdf(purchase_order_name):
#     po_name = purchase_order_name

#     # --------------------------------------------
#     # 0️⃣  INIT
#     # --------------------------------------------

#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     po_doc = frappe.get_doc("Purchase Order", po_name)
#     temp_dir = frappe.get_site_path("public", "files")

#     # merged_pdf_path = os.path.join(temp_dir, f"{po_name}_merged.pdf")
#     merged_pdf_path = os.path.join(temp_dir, f"PO_{timestamp}_merged.pdf")
#     print("merged_pdf_path ...",merged_pdf_path)
#     merger = PyPDF2.PdfMerger()

#     # --------------------------------------------
#     # 1️⃣  MAIN PURCHASE ORDER PDF
#     # --------------------------------------------
#     pdf_bytes = frappe.get_print(
#         "Purchase Order",
#         po_name,
#         print_format="Purchase Order Form Format",
#         as_pdf=True
#     )

#     # main_pdf_path = os.path.join(temp_dir, f"{po_name}_form.pdf")
#     main_pdf_path = os.path.join(temp_dir, f"PO_{timestamp}_form.pdf")
#     with open(main_pdf_path, "wb") as f:
#         f.write(pdf_bytes)

#     merger.append(main_pdf_path)

#     # --------------------------------------------
#     # 2️⃣  LOAD FILE ATTACHMENT INDEX
#     # --------------------------------------------
#     index_records = frappe.get_all(
#         "File Attachment Index",
#         filters={"module": "Request for Quotation"},
#         fields=["attachment_type", "idx"],
#         order_by="idx asc"
#     )
#     print("index_records ...",index_records)

#     index_map = {d["attachment_type"]: d["idx"] for d in index_records}

#     # --------------------------------------------
#     # 3️⃣  FIND RFQs VIA SUPPLIER QUOTATION
#     # --------------------------------------------
#     rfq_list = set()

#     for item in po_doc.items:
#         if not item.supplier_quotation:
#             continue

#         sq = frappe.get_doc("Supplier Quotation", item.supplier_quotation)

#         # supplier quotation items have rfq link
#         for sq_item in sq.items:
#             if sq_item.request_for_quotation:
#                 rfq_list.add(sq_item.request_for_quotation)

#     # --------------------------------------------
#     # 4️⃣  COLLECT ALL ATTACHMENTS FROM RFQs
#     # --------------------------------------------
#     all_attachments = []

#     for rfq_name in rfq_list:
#         rfq_doc = frappe.get_doc("Request for Quotation", rfq_name)

#         for row in rfq_doc.custom_addendum:
#             if not row.attachment:
#                 continue

#             att_type = row.attachment_type or ""
#             att_index = index_map.get(att_type, 999)

#             all_attachments.append({
#                 "path": get_file_path(row.attachment),
#                 "type": att_type,
#                 "idx": att_index
#             })

#     # sort all rfq attachments based on index table
#     all_attachments.sort(key=lambda x: x["idx"])

#     # --------------------------------------------
#     # 5️⃣  MERGE ATTACHMENTS INTO FINAL PDF
#     # --------------------------------------------
#     for att in all_attachments:

#         file_path = att["path"].lower()

#         if file_path.endswith(".pdf"):
#             merger.append(att["path"])

#         elif file_path.endswith((".jpg", ".jpeg", ".png")):
#             img_pdf = convert_image_to_pdf(att["path"], temp_dir)
#             if img_pdf:
#                 merger.append(img_pdf)

#     # --------------------------------------------
#     # 6️⃣  SAVE FINAL MERGED PDF
#     # --------------------------------------------
#     with open(merged_pdf_path, "wb") as f:
#         merger.write(f)

#     merger.close()

#     # return f"/files/{po_name}_merged.pdf"
#     return f"/files/PO_{timestamp}_merged.pdf"


# --------------------------------------------
# 🔹 Convert image to PDF
# --------------------------------------------
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






import frappe
import os
import PyPDF2
from frappe.utils.file_manager import get_file_path
from datetime import datetime

@frappe.whitelist()
def download_po_pdf(purchase_order_name):

    po_name = purchase_order_name
    po_name_1 = purchase_order_name.replace("/", "-")

    # --------------------------------------------
    # 0️⃣ INIT
    # --------------------------------------------
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"PO_{po_name_1}_{timestamp}.pdf"

    site_path = frappe.get_site_path()
    pdf_folder = os.path.join(site_path, "public", "files")
    output_pdf_path = os.path.join(pdf_folder, output_filename)

    os.makedirs(pdf_folder, exist_ok=True)

    merger = PyPDF2.PdfMerger()

    # --------------------------------------------
    # 1️⃣ ADD PO PDF
    # --------------------------------------------
    po_pdf = frappe.get_print("Purchase Order", po_name, as_pdf=True)
    po_pdf_path = os.path.join(pdf_folder, f"PO_TEMP_{timestamp}.pdf")

    with open(po_pdf_path, "wb") as f:
        f.write(po_pdf)

    merger.append(po_pdf_path)

    # --------------------------------------------
    #  2️⃣ ADD TERMS & CONDITIONS PDF
    # --------------------------------------------
    try:
        tc_path = get_file_path("REVA Terms and Condition.pdf")
        merger.append(tc_path)
    except Exception:
        frappe.throw("Terms & Conditions PDF not found in File List.")


    # --------------------------------------------
    # 3️⃣ ADD RFQ TECHNICAL PDF(s)
    # --------------------------------------------
    po_doc = frappe.get_doc("Purchase Order", po_name)

    rfq_list = set()

    # Find all RFQs linked through Supplier Quotation Items
    for item in po_doc.items:
        if not item.supplier_quotation:
            continue

        sq = frappe.get_doc("Supplier Quotation", item.supplier_quotation)

        for sq_item in sq.items:
            if sq_item.request_for_quotation:
                rfq_list.add(sq_item.request_for_quotation)

    # Now collect technical attachments from RFQ
    for rfq in rfq_list:
        rfq_doc = frappe.get_doc("Request for Quotation", rfq)
        for att in rfq_doc.custom_addendum:
            if att.attachment_type == "Technical" and att.attachment:
                try:
                    tech_file_path = get_file_path(att.attachment)
                    file_path = tech_file_path.lower()

                    if file_path.endswith(".pdf"):
                        merger.append(tech_file_path)

                    elif file_path.endswith((".jpg", ".jpeg", ".png")):
                        img_pdf = convert_image_to_pdf(tech_file_path, pdf_folder)
                        if img_pdf:
                            merger.append(img_pdf)

                    # merger.append(tech_file_path)
                except Exception as e:
                    print(e ,'.........')
                    pass

    # --------------------------------------------
    # 4️⃣ ADD SUPPLIER QUOTATION PDF(s)
    # --------------------------------------------


    # --------------------------------------------
    # 2️⃣  LOAD FILE ATTACHMENT INDEX
    # --------------------------------------------
    index_records = frappe.get_all(
        "File Attachment Index",
        filters={"module": "Purchase Order"},
        fields=["attachment_type", "idx"],
        order_by="idx asc"
    )

    index_map = {d["attachment_type"]: d["idx"] for d in index_records}

    # --------------------------------------------
    # 3️⃣  FIND RFQs VIA SUPPLIER QUOTATION
    # --------------------------------------------

    all_attachments = []
    for item in po_doc.items:
        if not item.supplier_quotation:
            continue

        sq = frappe.get_doc("Supplier Quotation", item.supplier_quotation)

        for row in sq.custom_addendum:
            if not row.attachment:
                continue

            att_type = row.attachment_type or ""
            att_index = index_map.get(att_type, 999)

            all_attachments.append({
                "path": get_file_path(row.attachment),
                "type": att_type,
                "idx": att_index
            })


    # --------------------------------------------
    # 5️⃣  MERGE ATTACHMENTS INTO FINAL PDF
    # --------------------------------------------
    for att in all_attachments:

        file_path = att["path"].lower()

        if file_path.endswith(".pdf"):
            merger.append(att["path"])

        elif file_path.endswith((".jpg", ".jpeg", ".png")):
            img_pdf = convert_image_to_pdf(att["path"], pdf_folder)
            if img_pdf:
                merger.append(img_pdf)

    
    # --------------------------------------------
    # 6️⃣  SAVE FINAL MERGED PDF
    # --------------------------------------------
    with open(output_pdf_path, "wb") as f:
        merger.write(f)
    merger.close()

    # --------------------------------------------
    # 6️⃣ RETURN IT TO USER
    # --------------------------------------------
    return f"/files/{output_filename}"
