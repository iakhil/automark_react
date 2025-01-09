from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import os
import openai

app = Flask(__name__)

# Configure upload folders
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TEACHER_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'teachers')
app.config['STUDENT_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'students')
os.makedirs(app.config['TEACHER_FOLDER'], exist_ok=True)
os.makedirs(app.config['STUDENT_FOLDER'], exist_ok=True)

# Placeholder AI grading logic
def grade_response(student_response, rubrix):
    # Use OpenAI API or a custom ML model for grading
    prompt = f"Grade the following student response based on the rubric:\n\nRubric:\n{rubrix}\n\nStudent Response:\n{student_response}\n"
    response = openai.Completion.create(
        model="gpt-4",
        prompt=prompt,
        max_tokens=500
    )
    return response.choices[0].text.strip()

# Route for teacher login and uploading question paper and rubric
@app.route('/upload_teacher', methods=['GET', 'POST'])
def upload_teacher():
    if request.method == 'POST':
        if 'file' not in request.files or 'rubrix' not in request.form:
            return jsonify({'error': 'File and rubric are required!'}), 400

        file = request.files['file']
        rubrix = request.form['rubrix']

        if file.filename == '':
            return jsonify({'error': 'No file selected!'}), 400

        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['TEACHER_FOLDER'], filename))

        with open(os.path.join(app.config['TEACHER_FOLDER'], 'rubrix.txt'), 'w') as f:
            f.write(rubrix)

        return jsonify({'message': 'Question paper and rubric uploaded successfully!'}), 200
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

        with open(os.path.join(app.config['TEACHER_FOLDER'], 'rubrix.txt'), 'r') as f:
            rubrix = f.read()

        with open(os.path.join(app.config['STUDENT_FOLDER'], filename), 'r') as f:
            student_response = f.read()

        grade = grade_response(student_response, rubrix)

        return jsonify({'grade': grade}), 200
    return render_template('upload_student.html')

if __name__ == '__main__':
    app.run(debug=True)
