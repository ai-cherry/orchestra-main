"""
Google Cloud Pub/Sub Client for File Ingestion System.

This module provides integration with Google Cloud Pub/Sub for asynchronous
messaging and event-driven processing of ingestion tasks.
"""

import json
import logging
import base64
from typing import Any, Dict, Optional, Callable, Awaitable, List

from google.cloud import pubsub_v1
from google.api_core.exceptions import AlreadyExists, NotFound
import aiohttp

from packages.ingestion.src.models.ingestion_models import PubSubMessage
from packages.ingestion.src.config.settings import get_settings

# Configure logging
logger = logging.getLogger(__name__)


class PubSubError(Exception):
    """Exception for Pub/Sub-related errors."""
    pass


class PubSubClient:
    """
    Google Cloud Pub/Sub client for asynchronous messaging.
    
    This class provides methods for publishing messages to topics and
    setting up subscriptions for processing ingestion tasks.
    """
    
    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize the Pub/Sub client.
        
        Args:
            project_id: Optional Google Cloud project ID. If not provided,
                      will be read from settings or environment.
        """
        settings = get_settings()
        self.project_id = project_id or settings.pubsub.project_id
        self.ingestion_topic = settings.pubsub.ingestion_topic
        self.ingestion_subscription = settings.pubsub.ingestion_subscription
        self._publisher = None
        self._subscriber = None
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize the Pub/Sub client and ensure topics and subscriptions exist."""
        if self._initialized:
            return
            
        try:
            # Create Pub/Sub clients (synchronous only)
            self._publisher = pubsub_v1.PublisherClient()
            self._subscriber = pubsub_v1.SubscriberClient()
            
            # Create full topic and subscription paths
            self.topic_path = self._publisher.topic_path(
                self.project_id, self.ingestion_topic
            )
            
            self.subscription_path = self._subscriber.subscription_path(
                self.project_id, self.ingestion_subscription
            )
            
            # Ensure topic exists
            try:
                self._publisher.get_topic(request={"topic": self.topic_path})
                logger.debug(f"Topic exists: {self.topic_path}")
            except NotFound:
                logger.info(f"Creating topic: {self.topic_path}")
                self._publisher.create_topic(request={"name": self.topic_path})
                
            # Ensure subscription exists
            try:
                self._subscriber.get_subscription(request={"subscription": self.subscription_path})
                logger.debug(f"Subscription exists: {self.subscription_path}")
            except NotFound:
                logger.info(f"Creating subscription: {self.subscription_path}")
                self._subscriber.create_subscription(
                    request={
                        "name": self.subscription_path,
                        "topic": self.topic_path,
                        # Configure retry and expiration if needed
                        "ack_deadline_seconds": 300,  # 5 minutes
                        "retry_policy": {
                            "minimum_backoff": "10s",
                            "maximum_backoff": "600s"
                        },
                        "message_retention_duration": {"seconds": 604800}  # 7 days
                    }
                )
                
            self._initialized = True
            logger.info("Pub/Sub client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Pub/Sub client: {e}")
            raise PubSubError(f"Failed to initialize Pub/Sub: {e}")
        
    async def close(self) -> None:
        """Close the Pub/Sub client."""
        if self._publisher:
            self._publisher.api.transport.channel.close()
            
        if self._subscriber:
            self._subscriber.api.transport.channel.close()
            
        self._publisher = None
        self._subscriber = None
        self._initialized = False
        logger.debug("Pub/Sub client closed")
        
    def _check_initialized(self) -> None:
        """Check if the client is initialized and raise error if not."""
        if not self._initialized or not self._publisher or not self._subscriber:
            raise PubSubError("Pub/Sub client not initialized")
            
    async def publish_task(self, message: PubSubMessage) -> str:
        """
        Publish a task message to the ingestion topic.
        
        Args:
            message: The message to publish
            
        Returns:
            The published message ID
            
        Raises:
            PubSubError: If publishing fails
        """
        self._check_initialized()
        
        try:
            # Convert message to JSON
            message_data = message.json().encode("utf-8")
            
            # Publish message
            future = self._publisher.publish(self.topic_path, message_data)
            message_id = future.result()
            
            logger.debug(f"Published message to {self.topic_path} with ID: {message_id}")
            return message_id
        except Exception as e:
            logger.error(f"Failed to publish message to Pub/Sub: {e}")
            raise PubSubError(f"Failed to publish message: {e}")
            
    async def pull_messages(self, max_messages: int = 10) -> List[Dict[str, Any]]:
        """
        Pull messages from the ingestion subscription.
        
        This is primarily for testing or manual processing. For production,
        use the process_messages method with a callback.
        
        Args:
            max_messages: Maximum number of messages to pull
            
        Returns:
            List of message dictionaries with data and attributes
            
        Raises:
            PubSubError: If pulling fails
        """
        self._check_initialized()
        
        try:
            # Pull messages
            response = self._subscriber.pull(
                request={
                    "subscription": self.subscription_path,
                    "max_messages": max_messages
                }
            )
            
            # Process messages
            messages = []
            for received_message in response.received_messages:
                # Extract message data
                message_data = received_message.message.data.decode("utf-8")
                attributes = dict(received_message.message.attributes)
                
                # Parse JSON if possible
                try:
                    message_json = json.loads(message_data)
                except json.JSONDecodeError:
                    message_json = None
                
                # Add message to result
                messages.append({
                    "ack_id": received_message.ack_id,
                    "message_id": received_message.message.message_id,
                    "data": message_json or message_data,
                    "attributes": attributes,
                    "publish_time": received_message.message.publish_time
                })
                
            logger.debug(f"Pulled {len(messages)} messages from {self.subscription_path}")
            return messages
        except Exception as e:
            logger.error(f"Failed to pull messages from Pub/Sub: {e}")
            raise PubSubError(f"Failed to pull messages: {e}")
            
    async def acknowledge_messages(self, ack_ids: List[str]) -> None:
        """
        Acknowledge messages to remove them from the subscription.
        
        Args:
            ack_ids: List of acknowledgment IDs
            
        Raises:
            PubSubError: If acknowledgment fails
        """
        self._check_initialized()
        
        if not ack_ids:
            return
            
        try:
            # Acknowledge messages
            self._subscriber.acknowledge(
                request={
                    "subscription": self.subscription_path,
                    "ack_ids": ack_ids
                }
            )
            
            logger.debug(f"Acknowledged {len(ack_ids)} messages")
        except Exception as e:
            logger.error(f"Failed to acknowledge messages: {e}")
            raise PubSubError(f"Failed to acknowledge messages: {e}")
            
    async def process_messages(
        self, 
        callback: Callable[[Dict[str, Any]], Awaitable[bool]],
        max_messages: int = 10
    ) -> int:
        """
        Pull and process messages using a callback function.
        
        The callback function should return True if the message was successfully
        processed and should be acknowledged, or False if it should be retried.
        
        Args:
            callback: Async function to process each message
            max_messages: Maximum number of messages to pull
            
        Returns:
            Number of messages processed
            
        Raises:
            PubSubError: If processing fails
        """
        self._check_initialized()
        
        try:
            # Pull messages
            messages = await self.pull_messages(max_messages)
            
            if not messages:
                return 0
                
            # Process messages and collect ack IDs for successful ones
            ack_ids = []
            for message in messages:
                try:
                    # Process message with callback
                    success = await callback(message)
                    
                    if success:
                        ack_ids.append(message["ack_id"])
                    else:
                        logger.warning(f"Message {message['message_id']} not processed successfully, will be retried")
                except Exception as e:
                    logger.error(f"Error processing message {message['message_id']}: {e}")
                    # Message not acknowledged, will be retried automatically
                    
            # Acknowledge successful messages
            if ack_ids:
                await self.acknowledge_messages(ack_ids)
                
            return len(ack_ids)
        except Exception as e:
            logger.error(f"Error in process_messages: {e}")
            raise PubSubError(f"Failed to process messages: {e}")
            
    @staticmethod
    def parse_push_message(request_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a Pub/Sub push message from Cloud Run or Cloud Functions.
        
        This method extracts the message data and attributes from a push
        subscription request body.
        
        Args:
            request_json: The request body as a dictionary
            
        Returns:
            Dictionary containing parsed message data and attributes
            
        Raises:
            PubSubError: If parsing fails
        """
        try:
            message = request_json.get("message", {})
            
            # Decode data if present
            data = None
            if "data" in message:
                # Decode base64 data
                decoded_data = base64.b64decode(message["data"]).decode("utf-8")
                
                # Try to parse as JSON
                try:
                    data = json.loads(decoded_data)
                except json.JSONDecodeError:
                    data = decoded_data
            
            # Get attributes
            attributes = message.get("attributes", {})
            
            # Get message ID and publish time
            message_id = message.get("messageId")
            publish_time = message.get("publishTime")
            
            return {
                "message_id": message_id,
                "data": data,
                "attributes": attributes,
                "publish_time": publish_time
            }
        except Exception as e:
            logger.error(f"Failed to parse Pub/Sub push message: {e}")
            raise PubSubError(f"Failed to parse push message: {e}")
