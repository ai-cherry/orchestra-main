#!/usr/bin/env python3
"""
memory_key.py - Hierarchical Memory Key Management

This module provides utilities for creating and managing hierarchical memory keys
that support scoping, namespacing, and user-specific memory isolation.
"""

import re
import uuid
from enum import Enum
from typing import Optional, Union

from .structured_logging import get_logger

logger = get_logger(__name__)

class MemoryKeyScope(str, Enum):
    """Predefined scopes for memory keys."""

    GLOBAL = "global"
    PROJECT = "project"
    MODULE = "module"
    USER = "user"
    SESSION = "session"
    AGENT = "agent"
    TOOL = "tool"

class MemoryKey:
    """Hierarchical memory key structure."""

    SEPARATOR = "::"
    USER_PREFIX = "user-"
    SESSION_PREFIX = "session-"

    def __init__(
        self,
        namespace: str,
        key: str,
        scope: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ):
        """Initialize a hierarchical memory key.

        Args:
            namespace: The namespace for the key (e.g., "RooMCP", "Project123")
            key: The base key name
            scope: Optional scope within the namespace (e.g., "AuthModule", "DataLayer")
            user_id: Optional user ID for user-specific memory
            session_id: Optional session ID for session-specific memory
            agent_id: Optional agent ID for agent-specific memory
        """
        self.namespace = namespace
        self.key = key
        self.scope = scope
        self.user_id = user_id
        self.session_id = session_id
        self.agent_id = agent_id

    def __str__(self) -> str:
        """Convert to string representation."""
        parts = [self.namespace]

        if self.scope:
            parts.append(self.scope)

        if self.user_id:
            parts.append(f"{self.USER_PREFIX}{self.user_id}")

        if self.session_id:
            parts.append(f"{self.SESSION_PREFIX}{self.session_id}")

        if self.agent_id:
            parts.append(f"agent-{self.agent_id}")

        parts.append(self.key)

        return self.SEPARATOR.join(parts)

    def __repr__(self) -> str:
        """Representation for debugging."""
        return (
            f"MemoryKey(namespace='{self.namespace}', key='{self.key}', "
            f"scope='{self.scope}', user_id='{self.user_id}', "
            f"session_id='{self.session_id}', agent_id='{self.agent_id}')"
        )

    def __eq__(self, other: object) -> bool:
        """Check equality with another memory key."""
        if not isinstance(other, MemoryKey):
            return False

        return str(self) == str(other)

    def __hash__(self) -> int:
        """Hash for use in dictionaries and sets."""
        return hash(str(self))

    @classmethod
    def parse(cls, key_str: str) -> Optional["MemoryKey"]:
        """Parse a string representation into a MemoryKey.

        Args:
            key_str: The string representation of the memory key

        Returns:
            A MemoryKey object, or None if parsing fails
        """
        if not key_str or cls.SEPARATOR not in key_str:
            return None

        parts = key_str.split(cls.SEPARATOR)

        if len(parts) < 2:
            return None

        namespace = parts[0]
        key = parts[-1]

        # Extract user_id if present
        user_id = None
        user_pattern = re.compile(f"{cls.USER_PREFIX}([a-zA-Z0-9_-]+)")

        # Extract session_id if present
        session_id = None
        session_pattern = re.compile(f"{cls.SESSION_PREFIX}([a-zA-Z0-9_-]+)")

        # Extract agent_id if present
        agent_id = None
        agent_pattern = re.compile(r"agent-([a-zA-Z0-9_-]+)")

        # Middle parts (excluding namespace and key)
        middle_parts = parts[1:-1]
        remaining_parts = []

        for part in middle_parts:
            user_match = user_pattern.match(part)
            if user_match:
                user_id = user_match.group(1)
                continue

            session_match = session_pattern.match(part)
            if session_match:
                session_id = session_match.group(1)
                continue

            agent_match = agent_pattern.match(part)
            if agent_match:
                agent_id = agent_match.group(1)
                continue

            remaining_parts.append(part)

        # Any remaining middle parts form the scope
        scope = cls.SEPARATOR.join(remaining_parts) if remaining_parts else None

        return cls(namespace, key, scope, user_id, session_id, agent_id)

    @classmethod
    def create(
        cls,
        namespace: str,
        key: str,
        scope: Optional[Union[str, MemoryKeyScope]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> "MemoryKey":
        """Create a memory key with validation and normalization.

        Args:
            namespace: The namespace for the key
            key: The base key name
            scope: Optional scope or predefined MemoryKeyScope
            user_id: Optional user ID
            session_id: Optional session ID
            agent_id: Optional agent ID

        Returns:
            A validated MemoryKey object

        Raises:
            ValueError: If validation fails
        """
        # Validate namespace
        if not namespace:
            raise ValueError("Namespace cannot be empty")

        # Validate key
        if not key:
            raise ValueError("Key cannot be empty")

        # Normalize scope if it's a MemoryKeyScope enum
        scope_str = None
        if scope:
            if isinstance(scope, MemoryKeyScope):
                scope_str = scope.value
            else:
                scope_str = str(scope)

        # Create the memory key
        return cls(namespace, key, scope_str, user_id, session_id, agent_id)

    def with_user(self, user_id: str) -> "MemoryKey":
        """Create a new memory key with the specified user ID.

        Args:
            user_id: The user ID to set

        Returns:
            A new MemoryKey with the user ID set
        """
        return MemoryKey(
            self.namespace,
            self.key,
            self.scope,
            user_id,
            self.session_id,
            self.agent_id,
        )

    def with_session(self, session_id: str) -> "MemoryKey":
        """Create a new memory key with the specified session ID.

        Args:
            session_id: The session ID to set

        Returns:
            A new MemoryKey with the session ID set
        """
        return MemoryKey(
            self.namespace,
            self.key,
            self.scope,
            self.user_id,
            session_id,
            self.agent_id,
        )

    def with_agent(self, agent_id: str) -> "MemoryKey":
        """Create a new memory key with the specified agent ID.

        Args:
            agent_id: The agent ID to set

        Returns:
            A new MemoryKey with the agent ID set
        """
        return MemoryKey(
            self.namespace,
            self.key,
            self.scope,
            self.user_id,
            self.session_id,
            agent_id,
        )

    def with_scope(self, scope: Union[str, MemoryKeyScope]) -> "MemoryKey":
        """Create a new memory key with the specified scope.

        Args:
            scope: The scope to set

        Returns:
            A new MemoryKey with the scope set
        """
        scope_str = scope.value if isinstance(scope, MemoryKeyScope) else str(scope)
        return MemoryKey(
            self.namespace,
            self.key,
            scope_str,
            self.user_id,
            self.session_id,
            self.agent_id,
        )

    def matches_pattern(self, pattern: "MemoryKeyPattern") -> bool:
        """Check if this key matches a pattern.

        Args:
            pattern: The pattern to match against

        Returns:
            True if the key matches the pattern
        """
        # Check namespace
        if pattern.namespace and pattern.namespace != self.namespace:
            return False

        # Check key pattern
        if pattern.key_pattern:
            if isinstance(pattern.key_pattern, re.Pattern):
                if not pattern.key_pattern.match(self.key):
                    return False
            elif pattern.key_pattern != self.key:
                return False

        # Check scope
        if pattern.scope and pattern.scope != self.scope:
            return False

        # Check user_id
        if pattern.user_id and pattern.user_id != self.user_id:
            return False

        # Check session_id
        if pattern.session_id and pattern.session_id != self.session_id:
            return False

        # Check agent_id
        if pattern.agent_id and pattern.agent_id != self.agent_id:
            return False

        return True

    def is_parent_of(self, other: "MemoryKey") -> bool:
        """Check if this key is a parent of another key.

        A key is a parent if it has the same namespace and scope (if any),
        but doesn't have user_id, session_id, or agent_id that the other key has.

        Args:
            other: The other key to check

        Returns:
            True if this key is a parent of the other key
        """
        # Must have same namespace
        if self.namespace != other.namespace:
            return False

        # If this key has a scope, the other key must have the same scope
        if self.scope and self.scope != other.scope:
            return False

        # This key must not have user_id, session_id, or agent_id that the other key has
        if self.user_id and self.user_id != other.user_id:
            return False

        if self.session_id and self.session_id != other.session_id:
            return False

        if self.agent_id and self.agent_id != other.agent_id:
            return False

        # This key must be less specific than the other key
        this_specificity = sum(1 for x in [self.scope, self.user_id, self.session_id, self.agent_id] if x)
        other_specificity = sum(1 for x in [other.scope, other.user_id, other.session_id, other.agent_id] if x)

        return this_specificity < other_specificity

    @staticmethod
    def generate_key(prefix: str = "") -> str:
        """Generate a unique key string.

        Args:
            prefix: Optional prefix for the key

        Returns:
            A unique key string
        """
        unique_id = str(uuid.uuid4())
        if prefix:
            return f"{prefix}-{unique_id}"
        return unique_id

class MemoryKeyPattern:
    """Pattern for matching memory keys."""

    def __init__(
        self,
        namespace: Optional[str] = None,
        key_pattern: Optional[Union[str, re.Pattern]] = None,
        scope: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ):
        """Initialize a memory key pattern.

        Args:
            namespace: The namespace to match
            key_pattern: The key pattern to match (string or regex)
            scope: The scope to match
            user_id: The user ID to match
            session_id: The session ID to match
            agent_id: The agent ID to match
        """
        self.namespace = namespace
        self.key_pattern = key_pattern
        self.scope = scope
        self.user_id = user_id
        self.session_id = session_id
        self.agent_id = agent_id

    def __str__(self) -> str:
        """String representation of the pattern."""
        parts = []

        if self.namespace:
            parts.append(f"namespace='{self.namespace}'")

        if self.key_pattern:
            if isinstance(self.key_pattern, re.Pattern):
                parts.append(f"key_pattern=/{self.key_pattern.pattern}/")
            else:
                parts.append(f"key_pattern='{self.key_pattern}'")

        if self.scope:
            parts.append(f"scope='{self.scope}'")

        if self.user_id:
            parts.append(f"user_id='{self.user_id}'")

        if self.session_id:
            parts.append(f"session_id='{self.session_id}'")

        if self.agent_id:
            parts.append(f"agent_id='{self.agent_id}'")

        return f"MemoryKeyPattern({', '.join(parts)})"

    def matches(self, key: Union[MemoryKey, str]) -> bool:
        """Check if a key matches this pattern.

        Args:
            key: The key to check (MemoryKey or string)

        Returns:
            True if the key matches the pattern
        """
        if isinstance(key, str):
            key_obj = MemoryKey.parse(key)
            if not key_obj:
                return False
        else:
            key_obj = key

        return key_obj.matches_pattern(self)

def create_memory_key(
    namespace: str,
    key: str,
    scope: Optional[Union[str, MemoryKeyScope]] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> MemoryKey:
    """Convenience function to create a memory key.

    Args:
        namespace: The namespace for the key
        key: The base key name
        scope: Optional scope or predefined MemoryKeyScope
        user_id: Optional user ID
        session_id: Optional session ID
        agent_id: Optional agent ID

    Returns:
        A validated MemoryKey object
    """
    return MemoryKey.create(namespace, key, scope, user_id, session_id, agent_id)

def parse_memory_key(key_str: str) -> Optional[MemoryKey]:
    """Convenience function to parse a memory key string.

    Args:
        key_str: The string representation of the memory key

    Returns:
        A MemoryKey object, or None if parsing fails
    """
    return MemoryKey.parse(key_str)

def create_memory_key_pattern(
    namespace: Optional[str] = None,
    key_pattern: Optional[Union[str, re.Pattern]] = None,
    scope: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> MemoryKeyPattern:
    """Convenience function to create a memory key pattern.

    Args:
        namespace: The namespace to match
        key_pattern: The key pattern to match (string or regex)
        scope: The scope to match
        user_id: The user ID to match
        session_id: The session ID to match
        agent_id: The agent ID to match

    Returns:
        A MemoryKeyPattern object
    """
    return MemoryKeyPattern(namespace, key_pattern, scope, user_id, session_id, agent_id)
