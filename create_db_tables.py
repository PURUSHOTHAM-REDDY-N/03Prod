"""
Script to create all database tables directly using SQLAlchemy.
This bypasses Flask-Migrate and just uses db.create_all() to ensure tables exist.
"""
import os
from dotenv import load_dotenv
from app import create_app, db

# Load environment variables
load_dotenv()

def create_all_tables():
    """Create all database tables directly."""
    # Force production environment for Railway
    app = create_app('production')
    
    with app.app_context():
        print("Creating database tables directly using SQLAlchemy...")
        # Create all tables defined in SQLAlchemy models
        db.create_all()
        print("Tables created successfully")
        
        # List all tables that were created
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Created tables: {tables}")
        
        return True

if __name__ == "__main__":
    create_all_tables()
