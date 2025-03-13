from app import db
from datetime import datetime
# Import func directly from installed sqlalchemy package
import sqlalchemy
from sqlalchemy import func

def calculate_topic_confidence(user_id, topic_id):
    """
    Calculate the confidence level for a topic based on its subtopics.
    Only calculates if there are actual subtopic confidence records.
    
    Args:
        user_id (int): The user ID
        topic_id (int): The topic ID
        
    Returns:
        int or None: Calculated confidence level (1-100) as an integer, or None if no calculation is possible
    """
    from app.models.curriculum import Topic, Subtopic
    
    # Get all subtopics for this topic
    subtopics = Subtopic.query.filter_by(topic_id=topic_id).all()
    
    # If no subtopics exist for this topic, no calculation is possible
    if not subtopics:
        return None
    
    # Get confidence for these subtopics
    subtopic_ids = [subtopic.id for subtopic in subtopics]
    
    # Query for confidence data
    confidence_data = SubtopicConfidence.query.filter(
        SubtopicConfidence.user_id == user_id,
        SubtopicConfidence.subtopic_id.in_(subtopic_ids)
    ).all()
    
    # If no confidence data exists, no calculation is possible
    if not confidence_data:
        return None
    
    # Calculate average confidence (as a float, temporarily)
    total_confidence = sum(conf.confidence_level for conf in confidence_data)
    avg_confidence = total_confidence / len(confidence_data)
    
    # Convert from 1-5 scale to 1-100 scale with standard rounding
    confidence_percent = round((avg_confidence / 5) * 100)
    
    # Ensure result is between 1-100
    return max(1, min(100, confidence_percent))

class TopicConfidence(db.Model):
    """Model tracking user confidence for topics."""
    __tablename__ = 'topic_confidences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)
    confidence_level = db.Column(db.Integer, default=50)  # 1-100 scale
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    priority = db.Column(db.Boolean, default=False)
    
    # Use explicit relationship to match User model's existing backref
    # user = db.relationship('User', backref is already defined in User model
    topic = db.relationship('Topic', lazy=True)
    
    # Create a unique constraint for user+topic
    __table_args__ = (db.UniqueConstraint('user_id', 'topic_id'),)
    
    def update_confidence(self, level):
        """Update the confidence level and timestamp."""
        if 1 <= level <= 100:
            self.confidence_level = level
            self.last_updated = datetime.utcnow()
        
    def toggle_priority(self):
        """Toggle the priority flag."""
        self.priority = not self.priority
        self.last_updated = datetime.utcnow()
        
    def set_priority(self, priority):
        """Set the priority flag to a specific value."""
        self.priority = bool(priority)
        self.last_updated = datetime.utcnow()
    
    def __repr__(self):
        return f"<TopicConfidence user_id={self.user_id} topic_id={self.topic_id} level={self.confidence_level}>"

class SubtopicConfidence(db.Model):
    """Model tracking user confidence for subtopics."""
    __tablename__ = 'subtopic_confidences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subtopic_id = db.Column(db.Integer, db.ForeignKey('subtopics.id'), nullable=False)
    confidence_level = db.Column(db.Integer, default=3)  # 1-5 scale with default of 3
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    last_addressed_date = db.Column(db.DateTime, nullable=True)
    priority = db.Column(db.Boolean, default=False)
    
    # Use explicit relationship to match User model's existing backref
    # user = db.relationship('User', backref is already defined in User model
    subtopic = db.relationship('Subtopic', back_populates='confidences', lazy=True)
    
    # Create a unique constraint for user+subtopic
    __table_args__ = (db.UniqueConstraint('user_id', 'subtopic_id'),)
    
    def update_confidence(self, level):
        """Update the confidence level and timestamp."""
        if 1 <= level <= 5:
            self.confidence_level = level
            self.last_updated = datetime.utcnow()
        
    def mark_addressed(self):
        """Mark this subtopic as addressed and update timestamp."""
        self.last_addressed_date = datetime.utcnow()
        
    def toggle_priority(self):
        """Toggle the priority flag."""
        self.priority = not self.priority
        self.last_updated = datetime.utcnow()
        
    def set_priority(self, priority):
        """Set the priority flag to a specific value."""
        self.priority = bool(priority)
        self.last_updated = datetime.utcnow()
        
    def __repr__(self):
        return f"<SubtopicConfidence user_id={self.user_id} subtopic_id={self.subtopic_id} level={self.confidence_level}>"
