// API base URL - use the exact same origin as the browser uses to avoid CORS issues

  // Use environment variable for the backend API URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000'; // Fallback for local dev
// Common fetch options
const commonFetchOptions = {
  credentials: 'include' as RequestCredentials,
  headers: {
    'Accept': 'application/json'
  }
};

// API service for authentication
export const authAPI = {
  login: async (username: string, password: string) => {
    const response = await fetch(`${API_BASE_URL}/api/login`, {
      method: 'POST',
      headers: {
        ...commonFetchOptions.headers,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
      credentials: commonFetchOptions.credentials,
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Login error:', response.status, errorText);
      throw new Error(`Login failed: ${response.status}`);
    }
    
    return response.json();
  },
  
  register: async (username: string, password: string, role: string = 'student') => {
    const response = await fetch(`${API_BASE_URL}/api/register`, {
      method: 'POST',
      headers: {
        ...commonFetchOptions.headers,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password, role }),
      credentials: commonFetchOptions.credentials,
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Registration error:', response.status, errorText);
      throw new Error(`Registration failed: ${response.status}`);
    }
    
    return response.json();
  },
  
  checkSession: async () => {
    console.log("API: Checking session status. Cookies:", document.cookie);
    try {
      const response = await fetch(`${API_BASE_URL}/api/check-session`, {
        ...commonFetchOptions
      });
      
      console.log("API: Session check response status:", response.status);
      
      if (!response.ok) {
        console.warn('API: Session check failed:', response.status);
        return { success: false, authenticated: false };
      }
      
      const data = await response.json();
      console.log("API: Session check data:", data);
      return data;
    } catch (error) {
      console.error("API: Session check exception:", error);
      return { success: false, authenticated: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  },
  
  logout: async () => {
    console.log("API: Logging out. Current cookies:", document.cookie);
    try {
      const response = await fetch(`${API_BASE_URL}/api/logout`, {
        method: 'POST',
        ...commonFetchOptions
      });
      
      console.log("API: Logout response status:", response.status);
      
      if (!response.ok) {
        console.warn('API: Logout failed:', response.status);
        return { success: false };
      }
      
      const data = await response.json();
      console.log("API: Logout successful, cookies after logout:", document.cookie);
      return data;
    } catch (error) {
      console.error("API: Logout exception:", error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }
};

// API service for exams
export const examAPI = {
  getExams: async () => {
    const response = await fetch(`${API_BASE_URL}/api/exams`, {
      ...commonFetchOptions
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Fetch exams error:', response.status, errorText);
      throw new Error(`Failed to fetch exams: ${response.status}`);
    }
    
    return response.json();
  },
  
  createExam: async (title: string, questionPaper: File, rubricFile: File) => {
    const formData = new FormData();
    formData.append('title', title);
    formData.append('question_paper', questionPaper);
    formData.append('rubric_file', rubricFile);
    
    const response = await fetch(`${API_BASE_URL}/api/create-exam`, {
      method: 'POST',
      body: formData,
      credentials: commonFetchOptions.credentials,
      headers: commonFetchOptions.headers
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Create exam error:', response.status, errorText);
      throw new Error(`Failed to create exam: ${response.status} ${errorText}`);
    }
    
    return response.json();
  },
  
  submitAnswer: async (examCode: string, answerSheet: File) => {
    console.log("API: Submitting answer for exam code:", examCode);
    
    try {
      const formData = new FormData();
      formData.append('exam_code', examCode);
      formData.append('answer_sheet', answerSheet);
      
      const response = await fetch(`${API_BASE_URL}/api/submit-answer`, {
        method: 'POST',
        body: formData,
        credentials: commonFetchOptions.credentials,
        headers: commonFetchOptions.headers
      });
      
      console.log("API: Submit answer response status:", response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('API: Submit answer error:', response.status, errorText);
        
        // Try to parse JSON response
        try {
          const errorData = JSON.parse(errorText);
          return {
            success: false,
            message: errorData.message || `Failed to submit answer: ${response.status}`
          };
        } catch (parseError) {
          throw new Error(`Failed to submit answer: ${response.status}`);
        }
      }
      
      const data = await response.json();
      console.log("API: Submit answer data:", data);
      return data;
    } catch (error) {
      console.error("API: Submit answer exception:", error);
      throw error;
    }
  },
  
  getSubmissions: async () => {
    console.log("API: Fetching submissions");
    try {
      const response = await fetch(`${API_BASE_URL}/api/submissions`, {
        ...commonFetchOptions
      });
      
      console.log("API: Submissions response status:", response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('API: Fetch submissions error:', response.status, errorText);
        
        // Try to parse JSON response
        try {
          const errorData = JSON.parse(errorText);
          return {
            success: false,
            message: errorData.message || `Failed to fetch submissions: ${response.status}`
          };
        } catch (parseError) {
          throw new Error(`Failed to fetch submissions: ${response.status}`);
        }
      }
      
      const data = await response.json();
      console.log("API: Submissions data:", data);
      return data;
    } catch (error) {
      console.error("API: Submissions fetch exception:", error);
      throw error;
    }
  },
  
  getTeacherSubmissions: async () => {
    console.log("API_SERVICE: getTeacherSubmissions called. Cookies:", document.cookie);
    try {
      const response = await fetch(`${API_BASE_URL}/api/teacher/submissions`, {
        ...commonFetchOptions
      });
      console.log("API_SERVICE: getTeacherSubmissions response status:", response.status);
      if (!response.ok) {
        const errorText = await response.text();
        console.error('API_SERVICE: getTeacherSubmissions error:', response.status, errorText);
        try {
          const errorData = JSON.parse(errorText);
          return { success: false, message: errorData.message || `Failed to fetch: ${response.status}` };
        } catch (parseError) {
          return { success: false, message: `Failed to fetch: ${response.status}, Response: ${errorText}` };
        }
      }
      const data = await response.json();
      console.log("API_SERVICE: getTeacherSubmissions response data:", data);
      return data;
    } catch (error) {
      console.error("API_SERVICE: getTeacherSubmissions exception:", error);
      return { success: false, message: error instanceof Error ? error.message : 'Unknown error' };
    }
  },
  
  publishGrade: async (submissionId: number) => {
    console.log("API: Publishing grade for submission:", submissionId);
    try {
      const response = await fetch(`${API_BASE_URL}/api/publish_grade/${submissionId}`, {
        method: 'POST',
        ...commonFetchOptions
      });
      
      console.log("API: Publish grade response status:", response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('API: Publish grade error:', response.status, errorText);
        
        // Try to parse JSON response
        try {
          const errorData = JSON.parse(errorText);
          return {
            success: false,
            message: errorData.message || `Failed to publish grade: ${response.status}`
          };
        } catch (parseError) {
          throw new Error(`Failed to publish grade: ${response.status}`);
        }
      }
      
      const data = await response.json();
      console.log("API: Publish grade data:", data);
      return data;
    } catch (error) {
      console.error("API: Publish grade exception:", error);
      throw error;
    }
  },

  updateGrade: async (submissionId: number, grade: string) => {
    console.log("API: Updating grade for submission:", submissionId);
    try {
      const response = await fetch(`${API_BASE_URL}/api/update_grade/${submissionId}`, {
        method: 'POST',
        headers: {
          ...commonFetchOptions.headers,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ grade }),
        credentials: commonFetchOptions.credentials,
      });
      
      console.log("API: Update grade response status:", response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('API: Update grade error:', response.status, errorText);
        
        // Try to parse JSON response
        try {
          const errorData = JSON.parse(errorText);
          return {
            success: false,
            message: errorData.message || `Failed to update grade: ${response.status}`
          };
        } catch (parseError) {
          throw new Error(`Failed to update grade: ${response.status}`);
        }
      }
      
      const data = await response.json();
      console.log("API: Update grade data:", data);
      return data;
    } catch (error) {
      console.error("API: Update grade exception:", error);
      throw error;
    }
  }
}; 