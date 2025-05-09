from extensions import db
from datetime import datetime

class Exam(db.Model):
    """
    Exam model representing a test created by a teacher
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_paper_file = db.Column(db.String(500), nullable=False)
    rubric_file = db.Column(db.String(500), nullable=False)
    exam_code = db.Column(db.String(6), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships defined in user.py and submission.py
    submissions = db.relationship('Submission', backref='exam', lazy=True)
    
    def to_dict(self):
        """
        Convert exam object to dictionary for API responses
        """
        return {
            'id': self.id,
            'title': self.title,
            'teacher_id': self.teacher_id,
            'exam_code': self.exam_code,
            'question_paper_file': self.question_paper_file,
            'rubric_file': self.rubric_file,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 