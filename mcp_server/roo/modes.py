"""
Centralized mode definitions for Roo.

This module provides a centralized location for defining Roo modes,
their capabilities, and relationships. It enables better organization
and management of mode-specific behavior.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field


class RooModeCapability(str, Enum):
    """Capabilities that can be assigned to Roo modes."""

    READ_FILES = "read_files"
    WRITE_FILES = "write_files"
    EXECUTE_COMMANDS = "execute_commands"
    ACCESS_INTERNET = "access_internet"
    MODIFY_MEMORY = "modify_memory"
    ANALYZE_CODE = "analyze_code"
    REFACTOR_CODE = "refactor_code"
    DESIGN_ARCHITECTURE = "design_architecture"
    DEBUG_CODE = "debug_code"
    REVIEW_CODE = "review_code"


class RooMode(BaseModel):
    """Definition of a Roo mode with its capabilities and settings."""

    slug: str = Field(..., description="Unique identifier for the mode")
    name: str = Field(..., description="Display name for the mode")
    description: str = Field(
        ..., description="Detailed description of the mode's purpose"
    )
    role: str = Field(..., description="Role description provided to the LLM")
    capabilities: List[RooModeCapability] = Field(
        default_factory=list, description="List of capabilities this mode has"
    )
    memory_access_level: str = Field(
        default="read",
        description="Level of memory access: 'read', 'write', or 'admin'",
    )
    can_transition_to: List[str] = Field(
        default_factory=list,
        description="List of mode slugs this mode can transition to",
    )
    default_rules: Dict[str, Any] = Field(
        default_factory=dict, description="Default rules applied to this mode"
    )
    file_patterns: List[str] = Field(
        default_factory=list, description="File patterns this mode can access or modify"
    )
    model: str = Field(default="", description="The LLM model to use for this mode")
    temperature: float = Field(
        default=0.7, description="Temperature setting for the LLM"
    )

    def can_access_memory(self) -> bool:
        """Check if this mode can access memory."""
        return self.memory_access_level in ["read", "write", "admin"]

    def can_modify_memory(self) -> bool:
        """Check if this mode can modify memory."""
        return self.memory_access_level in ["write", "admin"]

    def can_access_file(self, file_path: str) -> bool:
        """Check if this mode can access a specific file."""
        if not self.file_patterns:
            return True

        import re

        return any(re.match(pattern, file_path) for pattern in self.file_patterns)

    def can_transition_to_mode(self, target_mode_slug: str) -> bool:
        """Check if this mode can transition to a specific target mode."""
        return target_mode_slug in self.can_transition_to

    def has_capability(self, capability: RooModeCapability) -> bool:
        """Check if this mode has a specific capability."""
        return capability in self.capabilities


# Define standard modes
CODE_MODE = RooMode(
    slug="code",
    name="💻 Code",
    description="Expert software engineer focused on implementing features and refactoring code",
    role="You are Roo, a highly skilled software engineer with extensive knowledge in many programming languages, frameworks, design patterns, and best practices.",
    capabilities=[
        RooModeCapability.READ_FILES,
        RooModeCapability.WRITE_FILES,
        RooModeCapability.EXECUTE_COMMANDS,
        RooModeCapability.MODIFY_MEMORY,
        RooModeCapability.REFACTOR_CODE,
    ],
    memory_access_level="write",
    can_transition_to=["architect", "debug", "reviewer", "orchestrator"],
    file_patterns=[
        ".*\\.py$",
        ".*\\.js$",
        ".*\\.ts$",
        ".*\\.html$",
        ".*\\.css$",
        ".*\\.json$",
        ".*\\.yaml$",
        ".*\\.yml$",
    ],
    model="anthropic/claude-3.7-sonnet",
    temperature=0.7,
)

ARCHITECT_MODE = RooMode(
    slug="architect",
    name="🏗 Architect",
    description="Senior AI/Cloud architect and codebase strategist",
    role="You are Roo, a senior AI/Cloud architect and codebase strategist specializing in Python, FastAPI, multi-agent systems, GCP, Terraform, and CI/CD pipelines.",
    capabilities=[
        RooModeCapability.READ_FILES,
        RooModeCapability.ACCESS_INTERNET,
        RooModeCapability.DESIGN_ARCHITECTURE,
    ],
    memory_access_level="read",
    can_transition_to=["code", "strategy"],
    file_patterns=[".*\\.md$", ".*\\.tf$", ".*\\.hcl$", ".*\\.yaml$", ".*\\.yml$"],
    model="anthropic/claude-3.7-sonnet",
    temperature=0.7,
)

DEBUG_MODE = RooMode(
    slug="debug",
    name="🪲 Debug",
    description="Expert troubleshooter and debugger",
    role="You are Roo, an expert troubleshooter and debugger for the AI Orchestra project",
    capabilities=[
        RooModeCapability.READ_FILES,
        RooModeCapability.WRITE_FILES,
        RooModeCapability.EXECUTE_COMMANDS,
        RooModeCapability.DEBUG_CODE,
    ],
    memory_access_level="write",
    can_transition_to=["code", "reviewer"],
    file_patterns=[".*\\.py$", ".*\\.js$", ".*\\.ts$", ".*\\.log$", ".*\\.json$"],
    model="anthropic/claude-3.7-sonnet",
    temperature=0.2,
)

REVIEWER_MODE = RooMode(
    slug="reviewer",
    name="🕵️ Reviewer",
    description="Meticulous code reviewer and software quality analyst",
    role="You are a meticulous code reviewer and software quality analyst specializing in Python, Docker, Terraform, and AI frameworks.",
    capabilities=[RooModeCapability.READ_FILES, RooModeCapability.REVIEW_CODE],
    memory_access_level="read",
    can_transition_to=["code", "debug"],
    file_patterns=[
        ".*\\.py$",
        ".*\\.js$",
        ".*\\.ts$",
        ".*\\.tf$",
        ".*\\.dockerfile$",
        ".*Dockerfile.*",
    ],
    model="anthropic/claude-3.7-sonnet",
    temperature=0.2,
)

ORCHESTRATOR_MODE = RooMode(
    slug="orchestrator",
    name="🪃 Orchestrator",
    description="Meticulous code reviewer and static analysis expert",
    role="You are Roo, a meticulous code reviewer and static analysis expert for the AI Orchestra project",
    capabilities=[RooModeCapability.READ_FILES, RooModeCapability.ANALYZE_CODE],
    memory_access_level="read",
    can_transition_to=["code", "debug", "reviewer"],
    file_patterns=[".*\\.py$", ".*\\.js$", ".*\\.ts$"],
    model="anthropic/claude-3.7-sonnet",
    temperature=0.2,
)

STRATEGY_MODE = RooMode(
    slug="strategy",
    name="🧠 Strategy",
    description="Senior technical strategist and planner",
    role="You are a senior technical strategist and planner specialized in AI systems architecture and cloud deployment",
    capabilities=[
        RooModeCapability.READ_FILES,
        RooModeCapability.ACCESS_INTERNET,
        RooModeCapability.DESIGN_ARCHITECTURE,
    ],
    memory_access_level="read",
    can_transition_to=["architect", "code"],
    file_patterns=[".*\\.md$", ".*\\.tf$", ".*\\.hcl$", ".*\\.yaml$", ".*\\.yml$"],
    model="anthropic/claude-3.7-sonnet",
    temperature=0.7,
)

CREATIVE_MODE = RooMode(
    slug="creative",
    name="🎨 Creative",
    description="Technical writer and creative communicator",
    role="You are a technical writer and creative communicator",
    capabilities=[
        RooModeCapability.READ_FILES,
        RooModeCapability.WRITE_FILES,
        RooModeCapability.ACCESS_INTERNET,
    ],
    memory_access_level="read",
    can_transition_to=["code", "architect"],
    file_patterns=[".*\\.md$", ".*\\.txt$", ".*\\.html$", ".*\\.css$"],
    model="anthropic/claude-3.7-sonnet",
    temperature=0.9,
)

ASK_MODE = RooMode(
    slug="ask",
    name="❓ Ask",
    description="Research assistant with access to documentation and the internet",
    role="You are a research assistant with access to documentation and the internet",
    capabilities=[RooModeCapability.READ_FILES, RooModeCapability.ACCESS_INTERNET],
    memory_access_level="read",
    can_transition_to=["code", "creative"],
    file_patterns=[".*\\.md$", ".*\\.txt$", ".*\\.pdf$"],
    model="anthropic/claude-3.7-sonnet",
    temperature=0.7,
)

# Mode registry
MODES: Dict[str, RooMode] = {
    "code": CODE_MODE,
    "architect": ARCHITECT_MODE,
    "debug": DEBUG_MODE,
    "reviewer": REVIEWER_MODE,
    "orchestrator": ORCHESTRATOR_MODE,
    "strategy": STRATEGY_MODE,
    "creative": CREATIVE_MODE,
    "ask": ASK_MODE,
}


def get_mode(slug: str) -> Optional[RooMode]:
    """Get a mode by its slug."""
    return MODES.get(slug)


def get_available_transitions(current_mode_slug: str) -> List[RooMode]:
    """Get all modes that the current mode can transition to."""
    current_mode = get_mode(current_mode_slug)
    if not current_mode:
        return []

    return [MODES[slug] for slug in current_mode.can_transition_to if slug in MODES]


def get_modes_with_capability(capability: RooModeCapability) -> List[RooMode]:
    """Get all modes that have a specific capability."""
    return [mode for mode in MODES.values() if capability in mode.capabilities]


def get_mode_transition_graph() -> Dict[str, Set[str]]:
    """Get a graph representation of mode transitions."""
    graph = {}
    for slug, mode in MODES.items():
        graph[slug] = set(mode.can_transition_to)
    return graph
