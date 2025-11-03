

import frappe
import requests
from frappe.utils import get_datetime

@frappe.whitelist(allow_guest=True)
def fetch_attendance_from_middleware():
    try:
        response = requests.get("http://192.168.1.21:5000/import_attendance", timeout=30)
        # response = requests.get("http://172.31.28.159:5000/import_attendance", timeout=30)

        data = response.json()
        print("data ....",data)

        if data.get("status") != "success":
            return f"Error from middleware: {data.get('message')}"

        inserted_count = 0
        for record in data.get("records", []):
            if not frappe.db.exists("Bio Matric Attendance", {"attendance_id": record["id"]}):
                doc = frappe.get_doc({
                    "doctype": "Bio Matric Attendance",
                    "enroll_id": record["enroll_id"],
                    "record_time": get_datetime(record["records_time"]),
                    "in_out": record["in_out"],
                    "device_ser_no": record["device_serial_num"],
                    "event": record["event"],
                    "flag": record["flag"],
                    "io_status": record["io_status"],
                    "mode": record["mode"],
                    "temperature": record["temperature"],
                    "attendance_id": record["id"]
                })
                doc.insert(ignore_permissions=True)
                inserted_count += 1

        frappe.db.commit()
        return f"Attendance Imported Successfully. {inserted_count} new records inserted."

    except Exception as e:
        frappe.log_error(message=str(e), title="Fetch Attendance Error")
        return f"Error: {e}"
