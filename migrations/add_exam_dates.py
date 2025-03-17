"""
Add exam dates migration script.
This creates the exams table and adds example 2025 exam dates.
"""
from app import db, create_app
from app.models.curriculum import Subject, Exam
from datetime import datetime
from sqlalchemy import inspect

def run_migration():
    """Run the migration to add exam dates table and example 2025 exam dates."""
    app = create_app()
    with app.app_context():
        print("Creating exams table if it doesn't exist...")
        
        # Check if we need to create the table
        inspector = inspect(db.engine)
        if 'exams' not in inspector.get_table_names():
            Exam.__table__.create(db.engine)
            print("Exams table created.")
        else:
            print("Exams table already exists.")
        
        # Add some example 2025 exam dates
        # Get all subjects
        subjects = Subject.query.all()
        
        # Clear any existing exam dates
        Exam.query.delete()
        
        # Sample 2025 exam dates
        exam_dates = {
            # May 2025
            "Mathematics": [
                ("Mathematics Paper 1", "2025-05-12"),
                ("Mathematics Paper 2", "2025-05-19")
            ],
            "Physics": [
                ("Physics Paper 1", "2025-05-14"),
                ("Physics Paper 2", "2025-05-21")
            ],
            "Chemistry": [
                ("Chemistry Paper 1", "2025-05-16"),
                ("Chemistry Paper 2", "2025-05-23")
            ],
            # June 2025
            "Biology": [
                ("Biology Paper 1", "2025-06-02"),
                ("Biology Paper 2", "2025-06-09")
            ],
            "Computer Science": [
                ("Computer Science Theory", "2025-06-04"),
                ("Computer Science Practical", "2025-06-11")
            ],
            "English": [
                ("English Language", "2025-06-06"),
                ("English Literature", "2025-06-13")
            ]
        }
        
        print("Adding 2025 exam dates...")
        for subject in subjects:
            if subject.title in exam_dates:
                for exam_title, date_str in exam_dates[subject.title]:
                    exam_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    exam = Exam(
                        subject_id=subject.id,
                        title=exam_title,
                        exam_date=exam_date
                    )
                    db.session.add(exam)
                    print(f"Added exam: {exam_title} for {subject.title} on {date_str}")
        
        db.session.commit()
        print("Migration completed successfully!")

if __name__ == "__main__":
    run_migration() 