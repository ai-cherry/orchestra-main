"""
Enhanced Event Bus Service for AI Orchestration System.

This module provides an improved event bus implementation for decoupling components
through a publish-subscribe pattern, with enhanced error handling, concurrency
control, and comprehensive async support.
"""

import asyncio
import functools
import logging
import queue
import threading
import time
import traceback
from enum import Enum
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
)

# Configure logging
logger = logging.getLogger(__name__)

# Type definitions
EventData = Dict[str, Any]
EventHandler = Callable[[EventData], None]
AsyncEventHandler = Callable[[EventData], Awaitable[None]]
T = TypeVar("T")


class EventPriority(Enum):
    """
    Priority levels for event handlers.

    Higher priority handlers are executed first.
    """

    HIGH = 3
    NORMAL = 2
    LOW = 1


class EventHandlerInfo:
    """
    Container for event handler information.

    This class stores metadata about registered event handlers,
    including priority, handler function, and execution stats.
    """

    def __init__(
        self,
        handler: Union[EventHandler, AsyncEventHandler],
        priority: EventPriority = EventPriority.NORMAL,
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
        self.execution_count = 0
        self.last_execution_time = 0
        self.total_execution_time = 0
        self.error_count = 0

    def update_stats(self, execution_time: float, success: bool) -> None:
        """
        Update handler execution statistics.

        Args:
            execution_time: Time taken to execute the handler
            success: Whether execution was successful
        """
        self.execution_count += 1
        self.last_execution_time = time.time()
        self.total_execution_time += execution_time

        if not success:
            self.error_count += 1

    def avg_execution_time(self) -> float:
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

    def error_rate(self) -> float:
        """
        Get error rate as a percentage.

        Returns:
            Error rate percentage or 0 if never executed
        """
        if self.execution_count == 0:
            return 0

        return (self.error_count / self.execution_count) * 100


class EnhancedEventBus:
    """
    Enhanced event bus implementation with comprehensive async support.

    This class manages event subscriptions and notifications with:
    1. Prioritized event handlers
    2. Comprehensive async and sync support
    3. Robust error handling and retry capabilities
    4. Optional event queuing for high-throughput scenarios
    5. Detailed handler statistics and monitoring
    """

    def __init__(self, use_queuing: bool = False, queue_size: int = 1000):
        """
        Initialize the enhanced event bus.

        Args:
            use_queuing: Whether to use an event queue for high-throughput scenarios
            queue_size: Maximum size of the event queue if queuing is enabled
        """
        # Handlers by event type and handler ID
        self._handlers: Dict[str, Dict[int, EventHandlerInfo]] = {}
        self._wildcard_handlers: Dict[int, EventHandlerInfo] = {}

        # Handler IDs for efficient lookup and removal
        self._handler_ids: Dict[Callable, int] = {}
        self._next_handler_id = 1

        # Event queuing for high-throughput scenarios
        self._use_queuing = use_queuing
        if use_queuing:
            self._event_queue: queue.Queue = queue.Queue(maxsize=queue_size)
            self._worker_thread = threading.Thread(
                target=self._process_queue, daemon=True
            )
            self._running = True
            self._worker_thread.start()

        logger.debug("EnhancedEventBus initialized")

    def subscribe(
        self,
        event_type: str,
        handler: Union[EventHandler, AsyncEventHandler],
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
        handler_info = EventHandlerInfo(handler, priority)

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

    def unsubscribe(
        self, event_type: str, handler: Union[EventHandler, AsyncEventHandler]
    ) -> bool:
        """
        Unsubscribe a handler from an event type.

        Args:
            event_type: The type of event to unsubscribe from, or "*" for all events
            handler: The function to unsubscribe

        Returns:
            True if the handler was found and removed, False otherwise
        """
        if handler not in self._handler_ids:
            logger.warning(
                f"Cannot unsubscribe handler for '{event_type}': handler not found"
            )
            return False

        handler_id = self._handler_ids[handler]

        if event_type == "*":
            if handler_id in self._wildcard_handlers:
                del self._wildcard_handlers[handler_id]
                del self._handler_ids[handler]
                logger.debug(f"Handler unsubscribed from all events: id={handler_id}")
                return True
        elif event_type in self._handlers:
            if handler_id in self._handlers[event_type]:
                del self._handlers[event_type][handler_id]
                del self._handler_ids[handler]
                logger.debug(
                    f"Handler unsubscribed from '{event_type}': id={handler_id}"
                )

                # Clean up empty event type dictionaries
                if not self._handlers[event_type]:
                    del self._handlers[event_type]

                return True

        logger.warning(
            f"Cannot unsubscribe handler for '{event_type}': handler not registered for this event"
        )
        return False

    def unsubscribe_by_id(self, handler_id: int) -> bool:
        """
        Unsubscribe a handler by its ID.

        Args:
            handler_id: The handler ID

        Returns:
            True if the handler was found and removed, False otherwise
        """
        # Check wildcard handlers
        if handler_id in self._wildcard_handlers:
            handler = self._wildcard_handlers[handler_id].handler
            del self._wildcard_handlers[handler_id]
            del self._handler_ids[handler]
            logger.debug(f"Handler unsubscribed from all events: id={handler_id}")
            return True

        # Check specific event handlers
        for event_type, handlers in self._handlers.items():
            if handler_id in handlers:
                handler = handlers[handler_id].handler
                del handlers[handler_id]
                del self._handler_ids[handler]
                logger.debug(
                    f"Handler unsubscribed from '{event_type}': id={handler_id}"
                )

                # Clean up empty event type dictionaries
                if not handlers:
                    del self._handlers[event_type]

                return True

        logger.warning(
            f"Cannot unsubscribe handler with id={handler_id}: handler not found"
        )
        return False

    def publish(self, event_type: str, event_data: EventData = None) -> int:
        """
        Publish an event to synchronous subscribers.

        Args:
            event_type: The type of event being published
            event_data: The data associated with the event

        Returns:
            The number of handlers that were notified
        """
        event_data = event_data or {}

        # Use event queue for high-throughput scenarios
        if self._use_queuing:
            self._event_queue.put((event_type, event_data, False))
            return 0  # Actual count not available when queuing

        # Process event immediately
        return self._process_event(event_type, event_data, async_mode=False)

    async def publish_async(self, event_type: str, event_data: EventData = None) -> int:
        """
        Publish an event to all subscribers asynchronously.

        Args:
            event_type: The type of event being published
            event_data: The data associated with the event

        Returns:
            The number of handlers that were notified
        """
        event_data = event_data or {}

        # Use event queue for high-throughput scenarios
        if self._use_queuing:
            self._event_queue.put((event_type, event_data, True))
            return 0  # Actual count not available when queuing

        # Process event immediately
        return await self._process_event_async(event_type, event_data)

    def _process_event(
        self, event_type: str, event_data: EventData, async_mode: bool
    ) -> int:
        """
        Process an event by calling handlers synchronously.

        Args:
            event_type: Type of the event
            event_data: Event data
            async_mode: Whether to process async handlers

        Returns:
            Number of handlers that were notified
        """
        # Do not modify the original data
        event_data = dict(event_data)

        # Add event type to data for context
        event_data["_event_type"] = event_type

        # Track the number of handlers called
        handler_count = 0

        # Get handlers for this event type
        type_handlers = []
        if event_type in self._handlers:
            for handler_id, handler_info in self._handlers[event_type].items():
                # Only process sync handlers in sync mode, unless we're also including async handlers
                if not handler_info.is_async or async_mode:
                    type_handlers.append(handler_info)

        # Get wildcard handlers
        wildcard_handlers = []
        for handler_id, handler_info in self._wildcard_handlers.items():
            # Only process sync handlers in sync mode, unless we're also including async handlers
            if not handler_info.is_async or async_mode:
                wildcard_handlers.append(handler_info)

        # Combine and sort by priority (higher priority first)
        all_handlers = type_handlers + wildcard_handlers
        all_handlers.sort(key=lambda h: h.priority.value, reverse=True)

        # Call handlers
        for handler_info in all_handlers:
            if handler_info.is_async:
                # Skip async handlers in sync mode
                if not async_mode:
                    continue

                # We would run async handlers here in async mode,
                # but this is handled by _process_event_async
            else:
                # Call sync handler
                handler_count += self._call_handler(handler_info, event_data)

        if handler_count > 0:
            logger.debug(
                f"Event '{event_type}' published to {handler_count} synchronous handlers"
            )

        return handler_count

    async def _process_event_async(self, event_type: str, event_data: EventData) -> int:
        """
        Process an event by calling handlers asynchronously.

        Args:
            event_type: Type of the event
            event_data: Event data

        Returns:
            Number of handlers that were notified
        """
        # Call synchronous handlers first
        sync_count = self._process_event(event_type, event_data, async_mode=True)

        # Do not modify the original data
        event_data = dict(event_data)

        # Add event type to data for context
        event_data["_event_type"] = event_type

        # Get async handlers for this event type
        async_handlers = []
        if event_type in self._handlers:
            for handler_id, handler_info in self._handlers[event_type].items():
                if handler_info.is_async:
                    async_handlers.append(handler_info)

        # Get async wildcard handlers
        for handler_id, handler_info in self._wildcard_handlers.items():
            if handler_info.is_async:
                async_handlers.append(handler_info)

        # Sort by priority (higher priority first)
        async_handlers.sort(key=lambda h: h.priority.value, reverse=True)

        # Create tasks for all async handlers
        tasks = []
        for handler_info in async_handlers:
            task = self._call_handler_async(handler_info, event_data)
            tasks.append(task)

        # Wait for all tasks to complete
        if tasks:
            # Use gather with return_exceptions to prevent one failing handler from affecting others
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Count successes (True) in results
            async_count = sum(1 for r in results if r is True)
        else:
            async_count = 0

        total_count = sync_count + async_count

        if async_count > 0:
            logger.debug(
                f"Event '{event_type}' published to {async_count} asynchronous handlers"
            )

        return total_count

    def _call_handler(
        self, handler_info: EventHandlerInfo, event_data: EventData
    ) -> int:
        """
        Call a synchronous event handler with error handling and statistics tracking.

        Args:
            handler_info: Information about the handler
            event_data: Event data to pass to the handler

        Returns:
            1 if handler was called, 0 if it failed
        """
        start_time = time.time()
        success = False

        try:
            handler_info.handler(event_data)
            success = True
            return 1
        except Exception as e:
            error_stack = traceback.format_exc()
            logger.error(f"Error in event handler: {e}\n{error_stack}")
            return 0
        finally:
            execution_time = time.time() - start_time
            handler_info.update_stats(execution_time, success)

    async def _call_handler_async(
        self, handler_info: EventHandlerInfo, event_data: EventData
    ) -> bool:
        """
        Call an asynchronous event handler with error handling and statistics tracking.

        Args:
            handler_info: Information about the handler
            event_data: Event data to pass to the handler

        Returns:
            True if handler was called successfully, False otherwise
        """
        start_time = time.time()
        success = False

        try:
            await handler_info.handler(event_data)
            success = True
            return True
        except Exception as e:
            error_stack = traceback.format_exc()
            logger.error(f"Error in async event handler: {e}\n{error_stack}")
            return False
        finally:
            execution_time = time.time() - start_time
            handler_info.update_stats(execution_time, success)

    def _process_queue(self):
        """
        Process events from the queue in a background thread.

        This method runs in a separate thread and processes events
        from the queue as they arrive.
        """
        if not self._use_queuing:
            return

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while self._running:
            try:
                # Get event from queue with timeout
                try:
                    event_type, event_data, is_async = self._event_queue.get(
                        timeout=0.1
                    )
                except queue.Empty:
                    continue

                # Process event
                if is_async:
                    loop.run_until_complete(
                        self._process_event_async(event_type, event_data)
                    )
                else:
                    self._process_event(event_type, event_data, async_mode=False)

                # Mark task as done
                self._event_queue.task_done()
            except Exception as e:
                logger.error(f"Error processing event from queue: {e}")

        # Clean up
        loop.close()

    def close(self):
        """
        Close the event bus and release resources.

        This stops the queue processing thread if it's running.
        """
        if self._use_queuing and self._running:
            self._running = False
            self._worker_thread.join(timeout=5.0)
            logger.debug("EnhancedEventBus closed")

    def get_subscribers_count(self, event_type: str = None) -> int:
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

        if event_type == "*":
            # Count just wildcard handlers
            return len(self._wildcard_handlers)

        # Count handlers for specific event type
        type_count = len(self._handlers.get(event_type, {}))

        # Also include wildcard handlers
        return type_count + len(self._wildcard_handlers)

    def get_handler_stats(
        self, event_type: str = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get statistics for handlers by event type.

        Args:
            event_type: The type of event to get stats for, or None for all types

        Returns:
            Dictionary mapping event types to lists of handler statistics
        """
        stats = {}

        if event_type is None or event_type == "*":
            # Include wildcard handlers
            wildcard_stats = []
            for handler_id, handler_info in self._wildcard_handlers.items():
                wildcard_stats.append(
                    {
                        "handler_id": handler_id,
                        "is_async": handler_info.is_async,
                        "priority": handler_info.priority.name,
                        "execution_count": handler_info.execution_count,
                        "avg_execution_time_ms": handler_info.avg_execution_time(),
                        "error_rate_percent": handler_info.error_rate(),
                        "error_count": handler_info.error_count,
                    }
                )

            stats["*"] = wildcard_stats

        if event_type is None:
            # Include all event types
            for event_type, handlers in self._handlers.items():
                event_stats = []
                for handler_id, handler_info in handlers.items():
                    event_stats.append(
                        {
                            "handler_id": handler_id,
                            "is_async": handler_info.is_async,
                            "priority": handler_info.priority.name,
                            "execution_count": handler_info.execution_count,
                            "avg_execution_time_ms": handler_info.avg_execution_time(),
                            "error_rate_percent": handler_info.error_rate(),
                            "error_count": handler_info.error_count,
                        }
                    )

                stats[event_type] = event_stats
        elif event_type != "*" and event_type in self._handlers:
            # Include specific event type
            event_stats = []
            for handler_id, handler_info in self._handlers[event_type].items():
                event_stats.append(
                    {
                        "handler_id": handler_id,
                        "is_async": handler_info.is_async,
                        "priority": handler_info.priority.name,
                        "execution_count": handler_info.execution_count,
                        "avg_execution_time_ms": handler_info.avg_execution_time(),
                        "error_rate_percent": handler_info.error_rate(),
                        "error_count": handler_info.error_count,
                    }
                )

            stats[event_type] = event_stats

        return stats


# Global event bus instance
_enhanced_event_bus = EnhancedEventBus()


def get_enhanced_event_bus() -> EnhancedEventBus:
    """
    Get the global enhanced event bus instance.

    Returns:
        The global EnhancedEventBus instance
    """
    return _enhanced_event_bus


# Helper functions for more ergonomic API
def subscribe(
    event_type: str,
    handler: Union[EventHandler, AsyncEventHandler],
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
    return get_enhanced_event_bus().subscribe(event_type, handler, priority)


def unsubscribe(
    event_type: str, handler: Union[EventHandler, AsyncEventHandler]
) -> bool:
    """
    Unsubscribe a handler from an event using the global event bus.

    Args:
        event_type: Event type to unsubscribe from
        handler: Handler function

    Returns:
        Success status
    """
    return get_enhanced_event_bus().unsubscribe(event_type, handler)


def unsubscribe_by_id(handler_id: int) -> bool:
    """
    Unsubscribe a handler by ID using the global event bus.

    Args:
        handler_id: Handler ID

    Returns:
        Success status
    """
    return get_enhanced_event_bus().unsubscribe_by_id(handler_id)


def publish(event_type: str, event_data: EventData = None) -> int:
    """
    Publish an event using the global event bus.

    Args:
        event_type: Event type
        event_data: Event data

    Returns:
        Number of handlers notified
    """
    return get_enhanced_event_bus().publish(event_type, event_data)


async def publish_async(event_type: str, event_data: EventData = None) -> int:
    """
    Publish an event asynchronously using the global event bus.

    Args:
        event_type: Event type
        event_data: Event data

    Returns:
        Number of handlers notified
    """
    return await get_enhanced_event_bus().publish_async(event_type, event_data)
