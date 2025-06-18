from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB
from decimal import Decimal

from .user import db

class EnhancedConversation(db.Model):
    __tablename__ = 'enhanced_conversations'

    id = db.Column(db.Integer, primary_key=True)
    gong_call_id = db.Column(db.String(255), unique=True)
    title = db.Column(db.Text)
    duration = db.Column(db.Integer)
    apartment_relevance = db.Column(db.Numeric(5, 2))
    business_value = db.Column(db.Numeric(12, 2))
    call_outcome = db.Column(db.String(100))
    competitive_mentions = db.Column(JSONB)
    sophia_insights = db.Column(JSONB)
    created_at = db.Column(db.DateTime, server_default=func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'gong_call_id': self.gong_call_id,
            'title': self.title,
            'duration': self.duration,
            'apartment_relevance': float(self.apartment_relevance) if isinstance(self.apartment_relevance, Decimal) else self.apartment_relevance,
            'business_value': float(self.business_value) if isinstance(self.business_value, Decimal) else self.business_value,
            'call_outcome': self.call_outcome,
            'competitive_mentions': self.competitive_mentions,
            'sophia_insights': self.sophia_insights,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
