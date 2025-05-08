import React from 'react';
import { useNavigate } from 'react-router-dom';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div style={{
      fontFamily: "'Poppins', sans-serif",
      margin: 0,
      padding: 0,
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
    }}>
      <div style={{
        position: 'absolute', 
        width: '200px', 
        height: '200px', 
        borderRadius: '50%', 
        background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)', 
        zIndex: -1,
        top: '10%',
        left: '10%',
      }} className="decoration decoration-1"></div>
      <div style={{
        position: 'absolute', 
        width: '200px', 
        height: '200px', 
        borderRadius: '50%', 
        background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)', 
        zIndex: -1,
        bottom: '10%',
        right: '10%',
      }} className="decoration decoration-2"></div>
      
      <div style={{
        background: 'white',
        padding: '50px',
        borderRadius: '20px',
        boxShadow: '0 10px 20px rgba(0,0,0,0.1)',
        textAlign: 'center',
        maxWidth: '800px',
        width: '90%',
        animation: 'fadeIn 0.5s ease-out',
      }}>
        <h1 style={{
          color: '#2c3e50',
          marginBottom: '40px',
          fontSize: '2.8em',
          fontWeight: 700,
          backgroundImage: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
        }}>Welcome to the Exam Portal</h1>
        
        <p style={{
          color: '#64748b',
          fontSize: '1.2em',
          lineHeight: 1.6,
          marginBottom: '30px',
          maxWidth: '600px',
          marginLeft: 'auto',
          marginRight: 'auto',
        }} className="welcome-text">
          A modern platform for seamless exam management and assessment. 
          Choose your role to get started.
        </p>
        
        <div style={{
          display: 'flex',
          gap: '30px',
          justifyContent: 'center',
          marginTop: '40px',
        }}>
          <button 
            onClick={() => navigate('/teacher')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              padding: '15px 40px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              textDecoration: 'none',
              borderRadius: '12px',
              fontWeight: 500,
              fontSize: '1.1em',
              transition: 'all 0.3s ease',
              position: 'relative',
              overflow: 'hidden',
              border: 'none',
              cursor: 'pointer',
            }}
            onMouseOver={(e) => {
              const target = e.target as HTMLButtonElement;
              target.style.transform = 'translateY(-3px)';
              target.style.boxShadow = '0 8px 20px rgba(102, 126, 234, 0.3)';
            }}
            onMouseOut={(e) => {
              const target = e.target as HTMLButtonElement;
              target.style.transform = 'none';
              target.style.boxShadow = 'none';
            }}
          >
            <span style={{ position: 'relative', zIndex: 1 }}>Teacher Portal</span>
          </button>
          
          <button 
            onClick={() => navigate('/student')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              padding: '15px 40px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              textDecoration: 'none',
              borderRadius: '12px',
              fontWeight: 500,
              fontSize: '1.1em',
              transition: 'all 0.3s ease',
              position: 'relative',
              overflow: 'hidden',
              border: 'none',
              cursor: 'pointer',
            }}
            onMouseOver={(e) => {
              const target = e.target as HTMLButtonElement;
              target.style.transform = 'translateY(-3px)';
              target.style.boxShadow = '0 8px 20px rgba(102, 126, 234, 0.3)';
            }}
            onMouseOut={(e) => {
              const target = e.target as HTMLButtonElement;
              target.style.transform = 'none';
              target.style.boxShadow = 'none';
            }}
          >
            <span style={{ position: 'relative', zIndex: 1 }}>Student Portal</span>
          </button>
        </div>
      </div>
      
      <style>
        {`
          @keyframes fadeIn {
            from {
              opacity: 0;
              transform: translateY(20px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }
        `}
      </style>
    </div>
  );
};

export default Dashboard; 