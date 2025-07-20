# scripts/view_attendance.py
import mysql.connector
from datetime import datetime

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="a1b2c345678#",
    database="attendance_system"
)

cursor = db.cursor()

# Get today's date
today = datetime.now().date()

cursor.execute("SELECT * FROM attendance_log WHERE date = %s", (today,))
rows = cursor.fetchall()

print(f"Attendance for {today}:")
for row in rows:
    print(row)

db.close()
