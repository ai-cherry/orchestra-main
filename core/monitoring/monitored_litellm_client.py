"""
Monitored LiteLLM Client

Extends the LiteLLM client to automatically monitor all Claude API calls.
"""

import os
from typing import Any, Dict, List, Optional, Union

from core.logging_config import get_logger
from core.monitoring.claude_monitor import ClaudeMonitor
from core.orchestrator.src.llm.litellm_client import (
    LiteLLMClient,
    LLMEmbeddingResponse,
    LLMMessage,
    LLMResponse,
)

logger = get_logger(__name__)


class MonitoredLiteLLMClient(LiteLLMClient):
    """
    Extended LiteLLM client that automatically monitors Claude API calls.

    This client wraps the standard LiteLLM client and adds monitoring
    capabilities specifically for Claude models.
    """

    def __init__(
        self,
        monitor: Optional[ClaudeMonitor] = None,
        monitor_all_models: bool = False,
        **kwargs
    ):
        """
        Initialize the monitored client.

        Args:
            monitor: ClaudeMonitor instance (creates one if not provided)
            monitor_all_models: If True, monitor all models, not just Claude
            **kwargs: Arguments passed to LiteLLMClient
        """
        super().__init__(**kwargs)

        # Initialize monitor
        self.monitor = monitor or ClaudeMonitor(
            log_responses=True,
            log_prompts=True,
            storage_backend=os.getenv("MONITOR_STORAGE_BACKEND", "memory"),
        )

        self.monitor_all_models = monitor_all_models

        logger.info("Initialized monitored LiteLLM client")

    def _should_monitor(self, model: str) -> bool:
        """Check if the model should be monitored"""
        if self.monitor_all_models:
            return True

        # Monitor all Claude models
        return "claude" in model.lower()

    async def chat_completion(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[Union[str, List[str]]] = None,
        user: Optional[str] = None,
        timeout: Optional[int] = None,
        # Additional monitoring parameters
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """
        Generate a chat completion with automatic monitoring for Claude models.
        """
        model = model or self.default_model

        # Check if we should monitor this call
        if self._should_monitor(model):
            # Use monitoring context
            async with self.monitor.monitor_call(
                model=model, user_id=user, session_id=session_id, metadata=metadata
            ) as ctx:
                try:
                    # Make the actual API call
                    response = await super().chat_completion(
                        messages=messages,
                        model=model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        top_p=top_p,
                        frequency_penalty=frequency_penalty,
                        presence_penalty=presence_penalty,
                        stop=stop,
                        user=user,
                        timeout=timeout,
                    )

                    # Set token usage in monitor context
                    ctx.set_tokens(response.usage)

                    return response

                except Exception as e:
                    # Set error in monitor context
                    ctx.set_error(e)
                    raise
        else:
            # No monitoring for non-Claude models
            return await super().chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                stop=stop,
                user=user,
                timeout=timeout,
            )

    async def text_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[Union[str, List[str]]] = None,
        user: Optional[str] = None,
        timeout: Optional[int] = None,
        # Additional monitoring parameters
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """
        Generate a text completion with automatic monitoring for Claude models.
        """
        # Text completion uses chat completion internally, so monitoring is handled there
        messages = [LLMMessage(role="user", content=prompt)]
        return await self.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            stop=stop,
            user=user,
            timeout=timeout,
            session_id=session_id,
            metadata=metadata,
        )

    async def get_embedding(
        self,
        text: str,
        model: Optional[str] = None,
        user: Optional[str] = None,
        timeout: Optional[int] = None,
        # Additional monitoring parameters
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LLMEmbeddingResponse:
        """
        Generate an embedding with automatic monitoring for Claude models.
        """
        model = model or self.default_embedding_model

        # Check if we should monitor this call
        if self._should_monitor(model):
            # Use monitoring context
            async with self.monitor.monitor_call(
                model=model, user_id=user, session_id=session_id, metadata=metadata
            ) as ctx:
                try:
                    # Make the actual API call
                    response = await super().get_embedding(
                        text=text, model=model, user=user, timeout=timeout
                    )

                    # Set token usage in monitor context
                    ctx.set_tokens(response.usage)

                    return response

                except Exception as e:
                    # Set error in monitor context
                    ctx.set_error(e)
                    raise
        else:
            # No monitoring for non-Claude models
            return await super().get_embedding(
                text=text, model=model, user=user, timeout=timeout
            )

    def get_monitoring_summary(self, **kwargs) -> Dict[str, Any]:
        """
        Get monitoring summary for Claude API calls.

        Args:
            **kwargs: Arguments passed to monitor.get_metrics_summary()

        Returns:
            Dictionary containing aggregated metrics
        """
        summary = self.monitor.get_metrics_summary(**kwargs)

        return {
            "total_calls": summary.total_calls,
            "successful_calls": summary.successful_calls,
            "failed_calls": summary.failed_calls,
            "total_input_tokens": summary.total_input_tokens,
            "total_output_tokens": summary.total_output_tokens,
            "total_cost_usd": summary.total_cost_usd,
            "average_latency_ms": summary.average_latency_ms,
            "calls_by_model": dict(summary.calls_by_model),
            "tokens_by_model": dict(summary.tokens_by_model),
            "cost_by_model": dict(summary.cost_by_model),
            "errors_by_type": dict(summary.errors_by_type),
        }

    def export_monitoring_data(self, format: str = "json", **kwargs) -> str:
        """
        Export monitoring data in the specified format.

        Args:
            format: Export format (json, csv)
            **kwargs: Arguments passed to monitor.export_metrics()

        Returns:
            Exported data as string
        """
        return self.monitor.export_metrics(format=format, **kwargs)
