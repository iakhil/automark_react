const API_BASE_URL = 'http://localhost:5000';  // Change this to your deployed backend URL when deploying

class API {
    static async login(username, password) {
        const response = await fetch(`${API_BASE_URL}/api/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('Login failed');
        }
        
        return response.json();
    }

    static async submitAnswer(examCode, answerSheet) {
        const formData = new FormData();
        formData.append('exam_code', examCode);
        formData.append('answer_sheet', answerSheet);

        const response = await fetch(`${API_BASE_URL}/api/submit-answer`, {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });
        return response.json();
    }

    static async getSubmissions() {
        const response = await fetch(`${API_BASE_URL}/api/submissions`, {
            credentials: 'include'
        });
        return response.json();
    }

    static async createExam(title, questionPaper, rubric) {
        const formData = new FormData();
        formData.append('title', title);
        formData.append('question_paper', questionPaper);
        formData.append('rubric_file', rubric);

        const response = await fetch(`${API_BASE_URL}/api/create-exam`, {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });
        return response.json();
    }
} 