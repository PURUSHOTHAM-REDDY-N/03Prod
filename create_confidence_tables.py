#!/usr/bin/env python
"""
Script to create confidence-related tables in the database.
"""

from flask import Flask
from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy
from app.models.confidence import SubtopicConfidence, TopicConfidence

# Create minimal Flask application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

def create_confidence_tables():
    """Create all confidence-related tables in the database."""
    with app.app_context():
        try:
            # Import models to ensure they're registered with SQLAlchemy
            from app.models.user import User
            from app.models.curriculum import Subject, Topic, Subtopic
            
            # Create tables for confidence models
            db.create_all()
            
            print("Confidence tables successfully created.")
            print("Tables created: subtopic_confidences, topic_confidences")
            
            # Count existing users and curriculum items
            user_count = User.query.count()
            subtopic_count = Subtopic.query.count()
            topic_count = Topic.query.count()
            
            print(f"Database contains {user_count} users, {topic_count} topics, and {subtopic_count} subtopics.")
            print("You may want to initialize confidence data for existing users using the API endpoint:")
            print("POST /api/confidence/user/initialize")
            
        except Exception as e:
            print(f"Error creating confidence tables: {e}")

if __name__ == "__main__":
    create_confidence_tables()
