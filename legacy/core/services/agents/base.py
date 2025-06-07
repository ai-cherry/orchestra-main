"""
"""
    """Agent lifecycle status."""
    IDLE = "idle"
    BUSY = "busy"
    THINKING = "thinking"
    EXECUTING = "executing"
    ERROR = "error"
    STOPPED = "stopped"

class AgentCapability(Enum):
    """Agent capabilities."""
    CONVERSATION = "conversation"
    TASK_EXECUTION = "task_execution"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    CREATIVITY = "creativity"
    PLANNING = "planning"
    MONITORING = "monitoring"
    COLLABORATION = "collaboration"

@dataclass
class AgentMessage:
    """Message between agents or from users."""
    sender_id: str = ""
    recipient_id: Optional[str] = None
    content: str = ""
    message_type: str = "text"
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class AgentConfig:
    """Configuration for an agent."""
    """Current state of an agent."""
    """Abstract base class for AI agents."""
        """Process an incoming message and optionally return a response."""
        """Agent's thinking/reasoning process."""
        """Agent's action execution process."""
        """Start the agent."""
                type="agent.started",
                data={
                    "agent_id": self.config.id,
                    "agent_name": self.config.name,
                    "capabilities": [cap.value for cap in self.config.capabilities],
                },
            )
        )

        logger.info(f"Agent {self.config.name} started")

    async def stop(self) -> None:
        """Stop the agent."""
                type="agent.stopped",
                data={"agent_id": self.config.id, "agent_name": self.config.name},
            )
        )

        logger.info(f"Agent {self.config.name} stopped")

    async def send_message(self, recipient_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Send a message to another agent or user."""
                type="agent.message",
                data={
                    "message": message.__dict__,
                    "sender_id": self.config.id,
                    "recipient_id": recipient_id,
                },
            )
        )

    async def receive_message(self, message: AgentMessage) -> None:
        """Receive a message."""
        """Execute a workflow."""
            raise ValueError(f"Workflow '{workflow_name}' not available for this agent")

        # Update status
        self.state.status = AgentStatus.EXECUTING

        try:


            pass
            # Execute workflow
            context = await self._workflow_engine.execute_workflow(workflow_name, inputs)

            # Track active workflow
            self.state.active_workflows.append(context.workflow_id)

            return context

        finally:
            # Update status
            if not self.state.active_workflows:
                self.state.status = AgentStatus.IDLE

    async def remember(self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Store information in agent's memory."""
            "agent_id": self.config.id,
            "agent_name": self.config.name,
            **(metadata or {}),
        }

        await self._memory_service.store(key=f"agent:{self.config.id}:{key}", value=value, metadata=agent_metadata)

    async def recall(self, query: str, limit: int = 10) -> List[Any]:
        """Recall information from agent's memory."""
            query=query, limit=limit, metadata_filter={"agent_id": self.config.id}
        )

        return results

    async def collaborate_with(self, agent_id: str, task: str, context: Dict[str, Any]) -> Any:
        """Collaborate with another agent on a task."""
            raise ValueError("Collaboration is not enabled for this agent")

        # Send collaboration request
        await self.send_message(
            recipient_id=agent_id,
            content=f"Collaboration request: {task}",
            metadata={
                "type": "collaboration_request",
                "task": task,
                "context": context,
            },
        )

        # Wait for response (simplified - in practice would be more complex)
        # This is a placeholder for actual collaboration logic
        await asyncio.sleep(1)

        return {"status": "collaboration_initiated", "task": task}

    async def _main_loop(self) -> None:
        """Main agent loop."""
                logger.error(f"Error in agent {self.config.name} main loop: {e}", exc_info=True)
                self.state.status = AgentStatus.ERROR
                await asyncio.sleep(1)  # Back off on error

    async def _process_message_queue(self) -> None:
        """Process queued messages."""
                    f"Error processing message in agent {self.config.name}: {e}",
                    exc_info=True,
                )

    async def _subscribe_to_events(self) -> None:
        """Subscribe to relevant events."""
            if event.data.get("recipient_id") == self.config.id:
                message_data = event.data.get("message", {})
                message = AgentMessage(**message_data)
                await self.receive_message(message)

        await self._event_bus.subscribe("agent.message", handle_message)

        # Subscribe to collaboration requests if enabled
        if self.config.collaboration_enabled:

            async def handle_collaboration(event: Event) -> None:
                if event.data.get("recipient_id") == self.config.id:
                    # Handle collaboration request
                    pass

            await self._event_bus.subscribe("agent.collaboration", handle_collaboration)

class AgentManager:
    """Manages multiple agents and their interactions."""
        """Register an agent with the manager."""
        logger.info(f"Registered agent: {agent.config.name}")

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID."""
        """List all registered agents."""
        """Start a specific agent."""
        """Stop a specific agent."""
        """Start all registered agents."""
        """Stop all registered agents."""
        """Broadcast a message to all agents."""
        """Find agents with a specific capability."""
        """Assign a task to the most suitable agent."""
            AgentMessage(sender_id="system", content=task, metadata={"type": "task_assignment"})
        )

        return best_agent.config.id

# Global agent manager instance
_agent_manager: Optional[AgentManager] = None

def get_agent_manager() -> AgentManager:
    """Get the global agent manager instance."""