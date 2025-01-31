from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'teacher' or 'student'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_paper_url = db.Column(db.String(500), nullable=False)
    rubric_url = db.Column(db.String(500), nullable=False)
    exam_code = db.Column(db.String(10), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    answer_sheet_url = db.Column(db.String(500), nullable=False)
    grade = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, server_default=db.func.now()) 