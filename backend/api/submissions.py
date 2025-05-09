from flask import Blueprint, request, jsonify
from utils import login_required
from services import SubmissionService, ExamService

# Create a blueprint for submission routes
submission_bp = Blueprint('submissions', __name__)

@submission_bp.route('/api/submit-answer', methods=['POST'])
@login_required(role='student')
def submit_answer():
    """Submit an answer for an exam"""
    if 'answer_sheet' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded!'}), 400

    exam_code = request.form.get('exam_code')
    if not exam_code:
        return jsonify({'success': False, 'message': 'Exam code is required!'}), 400

    answer_sheet = request.files['answer_sheet']
    if answer_sheet.filename == '':
        return jsonify({'success': False, 'message': 'No file selected!'}), 400

    # Submit the answer
    success, result = SubmissionService.submit_answer(exam_code, answer_sheet)
    
    if success:
        return jsonify({
            'success': True,
            'message': 'Answer submitted successfully!',
            'submission_id': result.id
        })
    else:
        return jsonify({'success': False, 'message': f'Error submitting answer: {result}'}), 400

@submission_bp.route('/api/submissions', methods=['GET'])
@login_required(role='student')
def get_student_submissions():
    """Get all submissions for the current student"""
    submissions = SubmissionService.get_student_submissions()
    
    return jsonify({
        'success': True,
        'submissions': submissions
    })

@submission_bp.route('/api/teacher/submissions', methods=['GET'])
@login_required(role='teacher')
def get_teacher_submissions():
    """Get all submissions for exams created by the current teacher"""
    from flask import session
    
    # Debug authentication
    print(f"Authenticated request to /api/teacher/submissions")
    print(f"Session: {dict(session)}")
    
    submissions = ExamService.get_teacher_submissions()
    
    print(f"Retrieved {len(submissions)} submissions for teacher {session.get('user_id')}")
    
    return jsonify({
        'success': True,
        'submissions': submissions
    })

@submission_bp.route('/api/publish_grade/<int:submission_id>', methods=['POST'])
@login_required(role='teacher')
def publish_grade(submission_id):
    """Publish a grade for a submission"""
    success, result = SubmissionService.publish_grade(submission_id)
    
    if success:
        return jsonify({
            'success': True,
            'message': 'Grade published successfully!'
        })
    else:
        return jsonify({'success': False, 'message': f'Error publishing grade: {result}'}), 400

@submission_bp.route('/api/update_grade/<int:submission_id>', methods=['POST'])
@login_required(role='teacher')
def update_grade(submission_id):
    """Update a grade for a submission"""
    data = request.json
    updated_grade = data.get('grade')
    
    if not updated_grade:
        return jsonify({'success': False, 'message': 'No grade content provided'}), 400
        
    success, result = SubmissionService.update_grade(submission_id, updated_grade)
    
    if success:
        return jsonify({
            'success': True,
            'message': 'Grade updated successfully!'
        })
    else:
        return jsonify({'success': False, 'message': f'Error updating grade: {result}'}), 400

@submission_bp.route('/api/test-grading', methods=['POST'])
def test_grading():
    """Test endpoint for the grading functionality"""
    from utils import grade_response
    
    data = request.json
    student_response = data.get('student_response', '')
    rubric = data.get('rubric', '')
    
    if not student_response or not rubric:
        return jsonify({
            'success': False,
            'message': 'Both student_response and rubric are required'
        }), 400
    
    try:
        # Call the grading function
        grade = grade_response(student_response, rubric)
        
        return jsonify({
            'success': True,
            'grade': grade
        })
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        
        return jsonify({
            'success': False,
            'message': f'Error during grading: {str(e)}',
            'traceback': error_traceback
        }), 500 