"""
"""
router = APIRouter(prefix="/admin/llm", tags=["llm-admin"])

# Pydantic models for requests/responses
class ProviderUpdate(BaseModel):
    """Model for updating provider configuration"""
    """Model for creating/updating model assignments"""
    """Model for testing a specific configuration"""
    test_prompt: str = "Hello, please respond with 'Test successful' if you can read this."
    temperature: float = 0.5
    max_tokens: int = 100

class BulkModelUpdate(BaseModel):
    """Model for bulk updating model availability"""
@router.get("/providers")
async def get_providers(db: AsyncSession = Depends(get_db), include_inactive: bool = False) -> List[Dict[str, Any]]:
    """Get all LLM providers"""
@router.put("/providers/{provider_name}")
async def update_provider(
    provider_name: str, update: ProviderUpdate, db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Update provider configuration"""
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
@router.post("/models/discover")
async def discover_models(background_tasks: BackgroundTasks, force_refresh: bool = False) -> Dict[str, Any]:
    """Discover available models from providers"""
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
    return {"updated": updated_count, "is_available": update.is_available}

@router.get("/use-cases")
async def get_use_cases(db: AsyncSession = Depends(get_db), include_assignments: bool = True) -> List[Dict[str, Any]]:
    """Get all use cases with their configurations"""
@router.get("/assignments")
async def get_model_assignments(
    db: AsyncSession = Depends(get_db), use_case: Optional[str] = None, tier: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get model assignments with filtering"""
@router.post("/assignments")
async def create_or_update_assignment(
    assignment: ModelAssignmentCreate, db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Create or update a model assignment"""
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
        raise HTTPException(status_code=404, detail="Assignment not found")

    await db.delete(assignment)
    await db.commit()

    return {"status": "deleted"}

@router.post("/test")
async def test_model_configuration(test_request: ModelTestRequest) -> Dict[str, Any]:
    """Test a specific model configuration"""
            "status": "success",
            "model": response.get("model"),
            "response": response["choices"][0]["message"]["content"],
            "tokens_used": response.get("usage", {}).get("total_tokens", 0),
            "latency_ms": round(elapsed_ms, 2),
        }

    except Exception:


        pass
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