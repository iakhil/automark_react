from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session, send_from_directory
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
from google import genai
import httpx
import os.path
import stripe
from datetime import datetime, timedelta
import os

load_dotenv()
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI']  = os.environ.get('DATABASE_URL')
app.config['UPLOAD_FOLDER'] = 'uploads'
CORS(app, 
     supports_credentials=True, 
     origins=['http://localhost:5000', 'http://127.0.0.1:5000', 'http://localhost:3000'],
     allow_headers=['Content-Type'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
load_dotenv()

# Add file upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize database
db.init_app(app)

# Create all database tables
with app.app_context():
    # Create tables if they don't exist
    db.create_all()
    
    # Create a test user only if it doesn't exist
    if not User.query.filter_by(username='test').first():
        test_user = User(username='test', role='teacher')
        test_user.set_password('test')
        db.session.add(test_user)
        db.session.commit()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET")
)

# Initialize Gemini
# genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# AI grading logic using the new OpenAI API structure
def grade_response(student_response, rubrix):
    print(f"Student response: {student_response}")
    prompt = f"Grade the following student response based on the rubric. Provide the total marks obtained for each question. Generate the response in the form of HTML. Keep your remarks succinct.:\n\nRubric:\n{rubrix}\n\nStudent Response:\n{student_response}\n"
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

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register_page'))
        
        user = User(username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('index'))
        
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Update the save_file function to upload to Cloudinary and return URL
def save_file(file):
    if file and allowed_file(file.filename):
        try:
            # Upload to Cloudinary
            response = cloudinary.uploader.upload(
                file,
                resource_type="raw",
                format="pdf"
            )
            return response['secure_url']
        except Exception as e:
            print(f"Cloudinary upload error: {str(e)}")
            return None
    return None

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
            # Upload files to Cloudinary
            question_paper_url = save_file(question_paper)
            rubric_url = save_file(rubric_file)

            if not question_paper_url or not rubric_url:
                flash('Error uploading files!')
                return redirect(url_for('teacher_page'))

            # Create new exam with Cloudinary URLs
            exam = Exam(
                title=title,
                teacher_id=session['user_id'],
                question_paper_file=question_paper_url,
                rubric_file=rubric_url,
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
            flash('No file uploaded!', 'error')
            return redirect(url_for('student_page'))

        exam_code = request.form.get('exam_code')
        answer_sheet = request.files['answer_sheet']

        if answer_sheet.filename == '':
            flash('No file selected!', 'error')
            return redirect(url_for('student_page'))

        exam = Exam.query.filter_by(exam_code=exam_code).first()
        if not exam:
            flash('Invalid exam code!', 'error')
            return redirect(url_for('student_page'))

        try:
            # Upload answer sheet to Cloudinary
            answer_sheet_url = save_file(answer_sheet)
            if not answer_sheet_url:
                flash('Error uploading answer sheet!', 'error')
                return redirect(url_for('student_page'))

            # Download PDFs from Cloudinary URLs
            rubric_response = httpx.get(exam.rubric_file)
            answer_response = httpx.get(answer_sheet_url)

            # Create prompt for grading
            prompt = """Grade this answer sheet according to the rubric provided. Format your response in HTML as follows:

<h3>SECTION [NAME] ([TOTAL] marks)</h3>
<p><strong>Q[number] ([max_marks])</strong>: [Brief feedback] - [awarded]/[max_marks]</p>

There could be multiple choice questions. For these, the student might write the option in their response, e.g. 'B'. 
In the rubric, for these questions, the correct option might be present, e.g. 'C'. If they mismatch, then deduct points for that question.
Directly start your response with the grading without any preamble."""

            # Request grading from Gemini using the PDFs as bytes
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    {
                        "parts": [
                            {"text": prompt},
                            {"inline_data": {
                                "mime_type": "application/pdf",
                                "data": rubric_response.content
                            }},
                            {"inline_data": {
                                "mime_type": "application/pdf",
                                "data": answer_response.content
                            }}
                        ]
                    }
                ]
            )

            grade = response.text.strip()
            print("DEBUG - Grade content:", grade)

            # Save submission with HTML directly
            submission = Submission(
                student_id=session['user_id'],
                exam_id=exam.id,
                answer_sheet_file=answer_sheet_url,
                grade=grade,
                is_published=False
            )
            db.session.add(submission)
            db.session.commit()

            flash('Answer sheet submitted successfully! Your grade will be visible once approved by the teacher.', 'success')
            return redirect(url_for('student_page'))

        except Exception as e:
            print(f"Client: {client}")
            flash(f'Error processing submission: {str(e)}', 'error')
            print(f"Error details: {str(e)}")
            return redirect(url_for('student_page'))

    # Only show published grades to students
    submissions = Submission.query.filter_by(student_id=session['user_id']).all()
    return render_template('student.html', submissions=submissions)

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
                'answer_sheet_urls': sub.answer_sheet_urls  # Return all URLs
            }
            for sub in submissions
        ]
    })

# New route for publishing grades
@app.route('/publish_grade/<int:submission_id>', methods=['POST'])
@login_required(role='teacher')
def publish_grade(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    
    # Verify the teacher owns this exam
    if submission.exam.teacher_id != session['user_id']:
        flash('Unauthorized access', 'error')
        return redirect(url_for('teacher_page'))
    
    submission.is_published = True
    db.session.commit()
    
    flash('Grade published successfully!', 'success')
    return redirect(url_for('teacher_page'))

# Add this new route to serve files from the uploads directory
@app.route('/uploads/<path:filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Add these routes for handling payments
@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

@app.route('/create-checkout-session', methods=['POST'])
@login_required()
def create_checkout_session():
    try:
        price_id = request.form.get('price_id')
        
        # Create or get Stripe customer
        user = User.query.get(session['user_id'])
        if not user.subscription or not user.subscription.stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.username,  # Assuming username is email
                metadata={'user_id': user.id}
            )
            customer_id = customer.id
        else:
            customer_id = user.subscription.stripe_customer_id

        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            success_url=url_for('payment_success', _external=True),
            cancel_url=url_for('payment_cancel', _external=True),
        )

        return jsonify({'sessionId': checkout_session.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 403

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.environ.get('STRIPE_WEBHOOK_SECRET')
        )

        if event.type == 'checkout.session.completed':
            session = event.data.object
            handle_checkout_session(session)
        elif event.type == 'invoice.paid':
            invoice = event.data.object
            handle_subscription_updated(invoice)
        elif event.type == 'invoice.payment_failed':
            invoice = event.data.object
            handle_payment_failed(invoice)

        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

def handle_checkout_session(session):
    customer_id = session.customer
    subscription_id = session.subscription
    user_id = stripe.Customer.retrieve(customer_id).metadata.user_id

    subscription = Subscription(
        user_id=user_id,
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription_id,
        plan_type='premium',  # Adjust based on the price_id
        status='active',
        current_period_end=datetime.fromtimestamp(
            stripe.Subscription.retrieve(subscription_id).current_period_end
        )
    )
    db.session.add(subscription)
    db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
 