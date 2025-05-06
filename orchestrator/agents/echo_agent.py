"""
A simple echo agent for demonstration purposes.
"""
import logging
from typing import Dict, Any

from packages.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class EchoAgent(BaseAgent):
    """
    A simple agent that echoes back user input with some formatting.
    Used for demonstration and testing purposes.
    """
    
    def __init__(self, agent_id: str = None, name: str = None, description: str = None):
        """Initialize the echo agent."""
        config = {
            "id": agent_id or "echo-agent",
            "name": name or "Echo Agent",
            "description": description or "A simple echo agent that repeats user input"
        }
        super().__init__(config=config, persona=None)
    
    async def initialize(self) -> None:
        """Initialize the agent."""
        logger.info(f"Echo agent {self.name} initialized")
    
    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input by echoing it back with some formatting.
        
        Args:
            context: Dictionary containing:
                - input_text: The input text to echo
                - session_id: Optional session identifier
            
        Returns:
            Dictionary containing:
                - response: Formatted echo of the input
                - status: "success"
        """
        input_text = context.get("input_text", "")
        logger.info(f"Echo agent processing: {input_text[:50]}...")
        
        # Simple processing logic - echo with some formatting
        response = f"Echo: {input_text}"
        
        # Add some context information if available
        if context.get("session_id"):
            response += f"\nSession ID: {context['session_id']}"
        
        return {
            "status": "success",
            "response": response,
            "original_input": input_text
        }
    
    def process_feedback(self, feedback: Dict[str, Any]) -> None:
        """Process feedback about the agent's performance."""
        logger.info(f"Echo agent received feedback: {feedback}")
        super().process_feedback(feedback)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get the capabilities of this agent."""
        return {
            "capabilities": ["echo", "repeat"],
            "description": self.config.get("description", "")
        }
