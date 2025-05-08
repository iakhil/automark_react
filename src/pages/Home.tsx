import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Box } from '@mui/material';

const Home: React.FC = () => {
  const navigate = useNavigate();

  return (
    <>
      <header style={{
        backgroundColor: '#4CAF50',
        color: 'white',
        padding: '20px',
        fontSize: '1.5rem',
        textAlign: 'center'
      }}>
        AI Grader
      </header>
      <main style={{
        padding: '20px',
        textAlign: 'center'
      }}>
        <p>Welcome to the AI Grader application. Please choose your role:</p>
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
          <button
            onClick={() => navigate('/teacher')}
            style={{
              display: 'inline-block',
              margin: '10px',
              padding: '15px 30px',
              fontSize: '1rem',
              color: 'white',
              backgroundColor: '#4CAF50',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer'
            }}
            onMouseOver={(e) => {
              const target = e.target as HTMLButtonElement;
              target.style.backgroundColor = '#45a049';
            }}
            onMouseOut={(e) => {
              const target = e.target as HTMLButtonElement;
              target.style.backgroundColor = '#4CAF50';
            }}
          >
            Teacher
          </button>
          <button
            onClick={() => navigate('/student')}
            style={{
              display: 'inline-block',
              margin: '10px',
              padding: '15px 30px',
              fontSize: '1rem',
              color: 'white',
              backgroundColor: '#4CAF50',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer'
            }}
            onMouseOver={(e) => {
              const target = e.target as HTMLButtonElement;
              target.style.backgroundColor = '#45a049';
            }}
            onMouseOut={(e) => {
              const target = e.target as HTMLButtonElement;
              target.style.backgroundColor = '#4CAF50';
            }}
          >
            Student
          </button>
        </Box>
      </main>
    </>
  );
};

export default Home; 