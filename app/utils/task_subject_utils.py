"""
Subject selection utilities for task generation.
Handles subject distribution calculations and subject selection logic.
"""

import random
from datetime import datetime, timedelta
from sqlalchemy import text
from app import db
from app.models.curriculum import Subject, Topic

def get_subject_distribution_for_week(user):
    """
    Calculate a balanced subject distribution for the week.
    Handles special cases like Biology Y12/Y13 being counted together.
    
    Returns a dictionary with subject_id: percentage pairs.
    """
    # Get all subjects
    subjects = Subject.query.all()
    
    # If no subjects exist, return an empty dictionary
    if not subjects:
        return {}
    
    # Get tasks from the past week
    week_ago = datetime.utcnow() - timedelta(days=7)
    past_week_tasks = user.tasks.filter(
        db.and_(
            user.tasks.c.created_at >= week_ago
        )
    ).all()
    
    # Count tasks per subject
    subject_counts = {}
    biology_count = 0
    total_tasks = len(past_week_tasks)
    
    for task in past_week_tasks:
        # Special handling for Biology
        if "Biology" in task.subject.title:
            biology_count += 1
        else:
            subject_counts[task.subject_id] = subject_counts.get(task.subject_id, 0) + 1
    
    # Create balanced distribution
    distribution = {}
    
    # Handle no previous tasks case
    if total_tasks == 0:
        # Equal distribution - ensure we don't divide by zero
        equal_share = 1.0 / len(subjects) if subjects else 0
        
        # Handle Biology as one subject for distribution
        biology_subjects = [s for s in subjects if "Biology" in s.title]
        non_biology_subjects = [s for s in subjects if "Biology" not in s.title]
        
        # Assign equal share to biology as a whole
        if biology_subjects:
            biology_share = equal_share
            
            # Split biology share between Y12 and Y13 (weighted by topic count)
            bio_y12_topics = len(Topic.query.filter_by(subject_id=biology_subjects[0].id).all()) if len(biology_subjects) > 0 else 0
            bio_y13_topics = len(Topic.query.filter_by(subject_id=biology_subjects[1].id).all()) if len(biology_subjects) > 1 else 0
            
            total_bio_topics = bio_y12_topics + bio_y13_topics
            
            if total_bio_topics > 0:
                for subject in biology_subjects:
                    topic_count = len(Topic.query.filter_by(subject_id=subject.id).all())
                    # Safe division
                    distribution[subject.id] = biology_share * (topic_count / total_bio_topics) if total_bio_topics > 0 else 0
            else:
                # Equal split if no topic data
                for subject in biology_subjects:
                    distribution[subject.id] = biology_share / len(biology_subjects)
        
        # Assign share to other subjects
        for subject in non_biology_subjects:
            distribution[subject.id] = equal_share
    
    else:
        # Base distribution on past tasks but ensure balance
        # Subjects with fewer tasks get higher percentages
        
        # Calculate inverse frequency (subjects with fewer tasks get higher weighting)
        inverse_frequency = {}
        
        # Handle Biology specially
        biology_subjects = [s for s in subjects if "Biology" in s.title]
        if biology_subjects:
            bio_percentage = biology_count / total_tasks if total_tasks > 0 else 0
            
            # The less Biology appears, the more weight it should get
            bio_inverse = 1.0 - bio_percentage if bio_percentage > 0 else 1.0
            
            # Split between Biology Y12 and Y13 based on topic count
            bio_y12_topics = len(Topic.query.filter_by(subject_id=biology_subjects[0].id).all()) if len(biology_subjects) > 0 else 0
            bio_y13_topics = len(Topic.query.filter_by(subject_id=biology_subjects[1].id).all()) if len(biology_subjects) > 1 else 0
            
            total_bio_topics = bio_y12_topics + bio_y13_topics
            
            if total_bio_topics > 0:
                for subject in biology_subjects:
                    topic_count = len(Topic.query.filter_by(subject_id=subject.id).all())
                    inverse_frequency[subject.id] = bio_inverse * (topic_count / total_bio_topics)
            else:
                # Equal split if no topic data
                for subject in biology_subjects:
                    inverse_frequency[subject.id] = bio_inverse / len(biology_subjects)
        
        # Handle other subjects
        for subject in subjects:
            if "Biology" not in subject.title:
                subject_percentage = subject_counts.get(subject.id, 0) / total_tasks if total_tasks > 0 else 0
                inverse_frequency[subject.id] = 1.0 - subject_percentage if subject_percentage > 0 else 1.0
        
        # Normalize to make sum = 1.0
        total_inverse = sum(inverse_frequency.values())
        if total_inverse > 0:
            for subject_id, value in inverse_frequency.items():
                distribution[subject_id] = value / total_inverse
        else:
            # Fallback to equal distribution
            for subject in subjects:
                distribution[subject.id] = 1.0 / len(subjects)
    
    return distribution

def select_subject_based_on_distribution(subjects, distribution):
    """
    Select a subject based on the distribution weights.
    
    Args:
        subjects: List of Subject objects
        distribution: Dictionary with subject_id: weight pairs
        
    Returns:
        Selected Subject object or None if no subjects
    """
    if not subjects:
        return None
    
    # Create weighted list for selection
    subject_weights = [(subject, distribution.get(subject.id, 0)) for subject in subjects]
    
    # Filter out zero-weight subjects
    subject_weights = [(subject, weight) for subject, weight in subject_weights if weight > 0]
    
    if not subject_weights:
        # Fallback to equal weighting if all weights are zero
        subject_weights = [(subject, 1) for subject in subjects]
    
    # Calculate total weight
    total_weight = sum(weight for _, weight in subject_weights)
    
    if total_weight == 0:
        # Fallback to random selection if there are subjects
        if subjects:
            return random.choice(subjects)
        return None
    
    # Weighted random selection
    r = random.uniform(0, total_weight)
    current_weight = 0
    
    for subject, weight in subject_weights:
        current_weight += weight
        if r <= current_weight:
            return subject
    
    # Fallback (should not be reached)
    return subjects[0] if subjects else None
