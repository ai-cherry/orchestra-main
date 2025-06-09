"""
Main integration script for the feedback system.

This script validates the feedback system and ensures all components
are properly integrated with Orchestra AI.
"""

import asyncio
import logging
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.feedback.repository import FeedbackRepository
from src.feedback.sentiment import analyze_sentiment
from src.feedback.themes import extract_themes
from src.feedback.integration import FeedbackIntegrationManager
from src.personas.persona_manager import PersonaManager
from src.learning.adaptive_learning_system import AdaptiveLearningSystem
from src.knowledge.unified_knowledge_graph import UnifiedKnowledgeGraph
from src.context.adaptive_context_manager import AdaptiveContextManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connection string - would be retrieved from environment in production
DB_URL = "postgresql://admin:password@localhost:5432/orchestra_feedback"


async def validate_feedback_system():
    """Validate the feedback system and its integration with Orchestra AI."""
    logger.info("Starting feedback system validation")
    
    # Initialize repository
    repo = FeedbackRepository(DB_URL)
    
    # Create tables if they don't exist
    logger.info("Ensuring database tables exist")
    repo.create_tables()
    
    # Test sentiment analysis
    logger.info("Testing sentiment analysis")
    positive_text = "This is a great feature! I love how it works."
    negative_text = "This doesn't work at all. Very frustrating experience."
    neutral_text = "I'm just providing some information about my experience."
    
    positive_result = analyze_sentiment(positive_text)
    negative_result = analyze_sentiment(negative_text)
    neutral_result = analyze_sentiment(neutral_text)
    
    logger.info(f"Positive text sentiment: {positive_result['sentiment']}")
    logger.info(f"Negative text sentiment: {negative_result['sentiment']}")
    logger.info(f"Neutral text sentiment: {neutral_result['sentiment']}")
    
    # Test theme extraction
    logger.info("Testing theme extraction")
    feedback_batch = [
        {"id": 1, "text": "The search feature is very slow and often returns irrelevant results."},
        {"id": 2, "text": "Search functionality is too slow and the results aren't helpful."},
        {"id": 3, "text": "I love the new UI design, it's much more intuitive."},
        {"id": 4, "text": "The interface looks great but search is still problematic."},
        {"id": 5, "text": "Your customer service team was very helpful with my issue."}
    ]
    
    themes = extract_themes(feedback_batch)
    logger.info(f"Extracted themes: {list(themes.keys())}")
    
    # Test feedback repository
    logger.info("Testing feedback repository")
    
    # Add test feedback
    test_feedback = {
        "user_id": "test_user_123",
        "feedback_text": "This is a test feedback entry for validation.",
        "source": "validation_script",
        "persona_id": "cherry",
        "rating": 4
    }
    
    feedback = repo.add_feedback(test_feedback)
    logger.info(f"Added test feedback with ID: {feedback.id}")
    
    # Retrieve feedback
    retrieved = repo.get_feedback(feedback.id)
    logger.info(f"Retrieved feedback: {retrieved.id}, sentiment: {retrieved.sentiment}")
    
    # Test theme extraction
    theme_results = repo.extract_and_save_themes()
    logger.info(f"Theme extraction results: {theme_results}")
    
    # Test metrics update
    metrics_results = repo.update_persona_metrics("daily")
    logger.info(f"Metrics update results: {metrics_results}")
    
    # Initialize integration manager with mock components
    logger.info("Testing integration manager")
    
    # Mock persona manager
    persona_manager = PersonaManager()
    
    # Mock learning system
    learning_system = AdaptiveLearningSystem()
    
    # Mock knowledge graph
    knowledge_graph = UnifiedKnowledgeGraph()
    
    # Mock context manager
    context_manager = AdaptiveContextManager()
    
    # Create integration manager
    integration_manager = FeedbackIntegrationManager(
        feedback_repo=repo,
        persona_manager=persona_manager,
        learning_system=learning_system,
        knowledge_graph=knowledge_graph,
        context_manager=context_manager
    )
    
    # Test feedback processing
    integration_feedback = {
        "user_id": "test_user_456",
        "feedback_text": "Integration test feedback entry.",
        "source": "integration_test",
        "persona_id": "sophia",
        "rating": 3
    }
    
    process_results = await integration_manager.process_feedback(integration_feedback)
    logger.info(f"Integration process results: {process_results}")
    
    # Test persona insights
    insights = await integration_manager.get_persona_feedback_insights("sophia")
    logger.info(f"Persona insights: {insights}")
    
    logger.info("Feedback system validation completed successfully")
    return True


if __name__ == "__main__":
    asyncio.run(validate_feedback_system())
