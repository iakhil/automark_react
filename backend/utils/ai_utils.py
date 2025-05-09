from flask import current_app
from google import genai
import os
import httpx
from dotenv import load_dotenv

load_dotenv()
# Initialize the Gemini client at module level
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

def grade_response(student_response, rubric_url):
    """
    Grade a student's response using AI based on a rubric
    
    Args:
        student_response: URL to the student's answer sheet PDF
        rubric_url: URL to the rubric PDF
        
    Returns:
        str: The AI-generated grade and feedback
    """
    # Log input parameters
    print(f"Starting grading process...")
    print(f"Rubric URL: {rubric_url}")
    print(f"Student response URL: {student_response}")
    
    # Check if inputs are valid
    if not student_response:
        return "<p>Error: Student response is not provided.</p>"
        
    if not rubric_url:
        return "<p>Error: Rubric is not provided.</p>"
    
    try:
        # Download PDFs from Cloudinary URLs for grading
        print("Downloading PDFs from Cloudinary...")
        rubric_response = httpx.get(rubric_url)
        answer_response = httpx.get(student_response)
        
        if not rubric_response.status_code == 200:
            print(f"Error downloading rubric: {rubric_response.status_code}")
            return f"<p>Error: Could not download rubric (status {rubric_response.status_code})</p>"
            
        if not answer_response.status_code == 200:
            print(f"Error downloading answer sheet: {answer_response.status_code}")
            return f"<p>Error: Could not download answer sheet (status {answer_response.status_code})</p>"
            
        # Create grading prompt and request
        print("Starting AI grading process")
        prompt = """Grade this answer sheet according to the rubric provided. Format your response in HTML as follows:

<h3>SECTION [NAME] ([TOTAL] marks)</h3>
<p><strong>Q[number] ([max_marks])</strong>: [Brief feedback] - [awarded]/[max_marks]</p>

There could be multiple choice questions. For these, the student might write the option in their response, e.g. 'B'. 
In the rubric, for these questions, the correct option might be present, e.g. 'C'. If they mismatch, then deduct points for that question.
Directly start your response with the grading without any preamble."""

        # Request grading from AI
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                {
                    "parts": [
                        {"text": prompt},
                        {"inline_data": {
                            "mime_type": "application/pdf",
                            "data": rubric_response.content
                        }},
                        {"inline_data": {
                            "mime_type": "application/pdf",
                            "data": answer_response.content
                        }}
                    ]
                }
            ]
        )

        grade = response.text.strip()
        print("AI grading complete, result length:", len(grade))
        return grade
        
    except Exception as e:
        import traceback
        print(f"Error using Gemini API: {str(e)}")
        print(traceback.format_exc())
        return f"<p>Error during grading: {str(e)}</p>" 