#!/usr/bin/env python3
"""
rule_engine.py - Rules Engine for MCP

This module provides a flexible rules engine for enforcing constraints and validating
content against rules. It supports loading rules from files, dynamic rule activation,
and rule set management.
"""

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Pattern, Set, Union

import yaml

from ..utils.structured_logging import get_logger, with_correlation_id

logger = get_logger(__name__)


class RuleSeverity(str, Enum):
    """Severity levels for rules."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RuleCategory(str, Enum):
    """Categories of rules."""

    STYLE = "style"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"
    API_USAGE = "api_usage"
    DOCUMENTATION = "documentation"
    TESTING = "testing"


@dataclass
class RuleViolation:
    """Represents a rule violation."""

    rule_id: str
    message: str
    severity: RuleSeverity
    category: RuleCategory
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "rule_id": self.rule_id,
            "message": self.message,
            "severity": self.severity,
            "category": self.category,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuleViolation":
        """Create from dictionary."""
        return cls(
            rule_id=data["rule_id"],
            message=data["message"],
            severity=RuleSeverity(data["severity"]),
            category=RuleCategory(data["category"]),
            context=data.get("context", {}),
        )


@dataclass
class Rule:
    """Represents a rule in the rule engine."""

    id: str
    name: str
    description: str
    severity: RuleSeverity
    category: RuleCategory
    pattern: Optional[Union[str, Pattern]] = None
    check_func: Optional[Callable[[Any], List[RuleViolation]]] = None
    enabled: bool = True
    tags: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Post-initialization processing."""
        # Compile pattern if it's a string
        if isinstance(self.pattern, str):
            try:
                self.pattern = re.compile(self.pattern, re.MULTILINE)
            except re.error as e:
                logger.error(f"Invalid regex pattern in rule {self.id}: {e}")
                self.pattern = None

    def check(self, content: Any) -> List[RuleViolation]:
        """Check if the content violates this rule.

        Args:
            content: The content to check

        Returns:
            List of rule violations
        """
        if not self.enabled:
            return []

        violations = []

        # Check using pattern if available
        if self.pattern and isinstance(content, str):
            matches = list(self.pattern.finditer(content))
            for match in matches:
                violations.append(
                    RuleViolation(
                        rule_id=self.id,
                        message=f"Pattern match: {match.group(0)}",
                        severity=self.severity,
                        category=self.category,
                        context={
                            "match": match.group(0),
                            "span": f"{match.start()}-{match.end()}",
                            "line": content.count("\n", 0, match.start()) + 1,
                        },
                    )
                )

        # Check using function if available
        if self.check_func:
            try:
                func_violations = self.check_func(content)
                violations.extend(func_violations)
            except Exception as e:
                logger.error(f"Error in check function for rule {self.id}: {e}")
                # Add a violation for the rule check failure
                violations.append(
                    RuleViolation(
                        rule_id=self.id,
                        message=f"Rule check function failed: {e}",
                        severity=RuleSeverity.ERROR,
                        category=self.category,
                        context={"error": str(e)},
                    )
                )

        return violations

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "severity": self.severity,
            "category": self.category,
            "enabled": self.enabled,
            "tags": self.tags,
        }

        if isinstance(self.pattern, Pattern):
            result["pattern"] = self.pattern.pattern
        elif self.pattern:
            result["pattern"] = self.pattern

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Rule":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            description=data.get("description", ""),
            severity=RuleSeverity(data.get("severity", "warning")),
            category=RuleCategory(data.get("category", "style")),
            pattern=data.get("pattern"),
            enabled=data.get("enabled", True),
            tags=data.get("tags", []),
        )


class RuleEngine:
    """Engine for checking content against rules."""

    def __init__(self):
        """Initialize the rule engine."""
        self.rules: Dict[str, Rule] = {}
        self.rule_sets: Dict[str, Set[str]] = {}
        self.default_rule_set: Optional[str] = None

    @with_correlation_id
    def load_rules_from_file(self, file_path: str) -> bool:
        """Load rules from a YAML or JSON file.

        Args:
            file_path: Path to the rules file

        Returns:
            True if rules were loaded successfully
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"Rule file not found: {file_path}")
                return False

            # Load based on file extension
            if path.suffix.lower() in [".yaml", ".yml"]:
                with open(path, "r") as f:
                    rule_data = yaml.safe_load(f)
            elif path.suffix.lower() == ".json":
                with open(path, "r") as f:
                    rule_data = json.load(f)
            else:
                logger.error(f"Unsupported file format: {path.suffix}")
                return False

            # Process rules
            rules_loaded = 0
            for rule_dict in rule_data.get("rules", []):
                rule_id = rule_dict.get("id")
                if not rule_id:
                    logger.warning("Rule without ID found, skipping")
                    continue

                try:
                    rule = Rule.from_dict(rule_dict)
                    self.add_rule(rule)
                    rules_loaded += 1
                except Exception as e:
                    logger.error(f"Error loading rule {rule_id}: {e}")

            # Load rule sets
            for set_name, rule_ids in rule_data.get("rule_sets", {}).items():
                self.rule_sets[set_name] = set(rule_ids)

            # Set default rule set if specified
            if "default_rule_set" in rule_data:
                self.default_rule_set = rule_data["default_rule_set"]

            logger.info(f"Loaded {rules_loaded} rules from {file_path}")
            return rules_loaded > 0
        except Exception as e:
            logger.error(f"Error loading rules from file: {e}")
            return False

    def add_rule(self, rule: Rule) -> None:
        """Add a rule to the engine.

        Args:
            rule: The rule to add
        """
        self.rules[rule.id] = rule
        logger.debug(f"Added rule: {rule.id}")

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule from the engine.

        Args:
            rule_id: The ID of the rule to remove

        Returns:
            True if the rule was removed
        """
        if rule_id in self.rules:
            del self.rules[rule_id]

            # Remove from rule sets
            for rule_set in self.rule_sets.values():
                rule_set.discard(rule_id)

            logger.debug(f"Removed rule: {rule_id}")
            return True

        return False

    def enable_rule(self, rule_id: str) -> bool:
        """Enable a rule.

        Args:
            rule_id: The ID of the rule to enable

        Returns:
            True if the rule was enabled
        """
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            logger.debug(f"Enabled rule: {rule_id}")
            return True

        return False

    def disable_rule(self, rule_id: str) -> bool:
        """Disable a rule.

        Args:
            rule_id: The ID of the rule to disable

        Returns:
            True if the rule was disabled
        """
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            logger.debug(f"Disabled rule: {rule_id}")
            return True

        return False

    def create_rule_set(self, name: str, rule_ids: List[str]) -> bool:
        """Create a rule set.

        Args:
            name: The name of the rule set
            rule_ids: The IDs of the rules to include

        Returns:
            True if the rule set was created
        """
        # Validate rule IDs
        invalid_ids = [rule_id for rule_id in rule_ids if rule_id not in self.rules]
        if invalid_ids:
            logger.error(f"Invalid rule IDs in rule set {name}: {invalid_ids}")
            return False

        self.rule_sets[name] = set(rule_ids)
        logger.debug(f"Created rule set: {name} with {len(rule_ids)} rules")
        return True

    def add_to_rule_set(self, set_name: str, rule_id: str) -> bool:
        """Add a rule to a rule set.

        Args:
            set_name: The name of the rule set
            rule_id: The ID of the rule to add

        Returns:
            True if the rule was added
        """
        if set_name not in self.rule_sets:
            logger.error(f"Rule set not found: {set_name}")
            return False

        if rule_id not in self.rules:
            logger.error(f"Rule not found: {rule_id}")
            return False

        self.rule_sets[set_name].add(rule_id)
        logger.debug(f"Added rule {rule_id} to rule set {set_name}")
        return True

    def remove_from_rule_set(self, set_name: str, rule_id: str) -> bool:
        """Remove a rule from a rule set.

        Args:
            set_name: The name of the rule set
            rule_id: The ID of the rule to remove

        Returns:
            True if the rule was removed
        """
        if set_name not in self.rule_sets:
            logger.error(f"Rule set not found: {set_name}")
            return False

        if rule_id in self.rule_sets[set_name]:
            self.rule_sets[set_name].remove(rule_id)
            logger.debug(f"Removed rule {rule_id} from rule set {set_name}")
            return True

        return False

    def set_default_rule_set(self, set_name: Optional[str]) -> bool:
        """Set the default rule set.

        Args:
            set_name: The name of the rule set, or None to clear

        Returns:
            True if the default rule set was set
        """
        if set_name is not None and set_name not in self.rule_sets:
            logger.error(f"Rule set not found: {set_name}")
            return False

        self.default_rule_set = set_name
        logger.debug(f"Set default rule set: {set_name}")
        return True

    @with_correlation_id
    def check_content(
        self,
        content: Any,
        rule_set: Optional[str] = None,
        categories: Optional[List[RuleCategory]] = None,
        severities: Optional[List[RuleSeverity]] = None,
        tags: Optional[List[str]] = None,
    ) -> List[RuleViolation]:
        """Check content against rules.

        Args:
            content: The content to check
            rule_set: The rule set to use, or None to use the default
            categories: Optional list of categories to filter rules
            severities: Optional list of severities to filter rules
            tags: Optional list of tags to filter rules

        Returns:
            List of rule violations
        """
        violations = []

        # Determine which rule set to use
        active_rule_set = rule_set or self.default_rule_set

        # Determine which rules to check
        if active_rule_set and active_rule_set in self.rule_sets:
            rule_ids = self.rule_sets[active_rule_set]
            rules_to_check = [
                rule for rule_id, rule in self.rules.items() if rule_id in rule_ids
            ]
        else:
            rules_to_check = list(self.rules.values())

        # Apply filters
        if categories:
            rules_to_check = [
                rule for rule in rules_to_check if rule.category in categories
            ]

        if severities:
            rules_to_check = [
                rule for rule in rules_to_check if rule.severity in severities
            ]

        if tags:
            rules_to_check = [
                rule for rule in rules_to_check if any(tag in rule.tags for tag in tags)
            ]

        # Check each rule
        for rule in rules_to_check:
            if not rule.enabled:
                continue

            rule_violations = rule.check(content)
            violations.extend(rule_violations)

        logger.debug(f"Found {len(violations)} violations in content")
        return violations

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Get a rule by ID.

        Args:
            rule_id: The ID of the rule

        Returns:
            The rule, or None if not found
        """
        return self.rules.get(rule_id)

    def get_rules_by_category(self, category: RuleCategory) -> List[Rule]:
        """Get rules by category.

        Args:
            category: The category to filter by

        Returns:
            List of rules in the category
        """
        return [rule for rule in self.rules.values() if rule.category == category]

    def get_rules_by_severity(self, severity: RuleSeverity) -> List[Rule]:
        """Get rules by severity.

        Args:
            severity: The severity to filter by

        Returns:
            List of rules with the severity
        """
        return [rule for rule in self.rules.values() if rule.severity == severity]

    def get_rules_by_tag(self, tag: str) -> List[Rule]:
        """Get rules by tag.

        Args:
            tag: The tag to filter by

        Returns:
            List of rules with the tag
        """
        return [rule for rule in self.rules.values() if tag in rule.tags]

    def get_rule_set(self, set_name: str) -> Optional[Set[str]]:
        """Get a rule set by name.

        Args:
            set_name: The name of the rule set

        Returns:
            The rule set, or None if not found
        """
        return self.rule_sets.get(set_name)

    def get_rule_sets(self) -> Dict[str, Set[str]]:
        """Get all rule sets.

        Returns:
            Dictionary of rule sets
        """
        return self.rule_sets

    def save_rules_to_file(self, file_path: str) -> bool:
        """Save rules to a YAML or JSON file.

        Args:
            file_path: Path to save the rules file

        Returns:
            True if rules were saved successfully
        """
        try:
            # Convert rules to serializable format
            rules_data = []
            for rule in self.rules.values():
                rules_data.append(rule.to_dict())

            # Prepare data for serialization
            data = {
                "rules": rules_data,
                "rule_sets": {
                    name: list(rule_ids) for name, rule_ids in self.rule_sets.items()
                },
            }

            if self.default_rule_set:
                data["default_rule_set"] = self.default_rule_set

            # Save based on file extension
            path = Path(file_path)
            if path.suffix.lower() in [".yaml", ".yml"]:
                with open(path, "w") as f:
                    yaml.dump(data, f, default_flow_style=False)
            elif path.suffix.lower() == ".json":
                with open(path, "w") as f:
                    json.dump(data, f, indent=2)
            else:
                logger.error(f"Unsupported file format: {path.suffix}")
                return False

            logger.info(f"Saved {len(rules_data)} rules to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving rules to file: {e}")
            return False


# Singleton instance for global use
_default_instance: Optional[RuleEngine] = None


def get_rule_engine() -> RuleEngine:
    """Get the default RuleEngine instance."""
    global _default_instance
    if _default_instance is None:
        _default_instance = RuleEngine()
    return _default_instance


def check_content(
    content: Any,
    rule_set: Optional[str] = None,
    categories: Optional[List[RuleCategory]] = None,
    severities: Optional[List[RuleSeverity]] = None,
    tags: Optional[List[str]] = None,
) -> List[RuleViolation]:
    """Convenience function to check content using the default rule engine."""
    return get_rule_engine().check_content(
        content, rule_set, categories, severities, tags
    )


def load_rules_from_file(file_path: str) -> bool:
    """Convenience function to load rules from a file using the default rule engine."""
    return get_rule_engine().load_rules_from_file(file_path)
