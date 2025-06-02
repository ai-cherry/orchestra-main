"""
Event bus implementation for decoupled communication.

This module provides an event-driven architecture for loose coupling
between components.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

class EventPriority(Enum):
    """Event priority levels."""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

@dataclass
class Event:
    """Base event class."""

    name: str
    data: Dict[str, Any]
    timestamp: datetime = None
    priority: EventPriority = EventPriority.NORMAL
    source: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class EventHandler:
    """Wrapper for event handlers with metadata."""

    def __init__(
        self,
        handler: Callable,
        event_filter: Optional[Callable[[Event], bool]] = None,
        priority: EventPriority = EventPriority.NORMAL,
        max_retries: int = 0,
    ):
        self.handler = handler
        self.event_filter = event_filter
        self.priority = priority
        self.max_retries = max_retries
        self.is_async = asyncio.iscoroutinefunction(handler)

    async def handle(self, event: Event) -> Any:
        """Handle an event with retry logic."""
        if self.event_filter and not self.event_filter(event):
            return None

        retries = 0
        last_error = None

        while retries <= self.max_retries:
            try:
                if self.is_async:
                    return await self.handler(event)
                else:
                    return self.handler(event)
            except Exception as e:
                last_error = e
                retries += 1
                if retries <= self.max_retries:
                    await asyncio.sleep(0.1 * retries)  # Exponential backoff
                    logger.warning(f"Retry {retries}/{self.max_retries} for handler {self.handler.__name__}")

        logger.error(f"Handler {self.handler.__name__} failed after {retries} retries: {last_error}")
        raise last_error

class EventBus:
    """
    Central event bus for publish-subscribe communication.

    Features:
    - Async and sync handler support
    - Event filtering
    - Priority-based execution
    - Wildcard subscriptions
    - Event history
    - Statistics tracking
    """

    def __init__(self, history_size: int = 1000):
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._wildcard_handlers: List[EventHandler] = []
        self._event_history: List[Event] = []
        self._history_size = history_size
        self._stats: Dict[str, int] = {
            "events_published": 0,
            "events_handled": 0,
            "errors": 0,
        }
        self._lock = asyncio.Lock()

    def subscribe(
        self,
        event_name: str,
        handler: Callable,
        event_filter: Optional[Callable[[Event], bool]] = None,
        priority: EventPriority = EventPriority.NORMAL,
        max_retries: int = 0,
    ) -> None:
        """
        Subscribe to an event.

        Args:
            event_name: Name of the event or "*" for all events
            handler: Function to handle the event
            event_filter: Optional filter function
            priority: Handler priority
            max_retries: Maximum retry attempts on failure
        """
        event_handler = EventHandler(handler, event_filter, priority, max_retries)

        if event_name == "*":
            self._wildcard_handlers.append(event_handler)
        else:
            if event_name not in self._handlers:
                self._handlers[event_name] = []
            self._handlers[event_name].append(event_handler)

        # Sort by priority
        if event_name == "*":
            self._wildcard_handlers.sort(key=lambda h: h.priority.value, reverse=True)
        else:
            self._handlers[event_name].sort(key=lambda h: h.priority.value, reverse=True)

        logger.debug(f"Subscribed {handler.__name__} to {event_name}")

    def unsubscribe(self, event_name: str, handler: Callable) -> bool:
        """
        Unsubscribe from an event.

        Args:
            event_name: Name of the event
            handler: Handler function to remove

        Returns:
            True if handler was removed, False otherwise
        """
        removed = False

        if event_name == "*":
            self._wildcard_handlers = [h for h in self._wildcard_handlers if h.handler != handler]
            removed = True
        elif event_name in self._handlers:
            original_count = len(self._handlers[event_name])
            self._handlers[event_name] = [h for h in self._handlers[event_name] if h.handler != handler]
            removed = len(self._handlers[event_name]) < original_count

            # Clean up empty lists
            if not self._handlers[event_name]:
                del self._handlers[event_name]

        if removed:
            logger.debug(f"Unsubscribed {handler.__name__} from {event_name}")

        return removed

    async def publish(
        self,
        event_name: str,
        data: Dict[str, Any] = None,
        priority: EventPriority = EventPriority.NORMAL,
        source: Optional[str] = None,
    ) -> int:
        """
        Publish an event.

        Args:
            event_name: Name of the event
            data: Event data
            priority: Event priority
            source: Source identifier

        Returns:
            Number of handlers that processed the event
        """
        if data is None:
            data = {}

        event = Event(name=event_name, data=data, priority=priority, source=source)

        # Add to history
        async with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._history_size:
                self._event_history.pop(0)
            self._stats["events_published"] += 1

        # Get all applicable handlers
        handlers = []

        # Specific handlers
        if event_name in self._handlers:
            handlers.extend(self._handlers[event_name])

        # Wildcard handlers
        handlers.extend(self._wildcard_handlers)

        # Sort by priority
        handlers.sort(key=lambda h: h.priority.value, reverse=True)

        # Execute handlers
        handled_count = 0
        tasks = []

        for handler in handlers:
            try:
                task = asyncio.create_task(handler.handle(event))
                tasks.append(task)
                handled_count += 1
            except Exception as e:
                logger.error(f"Error creating task for handler: {e}")
                self._stats["errors"] += 1

        # Wait for all handlers to complete
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Log any errors
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Handler error: {result}")
                    self._stats["errors"] += 1
                else:
                    self._stats["events_handled"] += 1

        logger.debug(f"Published {event_name} to {handled_count} handlers")
        return handled_count

    def publish_sync(
        self,
        event_name: str,
        data: Dict[str, Any] = None,
        priority: EventPriority = EventPriority.NORMAL,
        source: Optional[str] = None,
    ) -> int:
        """Synchronous version of publish for non-async contexts."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.publish(event_name, data, priority, source))
        finally:
            loop.close()

    def get_handlers(self, event_name: str) -> List[Callable]:
        """Get all handlers for an event."""
        handlers = []

        if event_name in self._handlers:
            handlers.extend([h.handler for h in self._handlers[event_name]])

        handlers.extend([h.handler for h in self._wildcard_handlers])

        return handlers

    def get_event_history(self, event_name: Optional[str] = None, limit: int = 100) -> List[Event]:
        """Get event history, optionally filtered by event name."""
        history = self._event_history

        if event_name:
            history = [e for e in history if e.name == event_name]

        return history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        return {
            **self._stats,
            "total_handlers": sum(len(h) for h in self._handlers.values()) + len(self._wildcard_handlers),
            "event_types": list(self._handlers.keys()),
            "history_size": len(self._event_history),
        }

    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()

    def reset_stats(self) -> None:
        """Reset statistics."""
        self._stats = {
            "events_published": 0,
            "events_handled": 0,
            "errors": 0,
        }

# Global event bus instance
_event_bus: Optional[EventBus] = None

def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _event_bus

    if _event_bus is None:
        _event_bus = EventBus()

    return _event_bus
