from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from app.models.curriculum import Subject, Topic, Subtopic
from app.models.task import Task, TaskType, TaskTypePreference
from app.utils.task_generator import generate_task_for_subject, get_subject_distribution_for_week
from app.utils.analytics_utils import prepare_analytics_data, get_chart_data_for_dashboard
from app.utils.optimization_utils import get_optimized_subject_distribution, generate_tasks_in_batch
import os

# Create blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    """Main dashboard with daily tasks."""
    # Get today's active tasks
    today = datetime.utcnow().date()
    
    active_tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.due_date == today,
        Task.completed_at.is_(None),
        Task.skipped_at.is_(None)
    ).all()
    
    # Get completed tasks for today
    completed_tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.due_date == today,
        Task.completed_at.isnot(None)
    ).all()
    
    # Generate tasks if none exist
    if not active_tasks and not completed_tasks:
        # Calculate how many tasks to create based on study hours
        study_hours = current_user.study_hours_per_day
        
        # Weekend adjustment
        if datetime.utcnow().weekday() >= 5:  # 5=Saturday, 6=Sunday
            study_hours = current_user.weekend_study_hours
        
        # Approximately 1 task per 30 minutes of study time
        num_tasks = max(1, int(study_hours * 2))
        
        try:
            # Generate tasks in batch (more efficient)
            # The function now returns a dictionary with tasks
            result = generate_tasks_in_batch(current_user.id, num_tasks)
            
            if result and result.get('success') and result.get('tasks'):
                active_tasks = result['tasks']
            else:
                # Fallback if tasks generation failed
                active_tasks = []
                if result and result.get('error'):
                    # Log the error for debugging
                    print(f"Error generating tasks: {result.get('error')}")
        except Exception as e:
            # Handle any exceptions
            print(f"Exception while generating tasks: {str(e)}")
            active_tasks = []
    
    return render_template('main/index.html', 
                           active_tasks=active_tasks,
                           completed_tasks=completed_tasks,
                           current_date=today)

@main_bp.route('/calendar')
@login_required
def calendar():
    """Calendar view with exam dates."""
    # Get all tasks for the current month
    now = datetime.utcnow()
    start_date = datetime(now.year, now.month, 1).date()
    
    # Calculate end date (last day of current month)
    if now.month == 12:
        end_date = datetime(now.year + 1, 1, 1).date() - timedelta(days=1)
    else:
        end_date = datetime(now.year, now.month + 1, 1).date() - timedelta(days=1)
    
    # Get tasks within the date range
    tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.due_date.between(start_date, end_date)
    ).all()
    
    # Organize tasks by date
    calendar_data = {}
    
    for task in tasks:
        date_str = task.due_date.strftime('%Y-%m-%d')
        if date_str not in calendar_data:
            calendar_data[date_str] = []
        
        calendar_data[date_str].append(task)
    
    return render_template('main/calendar.html', 
                           calendar_data=calendar_data,
                           current_date=now.date(),
                           timedelta=timedelta)

@main_bp.route('/curriculum')
@login_required
def curriculum():
    """Browse curriculum structure."""
    # Redirect to the curriculum blueprint
    return redirect(url_for('curriculum.view_curriculum'))


@main_bp.route('/progress')
@login_required
def progress():
    """View progress and statistics with advanced analytics."""
    # Get basic task stats
    total_tasks = Task.query.filter_by(user_id=current_user.id).count()
    completed_tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.completed_at.isnot(None)
    ).count()
    
    # Calculate completion percentage
    completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Get subject breakdown
    subjects = Subject.query.all()
    subject_stats = {}
    
    for subject in subjects:
        subject_total = Task.query.filter_by(
            user_id=current_user.id,
            subject_id=subject.id
        ).count()
        
        subject_completed = Task.query.filter(
            Task.user_id == current_user.id,
            Task.subject_id == subject.id,
            Task.completed_at.isnot(None)
        ).count()
        
        subject_percentage = (subject_completed / subject_total * 100) if subject_total > 0 else 0
        
        subject_stats[subject.id] = {
            'name': subject.title,
            'total': subject_total,
            'completed': subject_completed,
            'percentage': subject_percentage
        }
    
    # Get recent tasks (last 10)
    recent_tasks = Task.query.filter_by(
        user_id=current_user.id
    ).order_by(Task.created_at.desc()).limit(10).all()
    
    # Get advanced analytics data
    analytics_data = prepare_analytics_data(current_user.id)
    
    # Prepare chart data in the format needed by Chart.js
    chart_data = get_chart_data_for_dashboard(current_user.id)
    
    return render_template('main/progress.html',
                           total_tasks=total_tasks,
                           completed_tasks=completed_tasks,
                           completion_percentage=completion_percentage,
                           subject_stats=subject_stats,
                           recent_tasks=recent_tasks,
                           analytics=analytics_data,
                           chart_data=chart_data)

@main_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """User settings page."""
    if request.method == 'POST':
        # Update study preferences
        study_hours = request.form.get('study_hours', type=float)
        weekend_hours = request.form.get('weekend_hours', type=float)
        
        if study_hours is not None:
            current_user.study_hours_per_day = max(0.5, min(12, study_hours))
        
        if weekend_hours is not None:
            current_user.weekend_study_hours = max(0, min(12, weekend_hours))
        
        # Update task type preferences
        task_types = TaskType.query.all()
        subjects = Subject.query.all()
        
        # Process global preferences
        for task_type in task_types:
            enabled = request.form.get(f'task_type_{task_type.id}') == 'on'
            
            # Get or create preference
            preference = TaskTypePreference.query.filter_by(
                user_id=current_user.id,
                task_type_id=task_type.id,
                subject_id=None  # Global preference
            ).first()
            
            if not preference:
                preference = TaskTypePreference(
                    user_id=current_user.id,
                    task_type_id=task_type.id,
                    is_enabled=enabled
                )
                db.session.add(preference)
            else:
                preference.is_enabled = enabled
        
        # Process subject-specific preferences
        for subject in subjects:
            # Check if Uplearn is enabled for this subject
            uplearn_enabled = request.form.get(f'uplearn_subject_{subject.id}') == 'on'
            uplearn_type = TaskType.query.filter_by(name='uplearn').first()
            
            if uplearn_type:
                # Get or create preference
                preference = TaskTypePreference.query.filter_by(
                    user_id=current_user.id,
                    task_type_id=uplearn_type.id,
                    subject_id=subject.id
                ).first()
                
                if not preference:
                    preference = TaskTypePreference(
                        user_id=current_user.id,
                        task_type_id=uplearn_type.id,
                        subject_id=subject.id,
                        is_enabled=uplearn_enabled
                    )
                    db.session.add(preference)
                else:
                    preference.is_enabled = uplearn_enabled
        
        # Update dark mode preference
        dark_mode = request.form.get('dark_mode') == 'on'
        current_user.dark_mode = dark_mode
        
        db.session.commit()
        flash('Settings updated successfully', 'success')
        return redirect(url_for('main.settings'))
    
    # Get task types
    task_types = TaskType.query.all()
    
    # Get subjects
    subjects = Subject.query.all()
    
    # Get task type preferences
    global_preferences = {}
    subject_preferences = {}
    
    for task_type in task_types:
        # Get global preference
        preference = TaskTypePreference.query.filter_by(
            user_id=current_user.id,
            task_type_id=task_type.id,
            subject_id=None
        ).first()
        
        global_preferences[task_type.id] = preference.is_enabled if preference else True
        
        # Get subject-specific preferences
        if task_type.name == 'uplearn':
            for subject in subjects:
                preference = TaskTypePreference.query.filter_by(
                    user_id=current_user.id,
                    task_type_id=task_type.id,
                    subject_id=subject.id
                ).first()
                
                if subject.id not in subject_preferences:
                    subject_preferences[subject.id] = {}
                
                subject_preferences[subject.id][task_type.id] = preference.is_enabled if preference else False
    
    return render_template('main/settings.html',
                           task_types=task_types,
                           subjects=subjects,
                           global_preferences=global_preferences,
                           subject_preferences=subject_preferences)

@main_bp.route('/pomodoro')
@login_required
def pomodoro():
    """Pomodoro timer with task integration."""
    # Get today's active tasks
    today = datetime.utcnow().date()
    
    active_tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.due_date == today,
        Task.completed_at.is_(None),
        Task.skipped_at.is_(None)
    ).all()
    
    return render_template('main/pomodoro.html', active_tasks=active_tasks)

@main_bp.route('/first-login-setup', methods=['GET', 'POST'])
@login_required
def first_login_setup():
    """First-time user setup."""
    if session.get('setup_complete', False):
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # Process study preferences
        study_hours = request.form.get('study_hours', type=float)
        weekend_hours = request.form.get('weekend_hours', type=float)
        
        if study_hours is not None:
            current_user.study_hours_per_day = max(0.5, min(12, study_hours))
        
        if weekend_hours is not None:
            current_user.weekend_study_hours = max(0, min(12, weekend_hours))
        
        # Process subject selections
        subjects = Subject.query.all()
        for subject in subjects:
            enabled = request.form.get(f'subject_{subject.id}') == 'on'
            
            # We might want to add a "SubjectPreference" model in the future
            # For now, we'll just note this in the UI and not enforce it in the backend
        
        # Process task type preferences
        task_types = TaskType.query.all()
        for task_type in task_types:
            enabled = request.form.get(f'task_type_{task_type.id}') == 'on'
            
            # Get or create preference
            preference = TaskTypePreference.query.filter_by(
                user_id=current_user.id,
                task_type_id=task_type.id,
                subject_id=None  # Global preference
            ).first()
            
            if not preference:
                preference = TaskTypePreference(
                    user_id=current_user.id,
                    task_type_id=task_type.id,
                    is_enabled=enabled
                )
                db.session.add(preference)
            else:
                preference.is_enabled = enabled
        
        # Process blank subject setup (if applicable)
        # We would handle this in a more advanced implementation
        
        db.session.commit()
        
        # Mark setup as complete
        session['setup_complete'] = True
        
        flash('Initial setup completed successfully!', 'success')
        return redirect(url_for('main.index'))
    
    # Get subjects and task types for the form
    subjects = Subject.query.all()
    task_types = TaskType.query.all()
    
    return render_template('main/first_login_setup.html',
                           subjects=subjects,
                           task_types=task_types)
