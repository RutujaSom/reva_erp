import frappe
import pyodbc

@frappe.whitelist(allow_guest=True)
def import_attendance_from_external_db():
    print('Connecting to SQL Server...')
    
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=114.29.233.189;"
        "DATABASE=devicemanagement;"
        "UID=sa;"
        "PWD=dsspl@123;"
    )

    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            id, device_serial_num, enroll_id, event, flag, io_status, image,
            in_out, mode, records_time, temperature
        FROM records
    """)

    records = cursor.fetchall()

    for record in records:
        print('record .......', record, ' ...... ////record.record_time ...',record.records_time)
        attendance_id = record.id
        exists = frappe.db.exists("Bio Matric Attendance", {"attendance_id": attendance_id})

        if not exists:
            attendance_doc = frappe.get_doc({
                "doctype": "Bio Matric Attendance",
                "enroll_id": record.enroll_id,
                "record_time": record.records_time,
                "in_out": record.in_out,
                "device_ser_no": record.device_serial_num,
                "event": record.event,
                "flag": record.flag,
                "io_status": record.io_status,
                "mode": record.mode,
                "temperature": record.temperature,
                "attendance_id": record.id
            })
            attendance_doc.insert(ignore_permissions=True)
            frappe.db.commit()

    cursor.close()
    conn.close()
    return "Data Imported Successfully"
