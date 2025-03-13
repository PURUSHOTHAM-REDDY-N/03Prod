import sys
import os
import json
from app import create_app, db
from app.models.curriculum import Subject, Topic, Subtopic
from app.models.confidence import SubtopicConfidence, TopicConfidence
from app.models.user import User

def test_confidence_update():
    app = create_app()
    with app.app_context():
        print("Testing confidence update functionality...")
        
        # Get test user
        user = User.query.filter_by(username='test').first()
        if not user:
            print("Creating test user...")
            user = User(username='test', password='test123', email='test@example.com')
            db.session.add(user)
            db.session.commit()
        
        print(f"Using user: {user.username} (id: {user.id})")
        
        # Get a subject, topic, and subtopic
        subject = Subject.query.first()
        if not subject:
            print("No subjects found in database. Test cannot proceed.")
            return
        
        print(f"Testing with subject: {subject.title} (id: {subject.id})")
        
        topic = Topic.query.filter_by(subject_id=subject.id).first()
        if not topic:
            print(f"No topics found for subject ID {subject.id}. Test cannot proceed.")
            return
            
        print(f"Testing with topic: {topic.title} (id: {topic.id})")
        
        # Get subtopics for this topic
        subtopics = Subtopic.query.filter_by(topic_id=topic.id).all()
        if not subtopics:
            print(f"No subtopics found for topic ID {topic.id}. Test cannot proceed.")
            return
        
        print(f"Found {len(subtopics)} subtopics for testing")
        
        # Get initial topic confidence
        topic_confidence = TopicConfidence.query.filter_by(user_id=user.id, topic_id=topic.id).first()
        if not topic_confidence:
            print("Creating initial topic confidence record...")
            topic_confidence = TopicConfidence(user_id=user.id, topic_id=topic.id, confidence_level=50)
            db.session.add(topic_confidence)
            db.session.commit()
        
        initial_topic_confidence = topic_confidence.confidence_level
        print(f"Initial topic confidence: {initial_topic_confidence}")
        
        # Update confidence for all subtopics to level 4
        updated_level = 4
        subtopic_count = 0
        
        for subtopic in subtopics:
            subtopic_confidence = SubtopicConfidence.query.filter_by(
                user_id=user.id, subtopic_id=subtopic.id
            ).first()
            
            if not subtopic_confidence:
                subtopic_confidence = SubtopicConfidence(
                    user_id=user.id, subtopic_id=subtopic.id, confidence_level=3
                )
                db.session.add(subtopic_confidence)
            
            # Update to the new level using the proper update method
            subtopic_confidence.update_confidence(updated_level)
            subtopic_count += 1
        
        db.session.commit()
        
        # Update the parent topic's confidence
        from app.utils.confidence_utils import update_topic_confidence
        update_topic_confidence(user.id, topic.id)
        print(f"Updated {subtopic_count} subtopics to confidence level {updated_level}")
        
        # Verify the topic confidence was updated
        topic_confidence = TopicConfidence.query.filter_by(user_id=user.id, topic_id=topic.id).first()
        final_topic_confidence = topic_confidence.confidence_level
        print(f"Final topic confidence: {final_topic_confidence}")
        
        # Check if the topic confidence was updated as expected
        if final_topic_confidence != initial_topic_confidence:
            print("✅ Topic confidence successfully updated after subtopic confidence change")
            print(f"   Changed from {initial_topic_confidence} to {final_topic_confidence}")
        else:
            print("❌ Topic confidence did not update as expected")
        
        # Return to initial levels for future tests
        for subtopic in subtopics:
            subtopic_confidence = SubtopicConfidence.query.filter_by(
                user_id=user.id, subtopic_id=subtopic.id
            ).first()
            subtopic_confidence.update_confidence(3)
        
        db.session.commit()
        
        # Update the parent topic's confidence again
        update_topic_confidence(user.id, topic.id)
        print("Reset subtopic confidence levels to 3 for future tests")

if __name__ == "__main__":
    test_confidence_update()
