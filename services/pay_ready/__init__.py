# TODO: Consider adding connection pooling configuration
"""
"""
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
