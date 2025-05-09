from flask import session
from models import Exam, User, Submission
from extensions import db
from utils import save_file
import random
import string

class ExamService:
    """Service for handling exam-related operations"""
    
    @staticmethod
    def get_teacher_exams(teacher_id=None):
        """
        Get all exams created by a specific teacher
        
        Args:
            teacher_id (int, optional): Teacher's ID. If not provided, uses the current user's ID.
            
        Returns:
            list: List of exams
        """
        if teacher_id is None:
            teacher_id = session.get('user_id')
            
        exams = Exam.query.filter_by(teacher_id=teacher_id).all()
        return exams
    
    @staticmethod
    def create_exam(title, question_paper, rubric_file, teacher_id=None):
        """
        Create a new exam
        
        Args:
            title (str): Title of the exam
            question_paper: Question paper file
            rubric_file: Rubric file
            teacher_id (int, optional): Teacher's ID. If not provided, uses the current user's ID.
            
        Returns:
            tuple: (success, exam or error_message)
        """
        if teacher_id is None:
            teacher_id = session.get('user_id')
        
        # Generate unique exam code
        exam_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        try:
            # Upload files to Cloudinary
            question_paper_url = save_file(question_paper)
            rubric_url = save_file(rubric_file)
            
            if not question_paper_url or not rubric_url:
                return False, "Error uploading files"
            
            # Create new exam with Cloudinary URLs
            exam = Exam(
                title=title,
                teacher_id=teacher_id,
                question_paper_file=question_paper_url,
                rubric_file=rubric_url,
                exam_code=exam_code
            )
            
            db.session.add(exam)
            db.session.commit()
            
            return True, exam
            
        except Exception as e:
            print(f"Error creating exam: {str(e)}")
            db.session.rollback()
            return False, str(e)
    
    @staticmethod
    def get_exam_by_code(exam_code):
        """
        Get an exam by its code
        
        Args:
            exam_code (str): Exam code
            
        Returns:
            Exam: The exam if found, None otherwise
        """
        return Exam.query.filter_by(exam_code=exam_code).first()

    @staticmethod
    def get_teacher_submissions(teacher_id=None):
        """
        Get all submissions for exams created by a specific teacher
        
        Args:
            teacher_id (int, optional): Teacher's ID. If not provided, uses the current user's ID.
            
        Returns:
            list: List of submissions with student and exam information
        """
        if teacher_id is None:
            teacher_id = session.get('user_id')
            
        # Query all submissions for exams created by this teacher
        submissions_query = (Submission.query
                           .join(Exam)
                           .join(User, Submission.student_id == User.id)
                           .filter(Exam.teacher_id == teacher_id)
                           .order_by(Submission.submitted_at.desc()))
        
        submissions = submissions_query.all()
        
        # Format the submissions for API response
        formatted_submissions = []
        for submission in submissions:
            formatted_submissions.append({
                'id': submission.id,
                'student_name': submission.student.username,
                'exam_title': submission.exam.title,
                'exam_code': submission.exam.exam_code,
                'submitted_at': submission.submitted_at.isoformat(),
                'is_published': submission.is_published,
                'grade': submission.grade,
                'answer_sheet_url': submission.answer_sheet_file
            })
            
        return formatted_submissions 