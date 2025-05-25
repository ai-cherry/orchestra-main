"""
Observable Agent Implementation for AI Orchestra.

This module provides an agent implementation with built-in observability features
like logging, metrics, and tracing to help with monitoring and debugging.
"""

import json
import logging
import time
import traceback
import uuid
from typing import Any, Dict, Optional

from core.orchestrator.src.agents.agent_base import Agent, AgentContext, AgentResponse
from core.orchestrator.src.memory.layered_memory import LayeredMemory

# Configure logging
logger = logging.getLogger(__name__)


class ObservableAgent(Agent):
    """
    Agent with built-in observability features.

    This agent wraps any other agent implementation and adds observability
    features like logging, metrics, and tracing to help with monitoring
    and debugging agent operations.
    """

    def __init__(
        self,
        wrapped_agent: Agent,
        agent_id: str,
        memory: Optional[LayeredMemory] = None,
        log_level: str = "INFO",
        enable_metrics: bool = True,
        enable_tracing: bool = True,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize an observable agent.

        Args:
            wrapped_agent: The agent to wrap with observability features
            agent_id: Unique identifier for this agent
            memory: Layered memory system for the agent
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            enable_metrics: Whether to collect metrics
            enable_tracing: Whether to enable distributed tracing
            config: Additional configuration options
        """
        super().__init__(config)
        self.wrapped_agent = wrapped_agent
        self.agent_id = agent_id
        self.memory = memory
        self.log_level = log_level
        self.enable_metrics = enable_metrics
        self.enable_tracing = enable_tracing
        self.config = config or {}

        # Configure logging level
        numeric_level = getattr(logging, log_level.upper(), None)
        if isinstance(numeric_level, int):
            logger.setLevel(numeric_level)

        logger.info(f"ObservableAgent initialized for agent_id: {agent_id}")

    async def process(self, context: AgentContext) -> AgentResponse:
        """
        Process user input with observability features.

        This method wraps the underlying agent's process method with
        logging, metrics, and tracing to provide observability.

        Args:
            context: The context for this interaction

        Returns:
            The agent's response
        """
        # Generate a unique operation ID for tracing
        operation_id = str(uuid.uuid4())
        start_time = time.time()

        # Add operation ID to context metadata
        if context.metadata is None:
            context.metadata = {}
        context.metadata["operation_id"] = operation_id
        context.metadata["agent_id"] = self.agent_id

        # Log the start of processing
        logger.info(
            f"Agent {self.agent_id} processing started",
            extra={
                "agent_id": self.agent_id,
                "operation_id": operation_id,
                "context_type": type(context).__name__,
                "user_input_length": (
                    len(context.user_input) if context.user_input else 0
                ),
            },
        )

        try:
            # Process with the wrapped agent
            response = await self.wrapped_agent.process(context)

            # Calculate processing time
            processing_time = time.time() - start_time

            # Log the successful completion
            logger.info(
                f"Agent {self.agent_id} processing completed",
                extra={
                    "agent_id": self.agent_id,
                    "operation_id": operation_id,
                    "processing_time_ms": int(processing_time * 1000),
                    "response_length": len(response.text) if response.text else 0,
                    "confidence": response.confidence,
                },
            )

            # Store in memory if available
            if self.memory:
                memory_key = f"interaction:{operation_id}"
                memory_value = {
                    "user_input": context.user_input,
                    "agent_response": response.text,
                    "confidence": response.confidence,
                    "processing_time": processing_time,
                    "timestamp": time.time(),
                }

                try:
                    await self.memory.store(
                        key=memory_key,
                        value=memory_value,
                        layer="short_term",
                        metadata={
                            "agent_id": self.agent_id,
                            "operation_id": operation_id,
                            "interaction_type": "user_query",
                        },
                    )
                except Exception as e:
                    logger.warning(f"Failed to store in memory: {e}")

            # Record metrics if enabled
            if self.enable_metrics:
                self._record_metrics(
                    operation_id=operation_id,
                    processing_time=processing_time,
                    response_length=len(response.text) if response.text else 0,
                    confidence=response.confidence,
                    success=True,
                )

            # Add observability metadata to response
            if response.metadata is None:
                response.metadata = {}
            response.metadata.update(
                {
                    "operation_id": operation_id,
                    "processing_time_ms": int(processing_time * 1000),
                    "agent_id": self.agent_id,
                }
            )

            return response

        except Exception as e:
            # Calculate processing time
            processing_time = time.time() - start_time

            # Log the error
            logger.error(
                f"Agent {self.agent_id} processing failed: {e}",
                extra={
                    "agent_id": self.agent_id,
                    "operation_id": operation_id,
                    "processing_time_ms": int(processing_time * 1000),
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                },
            )

            # Record metrics if enabled
            if self.enable_metrics:
                self._record_metrics(
                    operation_id=operation_id,
                    processing_time=processing_time,
                    response_length=0,
                    confidence=0.0,
                    success=False,
                    error=str(e),
                )

            # Create error response
            error_response = AgentResponse(
                text=f"An error occurred while processing your request: {e}",
                confidence=0.0,
                metadata={
                    "operation_id": operation_id,
                    "processing_time_ms": int(processing_time * 1000),
                    "agent_id": self.agent_id,
                    "error": str(e),
                },
            )

            return error_response

    def can_handle(self, context: AgentContext) -> float:
        """
        Determine if this agent can handle the given context.

        This method delegates to the wrapped agent's can_handle method.

        Args:
            context: The context for this interaction

        Returns:
            A score between 0 and 1
        """
        return self.wrapped_agent.can_handle(context)

    async def initialize_async(self) -> None:
        """Initialize the agent asynchronously."""
        logger.info(f"Initializing agent {self.agent_id}")

        # Initialize wrapped agent if it has an initialize_async method
        if hasattr(self.wrapped_agent, "initialize_async") and callable(
            self.wrapped_agent.initialize_async
        ):
            await self.wrapped_agent.initialize_async()

        logger.info(f"Agent {self.agent_id} initialized")

    async def close_async(self) -> None:
        """Close the agent and release resources asynchronously."""
        logger.info(f"Closing agent {self.agent_id}")

        # Close wrapped agent if it has a close_async method
        if hasattr(self.wrapped_agent, "close_async") and callable(
            self.wrapped_agent.close_async
        ):
            await self.wrapped_agent.close_async()

        logger.info(f"Agent {self.agent_id} closed")

    def _record_metrics(
        self,
        operation_id: str,
        processing_time: float,
        response_length: int,
        confidence: float,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """
        Record metrics for monitoring.

        In a production environment, this would send metrics to a monitoring system
        like Cloud Monitoring. For now, we just log them.

        Args:
            operation_id: Unique identifier for this operation
            processing_time: Time taken to process the request in seconds
            response_length: Length of the response text
            confidence: Confidence score of the response
            success: Whether the operation was successful
            error: Error message if the operation failed
        """
        metrics = {
            "agent_id": self.agent_id,
            "operation_id": operation_id,
            "processing_time_ms": int(processing_time * 1000),
            "response_length": response_length,
            "confidence": confidence,
            "success": success,
        }

        if error:
            metrics["error"] = error

        # In a production environment, send to Cloud Monitoring
        # For now, just log as JSON
        logger.debug(f"METRICS: {json.dumps(metrics)}")


class ObservableAgentFactory:
    """
    Factory for creating observable agents.

    This factory creates observable agents that wrap other agent implementations
    and add observability features.
    """

    def __init__(self, memory_factory=None):
        """
        Initialize the factory.

        Args:
            memory_factory: Factory for creating memory systems
        """
        self.memory_factory = memory_factory

    def create_observable_agent(
        self,
        wrapped_agent: Agent,
        agent_id: str,
        memory_config: Optional[Dict[str, Any]] = None,
        log_level: str = "INFO",
        enable_metrics: bool = True,
        enable_tracing: bool = True,
        config: Optional[Dict[str, Any]] = None,
    ) -> ObservableAgent:
        """
        Create an observable agent.

        Args:
            wrapped_agent: The agent to wrap with observability features
            agent_id: Unique identifier for this agent
            memory_config: Configuration for the agent's memory system
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            enable_metrics: Whether to collect metrics
            enable_tracing: Whether to enable distributed tracing
            config: Additional configuration options

        Returns:
            An observable agent instance
        """
        # Create memory system if memory_factory is available and memory_config is provided
        memory = None
        if self.memory_factory and memory_config:
            memory = self.memory_factory.create_layered_memory(memory_config)

        # Create observable agent
        return ObservableAgent(
            wrapped_agent=wrapped_agent,
            agent_id=agent_id,
            memory=memory,
            log_level=log_level,
            enable_metrics=enable_metrics,
            enable_tracing=enable_tracing,
            config=config,
        )
