from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import os
from flask_cors import CORS
import cloudinary
import cloudinary.api
import cloudinary.uploader
from dotenv import load_dotenv
from pdf2image import convert_from_bytes, convert_from_path
from io import BytesIO
from openai import OpenAI
import requests
from PyPDF2 import PdfReader
from models import db, User, Exam, Submission
import random
import string
from functools import wraps
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import tempfile
from PIL import Image
import fitz  # PyMuPDF
import io

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///exam_portal.db'
CORS(app, 
     supports_credentials=True, 
     origins=['http://localhost:5000', 'http://127.0.0.1:5000', 'http://localhost:3000'],
     allow_headers=['Content-Type'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
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

# Add this function to create a session with retries
def create_session_with_retry():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,  # number of retries
        backoff_factor=1,  # wait 1, 2, 4 seconds between retries
        status_forcelist=[429, 500, 502, 503, 504]  # HTTP status codes to retry on
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# Update the convert_pdf_to_image_and_upload function
def convert_pdf_to_image_and_upload(pdf_file, folder):
    try:
        # Read PDF content
        pdf_content = pdf_file.read()
        pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
        uploaded_urls = []

        # Convert each page to image
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            
            # Get page as image with higher resolution
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
            
            # Convert to PIL Image
            img_data = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Save image to bytes
            img_byte_array = io.BytesIO()
            img_data.save(img_byte_array, format='JPEG', quality=95)
            img_byte_array.seek(0)

            # Upload to Cloudinary with retries
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    upload_result = cloudinary.uploader.upload(
                        img_byte_array,
                        folder=folder,
                        quality='auto:best',
                        fetch_format='auto',
                        timeout=30,
                        public_id=f"{secure_filename(pdf_file.filename).rsplit('.', 1)[0]}_page_{page_num + 1}"
                    )
                    uploaded_urls.append(upload_result['url'])
                    break
                except Exception as upload_error:
                    if attempt == max_attempts - 1:
                        raise upload_error
                    time.sleep(2 ** attempt)

        pdf_document.close()
        return uploaded_urls

    except Exception as e:
        print(f"PDF processing error: {str(e)}")
        raise Exception(f"Failed to process the PDF file: {str(e)}")

# Helper function: Extract text from a PDF file
def extract_pdf_text(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Update the extract_rubric_text function
def extract_rubric_text(pdf_url):
    try:
        # Create session with retry mechanism
        session = create_session_with_retry()
        
        # Download PDF with retry mechanism
        response = session.get(pdf_url, timeout=30)
        response.raise_for_status()
        
        # Read PDF content
        pdf_content = response.content
        pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
        
        text = ""
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            text += page.get_text()
        
        pdf_document.close()
        return text
        
    except Exception as e:
        print(f"Rubric extraction error: {str(e)}")
        raise Exception(f"Failed to process rubric: {str(e)}")

# Authentication decorator
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login_page'))
            if role and session.get('role') != role:
                flash('Unauthorized access')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['role'] = user.role
            
            if user.role == 'teacher':
                return redirect(url_for('teacher_page'))
            return redirect(url_for('student_page'))
        
        flash('Invalid username or password')
        return redirect(url_for('index'))
    
    # GET request
    if 'user_id' in session:
        if session['role'] == 'teacher':
            return redirect(url_for('teacher_page'))
        return redirect(url_for('student_page'))
    return render_template('login.html')

@app.route('/register', methods=['GET'])
def register_page():
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

        try:
            # Upload files to Cloudinary and get all page URLs
            question_paper_urls = convert_pdf_to_image_and_upload(
                question_paper, 
                f"teachers/{exam_code}/question_papers"
            )
            rubric_urls = convert_pdf_to_image_and_upload(
                rubric_file, 
                f"teachers/{exam_code}/rubrics"
            )

            # Create new exam with all page URLs
            exam = Exam(
                title=title,
                teacher_id=session['user_id'],
                question_paper_urls=question_paper_urls,  # Store all URLs
                rubric_urls=rubric_urls,  # Store all URLs
                exam_code=exam_code
            )
            db.session.add(exam)
            db.session.commit()

            flash(f'Exam created successfully! Exam Code: {exam_code}')
            return redirect(url_for('teacher_page'))
            
        except Exception as e:
            flash(f'Error creating exam: {str(e)}')
            return redirect(url_for('teacher_page'))

    # Get all submissions for exams created by this teacher
    submissions = (Submission.query
                  .join(Exam)
                  .join(User, Submission.student_id == User.id)
                  .filter(Exam.teacher_id == session['user_id'])
                  .order_by(Submission.submitted_at.desc())
                  .all())

    # Get teacher's exams
    exams = Exam.query.filter_by(teacher_id=session['user_id']).all()
    
    return render_template('teacher.html', exams=exams, submissions=submissions)

@app.route('/student', methods=['GET', 'POST'])
@login_required(role='student')
def student_page():
    if request.method == 'POST':
        if 'answer_sheet' not in request.files:
            flash('Answer sheet is required!', 'error')
            return redirect(url_for('student_page'))

        exam_code = request.form.get('exam_code')
        answer_sheet = request.files['answer_sheet']

        if answer_sheet.filename == '':
            flash('No file selected!', 'error')
            return redirect(url_for('student_page'))

        # Verify exam code
        exam = Exam.query.filter_by(exam_code=exam_code).first()
        if not exam:
            flash('Invalid exam code!', 'error')
            return redirect(url_for('student_page'))

        # Check if student has already submitted
        existing_submission = Submission.query.filter_by(
            student_id=session['user_id'],
            exam_id=exam.id
        ).first()
        
        if existing_submission:
            flash('You have already submitted for this exam!', 'error')
            return redirect(url_for('student_page'))

        try:
            # Convert and upload answer sheet
            answer_sheet_urls = convert_pdf_to_image_and_upload(
                answer_sheet, 
                f"students/{exam_code}/{session['user_id']}/answers"
            )

            # Extract rubric text
            rubric_text = extract_rubric_text(exam.rubric_url)

            # Prepare content for GPT-4 Vision
            content = [
                {
                    "type": "text",
                    "text": f"""Grade this handwritten answer sheet based on the following rubric:

                    RUBRIC:
                    {rubric_text}

                    Format your response exactly as follows:

                    ### SECTION A: [SECTION NAME] ([TOTAL MARKS])
                    
                    **Q1 (i)**: [1-2 sentence specific feedback] - [marks]
                    **Q1 (ii)**: [1-2 sentence specific feedback] - [marks]
                    
                    Keep feedback concise and specific to each subquestion. 
                    Follow the rubric strictly for marking.
                    For each subquestion, provide:
                    1. What was done correctly/incorrectly
                    2. Marks awarded based on the rubric criteria
                    
                    Note: The answer sheet is handwritten. Please analyze the handwritten text carefully."""
                }
            ]

            # Add all pages of the answer sheet as high-quality images
            for url in answer_sheet_urls:
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": url,
                        "detail": "high"  # Request high detail analysis for handwriting
                    }
                })

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": content}],
                max_tokens=1000
            )

            grade = response.choices[0].message.content.strip()

            # Save submission with all page URLs
            submission = Submission(
                student_id=session['user_id'],
                exam_id=exam.id,
                answer_sheet_url=answer_sheet_urls[0],  # Store first page URL
                grade=grade
            )
            db.session.add(submission)
            db.session.commit()

            flash('Answer sheet submitted successfully!', 'success')
            return redirect(url_for('student_page'))

        except Exception as e:
            flash(f'Error processing PDF file: {str(e)}', 'error')
            print(f"Error details: {str(e)}")  # For debugging
            return redirect(url_for('student_page'))

    # Get student's submissions
    submissions = Submission.query.filter_by(student_id=session['user_id']).all()
    return render_template('student.html', submissions=submissions)

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    
    if User.query.filter_by(username=username).first():
        return jsonify({
            'success': False,
            'message': 'Username already exists'
        }), 400
    
    user = User(username=username, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Registration successful'
    })

@app.route('/api/submit-answer', methods=['POST'])
@login_required(role='student')
def api_submit_answer():
    if 'answer_sheet' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'}), 400

    exam_code = request.form.get('exam_code')
    answer_sheet = request.files['answer_sheet']

    # ... rest of submission logic ...
    return jsonify({
        'success': True,
        'message': 'Answer sheet submitted successfully!'
    })

@app.route('/api/submissions', methods=['GET'])
@login_required(role='student')
def api_get_submissions():
    submissions = Submission.query.filter_by(student_id=session['user_id']).all()
    return jsonify({
        'success': True,
        'submissions': [
            {
                'id': sub.id,
                'exam_title': sub.exam.title,
                'exam_code': sub.exam.exam_code,
                'submitted_at': sub.submitted_at.strftime('%Y-%m-%d %H:%M:%S'),
                'grade': sub.grade,
                'answer_sheet_url': sub.answer_sheet_url
            }
            for sub in submissions
        ]
    })

if __name__ == '__main__':
    app.run(debug=True)
 