"""
AI Collaboration Metrics Package
Handles metric collection, aggregation, and analysis
"""

from .collector import AIMetricsCollector, AggregationWindow, MetricStats

__all__ = [
    "AIMetricsCollector",
    "AggregationWindow", 
    "MetricStats"
]