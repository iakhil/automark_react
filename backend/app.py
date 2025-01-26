from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import os
from flask_cors import CORS
import cloudinary
import cloudinary.api
import cloudinary.uploader
from dotenv import load_dotenv
from pdf2image import convert_from_bytes
from io import BytesIO
from openai import OpenAI
import requests
from PyPDF2 import PdfReader

app = Flask(__name__, static_folder='static')
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
    print(f"Student response: {student_response}")
    prompt = f"Grade the following student response based on the rubric. Provide the total marks obtained for each question. Keep your remarks succinct.:\n\nRubric:\n{rubrix}\n\nStudent Response:\n{student_response}\n"
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

# Helper function: Convert PDF to image and upload to Cloudinary
def convert_pdf_to_image_and_upload(pdf_file, folder):
    images = convert_from_bytes(pdf_file.read(), dpi=300)
    uploaded_urls = []

    for i, image in enumerate(images):
        img_byte_array = BytesIO()
        image.save(img_byte_array, format='JPEG')
        img_byte_array.seek(0)

        upload_result = cloudinary.uploader.upload(
            img_byte_array,
            folder=folder,
            public_id=f"{secure_filename(pdf_file.filename).rsplit('.', 1)[0]}_page_{i + 1}"
        )
        uploaded_urls.append(upload_result['url'])

    return uploaded_urls

# Helper function: Extract text from a PDF file
def extract_pdf_text(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/teacher', methods=['GET', 'POST'])
def teacher_page():
    if request.method == 'POST':
        # Validate file inputs
        if 'question_paper' not in request.files or 'rubric_file' not in request.files:
            uploaded_files = cloudinary.api.resources(type="upload", prefix="teachers")
            file_list = [(resource['public_id'], resource['url']) for resource in uploaded_files.get('resources', [])]
            return render_template('teacher.html', message='Both files are required!', files=file_list)

        question_paper = request.files['question_paper']
        rubric_file = request.files['rubric_file']

        # Ensure files are provided
        if question_paper.filename == '' or rubric_file.filename == '':
            uploaded_files = cloudinary.api.resources(type="upload", prefix="teachers")
            file_list = [(resource['public_id'], resource['url']) for resource in uploaded_files.get('resources', [])]
            return render_template('teacher.html', message='No file selected!', files=file_list)

        # Convert and upload PDFs as images
        question_paper_urls = convert_pdf_to_image_and_upload(question_paper, folder="teachers/question_papers")
        rubric_urls = convert_pdf_to_image_and_upload(rubric_file, folder="teachers/rubrics")

        # Store the URLs in session or database for later use
        # For now, we'll just display them
        return render_template(
            'teacher.html',
            message='Files uploaded successfully!',
            question_paper_urls=question_paper_urls,
            rubric_urls=rubric_urls
        )

    return render_template('teacher.html')

@app.route('/student', methods=['GET', 'POST'])
def student_page():
    if request.method == 'POST':
        if 'answer_sheet' not in request.files:
            return render_template('student.html', message='Answer sheet is required!')

        answer_sheet = request.files['answer_sheet']

        if answer_sheet.filename == '':
            return render_template('student.html', message='No file selected!')

        # Convert and upload answer sheet
        answer_sheet_urls = convert_pdf_to_image_and_upload(answer_sheet, folder="students/answers")

        # Get the latest rubric and grade the answer
        # Note: You'll need to implement a way to fetch the correct rubric for this specific test
        rubric_files = cloudinary.api.resources(type="upload", prefix="teachers/rubrics")
        if not rubric_files.get('resources'):
            return render_template('student.html', message='No rubric found for grading!')

        rubric_url = rubric_files['resources'][-1]['url']  # Get the latest rubric

        content = [
            {"type": "text", "text": "Grade this student's answer based on the rubric provided. Provide specific feedback and marks for each question."}
        ]

        # Add rubric image URL
        content.append({"type": "image_url", "image_url": {"url": rubric_url}})

        # Add answer sheet URLs
        for url in answer_sheet_urls:
            content.append({"type": "image_url", "image_url": {"url": url}})

        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[{"role": "user", "content": content}],
            max_tokens=1000
        )

        grade = response.choices[0].message.content.strip()

        return render_template(
            'student.html',
            message='Answer submitted and graded successfully!',
            grade=grade
        )

    return render_template('student.html')

if __name__ == '__main__':
    app.run(debug=True)
 