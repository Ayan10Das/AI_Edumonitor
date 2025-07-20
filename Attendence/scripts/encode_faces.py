import os
import cv2
import numpy as np
import pickle
from keras_facenet import FaceNet

# Initialize the FaceNet embedder
embedder = FaceNet()

# Directory containing known face images
known_dir = os.path.join(os.path.dirname(__file__), '../known_faces')

# Lists to store names and corresponding embeddings
known_embeddings = []
known_names = []

# Loop through each image in the known_faces directory
for filename in os.listdir(known_dir):
    if filename.endswith(".jpg"):
        name = os.path.splitext(filename)[0]
        path = os.path.join(known_dir, filename)

        img = cv2.imread(path)
        if img is None:
            print(f"[!] Failed to load image: {filename}")
            continue

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Extract faces using FaceNet
        faces = embedder.extract(img_rgb, threshold=0.95)
        if faces:
            box = faces[0]["box"]
            x, y, w, h = box
            face_img = img_rgb[y:y+h, x:x+w]

            # Get the embedding
            embedding = embedder.embeddings([face_img])[0]

            known_embeddings.append(embedding)
            known_names.append(name)
            print(f"[+] Encoded: {name}")
        else:
            print(f"[!] No face detected in {filename}")

# Save the embeddings and names to a pickle file
output_path = os.path.join(os.path.dirname(__file__), '../data/known_faces.pkl')
with open(output_path, "wb") as f:
    pickle.dump((known_names, known_embeddings), f)

print("[OK] Faces encoded and saved successfully.")