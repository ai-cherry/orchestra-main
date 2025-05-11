#!/usr/bin/env python3
"""
Rules package for MCP.

This package provides rule-based validation and constraint enforcement
for the MCP system. It includes a flexible rule engine, predefined rules,
and utilities for rule management.
"""

from .rule_engine import (
    RuleEngine, Rule, RuleViolation, RuleSeverity, RuleCategory,
    get_rule_engine, check_content, load_rules_from_file
)

__all__ = [
    'RuleEngine',
    'Rule',
    'RuleViolation',
    'RuleSeverity',
    'RuleCategory',
    'get_rule_engine',
    'check_content',
    'load_rules_from_file'
]