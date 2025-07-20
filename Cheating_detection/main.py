import cv2
import dlib
import numpy as np
import time
from scipy.spatial import distance as dist
from datetime import datetime
import mysql.connector
from mysql.connector import Error
import os


if not os.path.exists('evidence'):
    os.makedirs('evidence')


def create_db_connection():
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="a1b2c345678#",
            database="ExamMonitoringSystem"
        )
        return db
    except Error as e:
        print(f"Database connection error: {e}")
        return None

# Initialize face detector and predictor
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")


# Cheating detection parameters
EYE_AR_THRESH = 0.25  # Eye aspect ratio threshold
EYE_AR_CONSEC_FRAMES = 20  # Frames for looking away
MOUTH_AR_THRESH = 0.75  # Mouth aspect ratio threshold (for talking)
GAZE_DEVIATION_THRESH = 25  # Degrees of gaze deviation

# Initialize counters and flags
COUNTER = 0
cheating_flag = False
last_cheating_time = time.time()

def eye_aspect_ratio(eye):
    # Compute Euclidean distances between eye landmarks
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

def mouth_aspect_ratio(mouth):
    # Compute mouth aspect ratio
    A = dist.euclidean(mouth[2], mouth[10])  # 51, 59
    B = dist.euclidean(mouth[4], mouth[8])   # 53, 57
    C = dist.euclidean(mouth[0], mouth[6])   # 49, 55
    mar = (A + B) / (2.0 * C)
    return mar

def get_head_pose(shape, frame):
    # 2D image points
    image_points = np.array([
        (shape.part(30).x, shape.part(30).y),  # Nose tip
        (shape.part(8).x, shape.part(8).y),    # Chin
        (shape.part(36).x, shape.part(36).y),  # Left eye left corner
        (shape.part(45).x, shape.part(45).y),  # Right eye right corner
        (shape.part(48).x, shape.part(48).y),  # Left mouth corner
        (shape.part(54).x, shape.part(54).y)   # Right mouth corner
    ], dtype="double")
    
    # 3D model points
    model_points = np.array([
        (0.0, 0.0, 0.0),          # Nose tip
        (0.0, -330.0, -65.0),     # Chin
        (-225.0, 170.0, -135.0),  # Left eye left corner
        (225.0, 170.0, -135.0),   # Right eye right corner
        (-150.0, -150.0, -125.0), # Left mouth corner
        (150.0, -150.0, -125.0)   # Right mouth corner
    ])
    
    # Camera internals
    size = frame.shape
    focal_length = size[1]
    center = (size[1]/2, size[0]/2)
    camera_matrix = np.array(
        [[focal_length, 0, center[0]],
         [0, focal_length, center[1]],
         [0, 0, 1]], dtype="double"
    )
    
    # Solve PnP
    dist_coeffs = np.zeros((4,1))
    (_, rotation_vector, translation_vector) = cv2.solvePnP(
        model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE)
    
    # Calculate head pose angles
    rmat, _ = cv2.Rodrigues(rotation_vector)
    angles = cv2.RQDecomp3x3(rmat)[0]  # We only need the first element
    
    return angles

def log_cheating_incident(db, student_id, incident_type, frame_path=None):
    try:
        cursor = db.cursor()
        query = """
        INSERT INTO CheatingIncidents 
        (student_id, incident_time, incident_type, frame_path)
        VALUES (%s, %s, %s, %s)
        """
        values = (student_id, datetime.now(), incident_type, frame_path)
        cursor.execute(query, values)
        db.commit()
        cursor.close()
        return True
    except Error as e:
        print(f"Error logging cheating incident: {e}")
        return False

def monitor_exam(student_id):
    global COUNTER, cheating_flag, last_cheating_time
    
    db = create_db_connection()
    if not db:
        print("Cannot connect to database")
        return
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        return
    
    # Get video properties for recording
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))
    out = cv2.VideoWriter(f'evidence/output_{student_id}.avi', 
                         cv2.VideoWriter_fourcc(*'XVID'), 
                         10, (frame_width, frame_height))
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)
        
        # Multiple faces detection (possible impersonation)
        if len(faces) > 1:
            cheating_flag = True
            cv2.putText(frame, "MULTIPLE FACES DETECTED!", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            if time.time() - last_cheating_time > 5:  # Throttle logging
                frame_path = f"evidence/multiple_faces_{student_id}_{int(time.time())}.jpg"
                cv2.imwrite(frame_path, frame)
                log_cheating_incident(db, student_id, "Multiple faces detected", frame_path)
                last_cheating_time = time.time()
        
        # Analyze each face
        for face in faces:
            shape = predictor(gray, face)
            shape = [(shape.part(i).x, shape.part(i).y) for i in range(68)]
            shape = np.array(shape)
            
            # Extract eye and mouth regions
            left_eye = shape[42:48]
            right_eye = shape[36:42]
            mouth = shape[48:68]
            
            # Calculate eye aspect ratio
            left_ear = eye_aspect_ratio(left_eye)
            right_ear = eye_aspect_ratio(right_eye)
            ear = (left_ear + right_ear) / 2.0
            
            # Calculate mouth aspect ratio
            mar = mouth_aspect_ratio(mouth)
            
            # Detect eye closure (possible cheating)
            if ear < EYE_AR_THRESH:
                COUNTER += 1
                if COUNTER >= EYE_AR_CONSEC_FRAMES:
                    cheating_flag = True
                    cv2.putText(frame, "LOOKING AWAY!", (10, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    if time.time() - last_cheating_time > 5:
                        frame_path = f"evidence/looking_away_{student_id}_{int(time.time())}.jpg"
                        cv2.imwrite(frame_path, frame)
                        log_cheating_incident(db, student_id, "Looking away", frame_path)
                        last_cheating_time = time.time()
            else:
                COUNTER = 0
            
            # Detect talking (mouth open)
            if mar > MOUTH_AR_THRESH:
                cheating_flag = True
                cv2.putText(frame, "TALKING DETECTED!", (10, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                if time.time() - last_cheating_time > 5:
                    frame_path = f"evidence/talking_{student_id}_{int(time.time())}.jpg"
                    cv2.imwrite(frame_path, frame)
                    log_cheating_incident(db, student_id, "Talking detected", frame_path)
                    last_cheating_time = time.time()
            
            # Detect head pose deviation
            angles = get_head_pose(predictor(gray, face), frame)
            x_angle, y_angle, z_angle = angles[:3]
            
            if abs(y_angle) > GAZE_DEVIATION_THRESH:
                cheating_flag = True
                cv2.putText(frame, f"GAZE DEVIATION: {y_angle:.1f} deg", (10, 120),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                if time.time() - last_cheating_time > 5:
                    frame_path = f"evidence/gaze_deviation_{student_id}_{int(time.time())}.jpg"
                    cv2.imwrite(frame_path, frame)
                    log_cheating_incident(db, student_id, "Gaze deviation", frame_path)
                    last_cheating_time = time.time()
            
            # Draw face landmarks for visualization
            for (x, y) in shape:
                cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)
        
        # Display frame
        out.write(frame)
        cv2.imshow("Exam Monitoring", frame)
        
        # Reset cheating flag after display
        cheating_flag = False
        
        # Exit on 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Cleanup
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    db.close()

if __name__ == "__main__":
    student_id = 1  # Should be a valid student ID from your database
    monitor_exam(student_id)