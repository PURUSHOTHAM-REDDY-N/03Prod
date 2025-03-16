#!/usr/bin/env python
"""
Comprehensive test script for the confidence system.
Outputs detailed results directly to the console.
"""

import os
import sys
import random
from flask import Flask
from sqlalchemy import text, inspect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Create minimal Flask application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

def run_test():
    """Run comprehensive confidence system tests."""
    with app.app_context():
        try:
            print("\n" + "="*60)
            print("CONFIDENCE SYSTEM VERIFICATION TEST")
            print("="*60)
            
            # Step 1: Check if the confidence tables exist
            print("\n[STEP 1] Checking database tables...")
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"Found {len(tables)} tables in database:")
            for table in tables:
                print(f"  - {table}")
                
            if 'subtopic_confidences' in tables:
                print("  ✓ subtopic_confidences table exists")
            else:
                print("  ✗ subtopic_confidences table NOT found")
                print("  Creating tables...")
                db.create_all()
                print("  Tables created.")
                
            if 'topic_confidences' in tables:
                print("  ✓ topic_confidences table exists")
            else:
                print("  ✗ topic_confidences table NOT found")
                
            # Step 2: Import models and check for a test user
            print("\n[STEP 2] Checking for test user and curriculum data...")
            
            # Import models
            from app.models.user import User
            from app.models.curriculum import Subject, Topic, Subtopic
            from app.models.confidence import SubtopicConfidence, TopicConfidence
            
            # Check for test user
            test_user = User.query.first()
            if test_user:
                print(f"  ✓ Found test user: {test_user.username} (ID: {test_user.id})")
            else:
                print("  ✗ No test users found in database")
                print("  Creating test user...")
                test_user = User(username="testuser", email="test@example.com")
                test_user.set_password("testpassword")
                db.session.add(test_user)
                db.session.commit()
                print(f"  ✓ Created test user: {test_user.username} (ID: {test_user.id})")
                
            # Check for curriculum data
            subjects_count = Subject.query.count()
            topics_count = Topic.query.count()
            subtopics_count = Subtopic.query.count()
            
            print(f"  Curriculum data: {subjects_count} subjects, {topics_count} topics, {subtopics_count} subtopics")
            
            if topics_count == 0:
                print("  ✗ No curriculum data found. Tests cannot continue.")
                return
                
            # Step 3: Select a random topic for testing
            print("\n[STEP 3] Selecting test topic and subtopics...")
            topic = Topic.query.order_by(db.func.random()).first()
            print(f"  Selected topic: {topic.title} (ID: {topic.id})")
            print(f"  Subject: {topic.subject.title if topic.subject else 'Unknown'}")
            
            subtopics = Subtopic.query.filter_by(topic_id=topic.id).all()
            if not subtopics:
                print(f"  ✗ No subtopics found for topic {topic.title}. Tests cannot continue.")
                return
            
            print(f"  Found {len(subtopics)} subtopics for this topic")
            for i, subtopic in enumerate(subtopics[:5], 1):  # Show first 5 subtopics
                print(f"    {i}. {subtopic.title}")
            if len(subtopics) > 5:
                print(f"    ... and {len(subtopics) - 5} more subtopics")
                
            # Step 4: Create or get confidence data for these subtopics
            print("\n[STEP 4] Checking existing confidence data...")
            current_subtopic_confidences = []
            
            for subtopic in subtopics:
                confidence = SubtopicConfidence.query.filter_by(
                    user_id=test_user.id,
                    subtopic_id=subtopic.id
                ).first()
                
                if confidence:
                    status = "Existing"
                    current_subtopic_confidences.append(confidence)
                else:
                    status = "Default (new)"
                    confidence = SubtopicConfidence.get_or_create(test_user.id, subtopic.id)
                    current_subtopic_confidences.append(confidence)
                
                # Only show first 5 for brevity
                if len(current_subtopic_confidences) <= 5:
                    print(f"  {status}: Subtopic '{subtopic.title}' - Confidence: {confidence.confidence_level}/5")
            
            if len(subtopics) > 5:
                print(f"  ... and {len(subtopics) - 5} more confidence records")
                
            # Step 5: Update confidence levels to new random values
            print("\n[STEP 5] Updating subtopic confidence levels...")
            for i, subtopic in enumerate(subtopics):
                confidence = SubtopicConfidence.query.filter_by(
                    user_id=test_user.id,
                    subtopic_id=subtopic.id
                ).first()
                
                old_level = confidence.confidence_level
                new_level = random.randint(1, 5)
                confidence.confidence_level = new_level
                
                # Only show first 5 for brevity
                if i < 5:
                    print(f"  Subtopic '{subtopic.title}' - Updated: {old_level}/5 → {new_level}/5")
            
            # Commit changes to database
            print("  Committing changes to database...")
            db.session.commit()
            print("  ✓ Changes committed successfully")
                
            # Step 6: Calculate and verify topic confidence
            print("\n[STEP 6] Calculating topic confidence...")
            topic_confidence = TopicConfidence.update_for_topic(topic.id, test_user.id)
            print(f"  Topic confidence percentage: {topic_confidence.confidence_percent:.2f}%")
            
            # Manual verification
            print("  Performing manual verification...")
            updated_subtopic_confidences = SubtopicConfidence.query.filter_by(user_id=test_user.id).filter(
                SubtopicConfidence.subtopic_id.in_([s.id for s in subtopics])
            ).all()
            
            total = sum(sc.confidence_level for sc in updated_subtopic_confidences)
            average = total / len(updated_subtopic_confidences)
            percent = (average / 5.0) * 100.0
            
            print(f"    Sum of all confidence levels: {total}")
            print(f"    Number of subtopics: {len(updated_subtopic_confidences)}")
            print(f"    Average confidence level: {average:.2f}/5")
            print(f"    Manual calculation: {percent:.2f}%")
            print(f"    Database value: {topic_confidence.confidence_percent:.2f}%")
            
            if abs(percent - topic_confidence.confidence_percent) < 0.01:
                print("    ✓ Calculation verified (match within 0.01%)")
            else:
                print("    ✗ Calculation error (values don't match)")
                
            # Step 7: Verify priority weighting system
            print("\n[STEP 7] Testing priority weight calculations...")
            print("  Formula: (7 - confidence_level)²")
            
            # Show weights for each confidence level 1-5
            print("  Reference weights:")
            for level in range(1, 6):
                weight = (7 - level) ** 2
                print(f"    Confidence {level}/5 → Weight: {weight}")
                
            # Check a few actual weights
            print("\n  Sample weights from database:")
            sample_confidences = updated_subtopic_confidences[:3]  # First 3 for brevity
            
            for sc in sample_confidences:
                subtopic = next(s for s in subtopics if s.id == sc.subtopic_id)
                weight = sc.calculate_weight()
                expected_weight = (7 - sc.confidence_level) ** 2
                
                print(f"    Subtopic '{subtopic.title}' - Level: {sc.confidence_level}/5")
                print(f"    Calculated weight: {weight}")
                print(f"    Expected weight: {expected_weight}")
                
                if weight == expected_weight:
                    print("    ✓ Weight calculation verified")
                else:
                    print("    ✗ Weight calculation error")
                    
            print("\n" + "="*60)
            print("CONFIDENCE SYSTEM TEST COMPLETED SUCCESSFULLY")
            print("="*60)
            
        except Exception as e:
            print(f"\nERROR testing confidence system: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    run_test()
