#!/usr/bin/env python
"""
Test script for the confidence system that writes results to a file.
"""

import os
import sys
import json
from flask import Flask
from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy
import random
from datetime import datetime

# Create minimal Flask application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Output file
output_file = "confidence_test_results.txt"

def write_output(message):
    """Write message to both console and file."""
    print(message)
    with open(output_file, "a") as f:
        f.write(message + "\n")

def test_confidence_system():
    """Test the confidence system and write results to a file."""
    # Clear previous results
    with open(output_file, "w") as f:
        f.write(f"Confidence System Test Results - {datetime.now()}\n")
        f.write("="*50 + "\n\n")
    
    with app.app_context():
        try:
            write_output("Testing the confidence system...")
            
            # Import models
            from app.models.user import User
            from app.models.curriculum import Subject, Topic, Subtopic
            from app.models.confidence import SubtopicConfidence, TopicConfidence
            
            # Check if tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            write_output(f"Database tables: {tables}")
            
            if 'subtopic_confidences' not in tables or 'topic_confidences' not in tables:
                write_output("Error: Confidence tables not found. Running db.create_all()...")
                db.create_all()
                tables = inspector.get_table_names()
                write_output(f"Tables after create_all: {tables}")
            
            # Get a test user
            test_user = User.query.first()
            if not test_user:
                write_output("No users found in the database. Please create a user first.")
                return
            
            write_output(f"Using test user: {test_user.username} (ID: {test_user.id})")
            
            # Get a random topic to test with
            topic = Topic.query.order_by(db.func.random()).first()
            if not topic:
                write_output("No topics found in the database. Please import curriculum data first.")
                return
            
            write_output(f"Using test topic: {topic.title} (ID: {topic.id})")
            
            # Get subtopics for this topic
            subtopics = Subtopic.query.filter_by(topic_id=topic.id).all()
            if not subtopics:
                write_output(f"No subtopics found for topic {topic.title}. Please import curriculum data first.")
                return
            
            write_output(f"This topic has {len(subtopics)} subtopics")
            
            # Create or get confidence data for these subtopics
            for subtopic in subtopics:
                confidence = SubtopicConfidence.get_or_create(test_user.id, subtopic.id)
                write_output(f"  Subtopic: {subtopic.title} - Confidence: {confidence.confidence_level}/5")
            
            # Update confidence levels to random values
            write_output("\nUpdating subtopic confidence levels to random values...")
            for subtopic in subtopics:
                confidence = SubtopicConfidence.query.filter_by(
                    user_id=test_user.id,
                    subtopic_id=subtopic.id
                ).first()
                
                # Set to a random value between 1 and 5
                new_level = random.randint(1, 5)
                confidence.confidence_level = new_level
                write_output(f"  Subtopic: {subtopic.title} - New confidence: {new_level}/5")
            
            # Update topic confidence
            db.session.commit()
            
            # Calculate and get topic confidence
            topic_confidence = TopicConfidence.update_for_topic(topic.id, test_user.id)
            
            write_output(f"\nTopic confidence for {topic.title}: {topic_confidence.confidence_percent:.2f}%")
            
            # Verify calculation manually
            subtopic_confidences = SubtopicConfidence.query.filter_by(user_id=test_user.id).filter(
                SubtopicConfidence.subtopic_id.in_([s.id for s in subtopics])
            ).all()
            
            total = sum(sc.confidence_level for sc in subtopic_confidences)
            average = total / len(subtopic_confidences)
            percent = (average / 5.0) * 100.0
            
            write_output(f"Manual calculation verification:")
            write_output(f"  Sum of confidence levels: {total}")
            write_output(f"  Average confidence level: {average:.2f}/5")
            write_output(f"  Confidence percentage: {percent:.2f}%")
            write_output(f"  Stored in database: {topic_confidence.confidence_percent:.2f}%")
            
            # Calculate priority weights
            write_output("\nPriority weights using formula (7 - confidence_level)²:")
            for sc in subtopic_confidences:
                subtopic = next(s for s in subtopics if s.id == sc.subtopic_id)
                weight = sc.calculate_weight()
                write_output(f"  Subtopic: {subtopic.title} - Confidence: {sc.confidence_level}/5 - Weight: {weight}")
            
            write_output("\nTest completed successfully.")
            
        except Exception as e:
            write_output(f"Error testing confidence system: {e}")
            import traceback
            traceback_text = traceback.format_exc()
            write_output(traceback_text)

if __name__ == "__main__":
    test_confidence_system()
    print(f"Full test results written to {output_file}")
