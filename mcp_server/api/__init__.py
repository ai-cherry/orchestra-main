"""Cherry AI API with single-user optimizations"""

from .main import app
from mcp_server.monitoring.performance import (
    PerformanceMiddleware,
    get_performance_monitor
)

# Add performance monitoring
app.add_middleware(PerformanceMiddleware)

# Start background monitoring
import asyncio

@app.on_event("startup")
async def startup_monitoring():
    monitor = get_performance_monitor()
    asyncio.create_task(monitor.collect_system_metrics())

__all__ = ["app"]
