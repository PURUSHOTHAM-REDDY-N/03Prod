"""
Test script for subject distribution in task generation.
Verifies that Biology subjects are not overrepresented in task selection.
"""

import sys
from collections import Counter
# Removing matplotlib dependency
from flask import current_app
from app import create_app, db
from app.models.user import User
from app.models.curriculum import Subject
from app.utils.task_generator_main import generate_replacement_task
from app.utils.task_subject_utils import get_subject_distribution_for_week, select_subject_based_on_distribution

def test_subject_distribution(sample_size=100):
    """
    Test subject distribution by generating multiple tasks and counting subject frequencies.
    
    Args:
        sample_size: Number of tasks to generate for testing
        
    Returns:
        A Counter object with subject titles and their frequencies
    """
    print(f"\n=== Testing Subject Distribution with {sample_size} Tasks ===")
    
    # Get a test user
    user = User.query.first()
    if not user:
        print("Error: No users found. Please create a user first.")
        return None
    
    print(f"Using test user: {user.username} (ID: {user.id})")
    
    # Get all subjects
    subjects = Subject.query.all()
    if not subjects:
        print("Error: No subjects found. Please import curriculum data first.")
        return None
    
    print(f"Found {len(subjects)} subjects:")
    for subject in subjects:
        print(f"  - {subject.title} (ID: {subject.id})")
    
    # Get expected distribution
    distribution = get_subject_distribution_for_week(user)
    print("\nExpected distribution:")
    for subject_id, weight in distribution.items():
        subject = Subject.query.get(subject_id)
        if subject:
            print(f"  - {subject.title}: {weight:.2f}")
    
    # Count Biology subjects
    biology_subjects = [s for s in subjects if "Biology" in s.title]
    print(f"\nBiology subjects: {len(biology_subjects)}")
    for subject in biology_subjects:
        print(f"  - {subject.title} (ID: {subject.id})")
    
    # Test direct subject selection
    print("\nTesting subject selection directly:")
    direct_selection_counts = Counter()
    
    for _ in range(sample_size):
        selected_subject = select_subject_based_on_distribution(subjects, distribution)
        if selected_subject:
            direct_selection_counts[selected_subject.title] += 1
    
    print("Direct selection frequencies:")
    for subject_title, count in direct_selection_counts.items():
        percentage = (count / sample_size) * 100
        print(f"  - {subject_title}: {count} times ({percentage:.1f}%)")
    
    # Test task generation
    print("\nTesting task generation:")
    task_subject_counts = Counter()
    
    for i in range(sample_size):
        if i % 10 == 0:
            print(f"  Generating task {i+1}/{sample_size}...")
        
        task = generate_replacement_task(user)
        if task:
            subject = Subject.query.get(task.subject_id)
            if subject:
                task_subject_counts[subject.title] += 1
    
    print("\nTask generation subject frequencies:")
    for subject_title, count in task_subject_counts.items():
        percentage = (count / sample_size) * 100
        print(f"  - {subject_title}: {count} times ({percentage:.1f}%)")
    
    # Calculate expected frequencies
    print("\nAnalyzing Biology representation:")
    
    # Group Biology subjects
    biology_count = sum(count for title, count in task_subject_counts.items() if "Biology" in title)
    biology_percentage = (biology_count / sample_size) * 100
    
    # Expected Biology percentage (assuming equal distribution among main subjects)
    main_subject_categories = len([s for s in subjects if "Biology" not in s.title]) + 1  # +1 for all Biology
    expected_percentage = (1 / main_subject_categories) * 100
    
    print(f"  All Biology subjects combined: {biology_count} times ({biology_percentage:.1f}%)")
    print(f"  Expected frequency (fair distribution): {expected_percentage:.1f}%")
    print(f"  Ratio (actual/expected): {biology_percentage/expected_percentage:.2f}")
    
    # If Biology is close to the expected frequency, the fix worked
    if 0.8 <= (biology_percentage/expected_percentage) <= 1.2:
        print("\n✅ Biology representation is balanced (within 20% of expected frequency)")
    else:
        print("\n❌ Biology is still not balanced correctly")
    
    # Skip visualization code since matplotlib is not available
    print("\nNote: Visualization skipped - matplotlib not available")
    
    return task_subject_counts

if __name__ == "__main__":
    try:
        # Create app context for testing
        app = create_app()
        with app.app_context():
            # Test with 100 samples
            counts = test_subject_distribution(100)
            
            if counts:
                print("\n✅ Subject distribution test completed")
                sys.exit(0)
            else:
                print("\n❌ Subject distribution test failed")
                sys.exit(1)
    except Exception as e:
        print(f"Error running test: {str(e)}")
        sys.exit(1)
