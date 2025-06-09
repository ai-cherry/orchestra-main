"""
Database models for the feedback system.

This module defines the SQLAlchemy models for the feedback system,
including feedback entries, themes, and metrics.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel

Base = declarative_base()


class Feedback(Base):
    """Feedback table for storing user feedback."""
    
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50))
    feedback_text = Column(Text, nullable=False)
    sentiment = Column(String(20))
    source = Column(String(50))
    context_data = Column(JSON)
    persona_id = Column(String(50))
    task_id = Column(String(50))
    rating = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    theme_mappings = relationship("FeedbackThemeMapping", back_populates="feedback")
    
    def __repr__(self):
        return f"<Feedback(id={self.id}, user_id='{self.user_id}', sentiment='{self.sentiment}')>"


class FeedbackTheme(Base):
    """Themes extracted from feedback."""
    
    __tablename__ = "feedback_themes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    theme_name = Column(String(100), nullable=False)
    theme_keywords = Column(ARRAY(String))
    sentiment_distribution = Column(JSON)
    feedback_count = Column(Integer, default=0)
    first_detected_at = Column(DateTime, default=datetime.utcnow)
    last_detected_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    feedback_mappings = relationship("FeedbackThemeMapping", back_populates="theme")
    
    def __repr__(self):
        return f"<FeedbackTheme(id={self.id}, name='{self.theme_name}', count={self.feedback_count})>"


class FeedbackThemeMapping(Base):
    """Junction table for feedback-theme many-to-many relationship."""
    
    __tablename__ = "feedback_theme_mapping"
    
    feedback_id = Column(Integer, ForeignKey("feedback.id"), primary_key=True)
    theme_id = Column(Integer, ForeignKey("feedback_themes.id"), primary_key=True)
    confidence_score = Column(Float)
    
    # Relationships
    feedback = relationship("Feedback", back_populates="theme_mappings")
    theme = relationship("FeedbackTheme", back_populates="feedback_mappings")
    
    def __repr__(self):
        return f"<FeedbackThemeMapping(feedback_id={self.feedback_id}, theme_id={self.theme_id})>"


class PersonaFeedbackMetrics(Base):
    """Aggregated feedback metrics for personas."""
    
    __tablename__ = "persona_feedback_metrics"
    
    persona_id = Column(String(50), primary_key=True)
    time_period = Column(String(20), primary_key=True)
    period_start = Column(DateTime, primary_key=True)
    period_end = Column(DateTime)
    positive_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    average_rating = Column(Float)
    common_themes = Column(JSON)
    
    def __repr__(self):
        return f"<PersonaFeedbackMetrics(persona_id='{self.persona_id}', period='{self.time_period}')>"


# Pydantic models for API requests/responses

class FeedbackCreate(BaseModel):
    """Schema for creating a new feedback entry."""
    
    user_id: Optional[str] = None
    feedback_text: str
    source: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None
    persona_id: Optional[str] = None
    task_id: Optional[str] = None
    rating: Optional[int] = None
    
    class Config:
        orm_mode = True


class FeedbackResponse(BaseModel):
    """Schema for feedback response."""
    
    id: int
    user_id: Optional[str] = None
    feedback_text: str
    sentiment: str
    source: Optional[str] = None
    persona_id: Optional[str] = None
    task_id: Optional[str] = None
    rating: Optional[int] = None
    created_at: datetime
    
    class Config:
        orm_mode = True


class ThemeResponse(BaseModel):
    """Schema for theme response."""
    
    id: int
    theme_name: str
    theme_keywords: List[str]
    feedback_count: int
    sentiment_distribution: Dict[str, int]
    
    class Config:
        orm_mode = True


class FeedbackAnalyticsResponse(BaseModel):
    """Schema for feedback analytics response."""
    
    total_count: int
    sentiment_distribution: Dict[str, int]
    average_rating: Optional[float] = None
    common_themes: List[ThemeResponse]
    time_series: Optional[Dict[str, Any]] = None
    
    class Config:
        orm_mode = True
