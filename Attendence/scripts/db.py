import mysql.connector
from datetime import datetime

def mark_attendance(name):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="a1b2c345678#",
        database="attendance_system"
    )
    cursor = conn.cursor()

    today = datetime.now().strftime('%Y-%m-%d')

    # Check if already marked
    cursor.execute("SELECT * FROM attendance_log WHERE name=%s AND date=%s", (name, today))
    result = cursor.fetchone()

    if result:
        print(f"[INFO] {name} already marked present today.")
    else:
        time_now = datetime.now().strftime('%H:%M:%S')
        cursor.execute(
            "INSERT INTO attendance_log (name, date, time) VALUES (%s, %s, %s)",
            (name, today, time_now)
        )
        conn.commit()
        print(f"[SUCCESS] Attendance marked for {name} at {time_now}.")

    cursor.close()
    conn.close()