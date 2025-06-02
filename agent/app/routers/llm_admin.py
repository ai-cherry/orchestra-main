"""
Admin API endpoints for LLM configuration management
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from sqlalchemy.orm import selectinload

from core.llm_router_dynamic import get_dynamic_llm_router
from core.database.llm_config_models import (
    LLMProvider,
    LLMModel,
    LLMUseCase,
    LLMModelAssignment,
    LLMFallbackModel,
    LLMMetric,
)
from agent.app.core.database import get_db

router = APIRouter(prefix="/admin/llm", tags=["llm-admin"])

# Pydantic models for requests/responses
class ProviderUpdate(BaseModel):
    """Model for updating provider configuration"""

    api_key_env_var: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None

class ModelAssignmentCreate(BaseModel):
    """Model for creating/updating model assignments"""

    use_case: str
    tier: str
    primary_model_id: int
    fallback_model_ids: List[int] = Field(default_factory=list)
    temperature_override: Optional[float] = Field(None, ge=0, le=2)
    max_tokens_override: Optional[int] = Field(None, ge=1, le=32000)
    system_prompt_override: Optional[str] = None

class ModelTestRequest(BaseModel):
    """Model for testing a specific configuration"""

    model_identifier: str
    provider: str
    test_prompt: str = "Hello, please respond with 'Test successful' if you can read this."
    temperature: float = 0.5
    max_tokens: int = 100

class BulkModelUpdate(BaseModel):
    """Model for bulk updating model availability"""

    model_ids: List[int]
    is_available: bool

@router.get("/providers")
async def get_providers(db: AsyncSession = Depends(get_db), include_inactive: bool = False) -> List[Dict[str, Any]]:
    """Get all LLM providers"""
    query = select(LLMProvider)
    if not include_inactive:
        query = query.where(LLMProvider.is_active == True)

    result = await db.execute(query.order_by(LLMProvider.priority))
    providers = result.scalars().all()

    return [provider.to_dict() for provider in providers]

@router.put("/providers/{provider_name}")
async def update_provider(
    provider_name: str, update: ProviderUpdate, db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Update provider configuration"""
    result = await db.execute(select(LLMProvider).where(LLMProvider.name == provider_name))
    provider = result.scalar_one_or_none()

    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")

    # Update fields
    if update.api_key_env_var is not None:
        provider.api_key_env_var = update.api_key_env_var
    if update.is_active is not None:
        provider.is_active = update.is_active
    if update.priority is not None:
        provider.priority = update.priority

    await db.commit()
    await db.refresh(provider)

    return provider.to_dict()

@router.get("/models")
async def get_models(
    db: AsyncSession = Depends(get_db),
    provider: Optional[str] = None,
    available_only: bool = True,
    use_case: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get available models with optional filtering"""
    query = select(LLMModel).options(selectinload(LLMModel.provider))

    if available_only:
        query = query.where(LLMModel.is_available == True)

    if provider:
        query = query.join(LLMProvider).where(LLMProvider.name == provider)

    result = await db.execute(query.order_by(LLMModel.provider_id, LLMModel.model_identifier))
    models = result.scalars().all()

    return [model.to_dict() for model in models]

@router.post("/models/discover")
async def discover_models(background_tasks: BackgroundTasks, force_refresh: bool = False) -> Dict[str, Any]:
    """Discover available models from providers"""
    router = get_dynamic_llm_router()

    # Run discovery in background if not forcing refresh
    if not force_refresh:
        background_tasks.add_task(router.discover_available_models, force_refresh=True)
        return {"status": "discovery_started", "message": "Model discovery running in background"}

    # Run discovery immediately
    discovered = await router.discover_available_models(force_refresh=True)

    return {
        "status": "discovery_completed",
        "providers": {provider: len(models) for provider, models in discovered.items()},
        "total_models": sum(len(models) for models in discovered.values()),
    }

@router.put("/models/availability")
async def update_model_availability(update: BulkModelUpdate, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Bulk update model availability"""
    result = await db.execute(select(LLMModel).where(LLMModel.id.in_(update.model_ids)))
    models = result.scalars().all()

    updated_count = 0
    for model in models:
        model.is_available = update.is_available
        model.last_checked = datetime.utcnow()
        updated_count += 1

    await db.commit()

    return {"updated": updated_count, "is_available": update.is_available}

@router.get("/use-cases")
async def get_use_cases(db: AsyncSession = Depends(get_db), include_assignments: bool = True) -> List[Dict[str, Any]]:
    """Get all use cases with their configurations"""
    query = select(LLMUseCase)

    if include_assignments:
        query = query.options(
            selectinload(LLMUseCase.assignments)
            .selectinload(LLMModelAssignment.primary_model)
            .selectinload(LLMModel.provider)
        )

    result = await db.execute(query.order_by(LLMUseCase.use_case))
    use_cases = result.scalars().all()

    return [use_case.to_dict() for use_case in use_cases]

@router.get("/assignments")
async def get_model_assignments(
    db: AsyncSession = Depends(get_db), use_case: Optional[str] = None, tier: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get model assignments with filtering"""
    query = select(LLMModelAssignment).options(
        selectinload(LLMModelAssignment.use_case),
        selectinload(LLMModelAssignment.primary_model).selectinload(LLMModel.provider),
        selectinload(LLMModelAssignment.fallback_models).selectinload(LLMFallbackModel.model),
    )

    if use_case:
        query = query.join(LLMUseCase).where(LLMUseCase.use_case == use_case)

    if tier:
        query = query.where(LLMModelAssignment.tier == tier)

    result = await db.execute(query)
    assignments = result.scalars().all()

    return [assignment.to_dict() for assignment in assignments]

@router.post("/assignments")
async def create_or_update_assignment(
    assignment: ModelAssignmentCreate, db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Create or update a model assignment"""
    # Get use case
    use_case_result = await db.execute(select(LLMUseCase).where(LLMUseCase.use_case == assignment.use_case))
    use_case = use_case_result.scalar_one_or_none()

    if not use_case:
        raise HTTPException(status_code=404, detail=f"Use case {assignment.use_case} not found")

    # Check if assignment exists
    existing_result = await db.execute(
        select(LLMModelAssignment).where(
            and_(LLMModelAssignment.use_case_id == use_case.id, LLMModelAssignment.tier == assignment.tier)
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        # Update existing
        existing.primary_model_id = assignment.primary_model_id
        existing.temperature_override = assignment.temperature_override
        existing.max_tokens_override = assignment.max_tokens_override
        existing.system_prompt_override = assignment.system_prompt_override

        # Clear existing fallbacks
        await db.execute(delete(LLMFallbackModel).where(LLMFallbackModel.assignment_id == existing.id))

        db_assignment = existing
    else:
        # Create new
        db_assignment = LLMModelAssignment(
            use_case_id=use_case.id,
            tier=assignment.tier,
            primary_model_id=assignment.primary_model_id,
            temperature_override=assignment.temperature_override,
            max_tokens_override=assignment.max_tokens_override,
            system_prompt_override=assignment.system_prompt_override,
        )
        db.add(db_assignment)
        await db.flush()

    # Add fallback models
    for priority, model_id in enumerate(assignment.fallback_model_ids):
        fallback = LLMFallbackModel(assignment_id=db_assignment.id, model_id=model_id, priority=priority)
        db.add(fallback)

    await db.commit()

    # Reload with relationships
    await db.refresh(db_assignment)
    result = await db.execute(
        select(LLMModelAssignment)
        .options(
            selectinload(LLMModelAssignment.use_case),
            selectinload(LLMModelAssignment.primary_model),
            selectinload(LLMModelAssignment.fallback_models).selectinload(LLMFallbackModel.model),
        )
        .where(LLMModelAssignment.id == db_assignment.id)
    )
    db_assignment = result.scalar_one()

    return db_assignment.to_dict()

@router.delete("/assignments/{assignment_id}")
async def delete_assignment(assignment_id: int, db: AsyncSession = Depends(get_db)) -> Dict[str, str]:
    """Delete a model assignment"""
    result = await db.execute(select(LLMModelAssignment).where(LLMModelAssignment.id == assignment_id))
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    await db.delete(assignment)
    await db.commit()

    return {"status": "deleted"}

@router.post("/test")
async def test_model_configuration(test_request: ModelTestRequest) -> Dict[str, Any]:
    """Test a specific model configuration"""
    router = get_dynamic_llm_router()

    try:
        # Test the model directly
        start_time = datetime.utcnow()

        response = await router.complete(
            messages=test_request.test_prompt,
            model_override=test_request.model_identifier,
            temperature_override=test_request.temperature,
            max_tokens_override=test_request.max_tokens,
            cache=False,  # Don't cache test requests
        )

        elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        return {
            "status": "success",
            "model": response.get("model"),
            "response": response["choices"][0]["message"]["content"],
            "tokens_used": response.get("usage", {}).get("total_tokens", 0),
            "latency_ms": round(elapsed_ms, 2),
        }

    except Exception as e:
        return {"status": "error", "error": str(e), "model": test_request.model_identifier}

@router.get("/metrics")
async def get_metrics(
    db: AsyncSession = Depends(get_db),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    use_case: Optional[str] = None,
    model_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Get aggregated metrics for LLM usage"""
    query = select(LLMMetric).options(
        selectinload(LLMMetric.model).selectinload(LLMModel.provider), selectinload(LLMMetric.use_case)
    )

    if start_date:
        query = query.where(LLMMetric.date >= start_date.date())

    if end_date:
        query = query.where(LLMMetric.date <= end_date.date())

    if use_case:
        query = query.join(LLMUseCase).where(LLMUseCase.use_case == use_case)

    if model_id:
        query = query.where(LLMMetric.model_id == model_id)

    result = await db.execute(query.order_by(LLMMetric.date.desc()))
    metrics = result.scalars().all()

    # Aggregate metrics
    total_requests = sum(m.request_count for m in metrics)
    total_successes = sum(m.success_count for m in metrics)
    total_failures = sum(m.failure_count for m in metrics)
    total_tokens = sum(m.total_tokens for m in metrics)
    total_cost = sum(float(m.total_cost or 0) for m in metrics)

    # Group by model
    by_model = {}
    for metric in metrics:
        model_key = metric.model.model_identifier if metric.model else "unknown"
        if model_key not in by_model:
            by_model[model_key] = {
                "requests": 0,
                "successes": 0,
                "failures": 0,
                "tokens": 0,
                "cost": 0,
                "avg_latency_ms": [],
            }

        by_model[model_key]["requests"] += metric.request_count
        by_model[model_key]["successes"] += metric.success_count
        by_model[model_key]["failures"] += metric.failure_count
        by_model[model_key]["tokens"] += metric.total_tokens
        by_model[model_key]["cost"] += float(metric.total_cost or 0)
        if metric.avg_latency_ms:
            by_model[model_key]["avg_latency_ms"].append(float(metric.avg_latency_ms))

    # Calculate average latencies
    for model_data in by_model.values():
        latencies = model_data["avg_latency_ms"]
        model_data["avg_latency_ms"] = sum(latencies) / len(latencies) if latencies else 0

    return {
        "summary": {
            "total_requests": total_requests,
            "total_successes": total_successes,
            "total_failures": total_failures,
            "success_rate": (total_successes / total_requests * 100) if total_requests > 0 else 0,
            "total_tokens": total_tokens,
            "total_cost": round(total_cost, 4),
        },
        "by_model": by_model,
        "metrics": [metric.to_dict() for metric in metrics[:100]],  # Limit to 100 for performance
    }

@router.get("/configuration-summary")
async def get_configuration_summary() -> Dict[str, Any]:
    """Get a summary of current LLM configuration"""
    router = get_dynamic_llm_router()
    return await router.get_configuration_summary()
