from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models.curriculum import Subject, Topic, Subtopic
from app.models.confidence import TopicConfidence, SubtopicConfidence

# Create a blueprint for curriculum routes
curriculum = Blueprint('curriculum', __name__)

@curriculum.route('/')
@login_required
def view_curriculum():
    """Curriculum browser view."""
    # Get all subjects
    subjects = Subject.query.all()
    return render_template('curriculum/index.html', subjects=subjects)

@curriculum.route('/api/subjects')
@login_required
def get_subjects():
    """API endpoint to get all subjects."""
    subjects = Subject.query.all()
    return jsonify({
        'subjects': [
            {
                'id': subject.id,
                'title': subject.title,
                'description': subject.description,
                'topic_count': len(subject.topics)
            }
            for subject in subjects
        ]
    })

@curriculum.route('/api/subject/<int:subject_id>/topics')
@login_required
def get_topics(subject_id):
    """API endpoint to get topics for a subject."""
    topics = Topic.query.filter_by(subject_id=subject_id).all()
    
    if not topics:
        return jsonify({'topics': []})
    
    return jsonify({
        'topics': [
            {
                'id': topic.id,
                'name': topic.name,
                'title': topic.title,
                'description': topic.description,
                'subtopics_count': len(topic.subtopics)
            }
            for topic in topics
        ]
    })

@curriculum.route('/api/topic/<int:topic_id>/subtopics')
@login_required
def get_subtopics(topic_id):
    """API endpoint to get subtopics for a topic."""
    subtopics = Subtopic.query.filter_by(topic_id=topic_id).all()
    
    if not subtopics:
        return jsonify({'subtopics': []})
    
    result = []
    for subtopic in subtopics:
        # Get user's confidence for this subtopic
        confidence = SubtopicConfidence.query.filter_by(
            user_id=current_user.id,
            subtopic_id=subtopic.id
        ).first()
        
        confidence_level = 1
        priority = False
        if confidence:
            confidence_level = confidence.confidence_level
            priority = confidence.priority
        
        result.append({
            'id': subtopic.id,
            'title': subtopic.title,
            'description': subtopic.description,
            'estimated_duration': subtopic.estimated_duration,
            'confidence_level': confidence_level,
            'priority': priority
        })
    
    return jsonify({'subtopics': result})

@curriculum.route('/api/curriculum/search')
@login_required
def search_curriculum():
    """API endpoint for curriculum search."""
    query = request.args.get('q', '').lower()
    if not query or len(query) < 2:
        return jsonify({'results': []})
    
    # Search subjects
    subjects = Subject.query.filter(Subject.title.ilike(f'%{query}%')).all()
    
    # Search topics
    topics = Topic.query.filter(Topic.title.ilike(f'%{query}%')).all()
    
    # Search subtopics
    subtopics = Subtopic.query.filter(Subtopic.title.ilike(f'%{query}%')).all()
    
    results = {
        'subjects': [{'id': s.id, 'title': s.title} for s in subjects],
        'topics': [{'id': t.id, 'title': t.title, 'subject_id': t.subject_id} for t in topics],
        'subtopics': [{'id': st.id, 'title': st.title, 'topic_id': st.topic_id} for st in subtopics]
    }
    
    return jsonify({'results': results})

@curriculum.route('/api/user/confidence')
@login_required
def get_user_confidence():
    """API endpoint to get user's confidence data."""
    # Get user's subtopic confidences
    subtopic_confidences = SubtopicConfidence.query.filter_by(user_id=current_user.id).all()
    
    return jsonify({
        'confidences': [
            {
                'subtopic_id': conf.subtopic_id,
                'level': conf.confidence_level,
                'priority': conf.priority,
                'last_updated': conf.last_updated.isoformat() if conf.last_updated else None
            }
            for conf in subtopic_confidences
        ]
    })

@curriculum.route('/api/subtopic/<int:subtopic_id>/confidence', methods=['POST'])
@login_required
def update_subtopic_confidence(subtopic_id):
    """Update a user's confidence level for a subtopic."""
    data = request.get_json()
    confidence_level = data.get('level')
    
    if not confidence_level or not 1 <= confidence_level <= 5:
        return jsonify({'success': False, 'error': 'Invalid confidence level'}), 400
    
    # Verify subtopic exists
    subtopic = Subtopic.query.get(subtopic_id)
    if not subtopic:
        return jsonify({'success': False, 'error': 'Subtopic not found'}), 404
    
    # Get or create the confidence record
    confidence = SubtopicConfidence.query.filter_by(
        user_id=current_user.id,
        subtopic_id=subtopic_id
    ).first()
    
    if not confidence:
        confidence = SubtopicConfidence(
            user_id=current_user.id,
            subtopic_id=subtopic_id
        )
        db.session.add(confidence)
    
    confidence.update_confidence(confidence_level)
    db.session.commit()
    
    return jsonify({'success': True})

@curriculum.route('/api/subtopic/<int:subtopic_id>/priority', methods=['POST'])
@login_required
def toggle_subtopic_priority(subtopic_id):
    """Toggle priority flag for a subtopic."""
    # Verify subtopic exists
    subtopic = Subtopic.query.get(subtopic_id)
    if not subtopic:
        return jsonify({'success': False, 'error': 'Subtopic not found'}), 404
    
    # Get or create the confidence record
    confidence = SubtopicConfidence.query.filter_by(
        user_id=current_user.id,
        subtopic_id=subtopic_id
    ).first()
    
    if not confidence:
        confidence = SubtopicConfidence(
            user_id=current_user.id,
            subtopic_id=subtopic_id
        )
        db.session.add(confidence)
    
    confidence.toggle_priority()
    db.session.commit()
    
    return jsonify({'success': True, 'priority': confidence.priority})
