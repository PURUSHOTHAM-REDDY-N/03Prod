from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models.curriculum import Subject, Topic, Subtopic
from app.models.confidence import TopicConfidence, SubtopicConfidence

# Create API blueprint for curriculum
curriculum_bp = Blueprint('curriculum_api', __name__, url_prefix='/api/curriculum')

@curriculum_bp.route('/subjects')
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

@curriculum_bp.route('/subject/<int:subject_id>/topics')
@login_required
def get_topics(subject_id):
    """API endpoint to get topics for a subject."""
    topics = Topic.query.filter_by(subject_id=subject_id).all()
    
    if not topics:
        return jsonify({'topics': []})
    
    # Get the subject title
    subject = Subject.query.get(subject_id)
    
    # Filter out specific Psychology topics with 0 subtopics
    if subject and subject.title == "Psychology":
        topics = [topic for topic in topics if topic.title not in [
            "Introductory Topics in Psychology - 0 subtopics",
            "Psychology in Context - 0 subtopics",
            "Issues and Options in Psychology - 0 subtopics"
        ]]
    
    # Import here to avoid circular import
    from app.models.confidence import calculate_topic_confidence
    
    result = []
    for topic in topics:
        # Calculate confidence for this topic based on its subtopics (now 1-100 scale)
        confidence_level = calculate_topic_confidence(current_user.id, topic.id)
        
        # Get priority status
        confidence = TopicConfidence.query.filter_by(
            user_id=current_user.id,
            topic_id=topic.id
        ).first()
        
        priority = False
        if confidence:
            priority = confidence.priority
        
        result.append({
            'id': topic.id,
            'name': topic.name,
            'title': topic.title,
            'description': topic.description,
            'subtopics_count': len(topic.subtopics),
            'confidence_level': confidence_level,
            'priority': priority
        })
    
    return jsonify({'topics': result})

@curriculum_bp.route('/topic/<int:topic_id>/subtopics')
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
        
        # Default to 3 for subtopics if no confidence record exists
        # This matches the model default
        confidence_level = 3
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

@curriculum_bp.route('/search')
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

@curriculum_bp.route('/user/confidence')
@login_required
def get_user_confidence():
    """API endpoint to get user's confidence data."""
    # Get user's subtopic confidences
    subtopic_confidences = SubtopicConfidence.query.filter_by(user_id=current_user.id).all()
    
    # Get user's topic confidences
    topic_confidences = TopicConfidence.query.filter_by(user_id=current_user.id).all()
    
    return jsonify({
        'confidences': [
            {
                'subtopic_id': conf.subtopic_id,
                'level': conf.confidence_level,
                'priority': conf.priority,
                'last_updated': conf.last_updated.isoformat() if conf.last_updated else None
            }
            for conf in subtopic_confidences
        ],
        'topic_confidences': [
            {
                'topic_id': conf.topic_id,
                'level': conf.confidence_level,
                'priority': conf.priority,
                'last_updated': conf.last_updated.isoformat() if conf.last_updated else None
            }
            for conf in topic_confidences
        ]
    })

@curriculum_bp.route('/subtopic/<int:subtopic_id>/confidence', methods=['POST'])
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
            subtopic_id=subtopic_id,
            confidence_level=3  # Explicitly set default value
        )
        db.session.add(confidence)
    
    # Update the confidence level
    confidence.update_confidence(confidence_level)
    db.session.commit()
    
    # Update the parent topic's confidence - import here to avoid circular imports
    from app.utils.confidence_utils import update_topic_confidence
    new_topic_confidence = update_topic_confidence(current_user.id, subtopic.topic_id)
    
    # Get more info about the topic to return to the client
    topic = Topic.query.get(subtopic.topic_id)
    
    return jsonify({
        'success': True,
        'subtopic': {
            'id': subtopic.id,
            'confidence_level': confidence_level
        },
        'topic': {
            'id': topic.id,
            'title': topic.title,
            'confidence_level': new_topic_confidence,
            'subtopics_count': len(topic.subtopics)
        }
    })

@curriculum_bp.route('/subtopic/<int:subtopic_id>/priority', methods=['POST'])
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
            subtopic_id=subtopic_id,
            confidence_level=3  # Explicitly set default value
        )
        db.session.add(confidence)
    
    confidence.toggle_priority()
    db.session.commit()
    
    # Update the parent topic's confidence to ensure everything stays in sync
    from app.utils.confidence_utils import update_topic_confidence
    new_topic_confidence = update_topic_confidence(current_user.id, subtopic.topic_id)
    
    # Get more info about the topic to return to the client
    topic = Topic.query.get(subtopic.topic_id)
    
    return jsonify({
        'success': True, 
        'priority': confidence.priority,
        'topic': {
            'id': topic.id,
            'title': topic.title,
            'confidence_level': new_topic_confidence,
            'subtopics_count': len(topic.subtopics)
        }
    })

@curriculum_bp.route('/topic/<int:topic_id>/confidence', methods=['POST'])
@login_required
def update_topic_confidence(topic_id):
    """Endpoint for topic confidence updates (disabled as topic confidence is derived from subtopics)."""
    # Topic confidence should not be directly editable as it's calculated from subtopics
    return jsonify({
        'success': False, 
        'error': 'Topic confidence cannot be directly set. It is automatically calculated as the average of subtopic confidences.'
    }), 400

@curriculum_bp.route('/topic/<int:topic_id>/priority', methods=['POST'])
@login_required
def toggle_topic_priority(topic_id):
    """Toggle priority flag for a topic."""
    # Verify topic exists
    topic = Topic.query.get(topic_id)
    if not topic:
        return jsonify({'success': False, 'error': 'Topic not found'}), 404
    
    # Get or create the confidence record
    confidence = TopicConfidence.query.filter_by(
        user_id=current_user.id,
        topic_id=topic_id
    ).first()
    
    if not confidence:
        confidence = TopicConfidence(
            user_id=current_user.id,
            topic_id=topic_id
        )
        db.session.add(confidence)
    
    confidence.toggle_priority()
    db.session.commit()
    
    return jsonify({'success': True, 'priority': confidence.priority})
