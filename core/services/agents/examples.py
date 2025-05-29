"""
Example agent implementations for Orchestra AI.

This module provides concrete agent examples that demonstrate
different agent capabilities and behaviors.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from core.business.llm.provider import LLMRequest, get_llm_service
from core.business.personas.base import PersonaTrait, ResponseStyle, get_persona_manager
from core.services.agents.base import Agent, AgentCapability, AgentConfig, AgentMessage, get_agent_manager

logger = logging.getLogger(__name__)


class ConversationalAgent(Agent):
    """Agent specialized in natural conversations."""

    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process conversation messages."""
        # Check if this is a conversation request
        if message.metadata.get("type") != "conversation":
            return None

        llm_service = get_llm_service()
        persona_manager = get_persona_manager()

        # Get conversational persona
        persona = persona_manager.get_persona("conversationalist")
        if not persona:
            # Create default conversational persona
            from core.business.personas.base import PersonaConfig

            persona = PersonaConfig(
                id="conversationalist",
                name="Friendly Assistant",
                description="A helpful and friendly conversational partner",
                traits=[
                    PersonaTrait.FRIENDLY,
                    PersonaTrait.HELPFUL,
                    PersonaTrait.EMPATHETIC,
                ],
                style=ResponseStyle.CONVERSATIONAL,
            )

        # Generate response
        response = await llm_service.complete_with_persona(prompt=message.content, persona=persona)

        # Remember the conversation
        await self.remember(
            key=f"conversation:{message.id}",
            value={
                "user_message": message.content,
                "agent_response": response.text,
                "timestamp": message.timestamp,
            },
        )

        return AgentMessage(
            sender_id=self.config.id,
            content=response.text,
            metadata={"type": "conversation_response"},
        )

    async def think(self) -> None:
        """Think about conversation patterns and user preferences."""
        # Analyze recent conversations
        recent_conversations = await self.recall("conversation:", limit=20)

        if recent_conversations:
            # Could analyze patterns, sentiment, topics, etc.
            logger.debug(f"Analyzed {len(recent_conversations)} recent conversations")

    async def act(self) -> None:
        """No autonomous actions for conversational agent."""
        pass


class TaskExecutorAgent(Agent):
    """Agent specialized in executing specific tasks."""

    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process task execution requests."""
        message_type = message.metadata.get("type")

        if message_type == "task_assignment":
            # Execute assigned task
            task_result = await self._execute_task(message.content, message.metadata)

            return AgentMessage(
                sender_id=self.config.id,
                content=f"Task completed: {task_result}",
                metadata={"type": "task_result", "result": task_result},
            )

        elif message_type == "workflow_request":
            # Execute workflow
            workflow_name = message.metadata.get("workflow_name")
            inputs = message.metadata.get("inputs", {})

            if workflow_name in self.config.workflow_names:
                context = await self.execute_workflow(workflow_name, inputs)

                return AgentMessage(
                    sender_id=self.config.id,
                    content=f"Workflow '{workflow_name}' completed",
                    metadata={
                        "type": "workflow_result",
                        "workflow_id": str(context.workflow_id),
                        "outputs": context.outputs,
                    },
                )

        return None

    async def think(self) -> None:
        """Think about task optimization and resource allocation."""
        # Check active workflows
        if len(self.state.active_workflows) > self.config.max_concurrent_tasks * 0.8:
            logger.warning(f"Agent {self.config.name} approaching task limit")

    async def act(self) -> None:
        """Check for pending tasks and optimize execution."""
        # Could implement task queue optimization, resource management, etc.
        pass

    async def _execute_task(self, task: str, metadata: Dict[str, Any]) -> Any:
        """Execute a specific task."""
        task_type = metadata.get("task_type", "generic")

        if task_type == "data_processing":
            # Simulate data processing
            await self.remember("task:processed", {"task": task, "status": "completed"})
            return {"processed_items": 100, "duration": "2.5s"}

        elif task_type == "analysis":
            # Use LLM for analysis
            llm_service = get_llm_service()
            request = LLMRequest(prompt=f"Analyze the following: {task}", max_tokens=500)
            response = await llm_service.complete(request)
            return {"analysis": response.text}

        else:
            # Generic task execution
            return {"task": task, "status": "completed"}


class ResearchAgent(Agent):
    """Agent specialized in research and information gathering."""

    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process research requests."""
        if message.metadata.get("type") != "research_request":
            return None

        topic = message.content
        depth = message.metadata.get("depth", "standard")

        # Perform research
        research_results = await self._research_topic(topic, depth)

        # Store research results
        await self.remember(
            key=f"research:{topic}",
            value=research_results,
            metadata={"topic": topic, "depth": depth},
        )

        return AgentMessage(
            sender_id=self.config.id,
            content=f"Research completed on '{topic}'",
            metadata={"type": "research_results", "results": research_results},
        )

    async def think(self) -> None:
        """Think about research strategies and knowledge gaps."""
        # Could analyze research patterns, identify knowledge gaps, etc.
        pass

    async def act(self) -> None:
        """Proactively research trending topics."""
        # Could implement autonomous research based on patterns
        pass

    async def _research_topic(self, topic: str, depth: str) -> Dict[str, Any]:
        """Research a specific topic."""
        llm_service = get_llm_service()

        # Generate research queries
        queries = await self._generate_research_queries(topic, depth)

        # Gather information
        results = []
        for query in queries:
            request = LLMRequest(
                prompt=f"Provide detailed information about: {query}",
                max_tokens=1000,
                temperature=0.3,
            )
            response = await llm_service.complete(request)
            results.append({"query": query, "findings": response.text})

        # Synthesize results
        synthesis_request = LLMRequest(
            prompt=f"Synthesize the following research findings about '{topic}':\n\n"
            + "\n\n".join([f"Query: {r['query']}\nFindings: {r['findings']}" for r in results]),
            max_tokens=1500,
            temperature=0.5,
        )
        synthesis = await llm_service.complete(synthesis_request)

        return {
            "topic": topic,
            "queries": queries,
            "raw_findings": results,
            "synthesis": synthesis.text,
            "depth": depth,
        }

    async def _generate_research_queries(self, topic: str, depth: str) -> List[str]:
        """Generate research queries based on topic and depth."""
        llm_service = get_llm_service()

        num_queries = 3 if depth == "standard" else 5 if depth == "deep" else 2

        request = LLMRequest(
            prompt=f"Generate {num_queries} specific research queries for the topic '{topic}'. "
            + "Return as a numbered list.",
            max_tokens=200,
            temperature=0.7,
        )

        response = await llm_service.complete(request)

        # Parse queries from response
        queries = []
        for line in response.text.split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                # Remove numbering/bullets
                query = line.lstrip("0123456789.-) ").strip()
                if query:
                    queries.append(query)

        return queries[:num_queries]


class CollaborativeAgent(Agent):
    """Agent that coordinates with other agents."""

    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process collaboration requests."""
        message_type = message.metadata.get("type")

        if message_type == "collaboration_request":
            task = message.metadata.get("task")
            context = message.metadata.get("context", {})

            # Coordinate task execution
            result = await self._coordinate_task(task, context)

            return AgentMessage(
                sender_id=self.config.id,
                content=f"Collaboration completed: {task}",
                metadata={"type": "collaboration_result", "result": result},
            )

        return None

    async def think(self) -> None:
        """Think about collaboration strategies."""
        # Analyze agent capabilities and workloads
        agent_manager = get_agent_manager()
        agents = agent_manager.list_agents()

        # Could optimize agent assignments based on capabilities and workload
        logger.debug(f"Monitoring {len(agents)} agents for collaboration")

    async def act(self) -> None:
        """Proactively identify collaboration opportunities."""
        # Could analyze pending tasks and suggest collaborations
        pass

    async def _coordinate_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate task execution across multiple agents."""
        agent_manager = get_agent_manager()

        # Determine required capabilities
        required_capabilities = self._analyze_task_requirements(task)

        # Assign subtasks to agents
        assignments = {}
        for capability in required_capabilities:
            agent_id = await agent_manager.assign_task(
                task=f"Subtask for {task}: {capability.value}",
                required_capability=capability,
            )
            if agent_id:
                assignments[capability.value] = agent_id

        # Wait for results (simplified)
        await asyncio.sleep(2)

        return {"task": task, "assignments": assignments, "status": "completed"}

    def _analyze_task_requirements(self, task: str) -> List[AgentCapability]:
        """Analyze task to determine required capabilities."""
        # Simple keyword-based analysis
        task_lower = task.lower()

        capabilities = []

        if any(word in task_lower for word in ["analyze", "research", "investigate"]):
            capabilities.append(AgentCapability.RESEARCH)

        if any(word in task_lower for word in ["create", "generate", "design"]):
            capabilities.append(AgentCapability.CREATIVITY)

        if any(word in task_lower for word in ["plan", "organize", "schedule"]):
            capabilities.append(AgentCapability.PLANNING)

        if any(word in task_lower for word in ["execute", "implement", "perform"]):
            capabilities.append(AgentCapability.TASK_EXECUTION)

        # Default to task execution if no specific capability identified
        if not capabilities:
            capabilities.append(AgentCapability.TASK_EXECUTION)

        return capabilities


def create_example_agents() -> List[Agent]:
    """Create example agent instances."""
    agents = []

    # Conversational Agent
    conv_agent = ConversationalAgent(
        AgentConfig(
            id="conv_agent_1",
            name="Friendly Conversationalist",
            description="Engages in natural conversations with users",
            capabilities={AgentCapability.CONVERSATION},
            persona_id="conversationalist",
            workflow_names=["conversation_workflow"],
        )
    )
    agents.append(conv_agent)

    # Task Executor Agent
    task_agent = TaskExecutorAgent(
        AgentConfig(
            id="task_agent_1",
            name="Efficient Task Executor",
            description="Executes various tasks and workflows",
            capabilities={AgentCapability.TASK_EXECUTION, AgentCapability.ANALYSIS},
            workflow_names=["document_analysis", "data_processing"],
        )
    )
    agents.append(task_agent)

    # Research Agent
    research_agent = ResearchAgent(
        AgentConfig(
            id="research_agent_1",
            name="Knowledge Researcher",
            description="Researches topics and gathers information",
            capabilities={AgentCapability.RESEARCH, AgentCapability.ANALYSIS},
            workflow_names=["research_workflow"],
        )
    )
    agents.append(research_agent)

    # Collaborative Agent
    collab_agent = CollaborativeAgent(
        AgentConfig(
            id="collab_agent_1",
            name="Team Coordinator",
            description="Coordinates tasks across multiple agents",
            capabilities={AgentCapability.COLLABORATION, AgentCapability.PLANNING},
            collaboration_enabled=True,
        )
    )
    agents.append(collab_agent)

    return agents


def register_example_agents() -> None:
    """Register all example agents with the manager."""
    agent_manager = get_agent_manager()

    agents = create_example_agents()
    for agent in agents:
        agent_manager.register_agent(agent)

    logger.info(f"Registered {len(agents)} example agents")
