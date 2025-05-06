"""
Message Handler Mixin for Agents.

This module provides a mixin class that adds message handling capabilities
to agent implementations.
"""

import asyncio
import logging
from typing import Dict, Any, Callable, Awaitable, Optional, List

from core.orchestrator.src.services.message_queue import get_message_queue, AgentMessage
from core.orchestrator.src.protocols.agent_protocol import MessageType

# Configure logging
logger = logging.getLogger(__name__)


class MessageHandlerMixin:
    """
    Mixin class that adds message handling capabilities to agents.
    
    This mixin provides methods for registering handlers for different
    message types and starting a background task to process messages.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize the mixin."""
        super().__init__(*args, **kwargs)
        self._message_handlers: Dict[str, List[Callable[[AgentMessage], Awaitable[None]]]] = {}
        self._message_processor_task = None
        self._processing_messages = False
        
    def register_message_handler(
        self, 
        message_type: str, 
        handler: Callable[[AgentMessage], Awaitable[None]]
    ):
        """
        Register a handler for a specific message type.
        
        Args:
            message_type: The type of message to handle
            handler: Async function to handle the message
        """
        if message_type not in self._message_handlers:
            self._message_handlers[message_type] = []
        self._message_handlers[message_type].append(handler)
        
    async def handle_message(self, message: AgentMessage) -> bool:
        """
        Handle an incoming message.
        
        Args:
            message: The message to handle
            
        Returns:
            True if the message was handled
        """
        if message.message_type in self._message_handlers:
            for handler in self._message_handlers[message.message_type]:
                try:
                    await handler(message)
                except Exception as e:
                    logger.error(f"Error in message handler: {e}")
            return True
        return False
        
    async def start_message_processing(self):
        """Start background task to process messages."""
        if self._message_processor_task is not None:
            return
            
        self._processing_messages = True
        self._message_processor_task = asyncio.create_task(self._process_messages())
        
    async def stop_message_processing(self):
        """Stop background message processing."""
        if self._message_processor_task is None:
            return
            
        self._processing_messages = False
        self._message_processor_task.cancel()
        try:
            await self._message_processor_task
        except asyncio.CancelledError:
            pass
        self._message_processor_task = None
        
    async def _process_messages(self):
        """Background task to process messages."""
        # Get agent ID from config or generate one
        agent_id = getattr(self, "config", {}).get(
            "agent_id", f"{self.__class__.__name__}_{id(self)}"
        )
        
        message_queue = get_message_queue()
        
        while self._processing_messages:
            try:
                # Wait for a message with a short timeout
                message = await message_queue.receive_message(agent_id, timeout=1.0)
                
                if message:
                    # Try to handle the message
                    handled = await self.handle_message(message)
                    
                    if not handled:
                        logger.warning(
                            f"No handler for message type: {message.message_type}"
                        )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing messages: {e}")
                await asyncio.sleep(1.0)  # Avoid tight loop on errors
