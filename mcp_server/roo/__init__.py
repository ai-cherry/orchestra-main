"""
Roo MCP Integration Module
"""

# Import only what exists
try:
    from .orchestra_integration import (
        OrchestraRooIntegration,
        orchestra_roo,
        initialize_orchestra_roo
    )
    __all__ = [
        "OrchestraRooIntegration",
        "orchestra_roo",
        "initialize_orchestra_roo"
    ]
except ImportError:
    # If orchestra_integration is not available, provide empty exports
    __all__ = []
