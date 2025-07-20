import cv2
from deepface import DeepFace
import mysql.connector
from datetime import datetime
import uuid
from collections import defaultdict

# --------------------- MySQL Setup ---------------------
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="a1b2c345678#",
    database="student_emotions_db"
)
cursor = conn.cursor()

# --------------------- Database Setup ---------------------
# Table to store each emotion record with session_id
cursor.execute(''' 
    CREATE TABLE IF NOT EXISTS emotions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        session_id VARCHAR(255),
        timestamp DATETIME,
        emotion VARCHAR(255)
    )
''')

# Table to store the average emotion summary for each session
cursor.execute(''' 
    CREATE TABLE IF NOT EXISTS emotion_summary (
        id INT AUTO_INCREMENT PRIMARY KEY,
        session_id VARCHAR(255),
        session_date DATE,
        happy_avg FLOAT,
        sad_avg FLOAT,
        angry_avg FLOAT,
        surprise_avg FLOAT,
        neutral_avg FLOAT,
        fear_avg FLOAT,
        disgust_avg FLOAT
    )
''')
conn.commit()

# --------------------- Generate Session ID ---------------------
session_id = str(uuid.uuid4())  # Unique session ID for each run

# --------------------- Emotion Tracking Setup ---------------------
emotion_counts = defaultdict(int)
frame_count = 0
session_date = datetime.now().date()

# --------------------- Webcam and Detection ---------------------
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
    faces = results if isinstance(results, list) else [results]

    for face in faces:
        x, y, w, h = face['region']['x'], face['region']['y'], face['region']['w'], face['region']['h']
        emotion = face['dominant_emotion'].lower()  # Normalize emotion to lowercase

        # Draw bounding box and emotion
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(frame, emotion, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

        # Save to emotion log table
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(''' 
            INSERT INTO emotions (session_id, timestamp, emotion) 
            VALUES (%s, %s, %s)
        ''', (session_id, timestamp, emotion))
        conn.commit()

        # Count emotion for session summary
        emotion_counts[emotion] += 1
        frame_count += 1

    cv2.imshow('Classroom Emotion Monitoring', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --------------------- Release Webcam ---------------------
cap.release()
cv2.destroyAllWindows()

# --------------------- Store Average Emotion Summary ---------------------
if frame_count > 0:
    summary_data = {
        "happy_avg": round((emotion_counts.get("happy", 0) / frame_count) * 100, 2),
        "sad_avg": round((emotion_counts.get("sad", 0) / frame_count) * 100, 2),
        "angry_avg": round((emotion_counts.get("angry", 0) / frame_count) * 100, 2),
        "surprise_avg": round((emotion_counts.get("surprise", 0) / frame_count) * 100, 2),
        "neutral_avg": round((emotion_counts.get("neutral", 0) / frame_count) * 100, 2),
        "fear_avg": round((emotion_counts.get("fear", 0) / frame_count) * 100, 2),
        "disgust_avg": round((emotion_counts.get("disgust", 0) / frame_count) * 100, 2)
    }

    # Insert emotion summary with session_id
    cursor.execute(''' 
        INSERT INTO emotion_summary (session_id, session_date, happy_avg, sad_avg, angry_avg, surprise_avg, neutral_avg, fear_avg, disgust_avg)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        session_id, session_date,
        summary_data["happy_avg"],
        summary_data["sad_avg"],
        summary_data["angry_avg"],
        summary_data["surprise_avg"],
        summary_data["neutral_avg"],
        summary_data["fear_avg"],
        summary_data["disgust_avg"]
    ))
    conn.commit()

# --------------------- Close MySQL Connection ---------------------
cursor.close()
conn.close()
