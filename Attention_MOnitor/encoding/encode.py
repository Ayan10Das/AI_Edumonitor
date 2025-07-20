
import face_recognition
import os
import pickle

KNOWN_DIR = "known_faces"
encodings = {}
for filename in os.listdir(KNOWN_DIR):
    path = os.path.join(KNOWN_DIR, filename)
    img = face_recognition.load_image_file(path)
    encoding = face_recognition.face_encodings(img)
    if encoding:
        name = os.path.splitext(filename)[0]
        encodings[name] = encoding[0]

with open("encodings.pkl", "wb") as f:
    pickle.dump(encodings, f)
print("✅ Encodings saved!")

