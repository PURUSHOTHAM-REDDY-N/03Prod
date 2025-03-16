import os
import sys
from dotenv import load_dotenv
from app import create_app, db
from app.utils.data_import import seed_default_data, verify_imported_data
from app.utils.curriculum_importer import import_curriculum_data as import_jsonc_curriculum

# Load environment variables
load_dotenv()

# Create app with appropriate config
# For Railway deployment, force production environment if RAILWAY_ENVIRONMENT exists
if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY_SERVICE_ID'):
    print("Detected Railway environment, forcing production mode")
    env = 'production'
else:
    env = os.environ.get('FLASK_ENV', 'development')
    
print(f"Using environment: {env}")
app = create_app(env)

# Initialize database tables on application startup when on Railway
if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY_SERVICE_ID'):
    with app.app_context():
        try:
            print("=== RAILWAY DATABASE INITIALIZATION ===")
            print(f"Database URL: {db.engine.url}")
            
            # Create all tables
            print("Creating database tables...")
            db.create_all()
            
            # List created tables
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Created tables: {tables}")
            
            if not tables:
                print("WARNING: No tables were created!")
            
            # Seed default data if tables were created
            if tables:
                print("Seeding default data...")
                stats = seed_default_data()
                print(f"Default data seeded: {stats}")
                
                # Import curriculum data
                print("Importing curriculum data...")
                success, message = import_jsonc_curriculum()
                if success:
                    print(f"Curriculum data imported: {message}")
                else:
                    print(f"Curriculum import issue: {message}")
                
                print("=== DATABASE INITIALIZATION COMPLETE ===")
        except Exception as e:
            print(f"ERROR during database initialization: {str(e)}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            # Don't exit - let the app continue even if DB init fails

@app.cli.command('init-db')
def init_db():
    """Initialize the database."""
    from app import db
    from flask import current_app
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Seed default data
        stats = seed_default_data()
        current_app.logger.info(f"Seeded default data: {stats}")
        
        current_app.logger.info("Database initialized successfully")

@app.cli.command('import-data')
def import_data():
    """Import curriculum data from JSON file."""
    from flask import current_app
    
    with app.app_context():
        # Path to curriculum data relative to this file
        json_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'data', 'curriculum.jsonc'
        )
        
        # Import data with validation
        stats = import_jsonc_curriculum(json_path, validate=True)
        
        # Log validation warnings if any
        if stats.get('validation_warnings'):
            current_app.logger.warning(f"Validation warnings: {stats['validation_warnings']}")
        
        # Check for errors
        if stats.get('errors'):
            current_app.logger.error(f"Import errors: {stats['errors']}")
            return
        
        # Verify imported data
        from app.utils.data_import import verify_imported_data
        verification = verify_imported_data()
        
        if not verification['success']:
            current_app.logger.error(f"Data verification failed: {verification['issues']}")
        elif verification['issues']:
            current_app.logger.warning(f"Verification warnings: {verification['issues']}")
        else:
            current_app.logger.info("Data verification successful")
        
        current_app.logger.info(f"Data import completed: {stats}")

@app.cli.command('import-curriculum')
def import_curriculum():
    """Import curriculum data from JSONC file."""
    from flask import current_app
    
    with app.app_context():
        success, message = import_jsonc_curriculum()
        if success:
            current_app.logger.info(message)
        else:
            current_app.logger.error(message)

@app.cli.command('verify-data')
def verify_data():
    """Verify the integrity of imported curriculum data."""
    from flask import current_app
    from app.utils.data_import import verify_imported_data
    
    with app.app_context():
        # Verify data
        verification = verify_imported_data()
        
        if not verification['success']:
            current_app.logger.error(f"Data verification failed: {verification['issues']}")
        elif verification['issues']:
            current_app.logger.warning(f"Verification warnings: {verification['issues']}")
        else:
            current_app.logger.info("Data verification successful")

@app.cli.command('rebuild-db')
def rebuild_db():
    """Drop all tables and rebuild the database from scratch."""
    from app import db
    from flask import current_app
    import click
    
    if click.confirm('This will delete all data in the database. Are you sure?'):
        with app.app_context():
            # Drop all tables
            db.drop_all()
            current_app.logger.info("All tables dropped")
            
            # Create tables
            db.create_all()
            current_app.logger.info("Tables created")
            
            # Seed default data
            seed_stats = seed_default_data()
            current_app.logger.info(f"Seeded default data: {seed_stats}")
            
            # Import curriculum data
            json_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'data', 'curriculum.jsonc'
            )
            
            # Import data - use import_curriculum_data without validate parameter
            success, message = import_jsonc_curriculum()
            
            if success:
                current_app.logger.info(message)
            else:
                current_app.logger.error(message)
                
            # Verify data
            from app.utils.data_import import verify_imported_data
            verification = verify_imported_data()
            
            if verification['success']:
                current_app.logger.info("Database rebuilt successfully")
            else:
                current_app.logger.error(f"Database rebuild completed with verification issues: {verification['issues']}")

if __name__ == '__main__':
    app.run(debug=True)
