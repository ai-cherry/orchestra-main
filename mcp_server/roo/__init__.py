"""
Roo integration with MCP working memory system.

This package provides the integration between Roo modes and the MCP working memory system,
enabling context preservation across mode transitions, efficient memory access patterns,
and structured rule definitions.
"""

from .memory_hooks import BoomerangOperation
from .modes import MODES, RooMode, RooModeCapability, get_mode
from .rules import Rule, RuleEngine, RuleIntent, RuleType
from .transitions import ModeTransitionManager, TransitionContext

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
