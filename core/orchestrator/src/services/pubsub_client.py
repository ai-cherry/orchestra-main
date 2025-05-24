"""
PubSub Client for AI Orchestra Agent Communication.

This module provides a client for interacting with Google Cloud PubSub
for agent communication and event distribution.
"""

import asyncio
import json
import logging
from typing import Any, Awaitable, Callable, Dict, Optional

from google.api_core.exceptions import AlreadyExists, NotFound
from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.subscriber.message import Message

from core.orchestrator.src.config.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class PubSubClient:
    """Client for interacting with Google Cloud PubSub."""

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize the PubSub client.

        Args:
            project_id: The GCP project ID (defaults to settings.GCP_PROJECT_ID)
        """
        self.project_id = project_id or settings.GCP_PROJECT_ID
        self.publisher = pubsub_v1.PublisherClient()
        self.subscriber = pubsub_v1.SubscriberClient()
        self.subscription_paths: Dict[str, str] = {}
        self.topic_paths: Dict[str, str] = {}
        self.subscription_futures: Dict[str, Any] = {}
        self.environment = settings.ENVIRONMENT or "dev"

    def get_topic_path(self, topic_name: str) -> str:
        """
        Get the full path for a topic.

        Args:
            topic_name: The base name of the topic

        Returns:
            The full topic path
        """
        if topic_name not in self.topic_paths:
            # Add environment suffix if not already present
            if not topic_name.endswith(f"-{self.environment}"):
                topic_name = f"{topic_name}-{self.environment}"
            self.topic_paths[topic_name] = self.publisher.topic_path(self.project_id, topic_name)
        return self.topic_paths[topic_name]

    def get_subscription_path(self, subscription_name: str) -> str:
        """
        Get the full path for a subscription.

        Args:
            subscription_name: The base name of the subscription

        Returns:
            The full subscription path
        """
        if subscription_name not in self.subscription_paths:
            # Add environment suffix if not already present
            if not subscription_name.endswith(f"-{self.environment}"):
                subscription_name = f"{subscription_name}-{self.environment}"
            self.subscription_paths[subscription_name] = self.subscriber.subscription_path(
                self.project_id, subscription_name
            )
        return self.subscription_paths[subscription_name]

    def create_topic(self, topic_name: str) -> str:
        """
        Create a topic if it doesn't exist.

        Args:
            topic_name: The base name of the topic

        Returns:
            The full topic path
        """
        topic_path = self.get_topic_path(topic_name)

        try:
            self.publisher.create_topic(request={"name": topic_path})
            logger.info(f"Created topic: {topic_path}")
        except AlreadyExists:
            logger.info(f"Topic already exists: {topic_path}")

        return topic_path

    def create_subscription(self, subscription_name: str, topic_name: str, filter_expr: Optional[str] = None) -> str:
        """
        Create a subscription if it doesn't exist.

        Args:
            subscription_name: The base name of the subscription
            topic_name: The base name of the topic
            filter_expr: Optional filter expression

        Returns:
            The full subscription path
        """
        subscription_path = self.get_subscription_path(subscription_name)
        topic_path = self.get_topic_path(topic_name)

        try:
            request = {
                "name": subscription_path,
                "topic": topic_path,
                "enable_message_ordering": True,
            }

            if filter_expr:
                request["filter"] = filter_expr

            self.subscriber.create_subscription(request=request)
            logger.info(f"Created subscription: {subscription_path}")
        except AlreadyExists:
            logger.info(f"Subscription already exists: {subscription_path}")
        except NotFound:
            logger.error(f"Topic not found: {topic_path}")
            self.create_topic(topic_name)
            return self.create_subscription(subscription_name, topic_name, filter_expr)

        return subscription_path

    def publish_message(
        self,
        topic_name: str,
        data: Dict[str, Any],
        ordering_key: Optional[str] = None,
        attributes: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Publish a message to a topic.

        Args:
            topic_name: The base name of the topic
            data: The message data
            ordering_key: Optional key for ordering messages
            attributes: Optional message attributes

        Returns:
            The published message ID
        """
        topic_path = self.get_topic_path(topic_name)

        # Convert data to JSON string
        data_bytes = json.dumps(data).encode("utf-8")

        # Prepare publish arguments
        publish_args = {}
        if ordering_key:
            publish_args["ordering_key"] = ordering_key
        if attributes:
            publish_args["attributes"] = attributes

        # Publish the message
        future = self.publisher.publish(topic_path, data=data_bytes, **publish_args)
        message_id = future.result()

        logger.debug(f"Published message {message_id} to {topic_path}")
        return message_id

    async def publish_message_async(
        self,
        topic_name: str,
        data: Dict[str, Any],
        ordering_key: Optional[str] = None,
        attributes: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Publish a message to a topic asynchronously.

        Args:
            topic_name: The base name of the topic
            data: The message data
            ordering_key: Optional key for ordering messages
            attributes: Optional message attributes

        Returns:
            The published message ID
        """
        # Run the synchronous method in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.publish_message(topic_name, data, ordering_key, attributes),
        )

    def subscribe(
        self,
        subscription_name: str,
        callback: Callable[[Message], None],
        auto_ack: bool = False,
    ) -> None:
        """
        Subscribe to a topic and process messages.

        Args:
            subscription_name: The base name of the subscription
            callback: Function to call for each message
            auto_ack: Whether to automatically acknowledge messages
        """
        subscription_path = self.get_subscription_path(subscription_name)

        def wrapped_callback(message: Message) -> None:
            try:
                callback(message)
                if auto_ack:
                    message.ack()
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                if auto_ack:
                    message.nack()

        # Start the subscription
        streaming_pull_future = self.subscriber.subscribe(subscription_path, wrapped_callback)
        self.subscription_futures[subscription_name] = streaming_pull_future

        logger.info(f"Listening for messages on {subscription_path}")

    async def subscribe_async(
        self,
        subscription_name: str,
        callback: Callable[[Dict[str, Any], Dict[str, str]], Awaitable[None]],
    ) -> None:
        """
        Subscribe to a topic and process messages asynchronously.

        Args:
            subscription_name: The base name of the subscription
            callback: Async function to call for each message
        """
        subscription_path = self.get_subscription_path(subscription_name)

        # Create a queue for messages
        queue = asyncio.Queue()

        def sync_callback(message: Message) -> None:
            # Parse the message data
            try:
                data = json.loads(message.data.decode("utf-8"))
                # Put the message in the queue
                asyncio.run_coroutine_threadsafe(
                    queue.put((data, message.attributes, message)),
                    asyncio.get_event_loop(),
                )
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                message.nack()

        # Start the subscription
        streaming_pull_future = self.subscriber.subscribe(subscription_path, sync_callback)
        self.subscription_futures[subscription_name] = streaming_pull_future

        logger.info(f"Listening for messages on {subscription_path}")

        # Process messages from the queue
        while True:
            try:
                # Get a message from the queue
                data, attributes, message = await queue.get()

                # Process the message
                try:
                    await callback(data, attributes)
                    message.ack()
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    message.nack()

                # Mark the task as done
                queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in message processing loop: {e}")
                await asyncio.sleep(1.0)

    def stop_subscription(self, subscription_name: str) -> None:
        """
        Stop a subscription.

        Args:
            subscription_name: The base name of the subscription
        """
        if subscription_name in self.subscription_futures:
            future = self.subscription_futures[subscription_name]
            future.cancel()
            future.result()
            del self.subscription_futures[subscription_name]
            logger.info(f"Stopped subscription: {subscription_name}")

    def close(self) -> None:
        """Close all connections."""
        # Stop all subscriptions
        for subscription_name in list(self.subscription_futures.keys()):
            self.stop_subscription(subscription_name)

        # Close clients
        self.publisher.close()
        self.subscriber.close()
        logger.info("PubSub client closed")


# Singleton instance
_pubsub_client = None


def get_pubsub_client() -> PubSubClient:
    """
    Get the global PubSub client instance.

    Returns:
        The global PubSubClient instance
    """
    global _pubsub_client
    if _pubsub_client is None:
        _pubsub_client = PubSubClient()
    return _pubsub_client
