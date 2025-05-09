from extensions import db
from datetime import datetime

class Submission(db.Model):
    """
    Submission model representing a student's answer to an exam
    """
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    answer_sheet_file = db.Column(db.String(500), nullable=False)
    grade = db.Column(db.Text)
    is_published = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships defined in user.py and exam.py
    
    def to_dict(self):
        """
        Convert submission object to dictionary for API responses
        """
        return {
            'id': self.id,
            'student_id': self.student_id,
            'exam_id': self.exam_id,
            'answer_sheet_file': self.answer_sheet_file,
            'grade': self.grade,
            'is_published': self.is_published,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None
        } 