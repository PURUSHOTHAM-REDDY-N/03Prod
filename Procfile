# Initialize database then start web server
web: python -c "from initialize_railway_db import initialize_database; initialize_database()" && gunicorn run:app
