"""
"""
    """Schema for a system component's health status."""
    status: str  # "healthy", "degraded", "unavailable"
    message: Optional[str] = None
    details: Dict[str, Any] = {}

class HealthStatus(BaseModel):
    """Schema for system health status."""
    status: str  # "healthy", "degraded", "unavailable"
    environment: str
    version: str = "1.0.0"
    timestamp: datetime = datetime.now()
    components: Dict[str, ComponentHealth]
    runtime_info: Dict[str, str] = {}
    cloud_info: Dict[str, Any] = {}

@router.get("/health", summary="Check system health")
async def check_health(
    request: Request,
    settings: Settings = Depends(get_settings),
    memory_manager=Depends(get_memory_manager),
    redis_cache=Depends(get_redis_cache),
) -> HealthStatus:
    """
    """
    overall_status = "healthy"
    components = {
        "api": ComponentHealth(status="healthy", message="API is responding normally"),
    }

    # Runtime information
    runtime_info = {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "hostname": platform.node(),
    }

    # Cloud information (removed GCP references)
    cloud_info = {}
    # If you want to add Vultr or other info, do it here, but do not reference GCP.

    # Check memory system health
    try:

        pass
        if hasattr(memory_manager, "health_check"):
            memory_health = await memory_manager.health_check()

            # Process memory health info
            if memory_health.get("status") == "healthy":
                components["memory"] = ComponentHealth(
                    status="healthy",
                    message="Memory system is working correctly",
                    details=memory_health,
                )
            else:
                components["memory"] = ComponentHealth(
                    status="degraded",
                    message=memory_health.get("message", "Memory system degraded"),
                    details=memory_health,
                )
                overall_status = "degraded"
        else:
            # No health check method, assume memory system is functional
            components["memory"] = ComponentHealth(
                status="healthy",
                message="Memory system is available (basic check)",
                details={"type": memory_manager.__class__.__name__},
            )
    except Exception:

        pass
        logger.error(f"Error checking memory system health: {e}")
        components["memory"] = ComponentHealth(
            status="unavailable",
            message=f"Memory system error: {str(e)}",
            details={"error": str(e), "type": "exception"},
        )
        overall_status = "degraded"

    # Check Redis cache health
    try:

        pass
        if hasattr(redis_cache, "health_check"):
            cache_health = await redis_cache.health_check()

            # Process cache health info
            if cache_health.get("status") == "healthy":
                components["cache"] = ComponentHealth(
                    status="healthy",
                    message="Cache system is working correctly",
                    details=cache_health,
                )
            elif cache_health.get("status") in ["disabled", "not_configured"]:
                components["cache"] = ComponentHealth(
                    status="unavailable",
                    message="Cache system is not enabled",
                    details=cache_health,
                )
                # Don't mark system as degraded if caching is intentionally disabled
            else:
                components["cache"] = ComponentHealth(
                    status="degraded",
                    message=cache_health.get("message", "Cache system degraded"),
                    details=cache_health,
                )
                # Only mark system as degraded if cache was supposed to be enabled
                if cache_health.get("enabled", False):
                    overall_status = "degraded"
        else:
            # No health check method, assume cache isn't critical
            components["cache"] = ComponentHealth(
                status="unavailable",
                message="Cache system health check unavailable",
                details={"type": redis_cache.__class__.__name__},
            )
    except Exception:

        pass
        logger.error(f"Error checking cache health: {e}")
        components["cache"] = ComponentHealth(
            status="unavailable",
            message=f"Cache system error: {str(e)}",
            details={"error": str(e), "type": "exception"},
        )
        # Don't mark system as degraded just for cache failure

    # Return health status
    return HealthStatus(
        status=overall_status,
        environment=settings.ENVIRONMENT,
        components=components,
        runtime_info=runtime_info,
        cloud_info=cloud_info,
    )

@router.get("/ping", summary="Simple ping endpoint")
async def ping() -> Dict[str, str]:
    """
        Dict with a "status" key set to "ok"
    """
    return {"status": "ok"}
