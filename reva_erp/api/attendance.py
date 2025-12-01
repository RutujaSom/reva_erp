import frappe
from datetime import datetime, timedelta
import pyodbc


@frappe.whitelist()
def sync_device_records():
    try:
        # SQL Server connection
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=114.29.233.189;'
            'DATABASE=deviceManagement;'
            'UID=sa;'
            'PWD=dsspl@123;'
        )

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM records")

        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]

        inserted_count = 0
        skipped_count = 0

        for row in rows:
            rec = dict(zip(columns, row))

            attendance_id = rec.get("id")

            # Skip if this attendance ID already exists
            if frappe.db.exists("Bio Matric Attendance", {"attendance_id": str(attendance_id)}):
                skipped_count += 1
                continue

            # Create new Frappe Doc
            doc = frappe.new_doc("Bio Matric Attendance")
            doc.attendance_id = rec.get("id")
            doc.device_ser_no = rec.get("device_serial_num")
            doc.enroll_id = rec.get("enroll_id")
            doc.event = rec.get("event")
            doc.flag = rec.get("flag")
            doc.io_status = rec.get("io_status")
            doc.in_out = rec.get("in_out")
            doc.mode = rec.get("mode")
            doc.record_time = rec.get("records_time")
            doc.temperature = rec.get("temperature")
            doc.save(ignore_permissions=True)

            inserted_count += 1

        frappe.db.commit()

        return {
            "status": "success",
            "inserted": inserted_count,
            "skipped_existing": skipped_count
        }

    except Exception as e:
        frappe.log_error(str(e), "SQL Server Sync Error")
        return {"error": str(e)}





@frappe.whitelist()
def generate_daily_attendance():

    employees = frappe.get_all("Employee",
        filters={"custom_attendance_id": ["!=", ""]},
        fields=["name", "custom_attendance_id"]
    )

    created = 0
    updated = 0

    for emp in employees:

        punches = frappe.get_all(
            "Bio Matric Attendance",
            filters={"enroll_id": emp.custom_attendance_id},
            fields=["record_time"],
            order_by="record_time asc"
        )

        if not punches:
            continue

        # Group punches by DATE
        daily_records = {}

        for p in punches:
            punch_date = p.record_time.date()

            if punch_date not in daily_records:
                daily_records[punch_date] = []

            daily_records[punch_date].append(p.record_time)

        # Now process each date
        for punch_date, times in daily_records.items():

            times = sorted(times)
            in_time = times[0]
            out_time = times[-1] if len(times) > 1 else None

            # Check existing attendance for that day
            exists = frappe.db.exists("Attendance", {
                "employee": emp.name,
                "attendance_date": punch_date
            })

            if exists:
                att = frappe.get_doc("Attendance", exists)
                att.in_time = in_time
                att.out_time = out_time
                att.shift = "General Shift"
                att.status = "Present"
                att.save(ignore_permissions=True)
                updated += 1
            else:
                att = frappe.new_doc("Attendance")
                att.employee = emp.name
                att.attendance_date = punch_date
                att.status = "Present"
                att.shift = "General Shift"
                att.in_time = in_time
                att.out_time = out_time
                att.save(ignore_permissions=True)
                created += 1
        frappe.db.commit()


    return {
        "created": created,
        "updated": updated
    }





@frappe.whitelist(allow_guest=True)
def generate_last_15_days_attendance():

    # Calculate date range
    end_date = datetime.today()
    start_date = end_date - timedelta(days=15)

    created = 0
    updated = 0

    employees = frappe.get_all(
        "Employee",
        filters={"custom_attendance_id": ["!=", ""]},
        fields=["name", "custom_attendance_id"]
    )

    for emp in employees:

        punches = frappe.get_all(
            "Bio Matric Attendance",
            filters={
                "enroll_id": emp.custom_attendance_id,
                "record_time": [
                    "between",
                    [
                        start_date.strftime("%Y-%m-%d 00:00:00"),
                        end_date.strftime("%Y-%m-%d 23:59:59")
                    ]
                ]
            },
            fields=["record_time", "in_out"],
            order_by="record_time asc"
        )

        if not punches:
            continue

        # Group by date
        daily_records = {}

        for p in punches:
            punch_date = p.record_time.date()

            if punch_date not in daily_records:
                daily_records[punch_date] = []

            daily_records[punch_date].append(p.record_time)

        # Process each date
        for punch_date, times in daily_records.items():

            times = sorted(times)
            in_time = times[0]
            out_time = times[-1] if len(times) > 1 else None

            exists = frappe.db.exists("Attendance", {
                "employee": emp.name,
                "attendance_date": punch_date
            })

            if exists:
                att = frappe.get_doc("Attendance", exists)
                att.in_time = in_time
                att.out_time = out_time
                att.status = "Present"
                att.shift = "General Shift"
                att.save(ignore_permissions=True)
                updated += 1

            else:
                att = frappe.new_doc("Attendance")
                att.employee = emp.name
                att.attendance_date = punch_date
                att.status = "Present"
                att.shift = "General Shift"
                att.in_time = in_time
                att.out_time = out_time
                att.save(ignore_permissions=True)
                created += 1

        frappe.db.commit()

    return {
        "created": created,
        "updated": updated
    }
