"""
Rule configurations for Roo.

This module provides a rule engine for defining and enforcing constraints
on Roo operations, capturing developer intent and ensuring consistent
behavior across different modes.
"""

import re
import logging
from enum import Enum
from typing import Dict, Any, List, Optional, Union, Pattern, Callable
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class RuleType(str, Enum):
    """Types of rules that can be applied to Roo operations."""
    FILE_ACCESS = "file_access"
    CODE_STYLE = "code_style"
    DEPENDENCY = "dependency"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"
    MEMORY_ACCESS = "memory_access"
    MODE_TRANSITION = "mode_transition"


class RuleIntent(str, Enum):
    """Developer intents that rules can capture."""
    ENFORCE_STYLE = "enforce_style"
    PREVENT_BUGS = "prevent_bugs"
    ENSURE_SECURITY = "ensure_security"
    OPTIMIZE_PERFORMANCE = "optimize_performance"
    MAINTAIN_ARCHITECTURE = "maintain_architecture"
    ENFORCE_CONVENTIONS = "enforce_conventions"
    PROTECT_MEMORY = "protect_memory"
    GUIDE_WORKFLOW = "guide_workflow"


class RuleSeverity(str, Enum):
    """Severity levels for rule violations."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class RuleCondition(BaseModel):
    """A condition that must be met for a rule to apply."""
    type: str = Field(..., description="Type of value to check")
    pattern: Union[str, Pattern] = Field(..., description="Pattern to match against")
    negated: bool = Field(default=False, description="Whether to negate the match")
    
    @validator("pattern", pre=True)
    def compile_pattern(cls, v):
        """Compile string patterns into regex patterns if they look like regex."""
        if isinstance(v, str) and v.startswith("^") or v.endswith("$") or "*" in v or "+" in v or "?" in v:
            try:
                return re.compile(v)
            except re.error:
                # If it's not a valid regex, treat it as a literal string
                return v
        return v
    
    def matches(self, value: str) -> bool:
        """
        Check if the condition matches a value.
        
        Args:
            value: The value to check against the pattern
            
        Returns:
            True if the condition matches, False otherwise
        """
        if value is None:
            return False
            
        if isinstance(self.pattern, Pattern):
            result = bool(self.pattern.search(str(value)))
        else:
            result = self.pattern == value
            
        return not result if self.negated else result


class Rule(BaseModel):
    """
    A rule that captures developer intent and enforces constraints
    on Roo operations.
    """
    id: str = Field(..., description="Unique identifier for the rule")
    name: str = Field(..., description="Display name for the rule")
    description: str = Field(..., description="Detailed description of the rule's purpose")
    type: RuleType = Field(..., description="Type of rule")
    intent: RuleIntent = Field(..., description="Developer intent captured by the rule")
    conditions: List[RuleCondition] = Field(..., description="Conditions that must be met for the rule to apply")
    action: str = Field(..., description="Action to take when the rule matches")
    enabled: bool = Field(default=True, description="Whether the rule is enabled")
    severity: RuleSeverity = Field(default=RuleSeverity.WARNING, description="Severity of rule violations")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the rule")
    
    def matches(self, context: Dict[str, Any]) -> bool:
        """
        Check if the rule matches a context.
        
        Args:
            context: Dictionary of values to check against the rule conditions
            
        Returns:
            True if all conditions match, False otherwise
        """
        if not self.enabled:
            return False
            
        for condition in self.conditions:
            value = context.get(condition.type)
            if not condition.matches(value):
                return False
                
        return True


class RuleEngine:
    """
    Engine for evaluating rules against operations and
    capturing developer intent.
    
    This class provides a centralized mechanism for registering and evaluating
    rules against operations, ensuring consistent behavior across different
    modes and operations.
    """
    
    def __init__(self):
        """Initialize the rule engine."""
        self.rules: Dict[str, Rule] = {}
    
    def register_rule(self, rule: Rule) -> None:
        """
        Register a rule with the engine.
        
        Args:
            rule: The rule to register
        """
        self.rules[rule.id] = rule
        logger.debug(f"Registered rule: {rule.id}")
    
    def register_rules(self, rules: List[Rule]) -> None:
        """
        Register multiple rules with the engine.
        
        Args:
            rules: The rules to register
        """
        for rule in rules:
            self.register_rule(rule)
    
    def evaluate(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluate all rules against a context and return
        matching rules with their actions.
        
        Args:
            context: Dictionary of values to check against rule conditions
            
        Returns:
            List of dictionaries containing rule information and actions
        """
        results = []
        
        for rule_id, rule in self.rules.items():
            if rule.matches(context):
                results.append({
                    "rule_id": rule_id,
                    "name": rule.name,
                    "description": rule.description,
                    "action": rule.action,
                    "severity": rule.severity,
                    "intent": rule.intent,
                    "metadata": rule.metadata
                })
                
        return results
    
    def get_rules_by_intent(self, intent: RuleIntent) -> List[Rule]:
        """
        Get all rules with a specific intent.
        
        Args:
            intent: The intent to filter by
            
        Returns:
            List of rules with the specified intent
        """
        return [rule for rule in self.rules.values() 
                if rule.intent == intent and rule.enabled]
    
    def get_rules_by_type(self, rule_type: RuleType) -> List[Rule]:
        """
        Get all rules of a specific type.
        
        Args:
            rule_type: The type to filter by
            
        Returns:
            List of rules of the specified type
        """
        return [rule for rule in self.rules.values() 
                if rule.type == rule_type and rule.enabled]


# Example rule definitions
FILE_PATTERN_RULES = [
    Rule(
        id="python_file_naming",
        name="Python File Naming Convention",
        description="Python files should use snake_case naming",
        type=RuleType.FILE_ACCESS,
        intent=RuleIntent.ENFORCE_CONVENTIONS,
        conditions=[
            RuleCondition(
                type="file_path",
                pattern=r".*\.py$"
            ),
            RuleCondition(
                type="file_name",
                pattern=r"^[a-z][a-z0-9_]*\.py$",
                negated=True
            )
        ],
        action="rename_file",
        severity=RuleSeverity.WARNING
    ),
    Rule(
        id="test_file_location",
        name="Test File Location",
        description="Test files should be in the tests directory",
        type=RuleType.FILE_ACCESS,
        intent=RuleIntent.MAINTAIN_ARCHITECTURE,
        conditions=[
            RuleCondition(
                type="file_path",
                pattern=r".*test_.*\.py$"
            ),
            RuleCondition(
                type="file_path",
                pattern=r"^tests/",
                negated=True
            )
        ],
        action="move_file",
        severity=RuleSeverity.WARNING,
        metadata={
            "target_directory": "tests/"
        }
    )
]

CODE_STYLE_RULES = [
    Rule(
        id="python_docstring_required",
        name="Python Docstring Required",
        description="All Python functions and classes should have docstrings",
        type=RuleType.CODE_STYLE,
        intent=RuleIntent.ENFORCE_STYLE,
        conditions=[
            RuleCondition(
                type="file_path",
                pattern=r".*\.py$"
            ),
            RuleCondition(
                type="code_content",
                pattern=r"(def|class)\s+\w+[^#\n]*:[^\"\']*$"
            )
        ],
        action="add_docstring",
        severity=RuleSeverity.WARNING
    ),
    Rule(
        id="python_type_hints_required",
        name="Python Type Hints Required",
        description="All Python functions should have type hints",
        type=RuleType.CODE_STYLE,
        intent=RuleIntent.PREVENT_BUGS,
        conditions=[
            RuleCondition(
                type="file_path",
                pattern=r".*\.py$"
            ),
            RuleCondition(
                type="code_content",
                pattern=r"def\s+\w+\s*\([^:]*\)\s*:[^\"\']*$"
            )
        ],
        action="add_type_hints",
        severity=RuleSeverity.WARNING
    )
]

SECURITY_RULES = [
    Rule(
        id="no_hardcoded_secrets",
        name="No Hardcoded Secrets",
        description="Secrets should not be hardcoded in source files",
        type=RuleType.SECURITY,
        intent=RuleIntent.ENSURE_SECURITY,
        conditions=[
            RuleCondition(
                type="code_content",
                pattern=r"(password|secret|key|token|credential)\s*=\s*['\"][^'\"]+['\"]"
            )
        ],
        action="use_secret_manager",
        severity=RuleSeverity.ERROR
    ),
    Rule(
        id="use_parameterized_queries",
        name="Use Parameterized Queries",
        description="SQL queries should use parameterized statements to prevent SQL injection",
        type=RuleType.SECURITY,
        intent=RuleIntent.ENSURE_SECURITY,
        conditions=[
            RuleCondition(
                type="code_content",
                pattern=r"execute\s*\(\s*f['\"].*\{.*\}.*['\"]"
            )
        ],
        action="use_parameterized_query",
        severity=RuleSeverity.ERROR
    )
]

MEMORY_ACCESS_RULES = [
    Rule(
        id="read_only_memory_access",
        name="Read-Only Memory Access",
        description="Some modes should only have read access to memory",
        type=RuleType.MEMORY_ACCESS,
        intent=RuleIntent.PROTECT_MEMORY,
        conditions=[
            RuleCondition(
                type="mode_slug",
                pattern=r"^(reviewer|architect|strategy)$"
            ),
            RuleCondition(
                type="memory_operation",
                pattern="write"
            )
        ],
        action="deny_access",
        severity=RuleSeverity.ERROR
    ),
    Rule(
        id="memory_access_logging",
        name="Memory Access Logging",
        description="All memory access should be logged",
        type=RuleType.MEMORY_ACCESS,
        intent=RuleIntent.ENSURE_SECURITY,
        conditions=[
            RuleCondition(
                type="memory_operation",
                pattern=r"^(read|write|delete)$"
            )
        ],
        action="log_access",
        severity=RuleSeverity.INFO
    )
]

MODE_TRANSITION_RULES = [
    Rule(
        id="valid_mode_transition",
        name="Valid Mode Transition",
        description="Mode transitions should follow the defined transition graph",
        type=RuleType.MODE_TRANSITION,
        intent=RuleIntent.GUIDE_WORKFLOW,
        conditions=[
            RuleCondition(
                type="transition_valid",
                pattern="false"
            )
        ],
        action="deny_transition",
        severity=RuleSeverity.ERROR
    ),
    Rule(
        id="preserve_context_on_transition",
        name="Preserve Context on Transition",
        description="Context should be preserved during mode transitions",
        type=RuleType.MODE_TRANSITION,
        intent=RuleIntent.GUIDE_WORKFLOW,
        conditions=[
            RuleCondition(
                type="has_context",
                pattern="false"
            )
        ],
        action="add_context",
        severity=RuleSeverity.WARNING
    )
]

# Combine all rules
DEFAULT_RULES = (
    FILE_PATTERN_RULES +
    CODE_STYLE_RULES +
    SECURITY_RULES +
    MEMORY_ACCESS_RULES +
    MODE_TRANSITION_RULES
)


def create_rule_engine() -> RuleEngine:
    """
    Create a rule engine with the default rules.
    
    Returns:
        A rule engine initialized with the default rules
    """
    engine = RuleEngine()
    engine.register_rules(DEFAULT_RULES)
    return engine