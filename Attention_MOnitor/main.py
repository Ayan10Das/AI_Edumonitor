import cv2
import dlib
import pickle
import numpy as np
import face_recognition
from datetime import datetime
import mysql.connector
from scipy.spatial import distance as dist

# Load encodings
with open("encodings.pkl", "rb") as f:
    known_encodings = pickle.load(f)

# MySQL DB connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="a1b2c345678#",
    database="student_attention_monitoring"
)
cursor = conn.cursor()

# Dlib models
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
LEFT_EYE = list(range(36, 42))
RIGHT_EYE = list(range(42, 48))
ALERT_THRESHOLD = 3
student_alert_counters = {}

# Eye aspect ratio thresholds
EYE_AR_THRESH = 0.25  # Threshold for eye closure detection
EYE_AR_CONSEC_FRAMES = 3  # Number of consecutive frames for eye closure

def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

def is_looking_forward(shape, frame_width):
    # Get the nose tip and chin points
    nose_tip = shape.part(30)
    chin = shape.part(8)
    
    # Calculate face center and width
    face_center_x = (shape.part(1).x + shape.part(15).x) / 2
    face_width = abs(shape.part(1).x - shape.part(15).x)
    
    # Calculate position relative to frame
    frame_center = frame_width / 2
    position_ratio = abs(face_center_x - frame_center) / frame_width
    
    # Simple heuristic for forward-looking
    # 1. Check if nose tip is above chin (not looking down)
    # 2. Check if face is reasonably centered in frame
    if (nose_tip.y < chin.y and 
        position_ratio < 0.3 and 
        abs(nose_tip.x - face_center_x) < face_width * 0.2):
        return True
    return False

cap = cv2.VideoCapture(0)
eye_counters = {}  # To track consecutive frames with closed eyes

while True:
    ret, frame = cap.read()
    if not ret:
        break
        
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb)
    face_encodings = face_recognition.face_encodings(rgb, face_locations)

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        name = "Unknown"
        status = "Unattentive"  # Default to unattentive

        matches = face_recognition.compare_faces(list(known_encodings.values()), face_encoding, tolerance=0.5)
        face_dist = face_recognition.face_distance(list(known_encodings.values()), face_encoding)

        if True in matches:
            match_index = np.argmin(face_dist)
            name = list(known_encodings.keys())[match_index]

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            rect = dlib.rectangle(left, top, right, bottom)
            shape = predictor(gray, rect)
            
            # Initialize eye counter for new students
            if name not in eye_counters:
                eye_counters[name] = 0

            # Calculate eye aspect ratio
            left_eye = np.array([(shape.part(i).x, shape.part(i).y) for i in LEFT_EYE])
            right_eye = np.array([(shape.part(i).x, shape.part(i).y) for i in RIGHT_EYE])
            ear = (eye_aspect_ratio(left_eye) + eye_aspect_ratio(right_eye)) / 2.0

            # Check for eye closure
            if ear < EYE_AR_THRESH:
                eye_counters[name] += 1
                if eye_counters[name] >= EYE_AR_CONSEC_FRAMES:
                    status = "Unattentive (Sleeping)"
            else:
                eye_counters[name] = 0
                # Check if looking forward
                if is_looking_forward(shape, frame.shape[1]):
                    status = "Attentive"
                else:
                    status = "Unattentive (Distracted)"

        # Alert system
        student_alert_counters.setdefault(name, 0)
        if status == "Attentive":
            student_alert_counters[name] = 0  # Reset counter if attentive
        else:
            student_alert_counters[name] += 1
            if student_alert_counters[name] >= ALERT_THRESHOLD:
                print(f"⚠️ ALERT: {name} is inattentive!")
                student_alert_counters[name] = 0  # Reset counter after alert

        # Store in database
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO attention_logs (timestamp, student_id, status) VALUES (%s, %s, %s)",
                      (timestamp, name, status))
        conn.commit()

        # Display on frame
        color = (0, 255, 0) if status == "Attentive" else (0, 0, 255)
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, f"{name}: {status}", (left, top - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    cv2.imshow("Student Attention Monitor", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
conn.close()
cv2.destroyAllWindows()