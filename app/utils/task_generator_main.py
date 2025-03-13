"""
Main task generation module.
Integrates subject, topic, and subtopic functionality to create tasks.
"""

import random
from datetime import datetime
from app import db
from app.models.curriculum import Subject
from app.models.task import Task, TaskType

from app.utils.task_subject_utils import (
    get_subject_distribution_for_week,
    select_subject_based_on_distribution
)
from app.utils.task_topic_utils import (
    select_weighted_topic,
    get_topics_for_subject,
    get_subtopic_categories
)
from app.utils.task_subtopic_utils import add_subtopics_to_task

def generate_task_for_subject(user, subject_id):
    """
    Generate a study task for a subject based on confidence levels.
    
    The process:
    1. Get the subject and available task types
    2. Check if Uplearn is enabled for this subject
    3. Select a topic weighted by confidence levels
    4. Create the task with appropriate task type
    5. Add subtopics to the task, prioritizing those needing attention
    
    Args:
        user: User object to generate task for
        subject_id: Subject ID to generate task for
        
    Returns:
        The created task object.
    """
    # Get the subject
    subject = Subject.query.get(subject_id)
    if not subject:
        return None
    
    # Get subject code for confidence keys
    subject_code = subject.get_subject_code()
    
    # Check if Uplearn is enabled for this subject
    uplearn_only = user.is_uplearn_enabled_for_subject(subject_id)
    
    # Get available task types
    if uplearn_only:
        # Only use Uplearn task type
        uplearn_id = TaskType.get_uplearn_id()
        if not uplearn_id:
            # Fallback if Uplearn type doesn't exist
            task_types = TaskType.query.all()
        else:
            task_types = [TaskType.query.get(uplearn_id)]
    else:
        # Use all enabled task types for the user
        task_types = user.get_enabled_task_types()
        
        # Fallback to all task types if none are enabled
        if not task_types:
            task_types = TaskType.query.all()
    
    if not task_types:
        return None
    
    # Select random task type from available options
    task_type = random.choice(task_types)
    
    # Get all topics for this subject
    if "Psychology" in subject.title:
        # Special handling for Psychology's nested structure
        # Get the paper topics (Paper 1, Paper 2, Paper 3)
        paper_topics = get_topics_for_subject(subject_id)
        
        # Select a paper topic weighted by confidence
        selected_paper = select_weighted_topic(paper_topics, user, subject_code)
        
        if not selected_paper:
            return None
        
        # Get subtopic categories under this paper
        subtopic_categories = get_subtopic_categories(selected_paper.id)
        
        # Select a subtopic category weighted by confidence
        selected_topic = select_weighted_topic(subtopic_categories, user, subject_code)
    else:
        # Normal subject structure
        topics = get_topics_for_subject(subject_id)
        
        # Select a topic weighted by confidence
        selected_topic = select_weighted_topic(topics, user, subject_code)
    
    if not selected_topic:
        return None
    
    # Create the task
    task = Task(
        user_id=user.id,
        subject_id=subject_id,
        task_type_id=task_type.id,
        title=f"{task_type.name.capitalize()}: {selected_topic.title}",
        description=selected_topic.description,
        topic_id=selected_topic.id,
        due_date=datetime.utcnow().date()
    )
    
    # Save task to get an ID
    db.session.add(task)
    db.session.commit()
    
    # Add subtopics to the task
    add_subtopics_to_task(task, selected_topic, user)
    
    return task

def generate_replacement_task(user, subject_id=None):
    """
    Generate a replacement task when one is skipped.
    If subject_id is provided, generates a task for that subject.
    Otherwise, selects a subject based on distribution.
    
    Args:
        user: User object to generate task for
        subject_id: Optional subject ID to generate task for
        
    Returns:
        The new task object.
    """
    if subject_id:
        # Generate a task for the specified subject
        return generate_task_for_subject(user, subject_id)
    
    # Get subject distribution
    distribution = get_subject_distribution_for_week(user)
    
    # Select subject based on distribution
    subjects = Subject.query.all()
    
    # Early return if no subjects exist
    if not subjects:
        return None
    
    selected_subject = select_subject_based_on_distribution(subjects, distribution)
    
    # Generate task for selected subject
    return generate_task_for_subject(user, selected_subject.id)
