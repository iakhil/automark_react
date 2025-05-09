from extensions import db
from datetime import datetime

class Subscription(db.Model):
    """
    Subscription model for handling payments and service tiers
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stripe_customer_id = db.Column(db.String(255), unique=True)
    stripe_subscription_id = db.Column(db.String(255), unique=True)
    plan_type = db.Column(db.String(50))  # 'free', 'basic', 'premium'
    status = db.Column(db.String(50))  # 'active', 'canceled', 'past_due'
    current_period_end = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """
        Convert subscription object to dictionary for API responses
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'plan_type': self.plan_type,
            'status': self.status,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 