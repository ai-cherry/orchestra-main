"""
Enhanced unified LLM router implementation.

This module provides a concrete implementation of the LLM router
with hardcoded model mappings as a fallback when database is unavailable.
"""

from typing import Dict, Optional
from functools import lru_cache

from core.llm_types import UseCase, ModelTier, ModelMapping, RouterConfig
from core.llm_router_base import BaseLLMRouter


class UnifiedLLMRouter(BaseLLMRouter):
    """
    Unified router with hardcoded model mappings.

    This router provides default model mappings that work without
    a database connection, useful for development and as a fallback.
    """

    # Default model mappings for each use case and tier
    DEFAULT_MAPPINGS: Dict[UseCase, Dict[ModelTier, ModelMapping]] = {
        UseCase.CODE_GENERATION: {
            ModelTier.PREMIUM: ModelMapping(
                use_case=UseCase.CODE_GENERATION,
                tier=ModelTier.PREMIUM,
                primary_model="anthropic/claude-3-opus",
                fallback_models=["openai/gpt-4-turbo", "google/gemini-1.5-pro"],
                max_tokens=4096,
                temperature=0.2,
                system_prompt="You are an expert software engineer focused on writing clean, efficient, and well-documented code.",
            ),
            ModelTier.STANDARD: ModelMapping(
                use_case=UseCase.CODE_GENERATION,
                tier=ModelTier.STANDARD,
                primary_model="anthropic/claude-3-sonnet",
                fallback_models=["openai/gpt-4", "google/gemini-1.5-flash"],
                max_tokens=2048,
                temperature=0.3,
            ),
            ModelTier.ECONOMY: ModelMapping(
                use_case=UseCase.CODE_GENERATION,
                tier=ModelTier.ECONOMY,
                primary_model="anthropic/claude-3-haiku",
                fallback_models=["openai/gpt-3.5-turbo", "mistralai/mixtral-8x7b"],
                max_tokens=1024,
                temperature=0.3,
            ),
        },
        UseCase.ARCHITECTURE_DESIGN: {
            ModelTier.PREMIUM: ModelMapping(
                use_case=UseCase.ARCHITECTURE_DESIGN,
                tier=ModelTier.PREMIUM,
                primary_model="google/gemini-1.5-pro",
                fallback_models=["anthropic/claude-3-opus", "openai/gpt-4-turbo"],
                max_tokens=8192,
                temperature=0.7,
                system_prompt="You are a senior software architect with expertise in distributed systems and cloud architecture.",
            ),
            ModelTier.STANDARD: ModelMapping(
                use_case=UseCase.ARCHITECTURE_DESIGN,
                tier=ModelTier.STANDARD,
                primary_model="google/gemini-1.5-flash",
                fallback_models=["anthropic/claude-3-sonnet", "openai/gpt-4"],
                max_tokens=4096,
                temperature=0.6,
            ),
            ModelTier.ECONOMY: ModelMapping(
                use_case=UseCase.ARCHITECTURE_DESIGN,
                tier=ModelTier.ECONOMY,
                primary_model="anthropic/claude-3-haiku",
                fallback_models=["openai/gpt-3.5-turbo"],
                max_tokens=2048,
                temperature=0.5,
            ),
        },
        UseCase.DEBUGGING: {
            ModelTier.PREMIUM: ModelMapping(
                use_case=UseCase.DEBUGGING,
                tier=ModelTier.PREMIUM,
                primary_model="openai/gpt-4-turbo",
                fallback_models=["anthropic/claude-3-opus", "google/gemini-1.5-pro"],
                max_tokens=4096,
                temperature=0.1,
                system_prompt="You are an expert debugger. Analyze code systematically and provide precise solutions.",
            ),
            ModelTier.STANDARD: ModelMapping(
                use_case=UseCase.DEBUGGING,
                tier=ModelTier.STANDARD,
                primary_model="openai/gpt-4",
                fallback_models=["anthropic/claude-3-sonnet"],
                max_tokens=2048,
                temperature=0.2,
            ),
        },
        UseCase.DOCUMENTATION: {
            ModelTier.STANDARD: ModelMapping(
                use_case=UseCase.DOCUMENTATION,
                tier=ModelTier.STANDARD,
                primary_model="anthropic/claude-3-sonnet",
                fallback_models=["openai/gpt-4", "google/gemini-1.5-flash"],
                max_tokens=4096,
                temperature=0.5,
                system_prompt="You are a technical writer creating clear, comprehensive documentation.",
            ),
            ModelTier.ECONOMY: ModelMapping(
                use_case=UseCase.DOCUMENTATION,
                tier=ModelTier.ECONOMY,
                primary_model="anthropic/claude-3-haiku",
                fallback_models=["openai/gpt-3.5-turbo"],
                max_tokens=2048,
                temperature=0.5,
            ),
        },
        UseCase.CHAT_CONVERSATION: {
            ModelTier.STANDARD: ModelMapping(
                use_case=UseCase.CHAT_CONVERSATION,
                tier=ModelTier.STANDARD,
                primary_model="anthropic/claude-3-sonnet",
                fallback_models=["openai/gpt-4", "google/gemini-1.5-flash"],
                max_tokens=2048,
                temperature=0.7,
            ),
            ModelTier.ECONOMY: ModelMapping(
                use_case=UseCase.CHAT_CONVERSATION,
                tier=ModelTier.ECONOMY,
                primary_model="anthropic/claude-3-haiku",
                fallback_models=["openai/gpt-3.5-turbo", "mistralai/mixtral-8x7b"],
                max_tokens=1024,
                temperature=0.7,
            ),
        },
        UseCase.MEMORY_PROCESSING: {
            ModelTier.STANDARD: ModelMapping(
                use_case=UseCase.MEMORY_PROCESSING,
                tier=ModelTier.STANDARD,
                primary_model="google/gemini-1.5-flash",
                fallback_models=["anthropic/claude-3-haiku", "openai/gpt-3.5-turbo"],
                max_tokens=2048,
                temperature=0.3,
                system_prompt="Extract and structure information efficiently for memory storage.",
            )
        },
        UseCase.WORKFLOW_ORCHESTRATION: {
            ModelTier.PREMIUM: ModelMapping(
                use_case=UseCase.WORKFLOW_ORCHESTRATION,
                tier=ModelTier.PREMIUM,
                primary_model="google/gemini-1.5-pro",
                fallback_models=["anthropic/claude-3-opus", "openai/gpt-4-turbo"],
                max_tokens=8192,
                temperature=0.4,
                system_prompt="You are an AI workflow orchestrator. Break down complex tasks and coordinate execution.",
            ),
            ModelTier.STANDARD: ModelMapping(
                use_case=UseCase.WORKFLOW_ORCHESTRATION,
                tier=ModelTier.STANDARD,
                primary_model="google/gemini-1.5-flash",
                fallback_models=["anthropic/claude-3-sonnet", "openai/gpt-4"],
                max_tokens=4096,
                temperature=0.4,
            ),
        },
        UseCase.GENERAL_PURPOSE: {
            ModelTier.PREMIUM: ModelMapping(
                use_case=UseCase.GENERAL_PURPOSE,
                tier=ModelTier.PREMIUM,
                primary_model="anthropic/claude-3-opus",
                fallback_models=["openai/gpt-4-turbo", "google/gemini-1.5-pro"],
                max_tokens=4096,
                temperature=0.5,
            ),
            ModelTier.STANDARD: ModelMapping(
                use_case=UseCase.GENERAL_PURPOSE,
                tier=ModelTier.STANDARD,
                primary_model="anthropic/claude-3-sonnet",
                fallback_models=["openai/gpt-4", "google/gemini-1.5-flash"],
                max_tokens=2048,
                temperature=0.5,
            ),
            ModelTier.ECONOMY: ModelMapping(
                use_case=UseCase.GENERAL_PURPOSE,
                tier=ModelTier.ECONOMY,
                primary_model="anthropic/claude-3-haiku",
                fallback_models=["openai/gpt-3.5-turbo", "mistralai/mixtral-8x7b"],
                max_tokens=1024,
                temperature=0.5,
            ),
        },
    }

    def __init__(self, config: Optional[RouterConfig] = None):
        """Initialize unified router"""
        super().__init__(config)

        # Custom mappings can be added here
        self.custom_mappings: Dict[UseCase, Dict[ModelTier, ModelMapping]] = {}

    @lru_cache(maxsize=128)
    async def get_model_mapping(self, use_case: UseCase, tier: ModelTier = ModelTier.STANDARD) -> ModelMapping:
        """
        Get model mapping for a specific use case and tier.

        This implementation uses hardcoded mappings with fallback logic.
        """
        # Check custom mappings first
        if use_case in self.custom_mappings:
            tier_mappings = self.custom_mappings[use_case]
            if tier in tier_mappings:
                return tier_mappings[tier]

        # Check default mappings
        use_case_mappings = self.DEFAULT_MAPPINGS.get(use_case, {})

        # Try requested tier
        if tier in use_case_mappings:
            return use_case_mappings[tier]

        # Fall back to standard tier if requested tier not available
        if ModelTier.STANDARD in use_case_mappings:
            return use_case_mappings[ModelTier.STANDARD]

        # Fall back to any available tier
        if use_case_mappings:
            return next(iter(use_case_mappings.values()))

        # Ultimate fallback to general purpose standard
        return self.DEFAULT_MAPPINGS[UseCase.GENERAL_PURPOSE][ModelTier.STANDARD]

    def add_custom_mapping(self, mapping: ModelMapping):
        """
        Add a custom model mapping.

        This allows runtime configuration without modifying defaults.
        """
        if mapping.use_case not in self.custom_mappings:
            self.custom_mappings[mapping.use_case] = {}

        self.custom_mappings[mapping.use_case][mapping.tier] = mapping

        # Clear cache to pick up new mapping
        self.get_model_mapping.cache_clear()

    def remove_custom_mapping(self, use_case: UseCase, tier: ModelTier):
        """Remove a custom model mapping"""
        if use_case in self.custom_mappings:
            self.custom_mappings[use_case].pop(tier, None)
            if not self.custom_mappings[use_case]:
                del self.custom_mappings[use_case]

        # Clear cache
        self.get_model_mapping.cache_clear()

    def get_available_models(self) -> Dict[UseCase, Dict[ModelTier, str]]:
        """Get all available model configurations"""
        result = {}

        for use_case in UseCase:
            result[use_case] = {}
            for tier in ModelTier:
                try:
                    mapping = asyncio.run(self.get_model_mapping(use_case, tier))
                    result[use_case][tier] = mapping.primary_model
                except:
                    pass

        return result
