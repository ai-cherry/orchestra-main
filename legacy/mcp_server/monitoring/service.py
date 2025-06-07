#!/usr/bin/env python3
"""Monitoring service for Cherry AI"""

import asyncio
from mcp_server.monitoring.performance import (
    get_performance_monitor,
    PerformanceOptimizer
)

async def main():
    monitor = get_performance_monitor()
    optimizer = PerformanceOptimizer(monitor)
    
    # Start monitoring and optimization tasks
    await asyncio.gather(
        monitor.collect_system_metrics(),
        optimizer.auto_optimize()
    )

if __name__ == "__main__":
    asyncio.run(main())
