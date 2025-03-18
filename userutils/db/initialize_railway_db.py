import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from app import create_app, db
from app.models.user import User
from app.models.task import Task
from app.models.curriculum import Subject, Topic, Subtopic
from app.models.confidence import SubtopicConfidence, TopicConfidence
from app.utils.curriculum_importer import import_curriculum_data

# Load environment variables from .env
load_dotenv()

def initialize_database():
    # Try to get the public database URL first (more reliable for external connections)
    database_public_url = os.environ.get('DATABASE_PUBLIC_URL')
    
    if database_public_url:
        # Format for SQLAlchemy with pg8000 driver
        if database_public_url.startswith('postgres://'):
            database_public_url = database_public_url.replace('postgres://', 'postgresql+pg8000://', 1)
        elif database_public_url.startswith('postgresql://'):
            database_public_url = database_public_url.replace('postgresql://', 'postgresql+pg8000://', 1)
        
        print(f"Connecting to database using DATABASE_PUBLIC_URL: {database_public_url}")
        connection_string = database_public_url
    else:
        # Fallback to regular DATABASE_URL
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("ERROR: No DATABASE_URL found in environment variables")
            return False
        
        # Format for SQLAlchemy with pg8000 driver (compatible with Python 3.13)
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql+pg8000://', 1)
        elif database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+pg8000://', 1)
        
        # Try using Railway TCP proxy domain if available
        railway_tcp_proxy = os.environ.get('RAILWAY_TCP_PROXY_DOMAIN')
        if railway_tcp_proxy and 'postgres.railway.internal' in database_url:
            print(f"Replacing internal hostname with TCP proxy domain: {railway_tcp_proxy}")
            database_url = database_url.replace('postgres.railway.internal', railway_tcp_proxy)
        
        print(f"Connecting to database using DATABASE_URL: {database_url}")
        connection_string = database_url
    
    # Create app with production configuration
    app = create_app('production')
    
    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        
        # Import curriculum data if needed
        print("Importing curriculum data...")
        success, message = import_curriculum_data()
        if success:
            print("Curriculum data imported successfully")
        else:
            print(f"Error importing curriculum data: {message}")
        
        print("Database initialization complete")
        return True

if __name__ == '__main__':
    initialize_database()
