"""
Integration of the feedback system with Orchestra AI.

This module provides integration points between the feedback system and
other Orchestra AI components, including personas, learning, and knowledge graph.
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from .repository import FeedbackRepository
from ..personas.persona_manager import PersonaManager
from ..learning.adaptive_learning_system import AdaptiveLearningSystem
from ..knowledge.unified_knowledge_graph import UnifiedKnowledgeGraph
from ..context.adaptive_context_manager import AdaptiveContextManager

# Configure logging
logger = logging.getLogger(__name__)


class FeedbackIntegrationManager:
    """Manager for integrating feedback with other Orchestra AI components."""
    
    def __init__(
        self,
        feedback_repo: FeedbackRepository,
        persona_manager: Optional[PersonaManager] = None,
        learning_system: Optional[AdaptiveLearningSystem] = None,
        knowledge_graph: Optional[UnifiedKnowledgeGraph] = None,
        context_manager: Optional[AdaptiveContextManager] = None
    ):
        """
        Initialize the feedback integration manager.
        
        Args:
            feedback_repo: Feedback repository
            persona_manager: Persona manager (optional)
            learning_system: Adaptive learning system (optional)
            knowledge_graph: Unified knowledge graph (optional)
            context_manager: Adaptive context manager (optional)
        """
        self.feedback_repo = feedback_repo
        self.persona_manager = persona_manager
        self.learning_system = learning_system
        self.knowledge_graph = knowledge_graph
        self.context_manager = context_manager
    
    async def process_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process feedback and integrate with other components.
        
        Args:
            feedback_data: Feedback data
            
        Returns:
            Dictionary with processing results
        """
        results = {
            "feedback_saved": False,
            "persona_notified": False,
            "learning_updated": False,
            "knowledge_updated": False,
            "context_updated": False
        }
        
        try:
            # Save feedback
            feedback = self.feedback_repo.add_feedback(feedback_data)
            results["feedback_saved"] = True
            results["feedback_id"] = feedback.id
            
            # Notify persona if applicable
            if self.persona_manager and feedback.persona_id:
                await self._notify_persona(feedback)
                results["persona_notified"] = True
            
            # Update learning system
            if self.learning_system:
                await self._update_learning_system(feedback)
                results["learning_updated"] = True
            
            # Update knowledge graph
            if self.knowledge_graph and feedback.sentiment == "negative":
                await self._update_knowledge_graph(feedback)
                results["knowledge_updated"] = True
            
            # Update context
            if self.context_manager and feedback.user_id:
                await self._update_context(feedback)
                results["context_updated"] = True
            
        except Exception as e:
            logger.error(f"Error processing feedback: {str(e)}")
            results["error"] = str(e)
        
        return results
    
    async def _notify_persona(self, feedback: Any) -> None:
        """
        Notify the relevant persona about feedback.
        
        Args:
            feedback: Feedback object
        """
        try:
            persona = self.persona_manager.get_persona(feedback.persona_id)
            if persona:
                await persona.notify_feedback(
                    feedback_id=feedback.id,
                    user_id=feedback.user_id,
                    sentiment=feedback.sentiment,
                    feedback_text=feedback.feedback_text
                )
        except Exception as e:
            logger.error(f"Error notifying persona: {str(e)}")
    
    async def _update_learning_system(self, feedback: Any) -> None:
        """
        Update the learning system with feedback.
        
        Args:
            feedback: Feedback object
        """
        try:
            # Convert feedback to learning signal
            signal = {
                "source": "user_feedback",
                "timestamp": datetime.utcnow().isoformat(),
                "feedback_id": feedback.id,
                "user_id": feedback.user_id,
                "persona_id": feedback.persona_id,
                "sentiment": feedback.sentiment,
                "rating": feedback.rating,
                "content": feedback.feedback_text
            }
            
            # Send signal to learning system
            await self.learning_system.process_feedback_signal(signal)
            
            # If negative feedback, trigger learning review
            if feedback.sentiment == "negative" and feedback.persona_id:
                await self.learning_system.schedule_performance_review(
                    persona_id=feedback.persona_id,
                    trigger="negative_feedback",
                    feedback_id=feedback.id
                )
        except Exception as e:
            logger.error(f"Error updating learning system: {str(e)}")
    
    async def _update_knowledge_graph(self, feedback: Any) -> None:
        """
        Update the knowledge graph with feedback insights.
        
        Args:
            feedback: Feedback object
        """
        try:
            # For negative feedback, identify potential knowledge gaps
            if feedback.sentiment == "negative":
                # Extract potential knowledge gaps from feedback
                knowledge_update = {
                    "source": "user_feedback",
                    "feedback_id": feedback.id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "content": feedback.feedback_text,
                    "metadata": {
                        "user_id": feedback.user_id,
                        "persona_id": feedback.persona_id,
                        "sentiment": feedback.sentiment
                    }
                }
                
                # Add to knowledge graph for analysis
                await self.knowledge_graph.add_feedback_node(knowledge_update)
        except Exception as e:
            logger.error(f"Error updating knowledge graph: {str(e)}")
    
    async def _update_context(self, feedback: Any) -> None:
        """
        Update the context manager with feedback.
        
        Args:
            feedback: Feedback object
        """
        try:
            if feedback.user_id:
                # Add feedback to user context
                context_update = {
                    "user_id": feedback.user_id,
                    "feedback_id": feedback.id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "sentiment": feedback.sentiment,
                    "content": feedback.feedback_text
                }
                
                # Update user context
                await self.context_manager.update_user_feedback_context(context_update)
        except Exception as e:
            logger.error(f"Error updating context: {str(e)}")
    
    async def get_persona_feedback_insights(self, persona_id: str) -> Dict[str, Any]:
        """
        Get feedback insights for a specific persona.
        
        Args:
            persona_id: ID of the persona
            
        Returns:
            Dictionary with feedback insights
        """
        try:
            # Get sentiment distribution
            sentiment_distribution = self.feedback_repo.get_sentiment_distribution(
                persona_id=persona_id
            )
            
            # Get recent feedback
            recent_feedback = self.feedback_repo.get_feedback_by_persona(
                persona_id=persona_id,
                limit=10
            )
            
            # Extract themes if available
            self.feedback_repo.extract_and_save_themes()
            
            # Update metrics
            self.feedback_repo.update_persona_metrics("daily")
            self.feedback_repo.update_persona_metrics("weekly")
            
            return {
                "persona_id": persona_id,
                "sentiment_distribution": sentiment_distribution,
                "recent_feedback": [
                    {
                        "id": f.id,
                        "text": f.feedback_text,
                        "sentiment": f.sentiment,
                        "created_at": f.created_at.isoformat()
                    }
                    for f in recent_feedback
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting persona feedback insights: {str(e)}")
            return {
                "persona_id": persona_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
