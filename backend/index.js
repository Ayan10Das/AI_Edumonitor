
# Replace 'your_user_here' and 'your_password_here' with your actual MySQL credentials before running locally.

const express = require("express");
const cors = require("cors");
const mysql = require("mysql");

const app = express();
const port = 3000;

// CORS configuration
app.use(cors({
  origin: "*",
  methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
  allowedHeaders: ["Content-Type", "Authorization"]
}));
app.use(express.json());

// ===============================
// Connection 1: Attendance System
// ===============================
const attendence_Db= mysql.connector.connect(
    host="localhost",
    user="your_user_here",
    password="your_password_here",
    database="edumonitor"
)

attendanceDb.connect((err) => {
  if (err) {
    console.error("❌ Attendance DB connection failed:", err);
    return;
  }
  console.log("✅ Connected to attendance_system database");
});

// Attendance route
app.get("/attendance", (req, res) => {
  const selectedDate = req.query.date;
  const query = `
    SELECT name, date, time
    FROM attendance_log
    WHERE date = ?
    ORDER BY time ASC
  `;
  attendanceDb.query(query, [selectedDate], (err, results) => {
    if (err) {
      console.error("❌ Error fetching attendance:", err);
      return res.status(500).json({ error: "Database error" });
    }
    res.json(results);
  });
});
// ===============================
// Connection Pool: Cheating System
// ===============================
app.get("/cheating-incidents", (req, res) => {
const examDb = mysql.connector.connect(
    host="localhost",
    user="your_user_here",
    password="your_password_here",
    database="edumonitor"
)


  const query = `
    SELECT ci.*, s.first_name, s.last_name 
    FROM CheatingIncidents ci
    JOIN Students s ON ci.student_id = s.student_id
    ORDER BY incident_time DESC
    LIMIT 10
  `;
  
  examDb.query(query, (err, results) => {
    if (err) {
      console.error("❌ Error fetching cheating incidents:", err);
      examDb.end();
      return res.status(500).json({ error: "Database error" });
    }
    examDb.end();
    res.json(results);
  });
});

// ===============================
// Connection Pool: Emotion System
// ===============================
const emotionDb = mysql.connector.connect(
    host="localhost",
    user="your_user_here",
    password="your_password_here",
    database="edumonitor"
)


// Emotion summary route
app.get("/emotion-summary", (req, res) => {
  const query = `
    SELECT * 
    FROM emotion_summary 
    ORDER BY session_date DESC, id DESC
    LIMIT 1
  `;
  emotionDb.query(query, (err, results) => {
    if (err) {
      console.error("❌ Error fetching emotion summary:", err);
      return res.status(500).json({ error: "Database error" });
    }
    if (results.length === 0) {
      return res.status(404).json({ message: "No emotion data found" });
    }
    const data = results[0];

    const emotionSummary = {
      happy_avg: data.happy_avg || 0,
      sad_avg: data.sad_avg || 0,
      angry_avg: data.angry_avg || 0,
      neutral_avg: data.neutral_avg || 0,
      scared_avg: data.scared_avg || 0,
      disgust_avg: data.disgust_avg || 0,
      surprise_avg: data.surprise_avg || 0,
      session_date: data.session_date || "N/A",
    };

    res.json(emotionSummary);
  });
});

// ===============================
// Connection Pool: Login System
// ===============================
const loginDb = mysql.connector.connect(
    host="localhost",
    user="your_user_here",
    password="your_password_here",
    database="edumonitor"
)


// Login route
app.post("/login", (req, res) => {
  const { username, password } = req.body;
  console.log("Login route hit", { username });

  const sql = "SELECT * FROM users WHERE username = ? AND password = ?";
  loginDb.query(sql, [username, password], (err, results) => {
    if (err) {
      console.error("❌ Error during login:", err);
      return res.status(500).json({ status: "error", message: "Database error" });
    }

    if (results.length > 0) {
      console.log(`✅ Login success for user: ${username}`);
      res.json({ status: "success", message: "Login successful" });
    } else {
      console.log(`❌ Invalid login attempt for user: ${username}`);
      res.json({ status: "fail", message: "Invalid username or password" });
    }
  });
});

// ===============================
// Attention Score System
// ===============================
app.get("/attention-score/:studentId", (req, res) => {
  const studentId = req.params.studentId;
  
  // Validate student ID
  if (!studentId || studentId.toLowerCase() === "undefined") {
    return res.status(400).json({ 
      error: "Invalid student ID",
      message: "Please provide a valid student name",
      example: "Try names like 'ayan'"
    });
  }

  console.log(`📊 Fetching attention score for student: ${studentId}`);

const attentionDb = mysql.connector.connect(
    host="localhost",
    user="your_user_here",
    password="your_password_here",
    database="edumonitor"
)


  attentionDb.connect(err => {
    if (err) {
      console.error("❌ Attention DB connection failed:", err);
      return res.status(500).json({ error: "Database connection failed" });
    }

    // Get records from last 24 hours
    const query = `
      SELECT status 
      FROM attention_logs
      WHERE student_id = ? 
        AND timestamp > NOW() - INTERVAL 24 HOUR
      ORDER BY timestamp DESC
    `;

    attentionDb.query(query, [studentId], (err, results) => {
      attentionDb.end(); // Always close connection

      if (err) {
        console.error("❌ Error fetching attention logs:", err);
        return res.status(500).json({ error: "Database query failed" });
      }

      if (results.length === 0) {
        return res.json({ 
          student_id: studentId, 
          score: 0,
          message: "No recent attention data found for this student",
          last_checked: new Date().toISOString()
        });
      }

      // Handle both "Attentive/Unattentive" and "attentive/distracted" formats
      const attentiveCount = results.filter(r => 
        r.status && (
          r.status.toLowerCase() === "attentive" || 
          r.status.toLowerCase() === "attentive" // Handle possible typo
        )
      ).length;

      const score = Math.round((attentiveCount / results.length) * 100);
      console.log(`🎯 Calculated attention score: ${score}%`);

      res.json({
        student_id: studentId,
        score: score,
        total_samples: results.length,
        attentive_samples: attentiveCount,
        last_checked: new Date().toISOString()
      });
    });
  });
});

// ===============================
// Start Server
// ===============================
app.listen(port, () => {
  console.log(`🚀 Server running on http://localhost:${port}`);
});
