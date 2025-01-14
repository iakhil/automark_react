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

if __name__ == '__main__':
    app.run(debug=True)
