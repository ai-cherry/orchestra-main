"""
Factory AI Bridge Package.

This package provides the bridge between Factory AI Droids and the existing
Roo/MCP infrastructure, enabling seamless integration and fallback capabilities.
"""

from .api_gateway import FactoryBridgeGateway

__all__ = ["FactoryBridgeGateway"]
__version__ = "1.0.0"
