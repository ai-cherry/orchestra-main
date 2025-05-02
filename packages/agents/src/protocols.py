"""
Protocols for agent interactions in the Orchestra system.

This module defines the interfaces for agent interactions, ensuring a clear contract
for implementations to follow.
"""

from typing import Protocol, Any
from packages.core.src.models import AgentInput, AgentOutput

class AgentProtocol(Protocol):
    """
    Protocol defining the interface for agent interactions.
    """
    async def run(self, input_data: AgentInput) -> AgentOutput:
        """
        Execute the agent with the given input data.
        
        Args:
            input_data: The input data for the agent to process.
            
        Returns:
            The output result from the agent.
        """
        ...
        
    async def health_check(self) -> bool:
        """
        Perform a health check on the agent.
        
        Returns:
            True if the agent is healthy, False otherwise.
        """
        ...
