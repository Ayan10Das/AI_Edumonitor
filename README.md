# AI.EduMonitor 🎓📊

**AI-Powered Smart Student Monitoring System**

EduMonitor.AI is a Final Year Project developed to monitor student engagement and integrity in real time using artificial intelligence and computer vision techniques. It integrates multiple AI models to detect **student emotions**, track **attention**, and identify **cheating behaviors during online exams**—all from a single dashboard.

---

## 📌 Project Overview

EduMonitor.AI aims to revolutionize digital classrooms and online examination systems by providing smart, real-time monitoring features. It is built using Python (with libraries like OpenCV, DeepFace, TensorFlow), MySQL for data storage, and a Node.js + HTML/CSS frontend.

---

## 🚀 Features

### 1. **Live Face Attendance System**  
- At first face encoding has to be done and known_faces.pkl file will be created.
- Detects and recognizes faces using deep learning models (FaceNet/DeepFace).
- Automatically marks attendance and logs data into a MySQL database.
- Real-time facial verification ensures authentic presence.

### 2. **Student Emotion Detection**  
- Detects emotions such as *happy, sad, angry, neutral, surprised* using DeepFace.
- Helps analyze classroom mood and emotional engagement.
- Stores emotion logs per session(for each class,total students) for review.

### 3. **Attention Monitoring System** 
- At first face encoding has to be done and known_faces.pkl file will be created.
- Uses head-pose estimation and gaze tracking to determine student attention., using shape_predictor.
- If the student looks away from the screen for more than 5–10 seconds, it logs "Inattentive".
- Calculates an overall **attention score** for each session.

### 4. **Exam Cheating Detection**  
- Monitors multiple faces, background movement, and eye direction during online exams.
- Detects suspicious behavior (looking away repeatedly, presence of another face, etc.).
- Records cheating incidents with timestamps into the database.Stores the captured suspicious behaviour pictures in evidance file.

### 5. **Admin Dashboard**  
- Beautifully designed dashboard built with HTML, CSS, JavaScript, and Node.js.
- Displays:
  - Attendance logs
  - Live emotion graphs
  - Attention scores
  - Cheating incident reports
- Enables faculty/admins to monitor multiple students easily from one interface.

---

## 🛠️ Technologies Used

| Category         | Tools/Technologies                    |
|------------------|----------------------------------------|
| **Frontend**     | HTML, CSS, JavaScript                 |
| **Backend**      | Node.js, Express.js                   |
| **AI & CV**      | Python, OpenCV, DeepFace, TensorFlow, Mediapipe |
| **Database**     | MySQL                                 |
| **Others**       | Git, GitHub, VS Code                  |

---

