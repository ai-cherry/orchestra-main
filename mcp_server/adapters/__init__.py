"""MCP Server Adapters for Factory AI Integration.

This package provides adapters that bridge Factory AI Droids with existing MCP servers,
enabling seamless integration while maintaining backward compatibility.
"""

from .factory_mcp_adapter import FactoryMCPAdapter, CircuitBreaker, CircuitBreakerError
from .architect_adapter import ArchitectAdapter
from .code_adapter import CodeAdapter
from .debug_adapter import DebugAdapter
from .reliability_adapter import ReliabilityAdapter
from .knowledge_adapter import KnowledgeAdapter

__all__ = [
    "FactoryMCPAdapter",
    "CircuitBreaker",
    "CircuitBreakerError",
    "ArchitectAdapter",
    "CodeAdapter",
    "DebugAdapter",
    "ReliabilityAdapter",
    "KnowledgeAdapter",
]
