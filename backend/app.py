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

@app.route('/upload_teacher', methods=['GET', 'POST'])
def upload_teacher():
    if request.method == 'POST':
        # Validate file inputs
        if 'file' not in request.files or 'rubric_file' not in request.files or 'answer_sheet' not in request.files:
            uploaded_files = cloudinary.api.resources(type="upload", prefix="teachers")
            file_list = [(resource['public_id'], resource['url']) for resource in uploaded_files.get('resources', [])]
            return render_template('upload_teacher.html', message='All three files are required!', files=file_list)

        question_paper = request.files['file']
        rubric_file = request.files['rubric_file']
        answer_sheet = request.files['answer_sheet']

        # Ensure files are provided
        if question_paper.filename == '' or rubric_file.filename == '' or answer_sheet.filename == '':
            uploaded_files = cloudinary.api.resources(type="upload", prefix="teachers")
            file_list = [(resource['public_id'], resource['url']) for resource in uploaded_files.get('resources', [])]
            return render_template('upload_teacher.html', message='No file selected!', files=file_list)

        # Convert and upload PDFs as images
        question_paper_urls = convert_pdf_to_image_and_upload(question_paper, folder="teachers/question_papers")
        rubric_urls = convert_pdf_to_image_and_upload(rubric_file, folder="teachers/rubrics")
        answer_sheet_urls = convert_pdf_to_image_and_upload(answer_sheet, folder="teachers/answer_sheets")

        # Call OpenAI API with the first page of the rubric and answer sheet
        rubric_image_url = rubric_urls[0]  # Use the first image URL
        answer_image_url = answer_sheet_urls[0]  # Use the first image URL

        # OpenAI API request
        prompt = {
            "role": "user",
            "content": [
                {"type": "text", "text": "Grade this student's answer based on the rubric provided. DO NOT USE ASTERISKS IN THE OUTPUT."},
                {"type": "image_url", "image_url": {"url": rubric_image_url}},
                {"type": "image_url", "image_url": {"url": answer_image_url}},
            ]
        }

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[prompt],
            max_tokens=1000
        )



        grade = response.choices[0].message.content.strip()

        print(f"Grade: {grade}")

        # Fetch updated list of uploaded files
        uploaded_files = cloudinary.api.resources(type="upload", prefix="teachers")
        file_list = [(resource['public_id'], resource['url']) for resource in uploaded_files.get('resources', [])]

        return render_template(
            'upload_teacher.html',
            message=f'Uploaded and graded successfully. Grade: {grade}',
            grade=grade,
            files=file_list
        )

    # Fetch already uploaded files for the teacher
    uploaded_files = cloudinary.api.resources(type="upload", prefix="teachers")
    file_list = [(resource['public_id'], resource['url']) for resource in uploaded_files.get('resources', [])]

    return render_template('upload_teacher.html', files=file_list)


if __name__ == '__main__':
    app.run(debug=True)
 