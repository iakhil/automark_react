import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { examAPI } from '../api';

interface Exam {
  id: number;
  title: string;
  exam_code: string;
  created_at: string;
  question_paper_file?: string;
  rubric_file?: string;
}

interface Submission {
  id: number;
  student_name: string;
  exam_title: string;
  exam_code?: string;
  submitted_at: string;
  is_published: boolean;
  answer_sheet_file?: string;
  grade?: string;
}

const TeacherPage: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('create-exam');
  const [title, setTitle] = useState('');
  const [questionPaper, setQuestionPaper] = useState<File | null>(null);
  const [rubricFile, setRubricFile] = useState<File | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [exams, setExams] = useState<Exam[]>([]);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loadingExams, setLoadingExams] = useState<boolean>(false);
  const [loadingSubmissions, setLoadingSubmissions] = useState<boolean>(false);

  // Toggle grades section
  const toggleGrade = (element: HTMLElement) => {
    const gradeText = element.nextElementSibling as HTMLElement;
    const chevron = element.querySelector('.chevron') as SVGElement;
    
    if (gradeText && gradeText.classList.contains('grade-text')) {
      if (gradeText.classList.contains('show')) {
        gradeText.classList.remove('show');
        if (chevron) chevron.classList.remove('rotated');
      } else {
        gradeText.classList.add('show');
        if (chevron) chevron.classList.add('rotated');
      }
    } else {
      // Keep error log in case structure changes
      console.error("Could not find the grade-text element next to the clicked header or it lacks class:", element);
    }
  };

  // Switch tabs
  const switchTab = (tabId: string) => {
    setActiveTab(tabId);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!title || !questionPaper || !rubricFile) {
      setMessage('All fields are required!');
      return;
    }

    try {
      // Use the API service for exam creation
      const response = await examAPI.createExam(title, questionPaper, rubricFile);
      
      if (response.success) {
        setMessage(response.message || 'Exam created successfully!');
        setTitle('');
        setQuestionPaper(null);
        setRubricFile(null);
        
        // Add the new exam to the state
        if (response.exam) {
          setExams(prevExams => [...prevExams, response.exam]);
        } else {
          // Fetch all exams if the response doesn't include the created exam
          fetchExams();
        }
      } else {
        setMessage(response.message || 'Error creating exam');
      }
    } catch (error) {
      setMessage('An error occurred. Please try again.');
      console.error('Error submitting form:', error);
    }
  };

  // Fetch exams from the backend
  const fetchExams = async () => {
    setLoadingExams(true);
    try {
      // Use the API service for fetching exams
      const response = await examAPI.getExams();
      
      if (response.success && response.exams) {
        setExams(response.exams);
      } else {
        console.error('Failed to fetch exams:', response.message);
        // For development fallback only
        if (process.env.NODE_ENV === 'development') {
          setExams([
            { 
              id: 1, 
              title: 'English Exam', 
              exam_code: 'YI8XIM', 
              created_at: '2025-05-07 16:39:09',
              question_paper_file: 'https://res.cloudinary.com/demo/image/upload/sample.pdf',
              rubric_file: 'https://res.cloudinary.com/demo/image/upload/sample.pdf'
            }
          ]);
        }
      }
    } catch (error) {
      console.error('Error fetching exams:', error);
      // For development fallback only
      if (process.env.NODE_ENV === 'development') {
        setExams([
          { 
            id: 1, 
            title: 'English Exam', 
            exam_code: 'YI8XIM', 
            created_at: '2025-05-07 16:39:09',
            question_paper_file: 'https://res.cloudinary.com/demo/image/upload/sample.pdf',
            rubric_file: 'https://res.cloudinary.com/demo/image/upload/sample.pdf'
          }
        ]);
      }
    } finally {
      setLoadingExams(false);
    }
  };

  // Fetch submissions from API
  const fetchSubmissions = async () => {
    // console.log("TeacherPage: fetchSubmissions called"); // Removed log
    setLoadingSubmissions(true);
    try {
      const data = await examAPI.getTeacherSubmissions();
      // console.log("TeacherPage: Received submissions data:", data); // Removed log
      if (data.success && data.submissions) {
        setSubmissions(data.submissions);
      } else {
        setMessage(data.message || 'Failed to load submissions');
      }
    } catch (error) {
      console.error('Error fetching submissions:', error); // Keep this error log
      setMessage('Could not load submissions. Please try again later.');
    } finally {
      setLoadingSubmissions(false);
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
    }

    // Fetch exams when component mounts
    fetchExams();
    // Also fetch submissions on initial load
    fetchSubmissions();
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('user');
    navigate('/login');
  };

  const publishGrade = async (submissionId: number) => {
    // console.log("TeacherPage: Publishing grade for submission:", submissionId); // Removed log
    try {
      const response = await examAPI.publishGrade(submissionId);
      // console.log("TeacherPage: Publish grade response:", response); // Removed log
      
      if (response.success) {
        // Refresh submissions list to show updated status
        fetchSubmissions(); 
        setMessage('Grade published successfully!');
      } else {
        setMessage(response.message || 'Error publishing grade');
      }
    } catch (error) {
      console.error('Error publishing grade:', error); // Keep this error log
      setMessage('An error occurred. Please try again.');
    }
  };

  const handleQuestionPaperChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setQuestionPaper(e.target.files[0]);
    }
  };

  const handleRubricFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setRubricFile(e.target.files[0]);
    }
  };

  return (
    <div style={{
      fontFamily: "'Poppins', sans-serif",
      margin: 0,
      padding: 0,
      minHeight: '100vh',
      background: '#EDF2F7',
    }}>
      {/* Add CSS for toggleGrade functionality */}
      <style>{`
        .grade-text {
          /* Ensure initial state has consistent transition */
          transition: max-height 0.4s ease;
        }
        .grade-text.show {
          max-height: 5000px !important; /* Re-added !important due to conflict */
          transition: max-height 0.4s ease; /* Standardized transition */
        }
        .chevron.rotated {
          transform: rotate(180deg);
        }
      `}</style>

      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '20px',
        position: 'relative',
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'flex-end', 
          marginBottom: '50px', /* Added space for the centered title */
        }}>
          <h1 style={{
            color: '#2D3748',
            margin: 0,
            fontSize: '2.5rem',
            fontWeight: 'bold',
            position: 'absolute',
            left: '50%',
            top: '20px',
            transform: 'translateX(-50%)',
            textAlign: 'center',
          }}>
            Teacher<br />Portal
          </h1>
          
          <button 
            onClick={handleLogout}
            style={{
              padding: '12px 0',
              width: '100px',
              background: 'linear-gradient(90deg, #6366F1 0%, #8B5CF6 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '16px',
              fontWeight: 500,
              cursor: 'pointer',
            }}
          >
            Logout
          </button>
        </div>

        {message && (
          <div style={{
            padding: '12px',
            marginBottom: '20px',
            borderRadius: '8px',
            backgroundColor: '#fef9c3',
            color: '#854d0e',
          }}>
            {message}
          </div>
        )}

        <div style={{
          display: 'flex',
          gap: '10px',
          marginBottom: '20px',
        }}>
          <div 
            onClick={() => switchTab('create-exam')}
            style={{
              padding: '15px 25px',
              background: activeTab === 'create-exam' ? '#6366F1' : '#FFFFFF',
              borderRadius: '8px',
              color: activeTab === 'create-exam' ? 'white' : '#4A5568',
              cursor: 'pointer',
              fontWeight: 500,
            }}
          >
            Create Exam
          </div>
          <div 
            onClick={() => {
              switchTab('view-submissions');
              fetchSubmissions(); // Fetch submissions when tab is clicked
            }}
            style={{
              padding: '15px 25px',
              background: activeTab === 'view-submissions' ? '#6366F1' : '#FFFFFF',
              borderRadius: '8px',
              color: activeTab === 'view-submissions' ? 'white' : '#4A5568',
              cursor: 'pointer',
              fontWeight: 500,
            }}
          >
            View Submissions
          </div>
        </div>

        <div 
          style={{
            display: activeTab === 'create-exam' ? 'block' : 'none',
          }}
        >
          <div style={{
            background: 'white',
            padding: '30px',
            borderRadius: '12px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            marginBottom: '20px',
          }}>
            <h2 style={{
              textAlign: 'center',
              marginTop: 0,
              marginBottom: '30px',
              fontSize: '1.5rem',
              color: '#2D3748',
              fontWeight: 'bold',
            }}>Create New Exam</h2>
            
            <form onSubmit={handleSubmit}>
              <div style={{ marginBottom: '20px' }}>
                <label 
                  htmlFor="title"
                  style={{
                    display: 'block',
                    marginBottom: '10px',
                    color: '#4A5568',
                    fontWeight: 500,
                  }}
                >
                  Exam Title
                </label>
                <input 
                  type="text" 
                  id="title" 
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required 
                  placeholder="Enter exam title"
                  style={{
                    width: '100%',
                    padding: '12px',
                    border: '1px solid #E2E8F0',
                    borderRadius: '6px',
                    fontSize: '16px',
                  }}
                />
              </div>

              <div style={{ marginBottom: '20px' }}>
                <label 
                  htmlFor="question_paper"
                  style={{
                    display: 'block',
                    marginBottom: '10px',
                    color: '#4A5568',
                    fontWeight: 500,
                  }}
                >
                  Question Paper (PDF)
                </label>
                <div style={{
                  position: 'relative',
                }}>
                  <label 
                    style={{
                      display: 'block',
                      padding: '12px',
                      background: '#F5F7FF',
                      border: '1px dashed #6366F1',
                      borderRadius: '6px',
                      textAlign: 'center',
                      cursor: 'pointer',
                      color: '#6366F1',
                      transition: 'all 0.2s ease',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                    }}
                    onMouseOver={(e) => {
                      e.currentTarget.style.backgroundColor = '#EEF2FF';
                      e.currentTarget.style.borderColor = '#818CF8';
                    }}
                    onMouseOut={(e) => {
                      e.currentTarget.style.backgroundColor = '#F5F7FF';
                      e.currentTarget.style.borderColor = '#6366F1';
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 16L12 8" stroke="#6366F1" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        <path d="M9 11L12 8 15 11" stroke="#6366F1" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        <path d="M3 15L3 16C3 18.2091 4.79086 20 7 20L17 20C19.2091 20 21 18.2091 21 16L21 15" stroke="#6366F1" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                      <span>{questionPaper ? questionPaper.name : "Click to upload question paper"}</span>
                    </div>
                    <input 
                      type="file" 
                      id="question_paper" 
                      accept=".pdf" 
                      required
                      onChange={handleQuestionPaperChange}
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
                  </label>
                </div>
              </div>

              <div style={{ marginBottom: '30px' }}>
                <label 
                  htmlFor="rubric_file"
                  style={{
                    display: 'block',
                    marginBottom: '10px',
                    color: '#4A5568',
                    fontWeight: 500,
                  }}
                >
                  Rubric (PDF)
                </label>
                <div style={{
                  position: 'relative',
                }}>
                  <label 
                    style={{
                      display: 'block',
                      padding: '12px',
                      background: '#F5F7FF',
                      border: '1px dashed #6366F1',
                      borderRadius: '6px',
                      textAlign: 'center',
                      cursor: 'pointer',
                      color: '#6366F1',
                      transition: 'all 0.2s ease',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                    }}
                    onMouseOver={(e) => {
                      e.currentTarget.style.backgroundColor = '#EEF2FF';
                      e.currentTarget.style.borderColor = '#818CF8';
                    }}
                    onMouseOut={(e) => {
                      e.currentTarget.style.backgroundColor = '#F5F7FF';
                      e.currentTarget.style.borderColor = '#6366F1';
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 16L12 8" stroke="#6366F1" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        <path d="M9 11L12 8 15 11" stroke="#6366F1" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        <path d="M3 15L3 16C3 18.2091 4.79086 20 7 20L17 20C19.2091 20 21 18.2091 21 16L21 15" stroke="#6366F1" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                      <span>{rubricFile ? rubricFile.name : "Click to upload rubric"}</span>
                    </div>
                    <input 
                      type="file" 
                      id="rubric_file" 
                      accept=".pdf" 
                      required
                      onChange={handleRubricFileChange}
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
                  </label>
                </div>
              </div>

              <div style={{ textAlign: 'center' }}>
                <button 
                  type="submit" 
                  style={{
                    padding: '12px 24px',
                    background: '#6366F1',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '16px',
                    fontWeight: 500,
                    cursor: 'pointer',
                    minWidth: '180px',
                  }}
                >
                  Create Exam
                </button>
              </div>
            </form>
          </div>

          {/* Exams Section Loading/Empty State */}
          {loadingExams ? (
            <p>Loading exams...</p>
          ) : exams.length === 0 ? (
            <p>No exams created yet.</p>
          ) : (
            <>
              <h2 style={{ 
                fontSize: '1.75rem', 
                color: '#2D3748',
                fontWeight: 'bold',
                marginBottom: '20px'
              }}>
                Your Exams
              </h2>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
                gap: '20px',
              }}>
                {exams.map(exam => (
                  <div 
                    key={exam.id}
                    style={{
                      background: 'white',
                      padding: '25px',
                      borderRadius: '16px',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                    }}
                  >
                    <h3 style={{
                      fontSize: '1.5rem',
                      fontWeight: 'bold',
                      color: '#2D3748',
                      marginTop: 0,
                      marginBottom: '15px'
                    }}>
                      {exam.title}
                    </h3>
                    <div style={{ marginBottom: '10px' }}>
                      <span style={{ 
                        color: '#4A5568', 
                        fontWeight: '500' 
                      }}>Exam Code: </span>
                      <span style={{ 
                        fontFamily: 'monospace',
                        backgroundColor: '#F7FAFC',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        marginLeft: '5px'
                      }}>{exam.exam_code}</span>
                    </div>
                    <div style={{ marginBottom: '20px' }}>
                      <span style={{ 
                        color: '#4A5568', 
                        fontWeight: '500' 
                      }}>Created: </span>
                      <span style={{ color: '#718096' }}>{exam.created_at}</span>
                    </div>
                    <div style={{
                      display: 'flex',
                      gap: '15px',
                    }}>
                      <a
                        href={exam.question_paper_file || '#'}
                        target="_blank"
                        rel="noreferrer"
                        style={{
                          display: 'block',
                          flex: 1,
                          padding: '12px 0',
                          background: '#6366F1',
                          color: 'white',
                          textAlign: 'center',
                          borderRadius: '8px',
                          textDecoration: 'none',
                          fontWeight: '500',
                          fontSize: '0.95rem',
                          transition: 'background-color 0.2s',
                        }}
                        onMouseOver={(e) => {
                          e.currentTarget.style.backgroundColor = '#4F46E5';
                        }}
                        onMouseOut={(e) => {
                          e.currentTarget.style.backgroundColor = '#6366F1';
                        }}
                      >
                        View Question Paper
                      </a>
                      <a
                        href={exam.rubric_file || '#'}
                        target="_blank"
                        rel="noreferrer"
                        style={{
                          display: 'block',
                          flex: 1,
                          padding: '12px 0',
                          background: '#6366F1',
                          color: 'white',
                          textAlign: 'center',
                          borderRadius: '8px',
                          textDecoration: 'none',
                          fontWeight: '500',
                          fontSize: '0.95rem',
                          transition: 'background-color 0.2s',
                        }}
                        onMouseOver={(e) => {
                          e.currentTarget.style.backgroundColor = '#4F46E5';
                        }}
                        onMouseOut={(e) => {
                          e.currentTarget.style.backgroundColor = '#6366F1';
                        }}
                      >
                        View Rubric
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        <div 
          style={{
            display: activeTab === 'view-submissions' ? 'block' : 'none',
          }}
        >
          <h2>Student Submissions</h2>
          {loadingSubmissions ? (
            <div style={{ textAlign: 'center', padding: '20px' }}>
              <p>Loading submissions...</p>
            </div>
          ) : submissions.length === 0 ? (
            <div style={{ background: 'white', padding: '30px', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', textAlign: 'center' }}>
              <p style={{ fontSize: '1.1rem', color: '#4A5568' }}>No submissions yet</p>
            </div>
          ) : (
            <>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
                gap: '20px',
              }}>
                {submissions.map(submission => {
                  return (
                    <div 
                      key={submission.id}
                      style={{
                        background: 'white',
                        padding: '20px',
                        borderRadius: '12px',
                        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                      }}
                    >
                      <h3>{submission.student_name}</h3>
                      <p>Exam: {submission.exam_title}</p>
                      <p>Submitted: {submission.submitted_at}</p>
                      
                      {/* Add View Answer Sheet Button */}
                      {submission.answer_sheet_file && (
                        <a 
                          href={submission.answer_sheet_file} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          style={{
                            display: 'inline-block',
                            padding: '10px 20px',
                            background: 'linear-gradient(90deg, #6366F1 0%, #8B5CF6 100%)', // Matching gradient
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            textDecoration: 'none',
                            fontWeight: 500,
                            fontSize: '0.9rem',
                            textAlign: 'center',
                            marginBottom: '15px' // Add margin below
                          }}
                        >
                          View Answer Sheet
                        </a>
                      )}
                      
                      {/* Add Status/Publish Button */}
                      {submission.is_published ? (
                        <div style={{
                          background: '#dcfce7', // Light green background
                          color: '#16a34a', // Darker green text
                          padding: '10px 15px',
                          borderRadius: '6px',
                          textAlign: 'center',
                          fontWeight: 500,
                          marginBottom: '15px' // Add margin below
                        }}>
                          Grade Published
                        </div>
                      ) : (
                        <button
                          onClick={() => publishGrade(submission.id)}
                          style={{
                            width: '100%',
                            padding: '10px',
                            background: '#f59e0b', // Orange background for publish
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            fontWeight: 500,
                            marginBottom: '15px' // Add margin below
                          }}
                          // Add disabled state if needed
                          // disabled={loadingSubmissions}
                        >
                          Publish Grade
                        </button>
                      )}

                      {/* Grade & Feedback Section */}
                      <div style={{
                        background: '#F7FAFC', // Light grey background
                        borderRadius: '8px',
                        border: '1px solid #E2E8F0',
                        overflow: 'hidden' // Ensures content stays within rounded corners
                      }}>
                        <div 
                          onClick={(e) => toggleGrade(e.currentTarget)}
                          style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            padding: '12px 15px',
                            cursor: 'pointer',
                            borderBottom: '1px solid #E2E8F0', // Separator line
                          }}
                        >
                          <span style={{ fontWeight: 500, color: '#4A5568' }}>Grade & Feedback</span>
                          {/* Chevron Icon */}
                          <svg className="chevron" width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ transition: 'transform 0.3s' }}>
                            <path d="M4 6L8 10L12 6" stroke="#718096" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                          </svg>
                        </div>
                        {/* Collapsible Content */}
                        <div 
                          className="grade-text" // Class used by toggleGrade
                          style={{
                            padding: '15px',
                            maxHeight: 0, // Initially hidden
                            overflow: 'hidden',
                            transition: 'max-height 0.3s ease-out', // Smooth transition
                            fontSize: '0.9rem',
                            lineHeight: 1.5,
                            color: '#4A5568'
                          }}
                        >
                          {/* Revert TEMP DEBUG: Render HTML content safely */}
                          <div dangerouslySetInnerHTML={{ __html: submission.grade || 'No grade available.' }} />
                        </div>
                      </div>

                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default TeacherPage; 