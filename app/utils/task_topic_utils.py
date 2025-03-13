"""
Topic selection utilities for task generation.
Handles topic selection and weighting based on user confidence.
"""

import random
from app.models.curriculum import Topic
from app.models.confidence import TopicConfidence

def select_weighted_topic(topics, user, subject_code):
    """
    Select a topic with weighting based on confidence.
    Topics with lower confidence levels are weighted more heavily.
    
    Args:
        topics: List of Topic objects to choose from
        user: User object for confidence lookup
        subject_code: Subject code for confidence keys
    
    Returns:
        The selected topic object.
    """
    if not topics:
        return None
    
    # Get confidences for all topics
    weighted_topics = []
    
    for topic in topics:
        # Generate topic key for confidence lookup
        topic_key = f"{subject_code}_{topic.name.replace(' ', '_') if topic.name else topic.title.replace(' ', '_')}"
        
        # Get confidence for this topic
        confidence = TopicConfidence.query.filter_by(
            user_id=user.id,
            topic_id=topic.id,
            topic_key=topic_key
        ).first()
        
        # Default confidence level if none exists
        confidence_level = confidence.confidence_level if confidence else 3
        
        # Weight calculation: (7 - confidence_level)²
        weight = (7 - confidence_level) ** 2
        
        weighted_topics.append((topic, weight))
    
    # Perform weighted random selection
    total_weight = sum(weight for _, weight in weighted_topics)
    
    if total_weight == 0:
        # Fallback to random selection if all weights are zero
        return random.choice(topics)
    
    # Random selection with weights
    r = random.uniform(0, total_weight)
    current_weight = 0
    
    for topic, weight in weighted_topics:
        current_weight += weight
        if r <= current_weight:
            return topic
    
    # Fallback (should not be reached)
    return topics[0]

def get_topics_for_subject(subject_id, include_nested=True):
    """
    Get topics for a subject, handling special cases like Psychology with nested topics.
    
    Args:
        subject_id: ID of the subject to get topics for
        include_nested: Whether to include nested topics (default: True)
        
    Returns:
        List of Topic objects
    """
    # Check if this is a nested structure (Psychology)
    paper_topics = Topic.query.filter_by(subject_id=subject_id, parent_topic_id=None).all()
    
    # If this is a standard (non-nested) subject or if include_nested is False
    if len(paper_topics) == 0 or not include_nested:
        return Topic.query.filter_by(subject_id=subject_id).all()
    
    return paper_topics

def get_subtopic_categories(paper_topic_id):
    """
    Get subtopic categories for a paper topic (Psychology).
    
    Args:
        paper_topic_id: ID of the paper topic to get categories for
        
    Returns:
        List of Topic objects representing subtopic categories
    """
    return Topic.query.filter_by(parent_topic_id=paper_topic_id).all()

def calculate_topic_priority(user_id, topic_id, days_threshold=14):
    """
    Calculate priority for a topic based on user confidence and last practice.
    
    Args:
        user_id: User ID to calculate priority for
        topic_id: Topic ID to calculate priority for
        days_threshold: Number of days after which a topic needs review
        
    Returns:
        Priority score (higher means higher priority)
    """
    from datetime import datetime, timedelta
    from app.models.task import Task
    
    # Get the topic confidence
    confidence = TopicConfidence.query.filter_by(
        user_id=user_id,
        topic_id=topic_id
    ).first()
    
    # Base priority on confidence
    base_priority = 5 - (confidence.confidence_level if confidence else 3)
    
    # Calculate days since last practice
    threshold_date = datetime.utcnow() - timedelta(days=days_threshold)
    
    # Find most recent task for this topic
    most_recent_task = Task.query.filter_by(
        user_id=user_id,
        topic_id=topic_id
    ).order_by(Task.created_at.desc()).first()
    
    # If no recent task or task is older than threshold, increase priority
    if not most_recent_task or most_recent_task.created_at < threshold_date:
        base_priority += 2
    
    # If topic is marked as priority, boost it
    if confidence and confidence.priority:
        base_priority += 3
    
    return base_priority
