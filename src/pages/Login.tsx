import React, { useState, FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../api';

const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      console.log("Attempting login with:", username);
      const data = await authAPI.login(username, password);
      
      if (data.success) {
        console.log("Login successful, user data:", data.user);
        // Store user info in localStorage
        localStorage.setItem('user', JSON.stringify(data.user));
        
        // Find all available cookies and log them for debugging
        console.log("Cookies after login:", document.cookie);
        
        // Also store session ID to help with authentication
        if (document.cookie.includes('session=')) {
          const sessionId = document.cookie
            .split('; ')
            .find(row => row.startsWith('session='))
            ?.split('=')[1];
          
          if (sessionId) {
            localStorage.setItem('sessionId', sessionId);
            console.log("Session ID stored in localStorage:", sessionId);
          } else {
            console.warn("Session cookie found but couldn't extract ID");
          }
        } else {
          console.warn("No session cookie found after login");
        }
        
        // Wait a moment for cookies to be properly set before redirecting
        setTimeout(() => {
          // Navigate based on user role
          if (data.user.role === 'teacher') {
            navigate('/teacher');
          } else {
            navigate('/student');
          }
        }, 100);
      } else {
        setMessage(data.message || 'Login failed');
      }
    } catch (error) {
      console.error("Login error:", error);
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
          textAlign: 'center',
          marginBottom: '60px',
        }} className="hero">
          <h1 style={{
            fontSize: '2.5em',
            color: '#ffffff',
            marginBottom: '20px',
          }}>AutoMark</h1>
          <p style={{
            fontSize: '1.2em',
            color: '#94a3b8',
            maxWidth: '800px',
            margin: '0 auto',
            lineHeight: 1.6,
          }}>Streamline your exam grading process with our AI-powered solution. Upload answer sheets and get instant, consistent grading based on your rubric.</p>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '30px',
          marginBottom: '60px',
        }} className="features">
          <div style={{
            background: '#1e293b',
            padding: '30px',
            borderRadius: '12px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.3)',
            border: '1px solid #334155',
          }} className="feature-card">
            <h3 style={{ color: '#60a5fa', marginTop: 0 }}>Automated Grading</h3>
            <p style={{ color: '#94a3b8' }}>Our AI analyzes student responses against your rubric for quick and accurate grading.</p>
          </div>
          <div style={{
            background: '#1e293b',
            padding: '30px',
            borderRadius: '12px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.3)',
            border: '1px solid #334155',
          }} className="feature-card">
            <h3 style={{ color: '#60a5fa', marginTop: 0 }}>Consistent Evaluation</h3>
            <p style={{ color: '#94a3b8' }}>Ensure fair grading with standardized criteria and detailed feedback.</p>
          </div>
          <div style={{
            background: '#1e293b',
            padding: '30px',
            borderRadius: '12px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.3)',
            border: '1px solid #334155',
          }} className="feature-card">
            <h3 style={{ color: '#60a5fa', marginTop: 0 }}>Time-Saving</h3>
            <p style={{ color: '#94a3b8' }}>Reduce grading time significantly while maintaining quality assessment.</p>
          </div>
        </div>

        <div style={{
          background: '#1e293b',
          padding: '30px',
          borderRadius: '12px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.3)',
          border: '1px solid #334155',
          marginBottom: '40px',
        }} className="how-to-use">
          <details>
            <summary style={{
              fontSize: '1.2em',
              fontWeight: 600,
              color: '#60a5fa',
              cursor: 'pointer',
              padding: '10px 0',
            }}>How to Use?</summary>
            <div>
              <h4>For Teachers:</h4>
              <ul style={{ marginTop: '20px', paddingLeft: '20px' }}>
                <li style={{ marginBottom: '10px', lineHeight: 1.5 }}>Upload your question paper and grading rubric</li>
                <li style={{ marginBottom: '10px', lineHeight: 1.5 }}>Share the generated exam code with students</li>
                <li style={{ marginBottom: '10px', lineHeight: 1.5 }}>Review and publish AI-generated grades</li>
              </ul>
              <h4>For Students:</h4>
              <ul style={{ marginTop: '20px', paddingLeft: '20px' }}>
                <li style={{ marginBottom: '10px', lineHeight: 1.5 }}>Enter the exam code provided by your teacher</li>
                <li style={{ marginBottom: '10px', lineHeight: 1.5 }}>Upload your answer sheet in PDF format</li>
                <li style={{ marginBottom: '10px', lineHeight: 1.5 }}>Receive detailed feedback once approved</li>
              </ul>
            </div>
          </details>
        </div>

        <div style={{
          maxWidth: '400px',
          margin: '0 auto',
          background: '#1e293b',
          padding: '30px',
          borderRadius: '12px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.3)',
          border: '1px solid #334155',
        }} className="login-section">
          <h2>Login</h2>
          
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
              Login
            </button>
          </form>
          
          <div style={{
            textAlign: 'center',
            marginTop: '20px',
          }} className="register-link">
            <p style={{ color: '#94a3b8' }}>
              Don't have an account? <Link 
                to="/register" 
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
                Register here
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login; 