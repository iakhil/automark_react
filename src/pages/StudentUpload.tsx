import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const StudentUpload: React.FC = () => {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [studentId, setStudentId] = useState('');

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!selectedFile || !studentId) return;

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('studentId', studentId);

    try {
      const response = await fetch('/api/upload/student', {
        method: 'POST',
        body: formData,
      });
      
      if (response.ok) {
        alert('File uploaded successfully!');
      } else {
        alert('Error uploading file');
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error uploading file');
    }
  };

  return (
    <>
      <header>
        AI Grader - Student Upload
        <button 
          onClick={() => navigate('/')}
          className="btn"
          style={{ float: 'right', padding: '10px 20px', margin: '0' }}
        >
          Home
        </button>
      </header>
      <main>
        <div style={{
          maxWidth: '600px',
          margin: '20px auto',
          padding: '20px',
          backgroundColor: 'white',
          borderRadius: '5px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <h2>Submit Your Assignment</h2>
          <p>Please upload your assignment file and enter your student ID.</p>
          <form onSubmit={handleSubmit}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', alignItems: 'center' }}>
              <div style={{ width: '100%', maxWidth: '300px' }}>
                <input
                  type="text"
                  value={studentId}
                  onChange={(e) => setStudentId(e.target.value)}
                  placeholder="Enter Student ID"
                  required
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid #ccc',
                    borderRadius: '5px',
                    fontSize: '1rem'
                  }}
                />
              </div>
              <div>
                <input
                  type="file"
                  onChange={handleFileChange}
                  style={{ display: 'none' }}
                  id="file-input"
                />
                <label htmlFor="file-input" className="btn">
                  Choose File
                </label>
              </div>
              {selectedFile && (
                <div>
                  Selected file: {selectedFile.name}
                </div>
              )}
              <button
                type="submit"
                className="btn"
                disabled={!selectedFile || !studentId}
                style={{ opacity: (!selectedFile || !studentId) ? '0.6' : '1' }}
              >
                Submit Assignment
              </button>
            </div>
          </form>
        </div>
      </main>
    </>
  );
};

export default StudentUpload; 