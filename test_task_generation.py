"""
Test script for task generation system with confidence integration.
Verifies that the fixes for SQL syntax and InstrumentedList errors are working.
"""

import sys
from flask import current_app
from app import create_app, db
from app.models.user import User
from app.models.curriculum import Subject, Topic, Subtopic
from app.models.confidence import TopicConfidence, SubtopicConfidence
from app.utils.task_generator_main import generate_replacement_task
from app.utils.optimization_queries import get_optimized_subject_distribution

def test_task_generation_with_confidence():
    """
    Test task generation with confidence weighting.
    
    This test:
    1. Checks if confidence tables exist
    2. Ensures a user has confidence data
    3. Tries to generate a task with confidence weighting
    4. Verifies the task was generated correctly
    """
    print("\n=== Testing Task Generation with Confidence ===")
    
    # Get a test user
    user = User.query.first()
    if not user:
        print("Error: No users found. Please create a user first.")
        return False
    
    print(f"Using test user: {user.username} (ID: {user.id})")
    
    # Check if we have subjects
    subjects = Subject.query.all()
    if not subjects:
        print("Error: No subjects found. Please import curriculum data first.")
        return False
    
    print(f"Found {len(subjects)} subjects")
    
    # Check if we have confidence data or initialize it
    topic_conf_count = TopicConfidence.query.filter_by(user_id=user.id).count()
    subtopic_conf_count = SubtopicConfidence.query.filter_by(user_id=user.id).count()
    
    print(f"Current confidence data: {topic_conf_count} topic records, {subtopic_conf_count} subtopic records")
    
    # If no confidence data, initialize some test data
    if topic_conf_count == 0 or subtopic_conf_count == 0:
        print("Initializing test confidence data...")
        
        # Get some topics and subtopics to set confidence for
        topics = Topic.query.limit(5).all()
        subtopics = Subtopic.query.limit(10).all()
        
        # Create varying confidence levels for testing weighting
        for i, topic in enumerate(topics):
            # Set confidence levels from 1-5 to test weighting
            conf_level = (i % 5) + 1  # 1, 2, 3, 4, 5
            
            # Skip if confidence already exists
            if TopicConfidence.query.filter_by(user_id=user.id, topic_id=topic.id).first():
                continue
                
            topic_conf = TopicConfidence(
                user_id=user.id,
                topic_id=topic.id,
                confidence_level=conf_level * 20  # Convert to percentage (0-100)
            )
            db.session.add(topic_conf)
            print(f"Added topic confidence: Topic #{topic.id}, Level: {conf_level}/5")
        
        for i, subtopic in enumerate(subtopics):
            # Set confidence levels from 1-5 to test weighting
            conf_level = (i % 5) + 1  # 1, 2, 3, 4, 5
            
            # Skip if confidence already exists
            if SubtopicConfidence.query.filter_by(user_id=user.id, subtopic_id=subtopic.id).first():
                continue
                
            subtopic_conf = SubtopicConfidence(
                user_id=user.id,
                subtopic_id=subtopic.id,
                confidence_level=conf_level
            )
            db.session.add(subtopic_conf)
            print(f"Added subtopic confidence: Subtopic #{subtopic.id}, Level: {conf_level}/5")
        
        db.session.commit()
        print("Test confidence data initialized")
    
    # Test subject distribution calculation (previously had SQL error)
    print("\nTesting subject distribution calculation...")
    try:
        distribution = get_optimized_subject_distribution(user.id)
        print(f"Subject distribution calculated successfully: {len(distribution)} subjects")
        
        # Print some sample distribution data
        for subject_id, weight in list(distribution.items())[:3]:
            subject = Subject.query.get(subject_id)
            print(f"Subject: {subject.title}, Weight: {weight:.2f}")
            
    except Exception as e:
        print(f"Error calculating subject distribution: {str(e)}")
        return False
    
    # Test task generation
    print("\nTesting task generation...")
    try:
        task = generate_replacement_task(user)
        
        if task:
            print(f"Task generated successfully: {task.title}")
            print(f"Task description: {task.description}")
            return True
        else:
            print("Error: No task was generated")
            return False
            
    except Exception as e:
        print(f"Error generating task: {str(e)}")
        return False

if __name__ == "__main__":
    # Create app context for testing
    app = create_app()
    with app.app_context():
        success = test_task_generation_with_confidence()
        
        if success:
            print("\n✅ Task generation system is working correctly with confidence integration")
            sys.exit(0)
        else:
            print("\n❌ Task generation system encountered errors")
            sys.exit(1)
