from app import db
from app.models.curriculum import Subject, Topic, Subtopic
from app.models.confidence import TopicConfidence, SubtopicConfidence, calculate_topic_confidence

def update_topic_confidence(user_id, topic_id):
    """
    Update a topic's confidence level based on its subtopics.
    Only creates or updates a record if there are subtopic confidences to calculate from.
    
    Args:
        user_id (int): User ID
        topic_id (int): Topic ID
    
    Returns:
        int or None: The calculated confidence level (1-100) or None if not calculable
    """
    # Calculate the new confidence level
    confidence_level = calculate_topic_confidence(user_id, topic_id)
    
    # Only proceed if we have a valid calculation (based on actual subtopic confidences)
    if confidence_level is not None:
        # Get or create the confidence record
        confidence = TopicConfidence.query.filter_by(
            user_id=user_id,
            topic_id=topic_id
        ).first()
        
        if not confidence:
            confidence = TopicConfidence(
                user_id=user_id,
                topic_id=topic_id,
                confidence_level=confidence_level
            )
            db.session.add(confidence)
        else:
            # Update the record
            confidence.update_confidence(confidence_level)
        
        db.session.commit()
    
    return confidence_level

def update_subtopic_confidence(user_id, subtopic_id, level):
    """
    Update a subtopic's confidence level.
    
    Args:
        user_id (int): User ID
        subtopic_id (int): Subtopic ID
        level (int): New confidence level (1-5)
    
    Returns:
        bool: Success indicator
    """
    if not 1 <= level <= 5:
        return False
    
    # Get or create the confidence record
    confidence = SubtopicConfidence.query.filter_by(
        user_id=user_id,
        subtopic_id=subtopic_id
    ).first()
    
    if not confidence:
        confidence = SubtopicConfidence(
            user_id=user_id,
            subtopic_id=subtopic_id,
            confidence_level=3  # Default starting level
        )
        db.session.add(confidence)
    
    # Update the record
    confidence.update_confidence(level)
    db.session.commit()
    
    # Update the parent topic's confidence
    subtopic = Subtopic.query.get(subtopic_id)
    if subtopic:
        update_topic_confidence(user_id, subtopic.topic_id)
    
    return True

def get_subtopic_confidences_for_task(user_id, task_id):
    """
    Get all subtopic confidences for a specific task.
    
    Args:
        user_id (int): User ID
        task_id (int): Task ID
    
    Returns:
        dict: Dictionary of subtopic confidences
    """
    from app.models.task import TaskSubtopic
    
    # Get all subtopics for this task
    task_subtopics = TaskSubtopic.query.filter_by(task_id=task_id).all()
    subtopic_ids = [ts.subtopic_id for ts in task_subtopics]
    
    # Get confidence for these subtopics
    confidences = SubtopicConfidence.query.filter(
        SubtopicConfidence.user_id == user_id,
        SubtopicConfidence.subtopic_id.in_(subtopic_ids)
    ).all()
    
    # Build a dictionary of subtopic_id -> confidence_level
    result = {}
    for confidence in confidences:
        result[confidence.subtopic_id] = confidence.confidence_level
    
    # Add default level for any missing subtopics
    for subtopic_id in subtopic_ids:
        if subtopic_id not in result:
            result[subtopic_id] = 3  # Default confidence level
    
    return result

def update_subtopics_confidence_from_dict(user_id, confidence_dict):
    """
    Update confidence levels for multiple subtopics at once.
    
    Args:
        user_id (int): The user ID
        confidence_dict (dict): A dictionary of subtopic_id -> (confidence_level, priority)
        
    Returns:
        bool: Success indicator
    """
    try:
        # Process each subtopic
        for subtopic_id, (confidence_level, priority) in confidence_dict.items():
            # Skip invalid values
            if not 1 <= confidence_level <= 5:
                continue
                
            # Get or create confidence record
            confidence = SubtopicConfidence.query.filter_by(
                user_id=user_id,
                subtopic_id=subtopic_id
            ).first()
            
            if not confidence:
                # Get subtopic for key generation
                subtopic = Subtopic.query.get(subtopic_id)
                if not subtopic:
                    continue
                    
                # Create new record with default of 3
                confidence = SubtopicConfidence(
                    user_id=user_id,
                    subtopic_id=subtopic_id,
                    confidence_level=3
                )
                db.session.add(confidence)
                
            # Update confidence level
            confidence.update_confidence(confidence_level)
            
            # Update priority if provided
            if priority is not None:
                confidence.priority = priority
                
            # Update parent topic confidence
            subtopic = Subtopic.query.get(subtopic_id)
            if subtopic:
                update_topic_confidence(user_id, subtopic.topic_id)
                
        # Commit all changes
        db.session.commit()
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating confidences: {str(e)}")
        return False

def initialize_user_confidence(user_id):
    """
    Initialize confidence records for all subtopics for a user.
    Topic confidences are not initialized directly - they will be calculated
    when subtopic confidences are accessed or modified.
    
    Args:
        user_id (int): The ID of the user to initialize confidence for
    
    Returns:
        dict: Stats about the initialization process
    """
    stats = {
        'subtopics_initialized': 0,
        'errors': []
    }
    
    try:
        # Get all subtopics
        subtopics = Subtopic.query.all()
        
        # Initialize subtopic confidence records
        for subtopic in subtopics:
            # Skip if record already exists
            existing = SubtopicConfidence.query.filter_by(
                user_id=user_id,
                subtopic_id=subtopic.id
            ).first()
            
            if not existing:
                confidence = SubtopicConfidence(
                    user_id=user_id,
                    subtopic_id=subtopic.id,
                    confidence_level=3  # Default subtopic confidence is 3
                )
                db.session.add(confidence)
                stats['subtopics_initialized'] += 1
        
        # Commit all changes
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        stats['errors'].append(str(e))
    
    return stats
