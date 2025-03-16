"""
Script to create all database tables directly using SQLAlchemy and import initial data.
This bypasses Flask-Migrate and just uses db.create_all() to ensure tables exist.
"""
import os
import sys
from dotenv import load_dotenv
from app import create_app, db
from app.utils.curriculum_importer import import_curriculum_data
from app.utils.data_import import seed_default_data, verify_imported_data

# Load environment variables
load_dotenv()

def create_all_tables():
    """Create all database tables directly and import initial data."""
    print("Starting database initialization...")
    
    # Force production environment for Railway
    app = create_app('production')
    
    try:
        with app.app_context():
            # Print debug info
            print(f"Database URL: {db.engine.url}")
            print(f"Engine: {db.engine}")
            
            # Create all tables defined in SQLAlchemy models
            print("Creating database tables directly using SQLAlchemy...")
            db.create_all()
            
            # List all tables that were created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Created tables: {tables}")
            
            # Seed default data
            print("Seeding default data...")
            seed_stats = seed_default_data()
            print(f"Default data seeded: {seed_stats}")
            
            # Import curriculum data
            print("Importing curriculum data...")
            success, message = import_curriculum_data()
            if success:
                print(f"Curriculum data imported: {message}")
            else:
                print(f"Curriculum import issue: {message}")
            
            # Verify data
            print("Verifying imported data...")
            verification = verify_imported_data()
            if verification['success']:
                print("Data verification successful")
            else:
                print(f"Data verification issues: {verification['issues']}")
            
            print("Database initialization complete!")
            return True
    except Exception as e:
        print(f"ERROR during database initialization: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_all_tables()
    if not success:
        sys.exit(1)  # Exit with error code if initialization failed
