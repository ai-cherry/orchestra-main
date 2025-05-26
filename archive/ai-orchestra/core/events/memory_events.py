"""
Memory Events module for the AI Orchestra platform.

This module defines event classes related to memory operations
that can be used for monitoring, logging, and triggering actions.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class MemoryEvent:
    """Base class for all memory-related events."""

    timestamp: datetime = datetime.now()
    event_type: str = "memory_event"
    source: str = "memory_system"


@dataclass
class MemoryItemCreatedEvent(MemoryEvent):
    """Event emitted when a new memory item is created."""

    item_id: str
    content_preview: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        self.event_type = "memory_item_created"


@dataclass
class MemoryItemAccessedEvent(MemoryEvent):
    """Event emitted when a memory item is accessed."""

    item_id: str
    access_type: str = "read"  # read, query, etc.
    context: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        self.event_type = "memory_item_accessed"


@dataclass
class MemoryItemUpdatedEvent(MemoryEvent):
    """Event emitted when a memory item is updated."""

    item_id: str
    updated_fields: List[str]
    context: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        self.event_type = "memory_item_updated"


@dataclass
class MemoryItemDeletedEvent(MemoryEvent):
    """Event emitted when a memory item is deleted."""

    item_id: str
    context: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        self.event_type = "memory_item_deleted"


# Event handler type for memory events
MemoryEventHandler = callable
"""Type definition for memory event handler functions."""


class MemoryEventBus:
    """
    Simple event bus for memory-related events.

    This class allows registration of event handlers and dispatching of
    memory events to the appropriate handlers.
    """

    def __init__(self):
        self._handlers: Dict[str, List[MemoryEventHandler]] = {}

    def register_handler(self, event_type: str, handler: MemoryEventHandler) -> None:
        """
        Register a handler for a specific event type.

        Args:
            event_type: The type of event to handle
            handler: The handler function to call when the event occurs
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def dispatch(self, event: MemoryEvent) -> None:
        """
        Dispatch an event to all registered handlers.

        Args:
            event: The event to dispatch
        """
        event_type = event.event_type
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                handler(event)
