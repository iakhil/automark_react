const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');

const app = express();
const PORT = 5000;

// Middleware
app.use(bodyParser.json());
app.use(cors());

// Mock users database
const users = [
  { id: 1, username: 'teacher', password: 'password', role: 'teacher' },
  { id: 2, username: 'student', password: 'password', role: 'student' }
];

// Mock exams database
const exams = [
  { 
    id: 1, 
    title: 'English Exam', 
    exam_code: 'YI8XIM', 
    created_at: '2025-05-07 16:39:09',
    question_paper_file: 'https://res.cloudinary.com/demo/image/upload/sample.pdf',
    rubric_file: 'https://res.cloudinary.com/demo/image/upload/sample.pdf',
    teacher_id: 1
  }
];

// LOGIN endpoint
app.post('/api/login', (req, res) => {
  const { username, password } = req.body;
  
  // Find user
  const user = users.find(u => u.username === username && u.password === password);
  
  if (user) {
    // In a production app, you'd use JWT or sessions for authentication
    res.json({ 
      success: true, 
      user: {
        id: user.id,
        username: user.username,
        role: user.role
      }
    });
  } else {
    res.status(401).json({ 
      success: false, 
      message: 'Invalid username or password' 
    });
  }
});

// REGISTER endpoint
app.post('/api/register', (req, res) => {
  const { username, password, role } = req.body;
  
  // Check if username already exists
  if (users.find(u => u.username === username)) {
    return res.status(400).json({ 
      success: false, 
      message: 'Username already exists' 
    });
  }
  
  // Create new user
  const newUser = {
    id: users.length + 1,
    username,
    password, // In production, you'd hash this password
    role
  };
  
  users.push(newUser);
  
  res.json({ 
    success: true, 
    message: 'Registration successful! Please login.' 
  });
});

// Teacher upload endpoint (mock)
app.post('/api/upload/teacher', (req, res) => {
  // In a real implementation, files would be uploaded to Cloudinary
  // and the returned URLs would be stored in the database
  const newExam = {
    id: exams.length + 1,
    title: 'New Test Exam',
    exam_code: generateExamCode(),
    created_at: new Date().toISOString().replace('T', ' ').substring(0, 19),
    question_paper_file: 'https://res.cloudinary.com/demo/image/upload/sample.pdf',
    rubric_file: 'https://res.cloudinary.com/demo/image/upload/sample.pdf',
    teacher_id: 1
  };
  
  exams.push(newExam);
  
  res.json({ 
    success: true, 
    message: 'Files uploaded successfully!',
    exam_code: newExam.exam_code
  });
});

// Get exams endpoint (mock)
app.get('/api/exams', (req, res) => {
  // In a real implementation, we would filter exams by the authenticated teacher's ID
  res.json({
    success: true,
    exams: exams
  });
});

// Student upload endpoint (mock)
app.post('/api/upload/student', (req, res) => {
  res.json({ success: true, message: 'File uploaded successfully!' });
});

// Helper function to generate a random 6-character alphanumeric exam code
function generateExamCode() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let code = '';
  for (let i = 0; i < 6; i++) {
    code += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return code;
}

app.listen(PORT, () => {
  console.log(`Mock API server running on http://localhost:${PORT}`);
}); 