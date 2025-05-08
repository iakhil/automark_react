import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { examAPI } from '../api';

interface Exam {
  id: number;
  title: string;
  exam_code: string;
  created_at: string;
}

interface Submission {
  id: number;
  student_name: string;
  exam_title: string;
  submitted_at: string;
  is_published: boolean;
  answer_sheet_url?: string;
}

const TeacherPortal: React.FC = () => {
  console.log("--- TeacherPortal Component Rendering ---");
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('create');
  const [exams, setExams] = useState<Exam[]>([]);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [title, setTitle] = useState('');
  const [questionPaper, setQuestionPaper] = useState<File | null>(null);
  const [rubricFile, setRubricFile] = useState<File | null>(null);
  const [message, setMessage] = useState<{ text: string; type: string } | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [debugInfo, setDebugInfo] = useState<string>('');

  // Fetch exams from API
  const fetchExams = async () => {
    try {
      setLoading(true);
      const data = await examAPI.getExams();
      
      if (data.success && data.exams) {
        setExams(data.exams);
      } else {
        setMessage({ 
          text: data.message || 'Failed to load exams', 
          type: 'error' 
        });
      }
    } catch (error) {
      console.error('Error fetching exams:', error);
      setMessage({ 
        text: 'Could not load your exams. Please try again later.', 
        type: 'error' 
      });
    } finally {
      setLoading(false);
    }
  };

  // Fetch submissions from API
  const fetchSubmissions = async () => {
    try {
      setLoading(true);
      setDebugInfo('');
      console.log("TeacherPortal: Starting to fetch teacher submissions");
      
      const data = await examAPI.getTeacherSubmissions();
      console.log("TeacherPortal: Received teacher submissions response:", data);
      
      if (data.success && data.submissions) {
        console.log("TeacherPortal: Setting submissions state with:", data.submissions);
        setSubmissions(data.submissions);
        setDebugInfo(`Successfully retrieved ${data.submissions.length} submissions.`);
      } else {
        console.error("TeacherPortal: Failed to load submissions:", data.message);
        setMessage({ 
          text: data.message || 'Failed to load submissions', 
          type: 'error' 
        });
        setDebugInfo(`Error: ${data.message || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('TeacherPortal: Error fetching submissions:', error);
      setMessage({ 
        text: 'Could not load submissions. Please try again later.', 
        type: 'error' 
      });
      setDebugInfo(`Exception: ${error instanceof Error ? error.message : String(error)}`);
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
    if (userData.role !== 'teacher') {
      navigate('/login');
      return;
    }

    // If we have a stored session ID, ensure it's in the cookie
    const sessionId = localStorage.getItem('sessionId');
    if (sessionId && !document.cookie.includes('session=')) {
      console.log("Restoring session from localStorage");
      document.cookie = `session=${sessionId}; path=/`;
      
      // Give the cookie a moment to set before making API calls
      setTimeout(() => {
        fetchExams();
        fetchSubmissions();
      }, 500);
    } else {
      // Cookie already exists, fetch data immediately
      fetchExams();
      fetchSubmissions();
    }

    // Fetch data when component mounts
    console.log("TeacherPortal: useEffect - Initializing, attempting to fetch exams and submissions.");
    fetchExams();
    fetchSubmissions();
  }, [navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!title || !questionPaper || !rubricFile) {
      setMessage({ text: 'All fields are required!', type: 'error' });
      return;
    }

    try {
      setLoading(true);
      const data = await examAPI.createExam(title, questionPaper, rubricFile);
      
      if (data.success) {
        setMessage({ text: 'Exam created successfully!', type: 'success' });
        setTitle('');
        setQuestionPaper(null);
        setRubricFile(null);
        
        // Refresh the exams list
        fetchExams();
      } else {
        setMessage({ text: data.message || 'Error creating exam', type: 'error' });
      }
    } catch (error) {
      console.error('Error creating exam:', error);
      setMessage({ text: 'An error occurred. Please try again.', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('user');
    localStorage.removeItem('sessionId');
    navigate('/login');
  };

  const publishGrade = async (submissionId: number) => {
    try {
      setLoading(true);
      console.log("TeacherPortal: Publishing grade for submission:", submissionId);
      
      const data = await examAPI.publishGrade(submissionId);
      console.log("TeacherPortal: Publish grade response:", data);
      
      if (data.success) {
        console.log("TeacherPortal: Grade published successfully");
        // Update the local state
        setSubmissions(
          submissions.map(sub => 
            sub.id === submissionId ? { ...sub, is_published: true } : sub
          )
        );
        setMessage({ text: 'Grade published successfully!', type: 'success' });
      } else {
        console.error("TeacherPortal: Failed to publish grade:", data.message);
        setMessage({ text: data.message || 'Failed to publish grade', type: 'error' });
      }
    } catch (error) {
      console.error('TeacherPortal: Error publishing grade:', error);
      setMessage({ text: 'An error occurred. Please try again.', type: 'error' });
    } finally {
      setLoading(false);
    }
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
            color: '#2c3e50',
            margin: 0,
            fontSize: '2.5em',
            textAlign: 'center',
          }}>Teacher Portal</h1>
          <button 
            onClick={handleLogout}
            style={{
              padding: '12px 24px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '16px',
              fontWeight: 500,
              cursor: 'pointer',
              transition: 'transform 0.3s ease, box-shadow 0.3s ease',
            }}
            className="button logout-btn"
            onMouseOver={(e) => {
              const target = e.target as HTMLButtonElement;
              target.style.transform = 'translateY(-2px)';
              target.style.boxShadow = '0 5px 15px rgba(0,0,0,0.2)';
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
              padding: '12px',
              marginBottom: '20px',
              borderRadius: '8px',
              backgroundColor: message.type === 'success' ? '#dcfce7' : '#fef9c3',
              color: message.type === 'success' ? '#166534' : '#854d0e',
            }}
            className="message"
          >
            {message.text}
          </div>
        )}

        <div style={{
          display: 'flex',
          gap: '20px',
          marginBottom: '30px',
        }} className="tabs">
          <div 
            style={{
              padding: '12px 24px',
              background: activeTab === 'create' 
                ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                : '#f1f5f9',
              borderRadius: '8px',
              color: activeTab === 'create' ? 'white' : '#64748b',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
            }}
            className={`tab ${activeTab === 'create' ? 'active' : ''}`}
            onClick={() => setActiveTab('create')}
          >
            Create Exam
          </div>
          <div 
            style={{
              padding: '12px 24px',
              background: activeTab === 'exams' 
                ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                : '#f1f5f9',
              borderRadius: '8px',
              color: activeTab === 'exams' ? 'white' : '#64748b',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
            }}
            className={`tab ${activeTab === 'exams' ? 'active' : ''}`}
            onClick={() => setActiveTab('exams')}
          >
            Your Exams
          </div>
          <div 
            style={{
              padding: '12px 24px',
              background: activeTab === 'submissions' 
                ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                : '#f1f5f9',
              borderRadius: '8px',
              color: activeTab === 'submissions' ? 'white' : '#64748b',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
            }}
            className={`tab ${activeTab === 'submissions' ? 'active' : ''}`}
            onClick={() => {
              console.log("TeacherPortal: 'Student Submissions' tab clicked.");
              setActiveTab('submissions');
              // Refresh submissions when this tab is selected
              fetchSubmissions();
            }}
          >
            Student Submissions
          </div>
        </div>

        <div style={{
          display: activeTab === 'create' ? 'block' : 'none',
        }} className={`tab-content ${activeTab === 'create' ? 'active' : ''}`}>
          <div style={{
            background: 'white',
            padding: '30px',
            borderRadius: '20px',
            boxShadow: '0 10px 20px rgba(0,0,0,0.1)',
            marginBottom: '40px',
          }} className="form-container">
            <h2>Create New Exam</h2>
            <form onSubmit={handleSubmit}>
              <div style={{ marginBottom: '20px' }} className="form-group">
                <label 
                  style={{
                    display: 'block',
                    marginBottom: '8px',
                    color: '#2c3e50',
                    fontWeight: 500,
                  }}
                  htmlFor="title"
                >
                  Exam Title
                </label>
                <input 
                  type="text" 
                  id="title" 
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                  style={{
                    width: '100%',
                    padding: '12px',
                    border: '2px solid #e1e8ed',
                    borderRadius: '8px',
                    fontSize: '16px',
                    transition: 'border-color 0.3s ease',
                    boxSizing: 'border-box',
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
                  Question Paper (PDF)
                </label>
                <div style={{
                  position: 'relative',
                  marginBottom: '15px',
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
                    htmlFor="question_paper"
                  >
                    {questionPaper ? questionPaper.name : "Choose Question Paper File"}
                  </label>
                  <input 
                    type="file" 
                    id="question_paper" 
                    onChange={(e) => e.target.files && setQuestionPaper(e.target.files[0])}
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

              <div style={{ marginBottom: '20px' }} className="form-group">
                <label 
                  style={{
                    display: 'block',
                    marginBottom: '8px',
                    color: '#2c3e50',
                    fontWeight: 500,
                  }}
                >
                  Rubric File (PDF)
                </label>
                <div style={{
                  position: 'relative',
                  marginBottom: '15px',
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
                    htmlFor="rubric_file"
                  >
                    {rubricFile ? rubricFile.name : "Choose Rubric File"}
                  </label>
                  <input 
                    type="file" 
                    id="rubric_file" 
                    onChange={(e) => e.target.files && setRubricFile(e.target.files[0])}
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
                  transition: 'transform 0.3s ease, box-shadow 0.3s ease',
                  opacity: loading ? 0.7 : 1,
                }}
                className="button"
                disabled={loading}
                onMouseOver={(e) => {
                  if (!loading) {
                    const target = e.target as HTMLButtonElement;
                    target.style.transform = 'translateY(-2px)';
                    target.style.boxShadow = '0 5px 15px rgba(0,0,0,0.2)';
                  }
                }}
                onMouseOut={(e) => {
                  const target = e.target as HTMLButtonElement;
                  target.style.transform = 'none';
                  target.style.boxShadow = 'none';
                }}
              >
                {loading ? 'Creating Exam...' : 'Create Exam'}
              </button>
            </form>
          </div>
        </div>

        <div style={{
          display: activeTab === 'exams' ? 'block' : 'none',
        }} className={`tab-content ${activeTab === 'exams' ? 'active' : ''}`}>
          <h2>Your Exams</h2>
          
          {loading ? (
            <div style={{
              background: 'white',
              padding: '30px',
              borderRadius: '15px',
              textAlign: 'center',
              boxShadow: '0 5px 15px rgba(0,0,0,0.1)',
              marginTop: '20px',
            }}>
              <p>Loading exams...</p>
            </div>
          ) : exams.length === 0 ? (
            <div style={{
              background: 'white',
              padding: '30px',
              borderRadius: '15px',
              textAlign: 'center',
              boxShadow: '0 5px 15px rgba(0,0,0,0.1)',
              marginTop: '20px',
            }}>
              <p>You haven't created any exams yet.</p>
              <p>Use the "Create Exam" tab to create your first exam.</p>
            </div>
          ) : (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
              gap: '20px',
              marginTop: '30px',
            }} className="exam-list">
              {exams.map(exam => (
                <div 
                  key={exam.id}
                  style={{
                    background: 'rgb(255, 255, 255)',
                    padding: '25px',
                    borderRadius: '20px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(255, 255, 255, 0.06)',
                    transition: 'transform 0.3s ease',
                  }}
                  className="exam-item"
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
                    color: '#1F2937',
                    fontSize: '1.5rem',
                    marginBottom: '15px',
                  }}>{exam.title}</h3>
                  <p style={{ color: '#64748b', margin: '8px 0' }}>
                    Created: {exam.created_at}
                  </p>
                  <p style={{ color: '#64748b', margin: '8px 0' }}>
                    Exam Code: <span style={{
                      background: '#F3F4F6',
                      padding: '4px 12px',
                      borderRadius: '6px',
                      fontFamily: 'monospace',
                      color: '#374151',
                    }} className="exam-code">{exam.exam_code}</span>
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        <div style={{
          display: activeTab === 'submissions' ? 'block' : 'none',
        }} className={`tab-content ${activeTab === 'submissions' ? 'active' : ''}`}>
          <h2>Student Submissions</h2>

          {debugInfo && (
            <div style={{
              marginTop: '10px',
              marginBottom: '20px',
              padding: '10px',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              background: '#f8fafc',
              fontSize: '14px',
              fontFamily: 'monospace',
            }}>
              <strong>Debug Info:</strong> {debugInfo}
              <button 
                onClick={() => fetchSubmissions()}
                style={{
                  marginLeft: '10px',
                  padding: '4px 8px',
                  fontSize: '12px',
                  background: '#e2e8f0',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                }}
              >
                Retry
              </button>
            </div>
          )}

          {loading ? (
            <div style={{
              background: 'white',
              padding: '30px',
              borderRadius: '15px',
              textAlign: 'center',
              boxShadow: '0 5px 15px rgba(0,0,0,0.1)',
              marginTop: '20px',
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
              marginTop: '20px',
            }}>
              <p>No submissions found.</p>
              <p>Once students submit their answer sheets, they will appear here.</p>
            </div>
          ) : (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
              gap: '20px',
              marginTop: '30px',
            }} className="submissions-grid">
              {submissions.map(submission => (
                <div
                  key={submission.id}
                  style={{
                    background: 'white',
                    padding: '25px',
                    borderRadius: '15px',
                    boxShadow: '0 5px 15px rgba(0,0,0,0.1)',
                  }}
                  className="submission-card"
                >
                  <div style={{
                    fontSize: '1.2em',
                    fontWeight: 600,
                    color: '#2c3e50',
                    marginBottom: '10px',
                  }} className="student-name">{submission.student_name}</div>
                  <div style={{
                    color: '#64748b',
                    fontSize: '0.9em',
                    marginBottom: '15px',
                  }} className="submission-details">
                    <p>Exam: {submission.exam_title}</p>
                    <p>Submitted: {submission.submitted_at}</p>
                    <p>Status: {submission.is_published ? 'Published' : 'Not Published'}</p>
                  </div>

                  {submission.answer_sheet_url && (
                    <div style={{ marginBottom: '15px' }}>
                      <a 
                        href={submission.answer_sheet_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        style={{
                          display: 'inline-block',
                          padding: '8px 16px',
                          background: '#f1f5f9',
                          color: '#475569',
                          borderRadius: '8px',
                          textDecoration: 'none',
                          fontSize: '14px',
                          marginBottom: '10px',
                        }}
                      >
                        View Answer Sheet
                      </a>
                    </div>
                  )}

                  {!submission.is_published && (
                    <button
                      onClick={() => publishGrade(submission.id)}
                      style={{
                        padding: '8px 16px',
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        color: 'white',
                        border: 'none',
                        borderRadius: '8px',
                        fontSize: '14px',
                        fontWeight: 500,
                        cursor: 'pointer',
                        transition: 'transform 0.3s ease, box-shadow 0.3s ease',
                      }}
                      className="button"
                      disabled={loading}
                    >
                      {loading ? 'Processing...' : 'Publish Grade'}
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TeacherPortal; 