"""
Unified Event Bus Service for AI Orchestration System.

This module provides a consolidated event bus implementation for decoupling components
through a publish-subscribe pattern. It combines the functionality of the original and
enhanced event bus implementations into a simpler, more maintainable design with
comprehensive async support, error handling, and event prioritization.
"""

import asyncio
import functools
import logging
import traceback
from enum import Enum, auto
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Union,
    Awaitable,
    TypeVar,
    Generic,
    cast,
)

# Configure logging
logger = logging.getLogger(__name__)

# Type definitions for clarity and safety
EventData = Dict[str, Any]
EventHandler = Callable[[EventData], None]
AsyncEventHandler = Callable[[EventData], Awaitable[None]]
HandlerType = Union[EventHandler, AsyncEventHandler]
T = TypeVar("T")


class EventPriority(Enum):
    """
    Priority levels for event handlers.

    Higher priority handlers are executed first.
    """

    HIGH = 100
    NORMAL = 50
    LOW = 10


class HandlerInfo:
    """
    Container for event handler information and statistics.

    This class encapsulates metadata about registered event handlers,
    including priority, execution stats, and error tracking.
    """

    def __init__(
        self, handler: HandlerType, priority: EventPriority = EventPriority.NORMAL
    ):
        """
        Initialize handler information.

        Args:
            handler: The event handler function
            priority: The handler's execution priority
        """
        self.handler = handler
        self.priority = priority
        self.is_async = asyncio.iscoroutinefunction(handler)

        # Statistics tracking
        self.execution_count = 0
        self.error_count = 0
        self.total_execution_time = 0.0

    def update_stats(self, execution_time: float, success: bool) -> None:
        """
        Update handler execution statistics.

        Args:
            execution_time: Time taken to execute the handler in seconds
            success: Whether execution was successful
        """
        self.execution_count += 1
        self.total_execution_time += execution_time

        if not success:
            self.error_count += 1

    @property
    def avg_execution_time_ms(self) -> float:
        """
        Get average execution time in milliseconds.

        Returns:
            Average execution time or 0 if never executed
        """
        if self.execution_count == 0:
            return 0

        return (
            self.total_execution_time / self.execution_count
        ) * 1000  # Convert to ms

    @property
    def error_rate(self) -> float:
        """
        Get error rate as a percentage.

        Returns:
            Error rate percentage or 0 if never executed
        """
        if self.execution_count == 0:
            return 0

        return (self.error_count / self.execution_count) * 100


class EventBus:
    """
    Unified event bus implementation with comprehensive features.

    This class provides a clean, unified implementation of the event bus pattern with:
    - Support for both synchronous and asynchronous handlers
    - Prioritized event processing
    - Robust error handling with isolation
    - Statistics tracking for monitoring and debugging
    - Clean type safety through modern Python typing
    """

    def __init__(self):
        """Initialize the event bus."""
        # Handlers organized by event type and handler ID
        self._handlers: Dict[str, Dict[int, HandlerInfo]] = {}
        self._wildcard_handlers: Dict[int, HandlerInfo] = {}

        # Handler ID tracking for efficient management
        self._handler_ids: Dict[HandlerType, int] = {}
        self._next_handler_id = 1

        logger.debug("EventBus initialized")

    def subscribe(
        self,
        event_type: str,
        handler: HandlerType,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> int:
        """
        Subscribe a handler to a specific event type.

        Args:
            event_type: The type of event to subscribe to, or "*" for all events
            handler: The function to call when the event occurs
            priority: Handler execution priority

        Returns:
            Handler ID that can be used for unsubscribing
        """
        # Generate a unique handler ID
        handler_id = self._next_handler_id
        self._next_handler_id += 1

        # Create handler info
        handler_info = HandlerInfo(handler, priority)

        # Store ID mapping for efficient lookup
        self._handler_ids[handler] = handler_id

        # Register handler
        if event_type == "*":
            self._wildcard_handlers[handler_id] = handler_info
            logger.debug(
                f"Handler subscribed to all events: id={handler_id}, priority={priority.name}"
            )
        else:
            if event_type not in self._handlers:
                self._handlers[event_type] = {}

            self._handlers[event_type][handler_id] = handler_info
            logger.debug(
                f"Handler subscribed to '{event_type}': id={handler_id}, priority={priority.name}"
            )

        return handler_id

    def unsubscribe(self, event_type: str, handler: HandlerType) -> bool:
        """
        Unsubscribe a handler from an event type.

        Args:
            event_type: The type of event to unsubscribe from, or "*" for all events
            handler: The function to unsubscribe

        Returns:
            True if the handler was found and removed, False otherwise
        """
        if handler not in self._handler_ids:
            logger.debug(
                f"Cannot unsubscribe handler for '{event_type}': handler not found"
            )
            return False

        handler_id = self._handler_ids[handler]
        return self.unsubscribe_by_id(event_type, handler_id)

    def unsubscribe_by_id(self, event_type: str, handler_id: int) -> bool:
        """
        Unsubscribe a handler by its ID.

        Args:
            event_type: The type of event to unsubscribe from, or "*" for all events
            handler_id: The handler ID to unsubscribe

        Returns:
            True if the handler was found and removed, False otherwise
        """
        if event_type == "*":
            if handler_id in self._wildcard_handlers:
                handler = self._wildcard_handlers[handler_id].handler
                del self._wildcard_handlers[handler_id]
                if handler in self._handler_ids:
                    del self._handler_ids[handler]
                logger.debug(f"Handler unsubscribed from all events: id={handler_id}")
                return True
        elif event_type in self._handlers:
            if handler_id in self._handlers[event_type]:
                handler = self._handlers[event_type][handler_id].handler
                del self._handlers[event_type][handler_id]
                if handler in self._handler_ids:
                    del self._handler_ids[handler]

                # Clean up empty event type dictionaries
                if not self._handlers[event_type]:
                    del self._handlers[event_type]

                logger.debug(
                    f"Handler unsubscribed from '{event_type}': id={handler_id}"
                )
                return True

        logger.debug(
            f"Cannot unsubscribe handler with id={handler_id} from '{event_type}': not found"
        )
        return False

    def publish(self, event_type: str, event_data: Optional[EventData] = None) -> int:
        """
        Publish an event to synchronous subscribers.

        This method only processes synchronous handlers. For async handlers, use
        publish_async() instead, which handles both sync and async handlers.

        Args:
            event_type: The type of event being published
            event_data: The data associated with the event

        Returns:
            The number of synchronous handlers that were notified
        """
        event_data = event_data or {}

        # Add event type to the data for context
        event_data_with_type = {**event_data, "_event_type": event_type}

        # Get and sort handlers for this event type
        handlers_to_call = self._get_handlers_for_event(event_type, async_mode=False)

        # Call synchronous handlers only
        count = 0
        for handler_info in handlers_to_call:
            if not handler_info.is_async:
                success = self._call_handler_sync(handler_info, event_data_with_type)
                if success:
                    count += 1

        if count > 0:
            logger.debug(
                f"Event '{event_type}' published to {count} synchronous handlers"
            )

        return count

    async def publish_async(
        self, event_type: str, event_data: Optional[EventData] = None
    ) -> int:
        """
        Publish an event to all subscribers, including asynchronous handlers.

        This method executes both synchronous and asynchronous handlers. The synchronous
        handlers are executed first, then async handlers are executed concurrently.

        Args:
            event_type: The type of event being published
            event_data: The data associated with the event

        Returns:
            The total number of handlers that were notified
        """
        event_data = event_data or {}

        # Add event type to the data for context
        event_data_with_type = {**event_data, "_event_type": event_type}

        # Get and sort handlers for this event type
        handlers_to_call = self._get_handlers_for_event(event_type, async_mode=True)

        # Call synchronous handlers first
        sync_count = 0
        async_tasks = []

        for handler_info in handlers_to_call:
            if handler_info.is_async:
                # Create tasks for async handlers
                task = self._call_handler_async(handler_info, event_data_with_type)
                async_tasks.append(task)
            else:
                # Call sync handlers directly
                success = self._call_handler_sync(handler_info, event_data_with_type)
                if success:
                    sync_count += 1

        # Wait for all async tasks to complete
        async_count = 0
        if async_tasks:
            results = await asyncio.gather(*async_tasks, return_exceptions=True)
            async_count = sum(1 for result in results if result is True)

        total_count = sync_count + async_count

        if total_count > 0:
            logger.debug(
                f"Event '{event_type}' published to {total_count} handlers "
                f"({sync_count} sync, {async_count} async)"
            )

        return total_count

    def _get_handlers_for_event(
        self, event_type: str, async_mode: bool
    ) -> List[HandlerInfo]:
        """
        Get all handlers that should be called for an event, sorted by priority.

        Args:
            event_type: The type of event
            async_mode: Whether async handlers should be included

        Returns:
            List of handler info objects sorted by priority
        """
        handlers = []

        # Get specific handlers for this event type
        if event_type in self._handlers:
            handlers.extend(self._handlers[event_type].values())

        # Add wildcard handlers
        handlers.extend(self._wildcard_handlers.values())

        # Filter by async mode if needed
        if not async_mode:
            handlers = [h for h in handlers if not h.is_async]

        # Sort by priority (higher values first)
        handlers.sort(key=lambda h: h.priority.value, reverse=True)

        return handlers

    def _call_handler_sync(
        self, handler_info: HandlerInfo, event_data: EventData
    ) -> bool:
        """
        Call a synchronous handler with error handling and statistics tracking.

        Args:
            handler_info: Information about the handler
            event_data: Event data to pass to the handler

        Returns:
            True if the handler completed successfully, False otherwise
        """
        import time

        start_time = time.time()
        success = False

        try:
            handler_info.handler(event_data)
            success = True
        except Exception as e:
            error_stack = traceback.format_exc()
            logger.error(f"Error in event handler: {e}\n{error_stack}")
        finally:
            execution_time = time.time() - start_time
            handler_info.update_stats(execution_time, success)

        return success

    async def _call_handler_async(
        self, handler_info: HandlerInfo, event_data: EventData
    ) -> bool:
        """
        Call an asynchronous handler with error handling and statistics tracking.

        Args:
            handler_info: Information about the handler
            event_data: Event data to pass to the handler

        Returns:
            True if the handler completed successfully, False otherwise
        """
        import time

        start_time = time.time()
        success = False

        try:
            await handler_info.handler(event_data)
            success = True
        except Exception as e:
            error_stack = traceback.format_exc()
            logger.error(f"Error in async event handler: {e}\n{error_stack}")
        finally:
            execution_time = time.time() - start_time
            handler_info.update_stats(execution_time, success)

        return success

    def get_subscribers_count(self, event_type: Optional[str] = None) -> int:
        """
        Get the number of subscribers for an event type or all event types.

        Args:
            event_type: The type of event to count subscribers for, or None for all types

        Returns:
            The number of subscribers
        """
        if event_type is None:
            # Count all handlers
            handler_count = sum(len(handlers) for handlers in self._handlers.values())
            handler_count += len(self._wildcard_handlers)
            return handler_count
        elif event_type == "*":
            # Count just wildcard handlers
            return len(self._wildcard_handlers)
        else:
            # Count handlers for specific event type + wildcards
            specific_count = len(self._handlers.get(event_type, {}))
            return specific_count + len(self._wildcard_handlers)

    def get_handler_stats(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get statistics for all registered handlers by event type.

        Returns:
            Dictionary mapping event types to lists of handler statistics
        """
        stats = {}

        # Add wildcard handlers
        wildcard_stats = [
            {
                "handler_id": handler_id,
                "is_async": info.is_async,
                "priority": info.priority.name,
                "execution_count": info.execution_count,
                "avg_execution_time_ms": info.avg_execution_time_ms,
                "error_rate": info.error_rate,
                "error_count": info.error_count,
            }
            for handler_id, info in self._wildcard_handlers.items()
        ]
        stats["*"] = wildcard_stats

        # Add handlers for specific event types
        for event_type, handlers in self._handlers.items():
            event_stats = [
                {
                    "handler_id": handler_id,
                    "is_async": info.is_async,
                    "priority": info.priority.name,
                    "execution_count": info.execution_count,
                    "avg_execution_time_ms": info.avg_execution_time_ms,
                    "error_rate": info.error_rate,
                    "error_count": info.error_count,
                }
                for handler_id, info in handlers.items()
            ]
            stats[event_type] = event_stats

        return stats

    def clear(self) -> None:
        """
        Clear all event subscriptions.

        This method removes all registered handlers from the event bus.
        Useful for testing or when shutting down the application.
        """
        self._handlers = {}
        self._wildcard_handlers = {}
        self._handler_ids = {}
        logger.debug("EventBus cleared")


# Global event bus instance
_event_bus = EventBus()


def get_event_bus() -> EventBus:
    """
    Get the global event bus instance.

    This function provides a simple dependency injection mechanism
    for accessing the event bus throughout the application.

    Returns:
        The global EventBus instance
    """
    return _event_bus


# Helper functions for more ergonomic API
def subscribe(
    event_type: str,
    handler: HandlerType,
    priority: EventPriority = EventPriority.NORMAL,
) -> int:
    """
    Subscribe a handler to an event using the global event bus.

    Args:
        event_type: Event type to subscribe to
        handler: Handler function
        priority: Handler execution priority

    Returns:
        Handler ID
    """
    return get_event_bus().subscribe(event_type, handler, priority)


def unsubscribe(event_type: str, handler: HandlerType) -> bool:
    """
    Unsubscribe a handler from an event using the global event bus.

    Args:
        event_type: Event type to unsubscribe from
        handler: Handler function

    Returns:
        Success status
    """
    return get_event_bus().unsubscribe(event_type, handler)


def unsubscribe_by_id(event_type: str, handler_id: int) -> bool:
    """
    Unsubscribe a handler by ID using the global event bus.

    Args:
        event_type: Event type to unsubscribe from
        handler_id: Handler ID

    Returns:
        Success status
    """
    return get_event_bus().unsubscribe_by_id(event_type, handler_id)


def publish(event_type: str, event_data: Optional[EventData] = None) -> int:
    """
    Publish an event using the global event bus.

    Args:
        event_type: Event type
        event_data: Event data

    Returns:
        Number of handlers notified
    """
    return get_event_bus().publish(event_type, event_data)


async def publish_async(event_type: str, event_data: Optional[EventData] = None) -> int:
    """
    Publish an event asynchronously using the global event bus.

    Args:
        event_type: Event type
        event_data: Event data

    Returns:
        Number of handlers notified
    """
    return await get_event_bus().publish_async(event_type, event_data)
