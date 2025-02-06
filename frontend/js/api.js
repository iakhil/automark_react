const API_BASE_URL = 'https://your-backend-url.com/api';  // Change this to your deployed backend URL

class API {
    static async login(username, password) {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
            credentials: 'include'
        });
        return await response.json();
    }

    static async submitAnswer(examCode, answerSheet) {
        const formData = new FormData();
        formData.append('exam_code', examCode);
        formData.append('answer_sheet', answerSheet);

        const response = await fetch(`${API_BASE_URL}/submit-answer`, {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });
        return await response.json();
    }

    static async getSubmissions() {
        const response = await fetch(`${API_BASE_URL}/submissions`, {
            credentials: 'include'
        });
        return await response.json();
    }

    static async createExam(title, questionPaper, rubric) {
        const formData = new FormData();
        formData.append('title', title);
        formData.append('question_paper', questionPaper);
        formData.append('rubric_file', rubric);

        const response = await fetch(`${API_BASE_URL}/create-exam`, {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });
        return await response.json();
    }
} 