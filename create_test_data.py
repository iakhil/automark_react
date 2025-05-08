import sys
sys.path.append('./backend')
from app import app, db, User, Exam, Submission
import datetime

# Add a test submission
with app.app_context():
    # Check if we have teachers and students
    teacher = User.query.filter_by(role='teacher').first()
    student = User.query.filter_by(role='student').first()
    
    if not teacher:
        print('Creating test teacher')
        teacher = User(username='teacher', role='teacher')
        teacher.set_password('teacher')
        db.session.add(teacher)
    else:
        print(f'Using existing teacher: {teacher.username}')
    
    if not student:
        print('Creating test student')
        student = User(username='student', role='student')
        student.set_password('student')
        db.session.add(student)
    else:
        print(f'Using existing student: {student.username}')
    
    # Create a test exam if none exists
    exam = Exam.query.filter_by(teacher_id=teacher.id).first()
    if not exam:
        print('Creating test exam')
        exam = Exam(
            title='Test Exam',
            teacher_id=teacher.id,
            question_paper_file='https://res.cloudinary.com/demo/image/upload/sample.pdf',
            rubric_file='https://res.cloudinary.com/demo/image/upload/sample.pdf',
            exam_code='TEST123'
        )
        db.session.add(exam)
    else:
        print(f'Using existing exam: {exam.title}')
    
    # Create a test submission if none exists
    if Submission.query.count() == 0:
        print('Creating test submission')
        submission = Submission(
            student_id=student.id,
            exam_id=exam.id,
            answer_sheet_file='https://res.cloudinary.com/demo/image/upload/sample.pdf',
            grade='<h3>SECTION A (10 marks)</h3><p><strong>Q1 (5)</strong>: Good answer - 4/5</p>',
            is_published=False,
            submitted_at=datetime.datetime.now()
        )
        db.session.add(submission)
    
    db.session.commit()
    
    # Print what we have
    exams = Exam.query.all()
    submissions = Submission.query.all()
    
    print(f'Database now has {len(exams)} exams and {len(submissions)} submissions')
    
    for sub in submissions:
        print(f'Submission {sub.id}: Student={sub.student.username}, Exam={sub.exam.title}, Published={sub.is_published}') 