import cv2
import numpy as np
import pickle
from keras_facenet import FaceNet
from db import mark_attendance
import os
import sys
print(sys.executable)


# Initialize FaceNet model
embedder = FaceNet()

# Load known face data
with open(os.path.join(os.path.dirname(__file__), '../data/known_faces.pkl'), "rb") as f:
    known_names, known_embeddings = pickle.load(f)

# Cosine similarity for face comparison
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# Start webcam
cap = cv2.VideoCapture(0)
print("[INFO] Webcam started. Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    faces = embedder.extract(img_rgb, threshold=0.95)

    for face in faces:
        x, y, w, h = face["box"]
        face_img = img_rgb[y:y+h, x:x+w]

        try:
            face_embedding = embedder.embeddings([face_img])[0]
        except:
            continue

        name = "Unknown"
        max_sim = -1

        for i, known_embed in enumerate(known_embeddings):
            sim = cosine_similarity(face_embedding, known_embed)
            if sim > 0.7 and sim > max_sim:
                max_sim = sim
                name = known_names[i]

        # Draw result
        label = f"{name} [{max_sim:.2f}]" if name != "Unknown" else "Unknown"
        color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        # Mark attendance if recognized
        if name != "Unknown":
            mark_attendance(name)

    cv2.imshow("Live Face Attendance", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()