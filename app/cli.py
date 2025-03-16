import click
import os
from flask.cli import with_appcontext
from app.utils.curriculum_importer import import_curriculum_data
from app import db, migrate

def register_commands(app):
    """Register Flask CLI commands."""
    
    @app.cli.command('db-init')
    @with_appcontext
    def db_init():
        """Initialize database migrations."""
        click.echo('Initializing database migrations...')
        # This creates the migrations directory and repository
        try:
            migrations_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'migrations')
            if not os.path.exists(migrations_dir):
                # If migrations directory doesn't exist, we need to initialize it
                from flask_migrate import init as migrate_init
                migrate_init()
                click.echo(click.style('Migration repository created successfully.', fg='green'))
            else:
                click.echo(click.style('Migration repository already exists.', fg='yellow'))
        except Exception as e:
            click.echo(click.style(f"Error initializing migrations: {str(e)}", fg='red'))
    
    @app.cli.command('import-curriculum')
    @with_appcontext
    def import_curriculum():
        """Import curriculum data from JSONC file."""
        click.echo('Importing curriculum data...')
        success, message = import_curriculum_data()
        
        if success:
            click.echo(click.style(message, fg='green'))
        else:
            click.echo(click.style(f"Error: {message}", fg='red'))
    
    @app.cli.command('init-db')
    @with_appcontext
    def init_db():
        """Initialize the database without dropping tables in production."""
        # Check if we're in production mode
        if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY_SERVICE_ID'):
            # In production, just create tables that don't exist yet
            click.echo('Production environment detected, creating missing tables...')
            db.create_all()
            click.echo(click.style('Database tables created successfully.', fg='green'))
        else:
            # In development, prompt for confirmation
            if click.confirm('This will delete all data in the database. Continue?'):
                click.echo('Dropping all tables...')
                db.drop_all()
                click.echo('Creating tables...')
                db.create_all()
                click.echo(click.style('Database initialized successfully.', fg='green'))
                
                # Import curriculum data
                click.echo('Importing curriculum data...')
                success, message = import_curriculum_data()
                if success:
                    click.echo(click.style(message, fg='green'))
                else:
                    click.echo(click.style(f"Error: {message}", fg='red'))
