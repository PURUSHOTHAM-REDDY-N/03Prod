#!/usr/bin/env python
"""
Verbose test script for the confidence system.
This script demonstrates how the confidence system works with detailed output by:
1. Creating the confidence tables
2. Initializing confidence data for a test user
3. Updating confidence levels
4. Verifying topic confidence calculation

Example usage:
python test_confidence_verbose.py
"""

import os
import sys
import json
from flask import Flask
from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy
import random

# Create minimal Flask application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

def test_confidence_system():
    """Test the confidence system with verbose output."""
    with app.app_context():
        try:
            print("=" * 50)
            print("CONFIDENCE SYSTEM VERBOSE TEST")
            print("=" * 50)
            
            # Import models
            print("\nImporting models...")
            from app.models.user import User
            from app.models.curriculum import Subject, Topic, Subtopic
            from app.models.confidence import SubtopicConfidence, TopicConfidence
            print("Models imported successfully.")
            
            # Ensure tables exist
            print("\nEnsuring database tables exist...")
            db.create_all()
            print("Database tables created/verified.")
            
            # Check if confidence tables exist
            print("\nVerifying confidence tables...")
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Database tables: {tables}")
            
            if 'subtopic_confidences' in tables and 'topic_confidences' in tables:
                print("Confidence tables verified ✓")
            else:
                print("ERROR: Confidence tables not found!")
                return
            
            # Get a test user
            print("\nFinding test user...")
            test_user = User.query.first()
            if not test_user:
                print("ERROR: No users found in the database. Please create a user first.")
                return
            
            print(f"Using test user: {test_user.username} (ID: {test_user.id})")
            
            # Get a random topic to test with
            print("\nFinding random topic...")
            topic = Topic.query.order_by(db.func.random()).first()
            if not topic:
                print("ERROR: No topics found in the database. Please import curriculum data first.")
                return
            
            print(f"Selected test topic: {topic.title} (ID: {topic.id})")
            print(f"Subject: {topic.subject.title if topic.subject else 'Unknown'}")
            
            # Get subtopics for this topic
            print("\nRetrieving subtopics...")
            subtopics = Subtopic.query.filter_by(topic_id=topic.id).all()
            if not subtopics:
                print(f"ERROR: No subtopics found for topic {topic.title}. Please import curriculum data first.")
                return
            
            print(f"Found {len(subtopics)} subtopics for this topic")
            
            # Create or get confidence data for these subtopics
            print("\nCurrent confidence levels for subtopics:")
            print("-" * 70)
            print(f"{'SUBTOPIC TITLE':<40} | {'CONFIDENCE':<10} | {'LAST UPDATED':<20}")
            print("-" * 70)
            
            for subtopic in subtopics:
                confidence = SubtopicConfidence.get_or_create(test_user.id, subtopic.id)
                print(f"{subtopic.title[:38]:<40} | {confidence.confidence_level}/5{' ':8} | {confidence.last_updated}")
            
            # Update confidence levels to random values
            print("\nUpdating subtopic confidence levels to random values...")
            print("-" * 70)
            print(f"{'SUBTOPIC TITLE':<40} | {'OLD LEVEL':<10} | {'NEW LEVEL':<10}")
            print("-" * 70)
            
            for subtopic in subtopics:
                confidence = SubtopicConfidence.query.filter_by(
                    user_id=test_user.id,
                    subtopic_id=subtopic.id
                ).first()
                
                old_level = confidence.confidence_level
                
                # Set to a random value between 1 and 5
                new_level = random.randint(1, 5)
                confidence.confidence_level = new_level
                print(f"{subtopic.title[:38]:<40} | {old_level}/5{' ':8} | {new_level}/5")
            
            # Update topic confidence
            print("\nCommitting changes to database...")
            db.session.commit()
            print("Changes committed successfully.")
            
            # Calculate and get topic confidence
            print("\nUpdating topic confidence...")
            topic_confidence = TopicConfidence.update_for_topic(topic.id, test_user.id)
            
            print(f"\nTopic confidence for {topic.title}: {topic_confidence.confidence_percent:.2f}%")
            print(f"Last updated: {topic_confidence.last_updated}")
            
            # Verify calculation manually
            print("\nVerifying calculation manually...")
            subtopic_confidences = SubtopicConfidence.query.filter_by(user_id=test_user.id).filter(
                SubtopicConfidence.subtopic_id.in_([s.id for s in subtopics])
            ).all()
            
            total = sum(sc.confidence_level for sc in subtopic_confidences)
            average = total / len(subtopic_confidences)
            percent = (average / 5.0) * 100.0
            
            print(f"  Sum of confidence levels: {total}")
            print(f"  Number of subtopics: {len(subtopic_confidences)}")
            print(f"  Average confidence level: {average:.2f}/5")
            print(f"  Calculated confidence percentage: {percent:.2f}%")
            print(f"  Stored topic confidence: {topic_confidence.confidence_percent:.2f}%")
            
            # Check if calculation matches
            if abs(percent - topic_confidence.confidence_percent) < 0.01:
                print("  ✓ Calculation verified (matches stored value)")
            else:
                print("  ✗ Calculation error (doesn't match stored value)")
            
            # Calculate priority weights
            print("\nPriority weights using formula (7 - confidence_level)²:")
            print("-" * 80)
            print(f"{'SUBTOPIC TITLE':<40} | {'CONFIDENCE':<10} | {'WEIGHT':<10} | {'PRIORITY':<10}")
            print("-" * 80)
            
            # Sort by weight (descending) for better visualization of priorities
            sorted_confidences = sorted(
                [(next(s for s in subtopics if s.id == sc.subtopic_id), sc) 
                 for sc in subtopic_confidences],
                key=lambda x: x[1].calculate_weight(),
                reverse=True
            )
            
            for subtopic, sc in sorted_confidences:
                weight = sc.calculate_weight()
                priority = "High" if weight > 16 else "Medium" if weight > 9 else "Low"
                print(f"{subtopic.title[:38]:<40} | {sc.confidence_level}/5{' ':8} | {weight:<10} | {priority:<10}")
            
            print("\n" + "=" * 50)
            print("TEST COMPLETED SUCCESSFULLY ✓")
            print("=" * 50)
            
        except Exception as e:
            print(f"ERROR testing confidence system: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_confidence_system()
