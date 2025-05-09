import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { examAPI } from '../api';

interface Submission {
  id: number;
  exam_title: string;
  exam_code?: string;
  submitted_at: string;
  grade: string;
  is_published: boolean;
  answer_sheet_urls?: string[];
}

const StudentPortal: React.FC = () => {
  console.log("Rendering StudentPortal component");
  const navigate = useNavigate();
  const [examCode, setExamCode] = useState('');
  const [answerSheet, setAnswerSheet] = useState<File | null>(null);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [message, setMessage] = useState<{ text: string; type: string } | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  // Fetch submissions from API
  const fetchSubmissions = async () => {
    try {
      setLoading(true);
      console.log("Fetching submissions...");
      
      const data = await examAPI.getSubmissions();
      console.log("Submissions response:", data);
      
      if (data.success && data.submissions) {
        console.log("Setting submissions:", data.submissions);
        setSubmissions(data.submissions);
      } else {
        console.error('Failed to load submissions:', data.message);
        // If authentication error, redirect to login
        if (data.message === 'Authentication required') {
          setMessage({ 
            text: 'Your session has expired. Please log in again.', 
            type: 'error' 
          });
          setTimeout(() => {
            localStorage.removeItem('user');
            localStorage.removeItem('sessionId');
            navigate('/login');
          }, 2000);
        } else {
          setMessage({ 
            text: data.message || 'Failed to load submissions. Please try again later.', 
            type: 'error' 
          });
        }
      }
    } catch (error: any) {
      console.error('Error fetching submissions:', error);
      
      // If it's a 401 error, handle authentication failure
      if (error.message && error.message.includes('401')) {
        console.log("Authentication error detected");
        setMessage({ 
          text: 'Your session has expired. Please log in again.', 
          type: 'error' 
        });
        setTimeout(() => {
          localStorage.removeItem('user');
          localStorage.removeItem('sessionId');
          navigate('/login');
        }, 2000);
      } else {
        setMessage({ 
          text: 'Could not load your submissions. Please try again later.', 
          type: 'error' 
        });
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Check if user is logged in
    const user = localStorage.getItem('user');
    if (!user) {
      navigate('/login');
      return;
    }

    // Parse user data
    const userData = JSON.parse(user);
    if (userData.role !== 'student') {
      navigate('/login');
      return;
    }

    // If we have a stored session ID, ensure it's in the cookie
    const sessionId = localStorage.getItem('sessionId');
    if (sessionId && !document.cookie.includes('session=')) {
      console.log("Restoring session from localStorage");
      document.cookie = `session=${sessionId}; path=/`;
    }

    // Fetch submissions when component mounts
    fetchSubmissions();
  }, [navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!examCode || !answerSheet) {
      setMessage({ text: 'Please enter exam code and select a file', type: 'error' });
      return;
    }

    try {
      setLoading(true);
      setMessage({ text: 'Uploading your answer sheet...', type: 'info' });
      
      const data = await examAPI.submitAnswer(examCode, answerSheet);
      
      if (data.success) {
        setLoading(false);
        setMessage({ 
          text: data.message || 'Answer sheet submitted successfully! Awaiting teacher to publish grade.', 
          type: 'success' 
        });
        
        setExamCode('');
        setAnswerSheet(null);
        
        // Refresh submissions list
        fetchSubmissions();
      } else {
        setLoading(false);
        setMessage({ 
          text: data.message || 'Error submitting answer sheet', 
          type: 'error' 
        });
      }
    } catch (error) {
      console.error('Error submitting answer:', error);
      setLoading(false);
      setMessage({ 
        text: 'An error occurred. Please try again.', 
        type: 'error' 
      });
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('user');
    localStorage.removeItem('sessionId');
    navigate('/login');
  };

  return (
    <div style={{
      fontFamily: "'Poppins', sans-serif",
      margin: 0,
      padding: 0,
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '40px 20px',
      }} className="container">
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '40px',
        }} className="header">
          <h1 style={{
            fontSize: '2.5em',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            margin: 0,
          }}>Student Portal</h1>
          <button 
            onClick={handleLogout}
            style={{
              padding: '8px 16px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: 500,
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              textDecoration: 'none',
              width: '80px',
            }}
            className="button"
            onMouseOver={(e) => {
              const target = e.target as HTMLButtonElement;
              target.style.transform = 'translateY(-2px)';
              target.style.boxShadow = '0 5px 15px rgba(102, 126, 234, 0.3)';
            }}
            onMouseOut={(e) => {
              const target = e.target as HTMLButtonElement;
              target.style.transform = 'none';
              target.style.boxShadow = 'none';
            }}
          >
            Logout
          </button>
        </div>

        {message && (
          <div 
            style={{
              padding: '15px',
              marginBottom: '20px',
              borderRadius: '8px',
              textAlign: 'center',
              fontWeight: 500,
              backgroundColor: message.type === 'success' ? '#dcfce7' : '#fef2f2',
              color: message.type === 'success' ? '#166534' : '#991b1b',
              border: `1px solid ${message.type === 'success' ? '#bbf7d0' : '#fecaca'}`,
            }}
            className={`message ${message.type}`}
          >
            {message.text}
          </div>
        )}

        <div style={{
          background: 'white',
          padding: '30px',
          borderRadius: '20px',
          boxShadow: '0 10px 20px rgba(0,0,0,0.1)',
          marginBottom: '40px',
          animation: 'fadeIn 0.5s ease-out',
        }} className="form-container">
          <h2 style={{
            color: '#2c3e50',
            margin: 0,
            marginBottom: '20px',
          }}>Submit Answer Sheet</h2>
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: '20px' }} className="form-group">
              <label 
                style={{
                  display: 'block',
                  marginBottom: '8px',
                  color: '#2c3e50',
                  fontWeight: 500,
                }}
                htmlFor="examCode"
              >
                Exam Code
              </label>
              <input 
                type="text" 
                id="examCode" 
                value={examCode}
                onChange={(e) => setExamCode(e.target.value)}
                required
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '2px solid #e1e8ed',
                  borderRadius: '8px',
                  fontSize: '16px',
                  transition: 'border-color 0.3s ease',
                  boxSizing: 'border-box',
                  opacity: loading ? 0.7 : 1,
                  cursor: loading ? 'not-allowed' : 'text',
                }}
              />
            </div>

            <div style={{ marginBottom: '20px' }} className="form-group">
              <label 
                style={{
                  display: 'block',
                  marginBottom: '8px',
                  color: '#2c3e50',
                  fontWeight: 500,
                }}
              >
                Answer Sheet (PDF)
              </label>
              <div style={{
                position: 'relative',
                marginBottom: '15px',
                opacity: loading ? 0.7 : 1,
                pointerEvents: loading ? 'none' : 'auto',
              }} className="file-input-container">
                <label 
                  style={{
                    display: 'block',
                    padding: '12px',
                    background: '#f8fafc',
                    border: '2px dashed #e1e8ed',
                    borderRadius: '8px',
                    textAlign: 'center',
                    cursor: 'pointer',
                    transition: 'all 0.3s ease',
                  }}
                  className="file-input-label"
                  htmlFor="answer_sheet"
                >
                  {answerSheet ? answerSheet.name : "Choose Answer Sheet File"}
                </label>
                <input 
                  type="file" 
                  id="answer_sheet" 
                  onChange={(e) => e.target.files && setAnswerSheet(e.target.files[0])}
                  accept=".pdf"
                  style={{
                    opacity: 0,
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    cursor: 'pointer',
                  }}
                />
              </div>
            </div>

            <button 
              type="submit" 
              style={{
                padding: '12px 24px',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '16px',
                fontWeight: 500,
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'all 0.3s ease',
                textDecoration: 'none',
                opacity: loading ? 0.7 : 1,
              }}
              className="button"
              disabled={loading}
              onMouseOver={(e) => {
                if (!loading) {
                  const target = e.target as HTMLButtonElement;
                  target.style.transform = 'translateY(-2px)';
                  target.style.boxShadow = '0 5px 15px rgba(102, 126, 234, 0.3)';
                }
              }}
              onMouseOut={(e) => {
                const target = e.target as HTMLButtonElement;
                target.style.transform = 'none';
                target.style.boxShadow = 'none';
              }}
            >
              {loading ? 'Submitting...' : 'Submit Answer Sheet'}
            </button>
          </form>
        </div>

        <h2 style={{
          color: '#2c3e50',
          margin: 0,
          marginBottom: '20px',
        }}>Your Submissions</h2>
        
        {loading ? (
          <div style={{
            background: 'white',
            padding: '30px',
            borderRadius: '15px',
            textAlign: 'center',
            boxShadow: '0 5px 15px rgba(0,0,0,0.1)',
          }}>
            <p>Loading submissions...</p>
          </div>
        ) : submissions.length === 0 ? (
          <div style={{
            background: 'white',
            padding: '30px',
            borderRadius: '15px',
            textAlign: 'center',
            boxShadow: '0 5px 15px rgba(0,0,0,0.1)',
          }}>
            <p>You haven't submitted any answer sheets yet.</p>
            <p>Upload an answer sheet to get started!</p>
          </div>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
            gap: '20px',
            marginTop: '30px',
          }} className="submission-list">
            {submissions.map(submission => (
              <div 
                key={submission.id}
                style={{
                  background: 'white',
                  padding: '25px',
                  borderRadius: '15px',
                  boxShadow: '0 5px 15px rgba(0,0,0,0.1)',
                  transition: 'transform 0.3s ease',
                }}
                className="submission-item"
                onMouseOver={(e) => {
                  const target = e.target as HTMLDivElement;
                  target.style.transform = 'translateY(-5px)';
                }}
                onMouseOut={(e) => {
                  const target = e.target as HTMLDivElement;
                  target.style.transform = 'none';
                }}
              >
                <h3 style={{
                  color: '#2c3e50',
                  marginTop: 0,
                  marginBottom: '15px',
                  fontSize: '1.2em',
                }}>{submission.exam_title}</h3>
                <div style={{
                  color: '#64748b',
                  fontSize: '0.9em',
                  marginBottom: '10px',
                }} className="submission-date">
                  Submitted: {submission.submitted_at}
                </div>
                
                {submission.is_published ? (
                  <>
                    <div style={{
                      color: '#2c3e50',
                      fontWeight: 500,
                      marginBottom: '8px',
                    }} className="grade-label">
                      Grade:
                    </div>
                    <div 
                      style={{
                        background: '#f8fafc',
                        padding: '15px',
                        borderRadius: '8px',
                        marginTop: '15px',
                        color: '#475569',
                        fontSize: '0.95em',
                        lineHeight: 1.6,
                        whiteSpace: 'pre-wrap',
                      }}
                      className="grade"
                      dangerouslySetInnerHTML={{ __html: submission.grade }}
                    />
                  </>
                ) : (
                  <div style={{
                    background: '#f1f5f9',
                    padding: '15px',
                    borderRadius: '8px',
                    marginTop: '15px',
                    color: '#64748b',
                    textAlign: 'center',
                  }}>
                    Awaiting teacher to publish grade
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default StudentPortal; 