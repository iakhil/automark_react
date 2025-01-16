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
    # Convert PDF to images
    images = convert_from_bytes(pdf_file.read(), dpi=300)
    uploaded_urls = []

    for i, image in enumerate(images):
        # Save each page to a BytesIO object
        img_byte_array = BytesIO()
        image.save(img_byte_array, format='JPEG')
        img_byte_array.seek(0)

        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            img_byte_array,
            folder=folder,
            public_id=f"{secure_filename(pdf_file.filename).rsplit('.', 1)[0]}_page_{i + 1}"
        )
        uploaded_urls.append(upload_result['url'])

    return uploaded_urls


@app.route('/upload_teacher', methods=['GET', 'POST'])
def upload_teacher():
    if request.method == 'POST':
        # Check for all required files
        if 'file' not in request.files or 'rubric_file' not in request.files or 'answer_sheet' not in request.files:
            uploaded_files = cloudinary.api.resources(type="upload", prefix="teachers")
            file_list = [(resource['public_id'], resource['url']) for resource in uploaded_files.get('resources', [])]
            return render_template('upload_teacher.html', message='All three files are required!', files=file_list)

        question_paper = request.files['file']
        rubric_file = request.files['rubric_file']
        answer_sheet = request.files['answer_sheet']

        if question_paper.filename == '' or rubric_file.filename == '' or answer_sheet.filename == '':
            uploaded_files = cloudinary.api.resources(type="upload", prefix="teachers")
            file_list = [(resource['public_id'], resource['url']) for resource in uploaded_files.get('resources', [])]
            return render_template('upload_teacher.html', message='No file selected!', files=file_list)

        # Convert and upload Question Paper PDF
        question_paper_urls = convert_pdf_to_image_and_upload(question_paper, folder="teachers/question_papers")
        
        # Convert and upload Rubric PDF
        rubric_urls = convert_pdf_to_image_and_upload(rubric_file, folder="teachers/rubrics")
        
        # Convert and upload Student Answer Sheet PDF
        answer_sheet_urls = convert_pdf_to_image_and_upload(answer_sheet, folder="teachers/answer_sheets")

        # Fetch the updated list of uploaded files
        uploaded_files = cloudinary.api.resources(type="upload", prefix="teachers")
        file_list = [(resource['public_id'], resource['url']) for resource in uploaded_files.get('resources', [])]

        # Log the uploaded URLs for debugging
        print(f"Question Paper URLs: {question_paper_urls}")
        print(f"Rubric URLs: {rubric_urls}")
        print(f"Answer Sheet URLs: {answer_sheet_urls}")

        return render_template(
            'upload_teacher.html',
            message='Uploaded successfully',
            files=file_list
        )

    # Fetch already uploaded files for the teacher
    uploaded_files = cloudinary.api.resources(type="upload", prefix="teachers")
    file_list = [(resource['public_id'], resource['url']) for resource in uploaded_files.get('resources', [])]

    return render_template('upload_teacher.html', files=file_list)


@app.route('/upload_student', methods=['GET', 'POST'])
def upload_student():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'File is required!'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected!'}), 400

        # Convert student response PDF to images and upload to Cloudinary
        student_response_urls = convert_pdf_to_image_and_upload(file, folder="students")

        # Placeholder: Fetch rubric content and student response content from Cloudinary
        rubrix = "Example rubric content fetched from Cloudinary"
        student_response = "Example student response fetched from Cloudinary"

        # Grade the response
        grade = grade_response(student_response, rubrix)

        return jsonify({'grade': grade, 'response_urls': student_response_urls}), 200

    return render_template('upload_student.html')

@app.route('/grade', methods=['POST'])
def grade():
    try:
        # Parse JSON data from the request
        data = request.json
        question_paper_url = data.get('question_paper_url')
        marking_scheme_url = data.get('marking_scheme_url')
        student_response_url = data.get('student_response_url')
        prompt = data.get('prompt', (
            "You are a teacher grading a student's work. "
            "Here's the question paper, marking scheme, and the student's response. "
            "Evaluate the student's response based on the provided materials, assign a score for each individual question."
        ))

        # Validate input URLs
        if not question_paper_url or not marking_scheme_url or not student_response_url:
            return jsonify({"status": "error", "message": "All file URLs are required!"}), 400

        # Download and process the question paper (PDF)
        question_paper_response = requests.get(question_paper_url)
        if question_paper_response.status_code != 200:
            return jsonify({"status": "error", "message": "Failed to fetch question paper!"}), 400

        # Extract text from the question paper PDF
        question_paper_text = extract_pdf_text(BytesIO(question_paper_response.content))

        # Download and process the marking scheme (image)
        marking_scheme_response = requests.get(marking_scheme_url)
        marking_scheme_content_type = marking_scheme_response.headers.get('Content-Type')
        if not marking_scheme_content_type.startswith('image/'):
            return jsonify({"status": "error", "message": f"Invalid image type for marking scheme: {marking_scheme_content_type}"}), 400

        marking_scheme_base64 = convert_image_to_base64(marking_scheme_url)

        # Download and process the student response (image)
        student_response_response = requests.get(student_response_url)
        student_response_content_type = student_response_response.headers.get('Content-Type')
        if not student_response_content_type.startswith('image/'):
            return jsonify({"status": "error", "message": f"Invalid image type for student response: {student_response_content_type}"}), 400

        student_response_base64 = convert_image_to_base64(student_response_url)

        # Use OpenAI Chat Completion API to grade the response
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "text", "text": f"Question Paper:\n{question_paper_text}"},
                        {"type": "image_url", "image_url": {"url": marking_scheme_base64}},
                        {"type": "image_url", "image_url": {"url": student_response_base64}},
                    ],
                }
            ],
            max_tokens=500,
        )

        # Extract and return the grading result
        grading_result = response.choices[0].message.content
        return jsonify({"status": "success", "result": grading_result})

    except Exception as e:
        # Handle errors gracefully
        return jsonify({"status": "error", "message": str(e)}), 500


# Helper function: Extract text from a PDF file
def extract_pdf_text(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text


if __name__ == '__main__':
    app.run(debug=True)
