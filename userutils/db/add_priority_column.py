from app import create_app, db
from sqlalchemy import text

app = create_app()  # Create the app instance

with app.app_context():
    # Add priority column to subtopic_confidences table if it doesn't exist
    sql = text("ALTER TABLE subtopic_confidences ADD COLUMN priority BOOLEAN DEFAULT 0 NOT NULL;")
    try:
        db.session.execute(sql)
        db.session.commit()
        print("Priority column added successfully!")
    except Exception as e:
        print(f"Error adding column: {e}")
        # Check if it's a duplicate column error
        if "duplicate column name" in str(e).lower():
            print("Column already exists, which is fine.")
        else:
            # For other errors, rollback the session
            db.session.rollback() 