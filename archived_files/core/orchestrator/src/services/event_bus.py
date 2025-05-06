"""
Event Bus Service for AI Orchestration System.

This module provides a simple event bus implementation for decoupling components
through a publish-subscribe pattern. It allows different parts of the system to
communicate without direct dependencies.
"""

import asyncio
import logging
from collections import defaultdict
from typing import Any, Callable, Dict, List, Union, Awaitable

# Configure logging
logger = logging.getLogger(__name__)

# Event handler types
EventHandler = Callable[[Dict[str, Any]], None]
AsyncEventHandler = Callable[[Dict[str, Any]], Awaitable[None]]


class EventBus:
    """
    Event bus implementation using the publish-subscribe pattern.

    This class manages event subscriptions and notification, allowing
    components to communicate without direct dependencies. It supports both
    synchronous and asynchronous event handlers.

    For distributed scenarios, this could be extended to use Redis PubSub
    or another message broker.
    """

    def __init__(self):
        """Initialize the event bus with empty handler collections."""
        # Synchronous handlers
        self._handlers = defaultdict(list)
        self._wildcard_handlers = []

        # Asynchronous handlers
        self._async_handlers = defaultdict(list)
        self._async_wildcard_handlers = []

        logger.debug("EventBus initialized")

    def subscribe(
        self, event_type: str, handler: Union[EventHandler, AsyncEventHandler]
    ) -> None:
        """
        Subscribe a handler to a specific event type.

        Args:
            event_type: The type of event to subscribe to, or "*" for all events
            handler: The function to call when the event occurs. Can be synchronous or asynchronous.
        """
        # Determine if handler is async or sync
        is_async = asyncio.iscoroutinefunction(handler)

        if event_type == "*":
            if is_async:
                self._async_wildcard_handlers.append(handler)
                logger.debug(
                    f"Async handler subscribed to all events: {handler.__name__}"
                )
            else:
                self._wildcard_handlers.append(handler)
                logger.debug(f"Handler subscribed to all events: {handler.__name__}")
        else:
            if is_async:
                self._async_handlers[event_type].append(handler)
                logger.debug(
                    f"Async handler subscribed to '{event_type}': {handler.__name__}"
                )
            else:
                self._handlers[event_type].append(handler)
                logger.debug(
                    f"Handler subscribed to '{event_type}': {handler.__name__}"
                )

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
        # Determine if handler is async or sync
        is_async = asyncio.iscoroutinefunction(handler)
        success = False

        if event_type == "*":
            if is_async:
                try:
                    self._async_wildcard_handlers.remove(handler)
                    logger.debug(
                        f"Async handler unsubscribed from all events: {handler.__name__}"
                    )
                    success = True
                except ValueError:
                    pass
            else:
                try:
                    self._wildcard_handlers.remove(handler)
                    logger.debug(
                        f"Handler unsubscribed from all events: {handler.__name__}"
                    )
                    success = True
                except ValueError:
                    pass
        else:
            if is_async:
                handlers = self._async_handlers[event_type]
                try:
                    handlers.remove(handler)
                    logger.debug(
                        f"Async handler unsubscribed from '{event_type}': {handler.__name__}"
                    )
                    success = True
                except ValueError:
                    pass
            else:
                handlers = self._handlers[event_type]
                try:
                    handlers.remove(handler)
                    logger.debug(
                        f"Handler unsubscribed from '{event_type}': {handler.__name__}"
                    )
                    success = True
                except ValueError:
                    pass

        return success

    def publish(self, event_type: str, event_data: Dict[str, Any]) -> int:
        """
        Publish an event to all synchronous subscribers.

        This method only executes synchronous handlers. Asynchronous handlers
        are ignored - use publish_async() for those.

        Args:
            event_type: The type of event being published
            event_data: The data associated with the event

        Returns:
            The number of synchronous handlers that were notified
        """
        count = 0

        # Add event_type to the data for wildcard handlers
        event_data_with_type = {**event_data, "_event_type": event_type}

        # Call handlers for this specific event type
        for handler in self._handlers[event_type]:
            try:
                handler(event_data)
                count += 1
            except Exception as e:
                logger.error(f"Error in event handler for '{event_type}': {e}")

        # Call wildcard handlers
        for handler in self._wildcard_handlers:
            try:
                handler(event_data_with_type)
                count += 1
            except Exception as e:
                logger.error(f"Error in wildcard event handler for '{event_type}': {e}")

        if count > 0:
            logger.debug(
                f"Event '{event_type}' published to {count} synchronous handlers"
            )

        return count

    async def publish_async(self, event_type: str, event_data: Dict[str, Any]) -> int:
        """
        Publish an event to all subscribers, including asynchronous handlers.

        This method executes both synchronous and asynchronous handlers.
        The synchronous handlers are executed in the current thread, while
        asynchronous handlers are executed concurrently.

        Args:
            event_type: The type of event being published
            event_data: The data associated with the event

        Returns:
            The total number of handlers that were notified
        """
        # First, call synchronous handlers
        sync_count = self.publish(event_type, event_data)

        # Then, handle async handlers
        async_count = 0
        event_data_with_type = {**event_data, "_event_type": event_type}

        # Collect async coroutines
        coros = []

        # From specific handlers
        for handler in self._async_handlers[event_type]:
            try:
                coros.append(handler(event_data))
                async_count += 1
            except Exception as e:
                logger.error(
                    f"Error creating coroutine for async handler of '{event_type}': {e}"
                )

        # From wildcard handlers
        for handler in self._async_wildcard_handlers:
            try:
                coros.append(handler(event_data_with_type))
                async_count += 1
            except Exception as e:
                logger.error(
                    f"Error creating coroutine for async wildcard handler of '{event_type}': {e}"
                )

        # Execute all coroutines concurrently
        if coros:
            try:
                await asyncio.gather(*coros, return_exceptions=True)
                logger.debug(
                    f"Event '{event_type}' published to {async_count} asynchronous handlers"
                )
            except Exception as e:
                logger.error(f"Error in asyncio.gather for event '{event_type}': {e}")

        total_count = sync_count + async_count
        return total_count

    def get_subscribers_count(
        self, event_type: str = None, include_async: bool = True
    ) -> int:
        """
        Get the number of subscribers for an event type or all event types.

        Args:
            event_type: The type of event to count subscribers for, or None for all types
            include_async: Whether to include asynchronous handlers in the count

        Returns:
            The number of subscribers
        """
        sync_count = 0
        async_count = 0

        if event_type:
            sync_count = len(self._handlers[event_type])
            if include_async:
                async_count = len(self._async_handlers[event_type])
        else:
            sync_count = sum(
                len(handlers) for handlers in self._handlers.values()
            ) + len(self._wildcard_handlers)
            if include_async:
                async_count = sum(
                    len(handlers) for handlers in self._async_handlers.values()
                ) + len(self._async_wildcard_handlers)

        return sync_count + async_count


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
