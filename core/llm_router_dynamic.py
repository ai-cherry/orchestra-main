"""
Enhanced LLM Router with Dynamic Database Configuration

This module extends the base LLM router to support dynamic model configuration
from the database, allowing real-time updates without code changes.
"""

import os
import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, selectinload
from sqlalchemy import select, and_, func

from core.llm_router import UnifiedLLMRouter, UseCase, ModelTier, ModelMapping, RouterConfig
from core.database.llm_config_models import (
    LLMProvider,
    LLMModel,
    LLMUseCase,
    LLMModelAssignment,
    LLMFallbackModel,
    LLMMetric,
)

logger = logging.getLogger(__name__)


class DynamicLLMRouter(UnifiedLLMRouter):
    """
    Enhanced LLM Router that loads configurations from database
    and supports real-time updates without restarts.
    """

    def __init__(self, config: Optional[RouterConfig] = None, db_url: Optional[str] = None):
        """Initialize the dynamic LLM router with database support"""
        super().__init__(config)

        # Database configuration
        self.db_url = db_url or os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/orchestra")
        self.engine = create_async_engine(self.db_url, echo=False, pool_size=10, max_overflow=20)
        self.async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

        # Cache configuration
        self._config_cache: Dict[str, Any] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=5)  # Refresh config every 5 minutes

        # Model discovery cache
        self._available_models_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._models_cache_timestamp: Optional[datetime] = None

        # Initialize configuration
        asyncio.create_task(self._load_configuration())

    async def _load_configuration(self):
        """Load model configurations from database"""
        try:
            async with self.async_session() as session:
                # Load all use cases with their assignments
                use_cases = await session.execute(
                    select(LLMUseCase).options(
                        selectinload(LLMUseCase.assignments).selectinload(LLMModelAssignment.primary_model),
                        selectinload(LLMUseCase.assignments).selectinload(LLMModelAssignment.fallback_models),
                    )
                )

                # Build MODEL_MAPPINGS from database
                new_mappings = {}
                for use_case in use_cases.scalars():
                    use_case_enum = UseCase(use_case.use_case)
                    new_mappings[use_case_enum] = {}

                    for assignment in use_case.assignments:
                        if assignment.primary_model and assignment.primary_model.is_available:
                            tier_enum = ModelTier(assignment.tier)

                            # Get fallback models
                            fallback_models = []
                            for fb in sorted(assignment.fallback_models, key=lambda x: x.priority):
                                if fb.model.is_available:
                                    fallback_models.append(fb.model.model_identifier)

                            # Create model mapping
                            mapping = ModelMapping(
                                use_case=use_case_enum,
                                tier=tier_enum,
                                primary_model=assignment.primary_model.model_identifier,
                                fallback_models=fallback_models,
                                max_tokens=assignment.max_tokens_override or use_case.default_max_tokens,
                                temperature=float(assignment.temperature_override or use_case.default_temperature),
                                system_prompt=assignment.system_prompt_override or use_case.default_system_prompt,
                            )

                            new_mappings[use_case_enum][tier_enum] = mapping

                # Update the MODEL_MAPPINGS
                self.MODEL_MAPPINGS = new_mappings
                self._cache_timestamp = datetime.utcnow()

                logger.info(f"Loaded {len(new_mappings)} use case configurations from database")

        except Exception as e:
            logger.error(f"Failed to load configuration from database: {str(e)}")
            # Fall back to hardcoded mappings if database fails

    async def _ensure_configuration_fresh(self):
        """Ensure configuration is fresh, reload if needed"""
        if not self._cache_timestamp or datetime.utcnow() - self._cache_timestamp > self._cache_ttl:
            await self._load_configuration()

    async def complete(
        self,
        messages: Union[str, List[Dict[str, str]]],
        use_case: UseCase = UseCase.GENERAL_PURPOSE,
        tier: ModelTier = ModelTier.STANDARD,
        **kwargs,
    ) -> Dict[str, Any]:
        """Override complete to ensure fresh configuration"""
        await self._ensure_configuration_fresh()

        # Track start time for metrics
        start_time = datetime.utcnow()
        model_used = None
        success = False
        tokens_used = 0

        try:
            # Call parent complete method
            response = await super().complete(messages, use_case, tier, **kwargs)

            # Extract metrics
            model_used = response.get("model")
            tokens_used = response.get("usage", {}).get("total_tokens", 0)
            success = True

            return response

        finally:
            # Record metrics
            if model_used:
                elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                await self._record_metrics(
                    model_identifier=model_used,
                    use_case=use_case.value,
                    success=success,
                    tokens=tokens_used,
                    latency_ms=elapsed_ms,
                )

    async def _record_metrics(
        self, model_identifier: str, use_case: str, success: bool, tokens: int, latency_ms: float
    ):
        """Record usage metrics to database"""
        try:
            async with self.async_session() as session:
                # Find model and use case IDs
                model_result = await session.execute(
                    select(LLMModel).where(LLMModel.model_identifier == model_identifier)
                )
                model = model_result.scalar_one_or_none()

                use_case_result = await session.execute(select(LLMUseCase).where(LLMUseCase.use_case == use_case))
                use_case_obj = use_case_result.scalar_one_or_none()

                if model and use_case_obj:
                    # Find or create today's metric record
                    today = datetime.utcnow().date()
                    metric_result = await session.execute(
                        select(LLMMetric).where(
                            and_(
                                LLMMetric.model_id == model.id,
                                LLMMetric.use_case_id == use_case_obj.id,
                                LLMMetric.date == today,
                            )
                        )
                    )
                    metric = metric_result.scalar_one_or_none()

                    if not metric:
                        metric = LLMMetric(model_id=model.id, use_case_id=use_case_obj.id, date=today)
                        session.add(metric)

                    # Update metrics
                    metric.request_count += 1
                    if success:
                        metric.success_count += 1
                    else:
                        metric.failure_count += 1

                    metric.total_tokens += tokens

                    # Calculate cost if available
                    if model.cost_per_1k_tokens:
                        cost = (tokens / 1000) * float(model.cost_per_1k_tokens)
                        metric.total_cost = Decimal(str(float(metric.total_cost or 0) + cost))

                    # Update average latency
                    if metric.avg_latency_ms:
                        current_avg = float(metric.avg_latency_ms)
                        new_avg = ((current_avg * (metric.request_count - 1)) + latency_ms) / metric.request_count
                        metric.avg_latency_ms = Decimal(str(new_avg))
                    else:
                        metric.avg_latency_ms = Decimal(str(latency_ms))

                    await session.commit()

        except Exception as e:
            logger.error(f"Failed to record metrics: {str(e)}")

    async def discover_available_models(self, force_refresh: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        """
        Discover available models from Portkey and OpenRouter

        Returns:
            Dict mapping provider names to lists of available models
        """
        # Check cache first
        if (
            not force_refresh
            and self._available_models_cache
            and self._models_cache_timestamp
            and datetime.utcnow() - self._models_cache_timestamp < timedelta(hours=24)
        ):
            return self._available_models_cache

        discovered_models = {}

        # Discover from Portkey
        if self.config.portkey_api_key:
            try:
                response = await self.portkey_client.get("/models")
                response.raise_for_status()
                models_data = response.json()

                discovered_models["portkey"] = [
                    {
                        "model_identifier": model["id"],
                        "display_name": model.get("name", model["id"]),
                        "capabilities": {
                            "max_tokens": model.get("max_tokens", 4096),
                            "supports_tools": model.get("supports_functions", False),
                            "supports_vision": model.get("supports_vision", False),
                        },
                    }
                    for model in models_data.get("data", [])
                ]

            except Exception as e:
                logger.error(f"Failed to discover Portkey models: {str(e)}")
                discovered_models["portkey"] = []

        # Discover from OpenRouter
        if self.config.openrouter_api_key:
            try:
                response = await self.openrouter_client.get("/models")
                response.raise_for_status()
                models_data = response.json()

                discovered_models["openrouter"] = [
                    {
                        "model_identifier": model["id"],
                        "display_name": model.get("name", model["id"]),
                        "capabilities": {
                            "max_tokens": model.get("context_length", 4096),
                            "supports_tools": "function_calling" in model.get("capabilities", []),
                            "supports_vision": "vision" in model.get("capabilities", []),
                        },
                        "cost_per_1k_tokens": model.get("pricing", {}).get("prompt", 0),
                    }
                    for model in models_data.get("data", [])
                ]

            except Exception as e:
                logger.error(f"Failed to discover OpenRouter models: {str(e)}")
                discovered_models["openrouter"] = []

        # Update cache
        self._available_models_cache = discovered_models
        self._models_cache_timestamp = datetime.utcnow()

        # Update database with discovered models
        await self._update_database_models(discovered_models)

        return discovered_models

    async def _update_database_models(self, discovered_models: Dict[str, List[Dict[str, Any]]]):
        """Update database with discovered models"""
        try:
            async with self.async_session() as session:
                # Get providers
                providers_result = await session.execute(select(LLMProvider))
                providers = {p.name: p for p in providers_result.scalars()}

                for provider_name, models in discovered_models.items():
                    provider = providers.get(provider_name)
                    if not provider:
                        continue

                    for model_data in models:
                        # Check if model exists
                        model_result = await session.execute(
                            select(LLMModel).where(
                                and_(
                                    LLMModel.provider_id == provider.id,
                                    LLMModel.model_identifier == model_data["model_identifier"],
                                )
                            )
                        )
                        model = model_result.scalar_one_or_none()

                        if not model:
                            # Create new model
                            model = LLMModel(
                                provider_id=provider.id,
                                model_identifier=model_data["model_identifier"],
                                display_name=model_data["display_name"],
                                capabilities=model_data["capabilities"],
                                cost_per_1k_tokens=model_data.get("cost_per_1k_tokens"),
                                is_available=True,
                                last_checked=datetime.utcnow(),
                            )
                            session.add(model)
                        else:
                            # Update existing model
                            model.display_name = model_data["display_name"]
                            model.capabilities = model_data["capabilities"]
                            if model_data.get("cost_per_1k_tokens"):
                                model.cost_per_1k_tokens = model_data["cost_per_1k_tokens"]
                            model.is_available = True
                            model.last_checked = datetime.utcnow()

                await session.commit()
                logger.info(f"Updated {sum(len(m) for m in discovered_models.values())} models in database")

        except Exception as e:
            logger.error(f"Failed to update database models: {str(e)}")

    async def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration for admin UI"""
        await self._ensure_configuration_fresh()

        summary = {
            "providers": [],
            "use_cases": [],
            "total_models": 0,
            "last_updated": self._cache_timestamp.isoformat() if self._cache_timestamp else None,
        }

        async with self.async_session() as session:
            # Get providers
            providers = await session.execute(select(LLMProvider).where(LLMProvider.is_active == True))
            for provider in providers.scalars():
                models_count = await session.execute(
                    select(func.count(LLMModel.id)).where(
                        and_(LLMModel.provider_id == provider.id, LLMModel.is_available == True)
                    )
                )
                summary["providers"].append(
                    {"name": provider.name, "models_count": models_count.scalar(), "priority": provider.priority}
                )

            # Get use cases with assignments
            use_cases = await session.execute(select(LLMUseCase).options(selectinload(LLMUseCase.assignments)))
            for use_case in use_cases.scalars():
                use_case_data = {"use_case": use_case.use_case, "display_name": use_case.display_name, "tiers": {}}

                for assignment in use_case.assignments:
                    if assignment.primary_model:
                        use_case_data["tiers"][assignment.tier] = {
                            "model": assignment.primary_model.model_identifier,
                            "provider": assignment.primary_model.provider.name,
                        }

                summary["use_cases"].append(use_case_data)

            # Total models count
            total_models = await session.execute(select(func.count(LLMModel.id)).where(LLMModel.is_available == True))
            summary["total_models"] = total_models.scalar()

        return summary

    async def close(self):
        """Close connections and cleanup"""
        await super().close()
        await self.engine.dispose()


# Singleton instance
_dynamic_router_instance: Optional[DynamicLLMRouter] = None


def get_dynamic_llm_router(config: Optional[RouterConfig] = None, db_url: Optional[str] = None) -> DynamicLLMRouter:
    """Get or create the singleton dynamic LLM router instance"""
    global _dynamic_router_instance
    if _dynamic_router_instance is None:
        _dynamic_router_instance = DynamicLLMRouter(config, db_url)
    return _dynamic_router_instance
