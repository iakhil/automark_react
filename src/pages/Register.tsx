import React, { useState, FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../api';

const Register: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('teacher');
  const [message, setMessage] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      const data = await authAPI.register(username, password, role);
      
      if (data.success) {
        navigate('/login');
      } else {
        setMessage(data.message || 'Registration failed');
      }
    } catch (error) {
      setMessage('An error occurred. Please try again.');
    }
  };

  return (
    <div style={{
      fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
      margin: 0,
      padding: 0,
      backgroundColor: '#0f172a',
      color: '#e2e8f0',
      minHeight: '100vh',
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '40px 20px',
      }} className="container">
        <div style={{
          maxWidth: '400px',
          margin: '0 auto',
          background: '#1e293b',
          padding: '30px',
          borderRadius: '12px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.3)',
          border: '1px solid #334155',
        }} className="register-section">
          <h2>Register</h2>
          
          {message && (
            <div style={{
              padding: '15px',
              marginBottom: '20px',
              borderRadius: '6px',
              textAlign: 'center',
              backgroundColor: '#7f1d1d',
              color: '#fecaca',
              border: '1px solid #ef4444',
            }} className="message error">
              {message}
            </div>
          )}
          
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: '20px' }} className="form-group">
              <label style={{
                display: 'block',
                marginBottom: '8px',
                fontWeight: 500,
                color: '#e2e8f0',
              }} htmlFor="username">Username</label>
              <input 
                type="text" 
                id="username" 
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '1px solid #334155',
                  background: '#0f172a',
                  color: '#e2e8f0',
                  borderRadius: '6px',
                  fontSize: '1em',
                  boxSizing: 'border-box',
                }}
              />
            </div>
            
            <div style={{ marginBottom: '20px' }} className="form-group">
              <label style={{
                display: 'block',
                marginBottom: '8px',
                fontWeight: 500,
                color: '#e2e8f0',
              }} htmlFor="password">Password</label>
              <input 
                type="password" 
                id="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '1px solid #334155',
                  background: '#0f172a',
                  color: '#e2e8f0',
                  borderRadius: '6px',
                  fontSize: '1em',
                  boxSizing: 'border-box',
                }}
              />
            </div>
            
            <div style={{ marginBottom: '20px' }} className="form-group">
              <label style={{
                display: 'block',
                marginBottom: '8px',
                fontWeight: 500,
                color: '#e2e8f0',
              }} htmlFor="role">Role</label>
              <select 
                id="role" 
                value={role}
                onChange={(e) => setRole(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '1px solid #334155',
                  background: '#0f172a',
                  color: '#e2e8f0',
                  borderRadius: '6px',
                  fontSize: '1em',
                  boxSizing: 'border-box',
                }}
              >
                <option value="teacher">Teacher</option>
                <option value="student">Student</option>
              </select>
            </div>
            
            <button 
              type="submit" 
              className="button"
              style={{
                background: '#3b82f6',
                color: 'white',
                padding: '12px 24px',
                border: 'none',
                borderRadius: '6px',
                fontSize: '1em',
                cursor: 'pointer',
                width: '100%',
                transition: 'background-color 0.2s ease',
              }}
              onMouseOver={(e) => {
                const target = e.target as HTMLButtonElement;
                target.style.background = '#2563eb';
              }}
              onMouseOut={(e) => {
                const target = e.target as HTMLButtonElement;
                target.style.background = '#3b82f6';
              }}
            >
              Register
            </button>
          </form>
          
          <div style={{
            textAlign: 'center',
            marginTop: '20px',
          }} className="login-link">
            <p style={{ color: '#94a3b8' }}>
              Already have an account? <Link 
                to="/login" 
                style={{
                  color: '#60a5fa',
                  textDecoration: 'none',
                  fontWeight: 500,
                }}
                onMouseOver={(e) => {
                  const target = e.target as HTMLAnchorElement;
                  target.style.color = '#3b82f6';
                }}
                onMouseOut={(e) => {
                  const target = e.target as HTMLAnchorElement;
                  target.style.color = '#60a5fa';
                }}
              >
                Login here
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register; 