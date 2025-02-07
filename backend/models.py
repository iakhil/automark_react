from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'teacher' or 'student'
    submissions = db.relationship('Submission', backref='student', lazy=True)
    exams = db.relationship('Exam', backref='teacher', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_paper_urls = db.Column(db.JSON, nullable=False)  # Store array of URLs
    rubric_urls = db.Column(db.JSON, nullable=False)  # Store array of URLs
    exam_code = db.Column(db.String(10), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    submissions = db.relationship('Submission', backref='exam', lazy=True)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    answer_sheet_urls = db.Column(db.JSON, nullable=False)  # Store array of URLs
    grade = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, server_default=db.func.now()) 