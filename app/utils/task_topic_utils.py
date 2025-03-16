"""
Topic selection utilities for task generation.
Handles topic selection for curriculum-based task generation.
"""

import random
from app.models.curriculum import Topic
from app.models.confidence import TopicConfidence

def select_weighted_topic(topics, user, subject_code):
    """
    Select a topic using confidence-based weighted selection.
    Uses the formula (7 - confidence_level)² to prioritize lower confidence topics.
    
    Args:
        topics: List of Topic objects to choose from
        user: User object
        subject_code: Subject code
    
    Returns:
        The selected topic object.
    """
    if not topics:
        return None
    
    # Get confidence levels for all topics in one query
    topic_ids = [topic.id for topic in topics]
    
    try:
        # Query topic confidence data for this user and these topics
        confidence_data = TopicConfidence.query.filter(
            TopicConfidence.user_id == user.id,
            TopicConfidence.topic_id.in_(topic_ids)
        ).all()
        
        # Create dictionary for quick lookup
        confidence_dict = {conf.topic_id: conf.confidence_percent for conf in confidence_data}
        
        # If no confidence data exists, initialize with default weights
        if not confidence_dict:
            # Default to equal selection if no confidence data
            return random.choice(topics)
        
        # Apply weighting formula (7 - confidence_level)²
        # Higher weight = higher priority for selection
        topic_weights = []
        
        for topic in topics:
            # Get confidence level (default to 3 if not found - 50% confidence)
            confidence_percent = confidence_dict.get(topic.id, 50.0)
            
            # Convert percentage (0-100) to scale (1-5)
            confidence_level = confidence_percent / 20  # 100% → 5, 80% → 4, etc.
                
            # Apply formula: (7 - confidence_level)²
            # This gives higher weights to topics with lower confidence
            weight = (7 - confidence_level) ** 2
            
            topic_weights.append((topic, weight))
        
        # Calculate total weight for normalization
        total_weight = sum(weight for _, weight in topic_weights)
        
        # Handle edge case of zero total weight
        if total_weight == 0:
            return random.choice(topics)
        
        # Weighted random selection (roulette wheel)
        r = random.uniform(0, total_weight)
        current_weight = 0
        
        for topic, weight in topic_weights:
            current_weight += weight
            if r <= current_weight:
                return topic
        
        # Fallback (should not be reached)
        return topics[0]
        
    except Exception as e:
        # Log the error but don't crash - fall back to random selection
        from flask import current_app
        current_app.logger.error(f"Error in topic selection: {str(e)}")
        return random.choice(topics)

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
    Calculate priority for a topic based on last practice.
    
    Args:
        user_id: User ID to calculate priority for
        topic_id: Topic ID to calculate priority for
        days_threshold: Number of days after which a topic needs review
        
    Returns:
        Priority score (higher means higher priority)
    """
    from datetime import datetime, timedelta
    from app.models.task import Task
    
    # Base priority score
    base_priority = 3
    
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
    
    return base_priority
