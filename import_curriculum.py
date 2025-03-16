from app import create_app
from app.utils.curriculum_importer import import_curriculum_data

# Create app context
app = create_app()
with app.app_context():
    success, message = import_curriculum_data()
    print(f"Import result: {success}")
    print(f"Message: {message}")
