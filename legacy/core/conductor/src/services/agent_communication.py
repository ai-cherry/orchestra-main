"""
"""
    """Service for agent communication using PubSub."""
        """Initialize the agent communication service."""
        self.environment = settings.ENVIRONMENT or "dev"
        self.agent_id = None
        self.conversation_id = None
        self.subscriptions: Set[str] = set()
        self.event_handlers: Dict[str, List[Callable[[Dict[str, Any]], Awaitable[None]]]] = {}
        self.task_handlers: Dict[str, Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = {}

    async def initialize(self, agent_id: str, conversation_id: Optional[str] = None) -> None:
        """
        """
        self.pubsub_client.create_topic("agent-events")
        self.pubsub_client.create_topic("agent-tasks")
        self.pubsub_client.create_topic("agent-results")

        # Create agent-specific subscription for events
        agent_filter = f'attributes.recipient_id = "{agent_id}" OR attributes.recipient_id = "all"'
        if conversation_id:
            agent_filter += f' AND attributes.conversation_id = "{conversation_id}"'

        self.pubsub_client.create_subscription(f"agent-events-{agent_id}", "agent-events", filter_expr=agent_filter)

        # Create agent-specific subscription for tasks
        task_filter = f'attributes.agent_id = "{agent_id}"'
        if conversation_id:
            task_filter += f' AND attributes.conversation_id = "{conversation_id}"'

        self.pubsub_client.create_subscription(f"agent-tasks-{agent_id}", "agent-tasks", filter_expr=task_filter)

        # Start listening for events
        await self.start_event_listener()

        # Start listening for tasks
        await self.start_task_listener()

        logger.info(f"Agent communication initialized for agent {agent_id}")

    async def start_event_listener(self) -> None:
        """Start listening for events."""
        subscription_name = f"agent-events-{self.agent_id}"

        # Define the callback for events
        async def event_callback(data: Dict[str, Any], attributes: Dict[str, str]) -> None:
            event_type = attributes.get("event_type")
            if not event_type:
                logger.warning(f"Received event without event_type: {attributes}")
                return

            # Call registered handlers for this event type
            if event_type in self.event_handlers:
                for handler in self.event_handlers[event_type]:
                    try:

                        pass
                        await handler(data)
                    except Exception:

                        pass
                        logger.error(f"Error in event handler for {event_type}: {e}")

        # Start the subscription
        asyncio.create_task(self.pubsub_client.subscribe_async(subscription_name, event_callback))
        self.subscriptions.add(subscription_name)

        logger.info(f"Started event listener for agent {self.agent_id}")

    async def start_task_listener(self) -> None:
        """Start listening for tasks."""
        subscription_name = f"agent-tasks-{self.agent_id}"

        # Define the callback for tasks
        async def task_callback(data: Dict[str, Any], attributes: Dict[str, str]) -> None:
            task_type = attributes.get("task_type")
            if not task_type:
                logger.warning(f"Received task without task_type: {attributes}")
                return

            # Call registered handler for this task type
            if task_type in self.task_handlers:
                try:

                    pass
                    # Process the task
                    result = await self.task_handlers[task_type](data)

                    # Publish the result
                    await self.publish_task_result(
                        task_id=attributes.get("task_id", str(uuid.uuid4())),
                        result=result,
                        task_type=task_type,
                    )
                except Exception:

                    pass
                    logger.error(f"Error in task handler for {task_type}: {e}")

                    # Publish error result
                    await self.publish_task_result(
                        task_id=attributes.get("task_id", str(uuid.uuid4())),
                        result={"error": str(e)},
                        task_type=task_type,
                        success=False,
                    )

        # Start the subscription
        asyncio.create_task(self.pubsub_client.subscribe_async(subscription_name, task_callback))
        self.subscriptions.add(subscription_name)

        logger.info(f"Started task listener for agent {self.agent_id}")

    def register_event_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        """
        """
        """
        """
    async def publish_event(self, event_type: str, data: Dict[str, Any], recipient_id: str = "all") -> str:
        """
            recipient_id: The recipient agent ID or "all"

        Returns:
            The published message ID
        """
            "event_type": event_type,
            "sender_id": self.agent_id,
            "recipient_id": recipient_id,
            "timestamp": str(int(time.time())),
        }

        if self.conversation_id:
            attributes["conversation_id"] = self.conversation_id

        return await self.pubsub_client.publish_message_async(
            "agent-events",
            data,
            ordering_key=self.conversation_id,
            attributes=attributes,
        )

    async def publish_task(
        self,
        task_type: str,
        data: Dict[str, Any],
        agent_id: str,
        task_id: Optional[str] = None,
    ) -> str:
        """
        """
            "task_type": task_type,
            "task_id": task_id,
            "sender_id": self.agent_id,
            "agent_id": agent_id,
            "timestamp": str(int(time.time())),
        }

        if self.conversation_id:
            attributes["conversation_id"] = self.conversation_id

        return await self.pubsub_client.publish_message_async(
            "agent-tasks", data, ordering_key=task_id, attributes=attributes
        )

    async def publish_task_result(
        self, task_id: str, result: Dict[str, Any], task_type: str, success: bool = True
    ) -> str:
        """
        """
            "task_id": task_id,
            "task_type": task_type,
            "agent_id": self.agent_id,
            "success": str(success).lower(),
            "timestamp": str(int(time.time())),
        }

        if self.conversation_id:
            attributes["conversation_id"] = self.conversation_id

        return await self.pubsub_client.publish_message_async(
            "agent-results", result, ordering_key=task_id, attributes=attributes
        )

    async def close(self) -> None:
        """Close the communication service."""
        logger.info(f"Agent communication closed for agent {self.agent_id}")

# Singleton instance
_agent_communication = None

async def get_agent_communication(
    agent_id: Optional[str] = None, conversation_id: Optional[str] = None
) -> AgentCommunicationService:
    """
    """