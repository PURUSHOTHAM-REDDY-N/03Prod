# Database migration sequence:
# 1. Initialize migrations
# 2. Generate migration script
# 3. Apply migrations
# 4. Initialize tables
# 5. Import curriculum data
# 6. Start web server
web: python -m flask --app run.py db-init && python -m flask --app run.py db migrate && python -m flask --app run.py db upgrade && python -m flask --app run.py init-db && python -m flask --app run.py import-curriculum && gunicorn run:app
