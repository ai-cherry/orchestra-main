"""
LangChain Adapter for LiteLLMClient

Provides a LangChain-compatible LLM and ChatModel interface that delegates to the orchestrator's LiteLLMClient.
This enables seamless use of orchestrator-managed LLMs in LangChain chains, tools, and agents.

Author: AI Orchestra
"""

import asyncio
from typing import Any, List, Optional

from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.chat_models.base import BaseChatModel
from langchain.llms.base import BaseLLM
from langchain.schema import BaseMessage, ChatGeneration, ChatMessage, LLMResult

from core.orchestrator.src.llm.litellm_client import LiteLLMClient, LLMMessage

class LiteLLMLangChainLLM(BaseLLM):
    """
    LangChain-compatible LLM interface for text completions using LiteLLMClient.
    """

    client: LiteLLMClient
    model: Optional[str] = None
    temperature: float = 0.02

    @property
    def _llm_type(self) -> str:
        return "litellm"

    def __init__(
        self,
        client: LiteLLMClient,
        model: Optional[str] = None,
        temperature: float = 0.02,
    ):
        super().__init__()
        self.client = client
        self.model = model
        self.temperature = temperature

    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        """
        Synchronous text completion for LangChain LLM interface.
        """
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            self.client.text_completion(
                prompt=prompt,
                model=self.model,
                temperature=self.temperature,
                stop=stop,
                **kwargs,
            )
        )
        return response.content

    async def _acall(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        """
        Async text completion for LangChain LLM interface.
        """
        response = await self.client.text_completion(
            prompt=prompt,
            model=self.model,
            temperature=self.temperature,
            stop=stop,
            **kwargs,
        )
        return response.content

class LiteLLMLangChainChat(BaseChatModel):
    """
    LangChain-compatible ChatModel interface for chat completions using LiteLLMClient.
    """

    client: LiteLLMClient
    model: Optional[str] = None
    temperature: float = 0.02

    @property
    def _llm_type(self) -> str:
        return "litellm-chat"

    def __init__(
        self,
        client: LiteLLMClient,
        model: Optional[str] = None,
        temperature: float = 0.02,
    ):
        super().__init__()
        self.client = client
        self.model = model
        self.temperature = temperature

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> LLMResult:
        """
        Synchronous chat completion for LangChain ChatModel interface.
        """
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self._achat(messages, stop=stop, **kwargs))
        return LLMResult(
            generations=[[ChatGeneration(message=ChatMessage(role="assistant", content=response))]],
            llm_output={"provider": "litellm"},
        )

    async def _achat(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        Async chat completion for LangChain ChatModel interface.
        """
        # Convert LangChain messages to LLMMessage
        llm_messages = [LLMMessage(role=msg.type, content=msg.content) for msg in messages]
        response = await self.client.chat_completion(
            messages=llm_messages,
            model=self.model,
            temperature=self.temperature,
            stop=stop,
            **kwargs,
        )
        return response.content
