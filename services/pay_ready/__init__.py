"""
Pay Ready Domain Services
========================

This module contains all services specific to the Pay Ready (Sophia) domain,
including ETL orchestration, entity resolution, and memory management.
"""

from .etl_orchestrator import PayReadyETLOrchestrator
from .entity_resolver import PayReadyEntityResolver
from .memory_manager import PayReadyMemoryManager
from .query_agent import PayReadyQueryAgent

__all__ = ["PayReadyETLOrchestrator", "PayReadyEntityResolver", "PayReadyMemoryManager", "PayReadyQueryAgent"]

# Domain configuration
DOMAIN_CONFIG = {
    "namespace": "pay_ready",
    "persona": "sophia",
    "database_schema": "pay_ready",
    "cache_prefix": "pr:",
    "weaviate_collections": [
        "PayReadySlackMessage",
        "PayReadyGongCallSegment",
        "PayReadyHubSpotNote",
        "PayReadySalesforceNote",
    ],
}
