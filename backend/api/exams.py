from flask import Blueprint, request, jsonify
from utils import login_required
from services import ExamService

# Create a blueprint for exam routes
exam_bp = Blueprint('exams', __name__)

@exam_bp.route('/api/exams', methods=['GET'])
@login_required(role='teacher')
def get_exams():
    """Get all exams for the current teacher"""
    exams = ExamService.get_teacher_exams()
    
    # Convert exam objects to dictionaries
    exams_data = [exam.to_dict() for exam in exams]
    
    return jsonify({
        'success': True,
        'exams': exams_data
    })

@exam_bp.route('/api/create-exam', methods=['POST'])
@login_required(role='teacher')
def create_exam():
    """Create a new exam"""
    if 'question_paper' not in request.files or 'rubric_file' not in request.files:
        return jsonify({'success': False, 'message': 'Both files are required!'}), 400

    question_paper = request.files['question_paper']
    rubric_file = request.files['rubric_file']
    title = request.form.get('title')

    if question_paper.filename == '' or rubric_file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected!'}), 400

    if not title:
        return jsonify({'success': False, 'message': 'Title is required!'}), 400

    success, result = ExamService.create_exam(title, question_paper, rubric_file)
    
    if success:
        return jsonify({
            'success': True,
            'message': f'Exam created successfully! Exam Code: {result.exam_code}',
            'exam': result.to_dict()
        })
    else:
        return jsonify({'success': False, 'message': f'Error creating exam: {result}'}), 500 