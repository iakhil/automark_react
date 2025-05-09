from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    """
    User model representing both teachers and students in the system
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'teacher' or 'student'
    
    # Relationships
    created_exams = db.relationship('Exam', backref='teacher', lazy=True,
                                  foreign_keys='Exam.teacher_id')
    student_submissions = db.relationship('Submission', backref='student', lazy=True,
                                       foreign_keys='Submission.student_id')
    
    def set_password(self, password):
        """
        Set password hash from plain text password
        """
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """
        Verify password against stored hash
        """
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """
        Convert user object to dictionary for API responses
        """
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role
        } 