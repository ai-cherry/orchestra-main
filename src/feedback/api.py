"""
API endpoints for the feedback system.

This module provides FastAPI endpoints for collecting, analyzing, and retrieving feedback.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session

from .models import FeedbackCreate, FeedbackResponse, FeedbackAnalyticsResponse, ThemeResponse
from .repository import FeedbackRepository
from ..api.dependencies import get_db

# Create router
router = APIRouter(prefix="/api/feedback", tags=["feedback"])

# Initialize repository
feedback_repo = None


def get_feedback_repository(db: Session = Depends(get_db)):
    """
    Get or initialize the feedback repository.
    
    Args:
        db: Database session
        
    Returns:
        FeedbackRepository instance
    """
    global feedback_repo
    if feedback_repo is None:
        # Use the same database connection as the main app
        feedback_repo = FeedbackRepository(str(db.bind.url))
    return feedback_repo


@router.post("/", response_model=FeedbackResponse)
async def create_feedback(
    feedback: FeedbackCreate,
    background_tasks: BackgroundTasks,
    repo: FeedbackRepository = Depends(get_feedback_repository)
):
    """
    Create a new feedback entry.
    
    Args:
        feedback: Feedback data
        background_tasks: FastAPI background tasks
        repo: Feedback repository
        
    Returns:
        Created feedback entry
    """
    try:
        # Create feedback entry
        feedback_entry = repo.add_feedback(feedback.dict())
        
        # Schedule theme extraction in the background
        background_tasks.add_task(repo.extract_and_save_themes)
        
        return feedback_entry
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create feedback: {str(e)}")


@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    feedback_id: int,
    repo: FeedbackRepository = Depends(get_feedback_repository)
):
    """
    Get a feedback entry by ID.
    
    Args:
        feedback_id: ID of the feedback to retrieve
        repo: Feedback repository
        
    Returns:
        Feedback entry
    """
    feedback = repo.get_feedback(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail=f"Feedback not found: {feedback_id}")
    return feedback


@router.get("/user/{user_id}", response_model=List[FeedbackResponse])
async def get_user_feedback(
    user_id: str,
    limit: int = Query(100, ge=1, le=1000),
    repo: FeedbackRepository = Depends(get_feedback_repository)
):
    """
    Get feedback entries for a specific user.
    
    Args:
        user_id: ID of the user
        limit: Maximum number of entries to return
        repo: Feedback repository
        
    Returns:
        List of feedback entries
    """
    return repo.get_feedback_by_user(user_id, limit)


@router.get("/persona/{persona_id}", response_model=List[FeedbackResponse])
async def get_persona_feedback(
    persona_id: str,
    limit: int = Query(100, ge=1, le=1000),
    repo: FeedbackRepository = Depends(get_feedback_repository)
):
    """
    Get feedback entries for a specific persona.
    
    Args:
        persona_id: ID of the persona
        limit: Maximum number of entries to return
        repo: Feedback repository
        
    Returns:
        List of feedback entries
    """
    return repo.get_feedback_by_persona(persona_id, limit)


@router.get("/analytics/sentiment", response_model=Dict[str, int])
async def get_sentiment_distribution(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    persona_id: Optional[str] = None,
    repo: FeedbackRepository = Depends(get_feedback_repository)
):
    """
    Get the distribution of sentiment across feedback.
    
    Args:
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        persona_id: Optional persona ID for filtering
        repo: Feedback repository
        
    Returns:
        Dictionary mapping sentiment to count
    """
    return repo.get_sentiment_distribution(start_date, end_date, persona_id)


@router.post("/analytics/extract-themes", response_model=Dict[str, Any])
async def extract_themes(
    batch_size: int = Query(100, ge=10, le=1000),
    repo: FeedbackRepository = Depends(get_feedback_repository)
):
    """
    Extract themes from recent feedback.
    
    Args:
        batch_size: Number of feedback entries to process
        repo: Feedback repository
        
    Returns:
        Dictionary with theme extraction results
    """
    return repo.extract_and_save_themes(batch_size)


@router.post("/analytics/update-metrics", response_model=Dict[str, Any])
async def update_persona_metrics(
    time_period: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    repo: FeedbackRepository = Depends(get_feedback_repository)
):
    """
    Update metrics for all personas.
    
    Args:
        time_period: Time period for metrics ('daily', 'weekly', 'monthly')
        repo: Feedback repository
        
    Returns:
        Dictionary with update results
    """
    return repo.update_persona_metrics(time_period)
