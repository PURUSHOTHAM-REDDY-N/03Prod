#!/usr/bin/env python
"""
Test script for the confidence system.
This script demonstrates how the confidence system works by:
1. Creating the confidence tables
2. Initializing confidence data for a test user
3. Updating confidence levels
4. Verifying topic confidence calculation

Example usage:
python test_confidence_system.py
"""

import os
import sys
import random
from run import app
from app import db

def test_confidence_system():
    """Test the confidence system."""
    with app.app_context():
        try:
            # Import models
            from app.models.user import User
            from app.models.curriculum import Subject, Topic, Subtopic
            from app.models.confidence import SubtopicConfidence, TopicConfidence
            
            print("Testing the confidence system...")
            
            # Ensure tables exist
            db.create_all()
            
            # Get a test user
            test_user = User.query.first()
            if not test_user:
                print("No users found in the database. Please create a user first.")
                return
            
            print(f"Using test user: {test_user.username} (ID: {test_user.id})")
            
            # Get a random topic to test with
            topic = Topic.query.order_by(db.func.random()).first()
            if not topic:
                print("No topics found in the database. Please import curriculum data first.")
                return
            
            print(f"Using test topic: {topic.title} (ID: {topic.id})")
            
            # Get subtopics for this topic
            subtopics = Subtopic.query.filter_by(topic_id=topic.id).all()
            if not subtopics:
                print(f"No subtopics found for topic {topic.title}. Please import curriculum data first.")
                return
            
            print(f"This topic has {len(subtopics)} subtopics")
            
            # Create or get confidence data for these subtopics
            for subtopic in subtopics:
                confidence = SubtopicConfidence.get_or_create(test_user.id, subtopic.id)
                print(f"  Subtopic: {subtopic.title} - Confidence: {confidence.confidence_level}/5")
            
            # Update confidence levels to random values
            print("\nUpdating subtopic confidence levels to random values...")
            for subtopic in subtopics:
                confidence = SubtopicConfidence.query.filter_by(
                    user_id=test_user.id,
                    subtopic_id=subtopic.id
                ).first()
                
                # Set to a random value between 1 and 5
                new_level = random.randint(1, 5)
                confidence.confidence_level = new_level
                print(f"  Subtopic: {subtopic.title} - New confidence: {new_level}/5")
            
            # Update topic confidence
            db.session.commit()
            
            # Calculate and get topic confidence
            topic_confidence = TopicConfidence.update_for_topic(topic.id, test_user.id)
            
            print(f"\nTopic confidence for {topic.title}: {topic_confidence.confidence_percent:.2f}%")
            
            # Verify calculation manually
            subtopic_confidences = SubtopicConfidence.query.filter_by(user_id=test_user.id).filter(
                SubtopicConfidence.subtopic_id.in_([s.id for s in subtopics])
            ).all()
            
            total = sum(sc.confidence_level for sc in subtopic_confidences)
            average = total / len(subtopic_confidences)
            percent = (average / 5.0) * 100.0
            
            print(f"Manual calculation verification:")
            print(f"  Sum of confidence levels: {total}")
            print(f"  Average confidence level: {average:.2f}/5")
            print(f"  Confidence percentage: {percent:.2f}%")
            
            # Calculate priority weights
            print("\nPriority weights using formula (7 - confidence_level)²:")
            for sc in subtopic_confidences:
                subtopic = next(s for s in subtopics if s.id == sc.subtopic_id)
                weight = sc.calculate_weight()
                print(f"  Subtopic: {subtopic.title} - Confidence: {sc.confidence_level}/5 - Weight: {weight}")
            
            print("\nTest completed successfully.")
            
        except Exception as e:
            print(f"Error testing confidence system: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_confidence_system()
