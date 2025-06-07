"""
Metrics collection for monitoring
"""

import time
from typing import Dict, Any
from collections import defaultdict
import asyncio

class MetricsCollector:
    """Collects system and application metrics"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.start_time = time.time()
        
    async def record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a metric value"""
        self.metrics[name].append({
            "value": value,
            "timestamp": time.time(),
            "tags": tags or {}
        })
        
    async def get_metrics(self, name: str = None) -> Dict[str, Any]:
        """Get recorded metrics"""
        if name:
            return {name: self.metrics.get(name, [])}
        return dict(self.metrics)
        
    def get_uptime(self) -> float:
        """Get system uptime in seconds"""
        return time.time() - self.start_time
