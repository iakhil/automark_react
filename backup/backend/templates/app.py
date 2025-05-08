from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
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
from models import db, User, Exam, Submission
import random
import string
from functools import wraps
import os

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
CORS(app)
load_dotenv()

db.init_app(app)

# Create all database tables
with app.app_context():
    db.create_all()

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

# Authentication decorator
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash('Unauthorized access')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['role'] = user.role
            return redirect(url_for(f'{user.role}_page'))
        
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        user = User(username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/teacher', methods=['GET', 'POST'])
@login_required(role='teacher')
def teacher_page():
    if request.method == 'POST':
        if 'question_paper' not in request.files or 'rubric_file' not in request.files:
            flash('Both files are required!')
            return redirect(url_for('teacher_page'))

        question_paper = request.files['question_paper']
        rubric_file = request.files['rubric_file']
        title = request.form.get('title')

        if question_paper.filename == '' or rubric_file.filename == '':
            flash('No file selected!')
            return redirect(url_for('teacher_page'))

        # Generate unique exam code
        exam_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        # Upload files to Cloudinary
        question_paper_urls = convert_pdf_to_image_and_upload(question_paper, f"teachers/{exam_code}/question_papers")
        rubric_urls = convert_pdf_to_image_and_upload(rubric_file, f"teachers/{exam_code}/rubrics")

        # Create new exam
        exam = Exam(
            title=title,
            teacher_id=session['user_id'],
            question_paper_url=question_paper_urls[0],  # Store first page URL
            rubric_url=rubric_urls[0],  # Store first page URL
            exam_code=exam_code
        )
        db.session.add(exam)
        db.session.commit()

        flash(f'Exam created successfully! Exam Code: {exam_code}')
        return redirect(url_for('teacher_page'))

    # Get all exams created by this teacher
    exams = Exam.query.filter_by(teacher_id=session['user_id']).all()
    return render_template('teacher.html', exams=exams)

@app.route('/student', methods=['GET', 'POST'])
@login_required(role='student')
def student_page():
    if request.method == 'POST':
        if 'answer_sheet' not in request.files:
            flash('Answer sheet is required!')
            return redirect(url_for('student_page'))

        exam_code = request.form.get('exam_code')
        answer_sheet = request.files['answer_sheet']

        if answer_sheet.filename == '':
            flash('No file selected!')
            return redirect(url_for('student_page'))

        # Verify exam code
        exam = Exam.query.filter_by(exam_code=exam_code).first()
        if not exam:
            flash('Invalid exam code!')
            return redirect(url_for('student_page'))

        # Check if student has already submitted
        existing_submission = Submission.query.filter_by(
            student_id=session['user_id'],
            exam_id=exam.id
        ).first()
        
        if existing_submission:
            flash('You have already submitted for this exam!')
            return redirect(url_for('student_page'))

        # Upload answer sheet
        answer_sheet_urls = convert_pdf_to_image_and_upload(
            answer_sheet, 
            f"students/{exam_code}/{session['user_id']}/answers"
        )

        # Grade the answer using GPT-4 Vision
        content = [
            {"type": "text", "text": "Grade this student's answer based on the rubric provided. Provide specific feedback and marks for each question."}
        ]
        content.append({"type": "image_url", "image_url": {"url": exam.rubric_url}})
        for url in answer_sheet_urls:
            content.append({"type": "image_url", "image_url": {"url": url}})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": content}],
            max_tokens=1000
        )

        grade = response.choices[0].message.content.strip()

        # Save submission
        submission = Submission(
            student_id=session['user_id'],
            exam_id=exam.id,
            answer_sheet_url=answer_sheet_urls[0],
            grade=grade
        )
        db.session.add(submission)
        db.session.commit()

        return render_template('student.html', grade=grade)

    # Get student's submissions
    submissions = Submission.query.filter_by(student_id=session['user_id']).all()
    return render_template('student.html', submissions=submissions)

if __name__ == '__main__':
    app.run(debug=True)
 