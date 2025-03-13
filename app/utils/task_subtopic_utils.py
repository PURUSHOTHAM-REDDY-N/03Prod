"""
Subtopic utilities for task generation.
Handles subtopic selection, prioritization and task subtopic management.
"""

from app import db
from app.models.confidence import SubtopicConfidence
from app.models.task import TaskSubtopic

def add_subtopics_to_task(task, parent_topic, user, max_duration=30):
    """
    Add subtopics to a task, prioritizing those that need attention.
    Subtopics with priority=True and not recently addressed are added first.
    Remaining time is filled with weighted selection based on confidence.
    
    Args:
        task: Task object to add subtopics to
        parent_topic: Topic object containing subtopics
        user: User object for confidence lookup
        max_duration: Maximum duration (in minutes) for the combined subtopics
        
    Returns:
        The updated task object with subtopics added.
    """
    from app.models.curriculum import Subtopic
    
    # Get all subtopics for this topic
    subtopics = Subtopic.query.filter_by(topic_id=parent_topic.id).all()
    
    if not subtopics:
        return task
    
    # Identify prioritized subtopics needing attention
    prioritized_subtopics = []
    normal_subtopics = []
    
    for subtopic in subtopics:
        subtopic_key = subtopic.generate_subtopic_key()
        
        # Get confidence for this subtopic
        confidence = SubtopicConfidence.query.filter_by(
            user_id=user.id,
            subtopic_id=subtopic.id,
            subtopic_key=subtopic_key
        ).first()
        
        if confidence and confidence.priority and confidence.needs_attention():
            prioritized_subtopics.append((subtopic, confidence))
        else:
            # Default confidence level if none exists
            confidence_level = confidence.confidence_level if confidence else 3
            
            # Weight calculation with priority multiplier
            weight = (7 - confidence_level) ** 2
            if confidence and confidence.priority:
                weight *= 1.5
            
            normal_subtopics.append((subtopic, weight))
    
    # Add prioritized subtopics first
    remaining_duration = max_duration
    added_subtopics = []
    
    for subtopic, _ in prioritized_subtopics:
        if remaining_duration >= subtopic.estimated_duration:
            task_subtopic = TaskSubtopic(
                task_id=task.id,
                subtopic_id=subtopic.id,
                duration=subtopic.estimated_duration
            )
            db.session.add(task_subtopic)
            
            remaining_duration -= subtopic.estimated_duration
            added_subtopics.append(subtopic.title)
    
    # Fill remaining time with weighted selection
    if remaining_duration > 0 and normal_subtopics:
        # Sort by weight for weighted selection
        normal_subtopics.sort(key=lambda x: x[1], reverse=True)
        
        for subtopic, _ in normal_subtopics:
            if remaining_duration >= subtopic.estimated_duration and subtopic.title not in added_subtopics:
                task_subtopic = TaskSubtopic(
                    task_id=task.id,
                    subtopic_id=subtopic.id,
                    duration=subtopic.estimated_duration
                )
                db.session.add(task_subtopic)
                
                remaining_duration -= subtopic.estimated_duration
                added_subtopics.append(subtopic.title)
                
                # Stop if we've reached the target duration
                if remaining_duration < 15:  # Minimum subtopic duration
                    break
    
    # Commit changes
    db.session.commit()
    
    # Update task description with subtopics
    update_task_description_with_subtopics(task, added_subtopics, prioritized_subtopics)
    
    # Update total duration
    task.update_total_duration()
    
    return task

def update_task_description_with_subtopics(task, added_subtopics, prioritized_subtopics):
    """
    Update a task's description to include the list of subtopics and highlight priorities.
    
    Args:
        task: Task object to update
        added_subtopics: List of subtopic titles that were added to the task
        prioritized_subtopics: List of (subtopic, confidence) tuples that are prioritized
        
    Returns:
        None (updates task in place)
    """
    if not added_subtopics:
        return
    
    # Update task description to include the subtopics
    task_description = task.description or ""
    subtopics_list = ", ".join(added_subtopics)
    
    # Check if there are prioritized subtopics in this task
    prioritized_titles = [subtopic.title for subtopic, _ in prioritized_subtopics 
                        if subtopic.title in added_subtopics]
    
    if prioritized_titles:
        priority_text = f"\n\nThis task includes prioritized subtopics: {', '.join(prioritized_titles)}"
        task_description += priority_text
    
    # Update task description
    task.description = f"{task_description}\n\nSubtopics: {subtopics_list}"
    db.session.commit()

def get_subtopics_by_confidence(user, topic_id=None, min_confidence=None, max_confidence=None, prioritized_only=False):
    """
    Get subtopics filtered by confidence levels and prioritization.
    
    Args:
        user: User object to get subtopics for
        topic_id: Optional topic ID to filter subtopics by
        min_confidence: Minimum confidence level (inclusive)
        max_confidence: Maximum confidence level (inclusive)
        prioritized_only: Whether to only include prioritized subtopics
        
    Returns:
        List of subtopics matching the criteria
    """
    from app.models.curriculum import Subtopic
    
    # Start with a basic query
    query = Subtopic.query
    
    # Filter by topic if specified
    if topic_id is not None:
        query = query.filter_by(topic_id=topic_id)
    
    # Get all subtopics that match the base criteria
    subtopics = query.all()
    
    # If no confidence filtering is needed, return all subtopics
    if min_confidence is None and max_confidence is None and not prioritized_only:
        return subtopics
    
    # Get confidence data for the subtopics
    subtopic_ids = [s.id for s in subtopics]
    
    # No subtopics found
    if not subtopic_ids:
        return []
    
    confidences = SubtopicConfidence.query.filter(
        SubtopicConfidence.user_id == user.id,
        SubtopicConfidence.subtopic_id.in_(subtopic_ids)
    ).all()
    
    # Create a map of subtopic_id to confidence
    confidence_map = {c.subtopic_id: c for c in confidences}
    
    # Filter subtopics based on confidence criteria
    result = []
    for subtopic in subtopics:
        confidence = confidence_map.get(subtopic.id)
        
        # Skip if we need prioritized only and this isn't prioritized
        if prioritized_only and (not confidence or not confidence.priority):
            continue
        
        # Skip if confidence is below minimum
        if min_confidence is not None and (not confidence or confidence.confidence_level < min_confidence):
            continue
        
        # Skip if confidence is above maximum
        if max_confidence is not None and (not confidence or confidence.confidence_level > max_confidence):
            continue
        
        # Add confidence data to subtopic
        subtopic.confidence = confidence
        result.append(subtopic)
    
    return result
