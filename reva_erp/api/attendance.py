import frappe
from datetime import datetime, timedelta
import pyodbc


# @frappe.whitelist()
# def sync_device_records():
#     try:
#         # SQL Server connection
#         conn = pyodbc.connect(
#             'DRIVER={ODBC Driver 17 for SQL Server};'
#             'SERVER=114.29.233.189;'
#             'DATABASE=deviceManagement;'
#             'UID=sa;'
#             'PWD=dsspl@123;'
#         )

#         cursor = conn.cursor()
#         cursor.execute("SELECT * FROM records")

#         rows = cursor.fetchall()
#         columns = [column[0] for column in cursor.description]

#         inserted_count = 0
#         skipped_count = 0

#         for row in rows:
#             rec = dict(zip(columns, row))

#             attendance_id = rec.get("id")

#             # Skip if this attendance ID already exists
#             if frappe.db.exists("Bio Matric Attendance", {"attendance_id": str(attendance_id)}):
#                 skipped_count += 1
#                 continue

#             # Create new Frappe Doc
#             doc = frappe.new_doc("Bio Matric Attendance")
#             doc.attendance_id = rec.get("id")
#             doc.device_ser_no = rec.get("device_serial_num")
#             doc.enroll_id = rec.get("enroll_id")
#             doc.event = rec.get("event")
#             doc.flag = rec.get("flag")
#             doc.io_status = rec.get("io_status")
#             doc.in_out = rec.get("in_out")
#             doc.mode = rec.get("mode")
#             doc.record_time = rec.get("records_time")
#             doc.temperature = rec.get("temperature")
#             doc.save(ignore_permissions=True)

#             inserted_count += 1

#         frappe.db.commit()

#         return {
#             "status": "success",
#             "inserted": inserted_count,
#             "skipped_existing": skipped_count
#         }

#     except Exception as e:
#         frappe.log_error(str(e), "SQL Server Sync Error")
#         return {"error": str(e)}



@frappe.whitelist()
def sync_device_records():
    try:
        # 1️⃣ Get last saved attendance ID from Frappe
        last_att_id = frappe.db.get_value(
            "Bio Matric Attendance",
            filters={},
            fieldname="attendance_id",
            order_by="attendance_id DESC"
        )

        # If no record found, set to 0
        last_att_id = int(last_att_id) if last_att_id else 0

        # 2️⃣ SQL Server connection
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 18 for SQL Server};'
            'SERVER=114.29.233.189;'
            'DATABASE=deviceManagement;'
            'UID=sa;'
            'PWD=dsspl@123;'
            'Encrypt=no;'
            'TrustServerCertificate=yes;'
        )

        cursor = conn.cursor()

        # 3️⃣ Fetch only NEW records
        query = f"""
            SELECT * FROM records
            WHERE id > {last_att_id}
            ORDER BY id ASC
        """
        cursor.execute(query)

        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]

        inserted_count = 0

        # 4️⃣ Insert new records
        for row in rows:
            # Skip if this attendance ID already exists
            rec = dict(zip(columns, row))
            attendance_id = rec.get("id")
            if frappe.db.exists("Bio Matric Attendance", {"attendance_id": attendance_id}):
                skipped_count += 1
                continue
            #rec = dict(zip(columns, row))

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
            "last_attendance_id": last_att_id
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
    start_date = end_date - timedelta(days=2)

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




@frappe.whitelist()
def create_employee_checkin_from_bio():
    try:
        # 1️⃣ Fetch only NEW biometric entries (added_in_attendance = 0)
        bio_records = frappe.db.get_all(
            "Bio Matric Attendance",
            filters={"added_in_attendance": 0},
            fields="*",
            order_by="record_time ASC"
        )

        created_count = 0

        for rec in bio_records:

            # 2️⃣ Map enroll_id → Employee
            employee_id = frappe.db.get_value(
                "Employee",
                {"custom_attendance_id": rec.get("enroll_id")},
                ["name", "employee_name"],as_dict=True
            )

            if not employee_id:
                continue  # No employee mapping → skip


            # 5️⃣ Create new Employee Checkin
            checkin_doc = frappe.new_doc("Employee Checkin")
            checkin_doc.employee = employee_id.name
            checkin_doc.employee_name = employee_id.employee_name
            checkin_doc.time = rec.get("record_time")
            # checkin_doc.log_type = log_type
            checkin_doc.device_id = rec.get("device_ser_no")
            checkin_doc.insert(ignore_permissions=True)
            print("checkin_doc.save",checkin_doc, '.....',rec.get('name'))

            created_count += 1

            # 6️⃣ Mark biometric record as processed
            frappe.db.set_value(
                "Bio Matric Attendance",
                rec.name,
                "added_in_attendance",
                1
            )
            print('in bio')

        frappe.db.commit()

        return {
            "status": "success",
            "employee_checkins_created": created_count
        }

    except Exception as e:
        frappe.log_error(str(e), "Employee Checkin Sync Error")
        return {"error": str(e)}













@frappe.whitelist()
def sync_device_records():
    try:
        # 0️⃣ Init counters
        inserted_count = 0
        skipped_count = 0

        # 1️⃣ Get last saved attendance ID correctly
        last_att_id = frappe.db.sql("""
            SELECT MAX(attendance_id) FROM `tabBio Matric Attendance`
        """)[0][0]

        last_att_id = int(last_att_id) if last_att_id else 0

        # 2️⃣ Connect SQL server
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 18 for SQL Server};'
            'SERVER=114.29.233.189;'
            'DATABASE=deviceManagement;'
            'UID=sa;'
            'PWD=dsspl@123;'
            'Encrypt=no;'
            'TrustServerCertificate=yes;'
        )
        cursor = conn.cursor()

        # 3️⃣ Fetch NEW records only
        cursor.execute("""
            SELECT id, device_serial_num, enroll_id, event, flag,
                   io_status, in_out, mode, records_time, temperature
            FROM records
            WHERE id > ?
            ORDER BY id ASC
        """, (last_att_id,))

        rows = cursor.fetchall()

        for row in rows:

            attendance_id = row.id

            # 4️⃣ Double-check duplicate BEFORE insertion
            if frappe.db.exists(
                "Bio Matric Attendance",
                {"attendance_id": attendance_id}
            ):
                skipped_count += 1
                continue

            # 5️⃣ Insert new record
            doc = frappe.new_doc("Bio Matric Attendance")
            doc.attendance_id = row.id
            doc.device_ser_no = row.device_serial_num
            doc.enroll_id = row.enroll_id
            doc.event = row.event
            doc.flag = row.flag
            doc.io_status = row.io_status
            doc.in_out = row.in_out
            doc.mode = row.mode
            doc.record_time = row.records_time
            doc.temperature = row.temperature
            doc.save(ignore_permissions=True)

            inserted_count += 1
            print("data .....")

        frappe.db.commit()

        return {
            "status": "success",
            "inserted": inserted_count,
            "skipped": skipped_count,
            "last_attendance_id_used": last_att_id
        }

    except Exception as e:
        frappe.log_error(str(e), "SQL Server Sync Error")
        return {"error": str(e)}
