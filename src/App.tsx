import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import TeacherUpload from './pages/TeacherUpload';
import StudentUpload from './pages/StudentUpload';
import TeacherPortal from './pages/TeacherPortal';
import StudentPortal from './pages/StudentPortal';
import TeacherPage from './pages/TeacherPage';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import './styles.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/home" element={<Home />} />
        <Route path="/teacher" element={<TeacherPage />} />
        <Route path="/student" element={<StudentPortal />} />
        <Route path="/teacher-upload" element={<TeacherUpload />} />
        <Route path="/student-upload" element={<StudentUpload />} />
      </Routes>
    </Router>
  );
}

export default App;
