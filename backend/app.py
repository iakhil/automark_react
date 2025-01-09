from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import os
import cloudinary
from flask_cors import CORS
import cloudinary.uploader
from dotenv import load_dotenv
from openai import OpenAI

app = Flask(__name__)
CORS(app)
load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name="your_cloud_name",
    api_key="your_api_key",
    api_secret="your_api_secret"
)

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)


# AI grading logic using the new OpenAI API structure
def grade_response(student_response, rubrix):
    prompt = f"Grade the following student response based on the rubric:\n\nRubric:\n{rubrix}\n\nStudent Response:\n{student_response}\n"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt}
            ]
        }],
        max_tokens=500
    )
    return response.choices[0].message.content.strip()

# Route for teacher login and uploading question paper and rubric
@app.route('/upload_teacher', methods=['GET', 'POST'])
def upload_teacher():
    if request.method == 'POST':
        if 'file' not in request.files or 'rubric_file' not in request.files:
            return jsonify({'error': 'Both question paper and rubric files are required!'}), 400

        question_paper = request.files['file']
        rubric_file = request.files['rubric_file']

        if question_paper.filename == '' or rubric_file.filename == '':
            return jsonify({'error': 'No file selected!'}), 400

        # Upload files to Cloudinary
        question_paper_result = cloudinary.uploader.upload(question_paper, folder="teachers")
        rubric_file_result = cloudinary.uploader.upload(rubric_file, folder="teachers")

        return jsonify({
            'message': 'Question paper and rubric uploaded successfully!',
            'question_paper_url': question_paper_result['url'],
            'rubric_file_url': rubric_file_result['url']
        }), 200
    return render_template('upload_teacher.html')

# Route for student login and uploading their responses
@app.route('/upload_student', methods=['GET', 'POST'])
def upload_student():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'File is required!'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected!'}), 400

        # Upload student response to Cloudinary
        student_response_result = cloudinary.uploader.upload(file, folder="students")

        # Fetch rubric file URL (assumes a single rubric file per teacher)
        rubric_file_url = None  # Replace this logic with a persistent lookup mechanism

        if not rubric_file_url:
            return jsonify({'error': 'Rubric file not found! Please upload it first.'}), 400

        # Placeholder: Fetch rubric content and student response content from Cloudinary
        rubrix = "Example rubric content fetched from Cloudinary"
        student_response = "Example student response fetched from Cloudinary"

        grade = grade_response(student_response, rubrix)

        return jsonify({'grade': grade, 'response_url': student_response_result['url']}), 200
    return render_template('upload_student.html')

if __name__ == '__main__':
    app.run(debug=True)
