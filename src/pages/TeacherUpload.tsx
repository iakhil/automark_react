import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const TeacherUpload: React.FC = () => {
  const navigate = useNavigate();
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setSelectedFiles(event.target.files);
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!selectedFiles) return;

    const formData = new FormData();
    Array.from(selectedFiles).forEach((file) => {
      formData.append('files', file);
    });

    try {
      const response = await fetch('/api/upload/teacher', {
        method: 'POST',
        body: formData,
      });
      
      if (response.ok) {
        alert('Files uploaded successfully!');
      } else {
        alert('Error uploading files');
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error uploading files');
    }
  };

  return (
    <>
      <header>
        AI Grader - Teacher Upload
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
          <h2>Upload Assignment Files</h2>
          <p>Please upload your assignment files and answer key.</p>
          <form onSubmit={handleSubmit}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', alignItems: 'center' }}>
              <div>
                <input
                  type="file"
                  multiple
                  onChange={handleFileChange}
                  style={{ display: 'none' }}
                  id="file-input"
                />
                <label htmlFor="file-input" className="btn">
                  Choose Files
                </label>
              </div>
              {selectedFiles && (
                <div>
                  Selected files: {Array.from(selectedFiles).map(file => file.name).join(', ')}
                </div>
              )}
              <button
                type="submit"
                className="btn"
                disabled={!selectedFiles}
                style={{ opacity: !selectedFiles ? '0.6' : '1' }}
              >
                Upload Files
              </button>
            </div>
          </form>
        </div>
      </main>
    </>
  );
};

export default TeacherUpload; 