"""
Roo integration with MCP working memory system.

This package provides the integration between Roo modes and the MCP working memory system,
enabling context preservation across mode transitions, efficient memory access patterns,
and structured rule definitions.
"""

from .modes import RooMode, RooModeCapability, get_mode, MODES
from .transitions import TransitionContext, ModeTransitionManager
from .memory_hooks import BoomerangOperation
from .rules import Rule, RuleType, RuleIntent, RuleEngine

__all__ = [
    "RooMode",
    "RooModeCapability",
    "get_mode",
    "MODES",
    "TransitionContext",
    "ModeTransitionManager",
    "BoomerangOperation",
    "Rule",
    "RuleType",
    "RuleIntent",
    "RuleEngine",
]
