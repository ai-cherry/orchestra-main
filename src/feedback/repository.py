"""
Repository for feedback data access.

This module provides a repository pattern implementation for accessing
and manipulating feedback data in the database.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import create_engine, func, desc, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

from .models import Feedback, FeedbackTheme, FeedbackThemeMapping, PersonaFeedbackMetrics
from .sentiment import analyze_sentiment
from .themes import extract_themes


class FeedbackRepository:
    """Repository for feedback data access."""
    
    def __init__(self, db_url: str):
        """
        Initialize the feedback repository.
        
        Args:
            db_url: Database connection URL
        """
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """Create all feedback-related tables if they don't exist."""
        Base = declarative_base()
        Base.metadata.create_all(bind=self.engine)
    
    def add_feedback(self, feedback_data: Dict[str, Any]) -> Feedback:
        """
        Add a new feedback entry.
        
        Args:
            feedback_data: Dictionary containing feedback data
            
        Returns:
            The created Feedback object
        """
        with self.SessionLocal() as session:
            # Analyze sentiment if not provided
            if 'sentiment' not in feedback_data:
                sentiment_result = analyze_sentiment(feedback_data['feedback_text'])
                feedback_data['sentiment'] = sentiment_result['sentiment']
            
            # Create feedback object
            feedback = Feedback(**feedback_data)
            session.add(feedback)
            session.commit()
            session.refresh(feedback)
            
            return feedback
    
    def get_feedback(self, feedback_id: int) -> Optional[Feedback]:
        """
        Get a feedback entry by ID.
        
        Args:
            feedback_id: ID of the feedback to retrieve
            
        Returns:
            The Feedback object if found, None otherwise
        """
        with self.SessionLocal() as session:
            return session.query(Feedback).filter(Feedback.id == feedback_id).first()
    
    def get_feedback_by_user(self, user_id: str, limit: int = 100) -> List[Feedback]:
        """
        Get feedback entries for a specific user.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of entries to return
            
        Returns:
            List of Feedback objects
        """
        with self.SessionLocal() as session:
            return session.query(Feedback)\
                .filter(Feedback.user_id == user_id)\
                .order_by(desc(Feedback.created_at))\
                .limit(limit)\
                .all()
    
    def get_feedback_by_persona(self, persona_id: str, limit: int = 100) -> List[Feedback]:
        """
        Get feedback entries for a specific persona.
        
        Args:
            persona_id: ID of the persona
            limit: Maximum number of entries to return
            
        Returns:
            List of Feedback objects
        """
        with self.SessionLocal() as session:
            return session.query(Feedback)\
                .filter(Feedback.persona_id == persona_id)\
                .order_by(desc(Feedback.created_at))\
                .limit(limit)\
                .all()
    
    def get_sentiment_distribution(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        persona_id: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Get the distribution of sentiment across feedback.
        
        Args:
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            persona_id: Optional persona ID for filtering
            
        Returns:
            Dictionary mapping sentiment to count
        """
        with self.SessionLocal() as session:
            query = session.query(Feedback.sentiment, func.count(Feedback.id))\
                .group_by(Feedback.sentiment)
            
            # Apply filters if provided
            if start_date:
                query = query.filter(Feedback.created_at >= start_date)
            if end_date:
                query = query.filter(Feedback.created_at <= end_date)
            if persona_id:
                query = query.filter(Feedback.persona_id == persona_id)
            
            # Execute query and format results
            results = query.all()
            return {sentiment: count for sentiment, count in results}
    
    def extract_and_save_themes(self, batch_size: int = 100) -> Dict[str, Any]:
        """
        Extract themes from recent feedback and save them.
        
        Args:
            batch_size: Number of feedback entries to process
            
        Returns:
            Dictionary with theme extraction results
        """
        with self.SessionLocal() as session:
            # Get feedback without themes
            feedback_entries = session.query(Feedback)\
                .outerjoin(FeedbackThemeMapping)\
                .filter(FeedbackThemeMapping.feedback_id == None)\
                .limit(batch_size)\
                .all()
            
            if not feedback_entries:
                return {"themes_extracted": 0, "feedback_processed": 0}
            
            # Prepare data for theme extraction
            feedback_data = [
                {"id": f.id, "text": f.feedback_text} 
                for f in feedback_entries
            ]
            
            # Extract themes
            themes = extract_themes(feedback_data)
            
            # Save themes and mappings
            theme_count = 0
            mapping_count = 0
            
            for theme_name, theme_data in themes.items():
                # Check if theme already exists
                existing_theme = session.query(FeedbackTheme)\
                    .filter(FeedbackTheme.theme_name == theme_name)\
                    .first()
                
                if existing_theme:
                    theme = existing_theme
                    # Update existing theme
                    theme.feedback_count += len(theme_data['feedback_ids'])
                    theme.last_detected_at = datetime.utcnow()
                else:
                    # Create new theme
                    theme = FeedbackTheme(
                        theme_name=theme_name,
                        theme_keywords=theme_data['keywords'],
                        feedback_count=len(theme_data['feedback_ids']),
                        sentiment_distribution={},
                        first_detected_at=datetime.utcnow(),
                        last_detected_at=datetime.utcnow()
                    )
                    session.add(theme)
                    session.flush()
                    theme_count += 1
                
                # Create mappings
                for feedback_id in theme_data['feedback_ids']:
                    mapping = FeedbackThemeMapping(
                        feedback_id=feedback_id,
                        theme_id=theme.id,
                        confidence_score=0.8  # Default confidence
                    )
                    session.add(mapping)
                    mapping_count += 1
            
            # Commit changes
            session.commit()
            
            return {
                "themes_extracted": theme_count,
                "feedback_processed": len(feedback_entries),
                "mappings_created": mapping_count
            }
    
    def update_persona_metrics(self, time_period: str = "daily") -> Dict[str, Any]:
        """
        Update metrics for all personas.
        
        Args:
            time_period: Time period for metrics ('daily', 'weekly', 'monthly')
            
        Returns:
            Dictionary with update results
        """
        with self.SessionLocal() as session:
            # Determine date range based on time period
            end_date = datetime.utcnow()
            
            if time_period == "daily":
                start_date = end_date - timedelta(days=1)
            elif time_period == "weekly":
                start_date = end_date - timedelta(weeks=1)
            elif time_period == "monthly":
                start_date = end_date - timedelta(days=30)
            else:
                raise ValueError(f"Invalid time period: {time_period}")
            
            # Get all personas with feedback in the period
            personas = session.query(Feedback.persona_id)\
                .filter(
                    Feedback.created_at >= start_date,
                    Feedback.created_at <= end_date,
                    Feedback.persona_id != None
                )\
                .distinct()\
                .all()
            
            personas_updated = 0
            
            for (persona_id,) in personas:
                # Get sentiment counts
                sentiment_counts = self.get_sentiment_distribution(
                    start_date=start_date,
                    end_date=end_date,
                    persona_id=persona_id
                )
                
                # Get average rating
                rating_result = session.query(func.avg(Feedback.rating))\
                    .filter(
                        Feedback.persona_id == persona_id,
                        Feedback.created_at >= start_date,
                        Feedback.created_at <= end_date,
                        Feedback.rating != None
                    )\
                    .first()
                
                average_rating = rating_result[0] if rating_result[0] else None
                
                # Get common themes
                theme_query = session.query(
                    FeedbackTheme.theme_name,
                    func.count(FeedbackThemeMapping.feedback_id).label('count')
                )\
                    .join(FeedbackThemeMapping)\
                    .join(Feedback)\
                    .filter(
                        Feedback.persona_id == persona_id,
                        Feedback.created_at >= start_date,
                        Feedback.created_at <= end_date
                    )\
                    .group_by(FeedbackTheme.theme_name)\
                    .order_by(desc('count'))\
                    .limit(5)\
                    .all()
                
                common_themes = [
                    {"theme": theme, "count": count}
                    for theme, count in theme_query
                ]
                
                # Create or update metrics
                metrics = session.query(PersonaFeedbackMetrics)\
                    .filter(
                        PersonaFeedbackMetrics.persona_id == persona_id,
                        PersonaFeedbackMetrics.time_period == time_period,
                        PersonaFeedbackMetrics.period_start == start_date
                    )\
                    .first()
                
                if metrics:
                    # Update existing metrics
                    metrics.positive_count = sentiment_counts.get('positive', 0)
                    metrics.neutral_count = sentiment_counts.get('neutral', 0)
                    metrics.negative_count = sentiment_counts.get('negative', 0)
                    metrics.average_rating = average_rating
                    metrics.common_themes = common_themes
                else:
                    # Create new metrics
                    metrics = PersonaFeedbackMetrics(
                        persona_id=persona_id,
                        time_period=time_period,
                        period_start=start_date,
                        period_end=end_date,
                        positive_count=sentiment_counts.get('positive', 0),
                        neutral_count=sentiment_counts.get('neutral', 0),
                        negative_count=sentiment_counts.get('negative', 0),
                        average_rating=average_rating,
                        common_themes=common_themes
                    )
                    session.add(metrics)
                
                personas_updated += 1
            
            # Commit changes
            session.commit()
            
            return {
                "personas_updated": personas_updated,
                "time_period": time_period,
                "start_date": start_date,
                "end_date": end_date
            }
