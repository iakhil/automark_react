from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import os
from flask_cors import CORS
import cloudinary
import cloudinary.api
import cloudinary.uploader
from dotenv import load_dotenv
from openai import OpenAI

app = Flask(__name__)
CORS(app)
load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET")
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

@app.route('/upload_teacher', methods=['GET', 'POST'])
def upload_teacher():
    if request.method == 'POST':
        if 'file' not in request.files or 'rubric_file' not in request.files:
            # Render the page with an error message
            uploaded_files = cloudinary.api.resources(type="upload", prefix="teachers")
            file_list = [(resource['public_id'], resource['url']) for resource in uploaded_files.get('resources', [])]
            return render_template('upload_teacher.html', message='Both question paper and rubric files are required!', files=file_list)

        question_paper = request.files['file']
        rubric_file = request.files['rubric_file']

        if question_paper.filename == '' or rubric_file.filename == '':
            # Render the page with an error message
            uploaded_files = cloudinary.api.resources(type="upload", prefix="teachers")
            file_list = [(resource['public_id'], resource['url']) for resource in uploaded_files.get('resources', [])]
            return render_template('upload_teacher.html', message='No file selected!', files=file_list)

        # Upload files to Cloudinary
        cloudinary.uploader.upload(question_paper, folder="teachers")
        cloudinary.uploader.upload(rubric_file, folder="teachers")

        # Fetch the updated list of uploaded files
        uploaded_files = cloudinary.api.resources(type="upload", prefix="teachers")
        file_list = [(resource['public_id'], resource['url']) for resource in uploaded_files.get('resources', [])]

        print(f"UPLOADED FILES {uploaded_files}")

        # Render the page with a success message
        return render_template('upload_teacher.html', message='Uploaded successfully', files=file_list)

    # Fetch already uploaded files for the teacher
    uploaded_files = cloudinary.api.resources(type="upload", prefix="teachers")
    file_list = [(resource['public_id'], resource['url']) for resource in uploaded_files.get('resources', [])]

    return render_template('upload_teacher.html', files=file_list)


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
