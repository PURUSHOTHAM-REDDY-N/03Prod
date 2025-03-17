"""
Update exam dates migration script.
This adds more specific 2025 A-level exam dates for Psychology (AQA), Biology (OCR A), and Chemistry (OCR A).
"""
from app import db, create_app
from app.models.curriculum import Subject, Exam
from datetime import datetime
from sqlalchemy import inspect

def run_migration():
    """Run the migration to update A-level exam dates."""
    app = create_app()
    with app.app_context():
        print("Updating A-level exam dates for 2025...")
        
        # Get relevant subjects
        psychology = Subject.query.filter_by(title="Psychology").first()
        biology = Subject.query.filter_by(title="Biology").first()
        chemistry = Subject.query.filter_by(title="Chemistry").first()
        
        # If subjects don't exist, create them
        if not psychology:
            psychology = Subject(title="Psychology", description="AQA Psychology A-level")
            db.session.add(psychology)
            print("Created Psychology subject")
        
        if not biology:
            biology = Subject(title="Biology", description="OCR A Biology A-level")
            db.session.add(biology)
            print("Created Biology subject")
            
        if not chemistry:
            chemistry = Subject(title="Chemistry", description="OCR A Chemistry A-level")
            db.session.add(chemistry)
            print("Created Chemistry subject")
            
        db.session.commit()
        
        # Remove any existing exams for these subjects
        for subject in [psychology, biology, chemistry]:
            Exam.query.filter_by(subject_id=subject.id).delete()
        
        # A-level exam dates for 2025 (these are estimates based on typical patterns)
        aqa_psychology_exams = [
            ("Paper 1: Introductory Topics in Psychology", "2025-05-14"),
            ("Paper 2: Psychology in Context", "2025-05-22"),
            ("Paper 3: Issues and Options in Psychology", "2025-06-04")
        ]
        
        ocr_a_biology_exams = [
            ("Paper 1: Biological Processes", "2025-05-15"),
            ("Paper 2: Biological Diversity", "2025-05-23"),
            ("Paper 3: Unified Biology", "2025-06-05")
        ]
        
        ocr_a_chemistry_exams = [
            ("Paper 1: Periodic Table, Elements and Physical Chemistry", "2025-05-19"),
            ("Paper 2: Synthesis and Analytical Techniques", "2025-05-27"),
            ("Paper 3: Unified Chemistry", "2025-06-09")
        ]
        
        # Add Psychology exams
        for title, date_str in aqa_psychology_exams:
            exam_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            exam = Exam(
                subject_id=psychology.id,
                title=f"Psychology: {title} (AQA)",
                exam_date=exam_date
            )
            db.session.add(exam)
            print(f"Added exam: {title} for Psychology on {date_str}")
        
        # Add Biology exams
        for title, date_str in ocr_a_biology_exams:
            exam_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            exam = Exam(
                subject_id=biology.id,
                title=f"Biology: {title} (OCR A)",
                exam_date=exam_date
            )
            db.session.add(exam)
            print(f"Added exam: {title} for Biology on {date_str}")
        
        # Add Chemistry exams
        for title, date_str in ocr_a_chemistry_exams:
            exam_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            exam = Exam(
                subject_id=chemistry.id,
                title=f"Chemistry: {title} (OCR A)",
                exam_date=exam_date
            )
            db.session.add(exam)
            print(f"Added exam: {title} for Chemistry on {date_str}")
        
        db.session.commit()
        print("A-level exam dates updated successfully!")

if __name__ == "__main__":
    run_migration() 