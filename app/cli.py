import click
import os
from flask.cli import with_appcontext
from app.utils.curriculum_importer import import_curriculum_data
from app import db

def register_commands(app):
    """Register Flask CLI commands."""
    
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
        """Clear and initialize the database."""
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
