from flask import session
from models import Submission, Exam, User
from extensions import db
from utils import save_file, extract_rubric_text, extract_pdf_text, grade_response
import time

class SubmissionService:
    """Service for handling submission-related operations"""
    
    @staticmethod
    def submit_answer(exam_code, answer_sheet, student_id=None):
        """
        Submit an answer for a specific exam
        
        Args:
            exam_code (str): The exam code
            answer_sheet: The answer sheet file
            student_id (int, optional): Student's ID. If not provided, uses the current user's ID.
            
        Returns:
            tuple: (success, submission or error_message)
        """
        if student_id is None:
            student_id = session.get('user_id')
        
        # Check if the exam exists
        exam = Exam.query.filter_by(exam_code=exam_code).first()
        if not exam:
            return False, "Invalid exam code"
        
        try:
            # Upload the answer sheet to Cloudinary
            answer_sheet_url = save_file(answer_sheet)
            if not answer_sheet_url:
                return False, "Error uploading answer sheet"
            
            # Create submission record
            submission = Submission(
                student_id=student_id,
                exam_id=exam.id,
                answer_sheet_file=answer_sheet_url
            )
            
            db.session.add(submission)
            db.session.commit()
            
            # Start the grading process in the background (simplified for now)
            # In a real implementation, this should be a background task
            try:
                print(f"Starting grading process for submission {submission.id}...")
                
                # We now pass the URLs directly to the grade_response function
                rubric_url = exam.rubric_file
                answer_sheet_url = submission.answer_sheet_file
                
                print(f"Sending URLs for grading... Rubric: {rubric_url}, Answer sheet: {answer_sheet_url}")
                
                # Grade the response using the URLs
                grading_result = grade_response(answer_sheet_url, rubric_url)
                print(f"Grading completed, result length: {len(grading_result)}")
                
                # Update the submission with the grade
                submission.grade = grading_result
                db.session.commit()
                print(f"Submission {submission.id} updated with grade")
                
            except Exception as grading_error:
                print(f"Error during grading: {str(grading_error)}")
                import traceback
                print(traceback.format_exc())
                # Don't fail the submission if grading fails
                # Just continue without a grade
                submission.grade = f"<p>Grading failed: {str(grading_error)}</p>"
                db.session.commit()
            
            return True, submission
            
        except Exception as e:
            print(f"Error submitting answer: {str(e)}")
            import traceback
            print(traceback.format_exc())
            db.session.rollback()
            return False, str(e)
    
    @staticmethod
    def get_student_submissions(student_id=None):
        """
        Get all submissions by a specific student
        
        Args:
            student_id (int, optional): Student's ID. If not provided, uses the current user's ID.
            
        Returns:
            list: List of submissions with exam information
        """
        if student_id is None:
            student_id = session.get('user_id')
            
        # Query all submissions by this student
        submissions_query = (Submission.query
                           .join(Exam)
                           .filter(Submission.student_id == student_id)
                           .order_by(Submission.submitted_at.desc()))
        
        submissions = submissions_query.all()
        
        # Format the submissions for API response
        formatted_submissions = []
        for submission in submissions:
            formatted_submissions.append({
                'id': submission.id,
                'exam_title': submission.exam.title,
                'exam_code': submission.exam.exam_code,
                'submitted_at': submission.submitted_at.isoformat(),
                'is_published': submission.is_published,
                'grade': submission.grade if submission.is_published else None,
                'answer_sheet_url': submission.answer_sheet_file
            })
            
        return formatted_submissions
    
    @staticmethod
    def publish_grade(submission_id, teacher_id=None):
        """
        Publish a grade for a submission
        
        Args:
            submission_id (int): The submission ID
            teacher_id (int, optional): Teacher's ID. If not provided, uses the current user's ID.
            
        Returns:
            tuple: (success, submission or error_message)
        """
        if teacher_id is None:
            teacher_id = session.get('user_id')
            
        # Get the submission
        submission = Submission.query.get(submission_id)
        if not submission:
            return False, "Submission not found"
            
        # Check if the teacher owns the exam
        if submission.exam.teacher_id != teacher_id:
            return False, "Unauthorized access"
            
        try:
            # Publish the grade
            submission.is_published = True
            db.session.commit()
            
            return True, submission
            
        except Exception as e:
            print(f"Error publishing grade: {str(e)}")
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def update_grade(submission_id, updated_grade, teacher_id=None):
        """
        Update a grade for a submission
        
        Args:
            submission_id (int): The submission ID
            updated_grade (str): The updated grade content (HTML)
            teacher_id (int, optional): Teacher's ID. If not provided, uses the current user's ID.
            
        Returns:
            tuple: (success, submission or error_message)
        """
        if teacher_id is None:
            teacher_id = session.get('user_id')
            
        # Get the submission
        submission = Submission.query.get(submission_id)
        if not submission:
            return False, "Submission not found"
            
        # Check if the teacher owns the exam
        if submission.exam.teacher_id != teacher_id:
            return False, "Unauthorized access"
            
        try:
            # Update the grade
            submission.grade = updated_grade
            db.session.commit()
            
            return True, submission
            
        except Exception as e:
            print(f"Error updating grade: {str(e)}")
            db.session.rollback()
            return False, str(e) 