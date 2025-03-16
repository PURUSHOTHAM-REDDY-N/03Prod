# Database migration sequence in release phase
release: FLASK_APP=run.py FLASK_ENV=production python -m flask db-init && FLASK_APP=run.py FLASK_ENV=production python -m flask db migrate && FLASK_APP=run.py FLASK_ENV=production python -m flask db upgrade && FLASK_APP=run.py FLASK_ENV=production python -m flask init-db

# Web server
web: gunicorn run:app
