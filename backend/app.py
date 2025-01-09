from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from flask_cors import CORS
import os
import openai
from dotenv import load_dotenv
import os
from openai import OpenAI


app = Flask(__name__)
CORS(app)
load_dotenv()

# Configure upload folders
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TEACHER_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'teachers')
app.config['STUDENT_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'students')
os.makedirs(app.config['TEACHER_FOLDER'], exist_ok=True)
os.makedirs(app.config['STUDENT_FOLDER'], exist_ok=True)


client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

# Placeholder AI grading logic
def grade_response(student_response, rubrix):


    prompt = f"Grade the following student response based on the rubric:\n\nRubric:\n{rubrix}\n\nStudent Response:\n{student_response}\n"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt}
            ]
        }
        ],
        max_tokens=500
        )

    grade = response.choices[0].message.content

    return grade

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

        question_paper_filename = secure_filename(question_paper.filename)
        rubric_file_filename = secure_filename(rubric_file.filename)

        question_paper.save(os.path.join(app.config['TEACHER_FOLDER'], question_paper_filename))
        rubric_file.save(os.path.join(app.config['TEACHER_FOLDER'], rubric_file_filename))

        return jsonify({
            'message': 'Question paper and rubric uploaded successfully!',
            'question_paper': question_paper_filename,
            'rubric_file': rubric_file_filename
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

        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['STUDENT_FOLDER'], filename))

        rubric_path = None
        for f in os.listdir(app.config['TEACHER_FOLDER']):
            if f.endswith('rubric.txt') or f.endswith('rubrix'):  # Ensure rubric file is located
                rubric_path = os.path.join(app.config['TEACHER_FOLDER'], f)
                break

        if not rubric_path:
            return jsonify({'error': 'Rubric file not found! Please upload it first.'}), 400

        with open(rubric_path, 'r') as f:
            rubrix = f.read()

        with open(os.path.join(app.config['STUDENT_FOLDER'], filename), 'r') as f:
            student_response = f.read()

        grade = grade_response(student_response, rubrix)

        return jsonify({'grade': grade}), 200
    return render_template('upload_student.html')

if __name__ == '__main__':
    app.run(debug=True)
