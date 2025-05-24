"""
AI Orchestra Agent Orchestration System - Domain Expert Agents

This module implements the "middle management" tier of domain expert agents that coordinate
specialized worker agents. These domain experts can manage context, delegate tasks, and
aggregate results while communicating through the unified gateway adapter.
"""

import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, Union, Set, Tuple
from enum import Enum
from datetime import datetime

from packages.shared.src.gateway_adapter import get_gateway_adapter, GatewayAdapter
from packages.shared.src.models.base_models import MemoryItem, AgentMessage

# Configure logging
logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Defines the roles that agents can play in the orchestration system."""

    # Core roles
    COORDINATOR = "coordinator"
    RESEARCHER = "researcher"
    EXECUTOR = "executor"
    VALIDATOR = "validator"
    SUMMARIZER = "summarizer"

    # Domain-specific expert roles
    SALES_EXPERT = "sales_expert"
    SERVICE_EXPERT = "service_expert"
    FINANCE_EXPERT = "finance_expert"
    TECH_EXPERT = "tech_expert"
    RESEARCH_EXPERT = "research_expert"

    # Worker roles
    CODER = "coder"
    ANALYST = "analyst"
    DATA_PROCESSOR = "data_processor"
    WEB_RESEARCHER = "web_researcher"
    CRM_INTEGRATOR = "crm_integrator"

    # Utility roles
    MEMORY_MANAGER = "memory_manager"
    ERROR_HANDLER = "error_handler"


class BaseAgent:
    """Base class for all agents in the orchestration system."""

    def __init__(self, agent_id: str, role: AgentRole):
        """Initialize the base agent."""
        self.agent_id = agent_id
        self.role = role
        self.gateway = None  # Will be set during initialization
        self.memory_items: List[MemoryItem] = []
        self.created_at = datetime.now().isoformat()

    async def initialize(self) -> bool:
        """Initialize the agent with required services."""
        try:
            # Get the gateway adapter
            self.gateway = await get_gateway_adapter()
            return True
        except Exception as e:
            logger.error(f"Failed to initialize agent {self.agent_id}: {str(e)}")
            return False

    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process a message and return a response."""
        # Base implementation just returns a simple response
        return AgentMessage(
            content=f"Received message from {message.sender}",
            sender=self.agent_id,
            recipient=message.sender,
            context={},
        )

    async def add_memory(self, memory_item: MemoryItem) -> bool:
        """Add a memory item to the agent's memory."""
        try:
            self.memory_items.append(memory_item)
            return True
        except Exception as e:
            logger.error(f"Failed to add memory to agent {self.agent_id}: {str(e)}")
            return False

    async def get_relevant_memories(self, query: str, limit: int = 5) -> List[MemoryItem]:
        """Get memories relevant to the query."""
        # This would typically use semantic search, but for now just return most recent
        return sorted(self.memory_items, key=lambda x: x.timestamp, reverse=True)[:limit]

    async def generate_completion(self, prompt: str, model: Optional[str] = None, temperature: float = 0.7) -> str:
        """Generate text using the gateway."""
        if not self.gateway:
            raise RuntimeError("Agent not initialized")

        try:
            response = await self.gateway.generate_completion(
                prompt=prompt,
                agent_type=self.role.value,
                model=model,
                temperature=temperature,
            )
            return response.get("text", "")
        except Exception as e:
            logger.error(f"Completion generation failed: {str(e)}")
            return f"Error generating completion: {str(e)}"

    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """Generate chat completion using the gateway."""
        if not self.gateway:
            raise RuntimeError("Agent not initialized")

        try:
            response = await self.gateway.generate_chat_completion(
                messages=messages,
                agent_type=self.role.value,
                model=model,
                temperature=temperature,
            )
            return response.get("message", "")
        except Exception as e:
            logger.error(f"Chat completion generation failed: {str(e)}")
            return f"Error generating chat completion: {str(e)}"

    def log_info(self, message_text: str) -> None:
        # Changed message to logger.info
        logger.info(f"[Agent: {self.agent_id}] {message_text}")

    def log_warning(self, message_text: str) -> None:
        # Changed message to logger.warning
        logger.warning(f"[Agent: {self.agent_id}] {message_text}")

    def log_error(self, message_text: str, exc_info: bool = False) -> None:
        # Changed message to logger.error
        logger.error(f"[Agent: {self.agent_id}] {message_text}", exc_info=exc_info)

    def log_debug(self, message_text: str) -> None:
        # Changed message to logger.debug
        logger.debug(f"[Agent: {self.agent_id}] {message_text}")

    def log_critical(self, message_text: str) -> None:
        # Changed message to logger.critical
        logger.critical(f"[Agent: {self.agent_id}] {message_text}")

    def log_exception(self, message_text: str) -> None:
        # Changed message to logger.exception
        logger.exception(f"[Agent: {self.agent_id}] {message_text}")


class DomainExpertAgent(BaseAgent):
    """
    Domain expert agent that acts as middle management for worker agents.
    It coordinates specialized workers, maintains context, and ensures tasks
    are completed effectively.
    """

    def __init__(self, agent_id: str, role: AgentRole, specialization: str):
        """Initialize the domain expert agent."""
        super().__init__(agent_id, role)
        self.specialization = specialization
        self.workers: Dict[str, BaseAgent] = {}
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.context_store: Dict[str, Any] = {}

    async def initialize(self) -> bool:
        """Initialize the domain expert and its worker agents."""
        # Initialize base functionality
        success = await super().initialize()
        if not success:
            return False

        # Initialize worker agents based on specialization
        try:
            await self._initialize_workers()
            return True
        except Exception as e:
            logger.error(f"Failed to initialize workers for {self.agent_id}: {str(e)}")
            return False

    async def _initialize_workers(self) -> None:
        """Initialize worker agents based on domain specialization."""
        # Different worker configurations based on specialization
        if self.specialization == "sales":
            # Sales domain needs analysts and CRM integrators
            self.workers["analyst"] = WorkerAgent(f"{self.agent_id}_analyst", AgentRole.ANALYST)
            self.workers["crm"] = WorkerAgent(f"{self.agent_id}_crm", AgentRole.CRM_INTEGRATOR)

        elif self.specialization == "research":
            # Research domain needs web researchers and data processors
            self.workers["web_researcher"] = WorkerAgent(f"{self.agent_id}_web_researcher", AgentRole.WEB_RESEARCHER)
            self.workers["data_processor"] = WorkerAgent(f"{self.agent_id}_data_processor", AgentRole.DATA_PROCESSOR)

        elif self.specialization == "tech":
            # Tech domain needs coders and analysts
            self.workers["coder"] = WorkerAgent(f"{self.agent_id}_coder", AgentRole.CODER)
            self.workers["analyst"] = WorkerAgent(f"{self.agent_id}_analyst", AgentRole.ANALYST)

        elif self.specialization == "service":
            # Service domain needs CRM integrators and data processors
            self.workers["crm"] = WorkerAgent(f"{self.agent_id}_crm", AgentRole.CRM_INTEGRATOR)
            self.workers["data_processor"] = WorkerAgent(f"{self.agent_id}_data_processor", AgentRole.DATA_PROCESSOR)

        # Initialize all worker agents
        for worker_id, worker in self.workers.items():
            await worker.initialize()

    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process a message, potentially delegating to worker agents."""
        # Extract task type and content
        task_type = message.context.get("task_type", "general")
        content = message.content

        # Generate a task ID
        task_id = f"task_{len(self.active_tasks) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Store task in active tasks
        self.active_tasks[task_id] = {
            "status": "processing",
            "message": message,
            "created_at": datetime.now().isoformat(),
            "worker_assignments": {},
            "results": [],
        }

        # Generate system prompt for understanding the task
        system_prompt = f"""
        You are a {self.specialization} domain expert. 
        You need to analyze this task and determine the best approach.
        Consider which specialized workers would be best suited for this task.
        Available workers: {', '.join(self.workers.keys())}
        """

        # Generate planning message to determine approach
        planning_messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Task: {content}\nPlease analyze this task and create a plan.",
            },
        ]

        plan = await self.generate_chat_completion(planning_messages)

        # Add plan to task record
        self.active_tasks[task_id]["plan"] = plan

        # Determine which workers to assign based on task
        worker_assignments = await self._determine_worker_assignments(task_type, content, plan)
        self.active_tasks[task_id]["worker_assignments"] = worker_assignments

        # Execute the plan by dispatching to workers
        results = await self._execute_with_workers(task_id, content, worker_assignments)

        # Integrate results
        final_response = await self._integrate_results(task_id, results, message)

        # Update task status
        self.active_tasks[task_id]["status"] = "completed"
        self.active_tasks[task_id]["completed_at"] = datetime.now().isoformat()

        # Return the integrated response
        return AgentMessage(
            content=final_response,
            sender=self.agent_id,
            recipient=message.sender,
            context={"task_id": task_id, "specialization": self.specialization},
        )

    async def _determine_worker_assignments(self, task_type: str, content: str, plan: str) -> Dict[str, List[str]]:
        """Determine which workers to assign to which subtasks."""
        # Create a message to help determine assignments
        messages = [
            {
                "role": "system",
                "content": f"You are a {self.specialization} domain expert. Assign workers to subtasks.",
            },
            {
                "role": "user",
                "content": f"Task: {content}\nPlan: {plan}\nAvailable workers: {list(self.workers.keys())}",
            },
        ]

        # Generate assignments
        assignment_text = await self.generate_chat_completion(messages)

        # Parse assignments - this would be more structured in a real implementation
        # For now, just assign all workers to the task
        return {worker_id: ["full_task"] for worker_id in self.workers.keys()}

    async def _execute_with_workers(
        self, task_id: str, content: str, worker_assignments: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Execute the task with assigned workers."""
        results = {}

        # Create tasks for each worker
        tasks = []
        for worker_id, subtasks in worker_assignments.items():
            if worker_id in self.workers:
                worker = self.workers[worker_id]
                worker_message = AgentMessage(
                    content=content,
                    sender=self.agent_id,
                    recipient=worker.agent_id,
                    context={"task_id": task_id, "subtasks": subtasks},
                )
                tasks.append(self._execute_worker_task(worker, worker_message))

        # Execute all worker tasks in parallel
        worker_results = await asyncio.gather(*tasks)

        # Organize results by worker
        for i, worker_id in enumerate(worker_assignments.keys()):
            if i < len(worker_results):
                results[worker_id] = worker_results[i]

        return results

    async def _execute_worker_task(self, worker: BaseAgent, message: AgentMessage) -> AgentMessage:
        """Execute a task with a specific worker."""
        try:
            return await worker.process_message(message)
        except Exception as e:
            logger.error(f"Worker task execution failed: {str(e)}")
            return AgentMessage(
                content=f"Error executing task: {str(e)}",
                sender=worker.agent_id,
                recipient=message.sender,
                context={"error": str(e)},
            )

    async def _integrate_results(
        self,
        task_id: str,
        worker_results: Dict[str, AgentMessage],
        original_message: AgentMessage,
    ) -> str:
        """Integrate results from workers into a coherent response."""
        # Extract results content from each worker
        results_content = {}
        for worker_id, result in worker_results.items():
            results_content[worker_id] = result.content

        # Format results for the integration prompt
        formatted_results = "\n\n".join(
            [f"{worker_id.upper()} RESULTS:\n{content}" for worker_id, content in results_content.items()]
        )

        # Create integration prompt
        messages = [
            {
                "role": "system",
                "content": f"You are a {self.specialization} domain expert. Integrate these worker results into a coherent response.",
            },
            {
                "role": "user",
                "content": f"ORIGINAL TASK: {original_message.content}\n\nWORKER RESULTS:\n{formatted_results}\n\nPlease integrate these results into a comprehensive, coherent response.",
            },
        ]

        # Generate integrated response
        return await self.generate_chat_completion(messages)

    async def update_context(self, key: str, value: Any) -> None:
        """Update a value in the context store."""
        self.context_store[key] = value

    async def get_context(self, key: str) -> Any:
        """Get a value from the context store."""
        return self.context_store.get(key)


class WorkerAgent(BaseAgent):
    """
    Worker agent that performs specialized tasks as directed by domain experts.
    Different worker types have different capabilities and specializations.
    """

    def __init__(self, agent_id: str, role: AgentRole):
        """Initialize the worker agent."""
        super().__init__(agent_id, role)
        # Additional initialization based on role
        self.capabilities = self._get_capabilities_for_role(role)

    def _get_capabilities_for_role(self, role: AgentRole) -> Set[str]:
        """Get the capabilities for a specific role."""
        # Define capabilities for each role
        capabilities_map = {
            AgentRole.ANALYST: {"data_analysis", "trend_identification", "reporting"},
            AgentRole.CODER: {"code_generation", "code_review", "debugging"},
            AgentRole.DATA_PROCESSOR: {
                "data_cleaning",
                "data_transformation",
                "data_validation",
            },
            AgentRole.WEB_RESEARCHER: {
                "web_search",
                "data_extraction",
                "source_validation",
            },
            AgentRole.CRM_INTEGRATOR: {
                "crm_query",
                "customer_analysis",
                "sales_forecasting",
            },
        }

        return capabilities_map.get(role, set())

    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process a task message from a domain expert."""
        # Extract task and context
        content = message.content
        subtasks = message.context.get("subtasks", [])

        # Select appropriate prompt based on role
        if self.role == AgentRole.ANALYST:
            return await self._process_analyst_task(content, subtasks)
        elif self.role == AgentRole.CODER:
            return await self._process_coder_task(content, subtasks)
        elif self.role == AgentRole.DATA_PROCESSOR:
            return await self._process_data_processor_task(content, subtasks)
        elif self.role == AgentRole.WEB_RESEARCHER:
            return await self._process_web_researcher_task(content, subtasks)
        elif self.role == AgentRole.CRM_INTEGRATOR:
            return await self._process_crm_task(content, subtasks)
        else:
            # Generic processing for other roles
            return await self._process_generic_task(content, subtasks)

    async def _process_analyst_task(self, content: str, subtasks: List[str]) -> AgentMessage:
        """Process an analyst task."""
        system_prompt = """
        You are a data analyst specialized in business intelligence.
        Analyze the given data or request and provide insights, trends, and recommendations.
        Focus on actionable insights that can drive business decisions.
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Task: {content}\nPlease analyze this and provide insights.",
            },
        ]

        analysis = await self.generate_chat_completion(messages)

        return AgentMessage(
            content=analysis,
            sender=self.agent_id,
            recipient=message.sender,
            context={"role": "analyst", "capabilities": list(self.capabilities)},
        )

    async def _process_coder_task(self, content: str, subtasks: List[str]) -> AgentMessage:
        """Process a coder task."""
        system_prompt = """
        You are an expert software developer.
        Generate high-quality, well-documented code based on the requirements.
        Follow best practices for the language/framework involved.
        Explain your implementation choices.
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Coding Task: {content}\nPlease implement this.",
            },
        ]

        code_result = await self.generate_chat_completion(messages)

        return AgentMessage(
            content=code_result,
            sender=self.agent_id,
            recipient=message.sender,
            context={"role": "coder", "capabilities": list(self.capabilities)},
        )

    async def _process_data_processor_task(self, content: str, subtasks: List[str]) -> AgentMessage:
        """Process a data processor task."""
        system_prompt = """
        You are a data processing specialist.
        Your job is to clean, transform, and validate data according to requirements.
        Explain the processing steps you've applied and any issues encountered.
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Data Processing Task: {content}\nPlease process this data.",
            },
        ]

        processing_result = await self.generate_chat_completion(messages)

        return AgentMessage(
            content=processing_result,
            sender=self.agent_id,
            recipient=message.sender,
            context={"role": "data_processor", "capabilities": list(self.capabilities)},
        )

    async def _process_web_researcher_task(self, content: str, subtasks: List[str]) -> AgentMessage:
        """Process a web researcher task."""
        system_prompt = """
        You are a web research specialist.
        Your job is to find, extract, and synthesize information from various online sources.
        Evaluate source credibility and provide accurate information with citations.
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Research Task: {content}\nPlease research this topic.",
            },
        ]

        research_result = await self.generate_chat_completion(messages)

        return AgentMessage(
            content=research_result,
            sender=self.agent_id,
            recipient=message.sender,
            context={"role": "web_researcher", "capabilities": list(self.capabilities)},
        )

    async def _process_crm_task(self, content: str, subtasks: List[str]) -> AgentMessage:
        """Process a CRM integration task."""
        system_prompt = """
        You are a CRM integration specialist.
        Your job is to analyze customer data, identify sales opportunities, and provide
        insights for improving customer relationships and sales performance.
        Focus on practical, actionable recommendations.
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"CRM Task: {content}\nPlease analyze this customer data.",
            },
        ]

        crm_result = await self.generate_chat_completion(messages)

        return AgentMessage(
            content=crm_result,
            sender=self.agent_id,
            recipient=message.sender,
            context={"role": "crm_integrator", "capabilities": list(self.capabilities)},
        )

    async def _process_generic_task(self, content: str, subtasks: List[str]) -> AgentMessage:
        """Process a generic task for other roles."""
        system_prompt = f"""
        You are a specialized worker with the following capabilities: {', '.join(self.capabilities)}.
        Complete the assigned task using your expertise.
        Provide a detailed explanation of your process and results.
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Task: {content}\nPlease complete this task."},
        ]

        result = await self.generate_chat_completion(messages)

        return AgentMessage(
            content=result,
            sender=self.agent_id,
            recipient=message.sender,
            context={"role": self.role.value, "capabilities": list(self.capabilities)},
        )


class AgentOrchestrator:
    """
    Main orchestrator that manages domain expert agents and routes user requests
    to the appropriate experts. It maintains the overall context and handles
    communication between user and agents.
    """

    def __init__(self):
        """Initialize the agent orchestrator."""
        self.domain_experts: Dict[str, DomainExpertAgent] = {}
        self.conversation_history: Dict[str, List[Dict[str, Any]]] = {}
        self.gateway = None

    async def initialize(self) -> bool:
        """Initialize the orchestrator and domain experts."""
        try:
            # Initialize gateway connection
            self.gateway = await get_gateway_adapter()

            # Initialize domain experts
            await self._initialize_domain_experts()

            return True
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {str(e)}")
            return False

    async def _initialize_domain_experts(self) -> None:
        """Initialize the domain expert agents."""
        # Initialize sales expert
        sales_expert = DomainExpertAgent("sales_expert", AgentRole.SALES_EXPERT, "sales")
        await sales_expert.initialize()
        self.domain_experts["sales"] = sales_expert

        # Initialize service expert
        service_expert = DomainExpertAgent("service_expert", AgentRole.SERVICE_EXPERT, "service")
        await service_expert.initialize()
        self.domain_experts["service"] = service_expert

        # Initialize tech expert
        tech_expert = DomainExpertAgent("tech_expert", AgentRole.TECH_EXPERT, "tech")
        await tech_expert.initialize()
        self.domain_experts["tech"] = tech_expert

        # Initialize research expert
        research_expert = DomainExpertAgent("research_expert", AgentRole.RESEARCH_EXPERT, "research")
        await research_expert.initialize()
        self.domain_experts["research"] = research_expert

    async def process_user_message(self, user_id: str, message: str, session_id: str = None) -> Dict[str, Any]:
        """Process a user message and return a response."""
        # Generate a session ID if not provided
        if not session_id:
            session_id = f"session_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Initialize conversation history for this session if needed
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []

        # Add user message to history
        self.conversation_history[session_id].append(
            {
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Determine which domain expert should handle this message
        domain = await self._determine_domain(message, self.conversation_history[session_id])

        # Create a message for the domain expert
        expert_message = AgentMessage(
            content=message,
            sender=user_id,
            recipient=f"{domain}_expert",
            context={"session_id": session_id},
        )

        # Process with the selected domain expert
        if domain in self.domain_experts:
            expert = self.domain_experts[domain]
            response = await expert.process_message(expert_message)

            # Add response to conversation history
            self.conversation_history[session_id].append(
                {
                    "role": "assistant",
                    "content": response.content,
                    "domain": domain,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Return formatted response
            return {
                "message": response.content,
                "session_id": session_id,
                "domain": domain,
                "context": response.context,
            }
        else:
            # Fallback if domain expert not found
            error_message = f"No domain expert available for {domain}"
            logger.error(error_message)

            # Add error to conversation history
            self.conversation_history[session_id].append(
                {
                    "role": "system",
                    "content": error_message,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            return {
                "message": "I apologize, but I'm unable to process your request at this time.",
                "session_id": session_id,
                "error": error_message,
            }

    async def _determine_domain(self, message: str, conversation_history: List[Dict[str, Any]]) -> str:
        """Determine which domain this message belongs to."""
        # Format conversation history for context
        formatted_history = "\n".join(
            [
                f"{item['role'].upper()}: {item['content']}"
                for item in conversation_history[-5:]  # Include last 5 messages for context
            ]
        )

        # Create prompt for domain classification
        messages = [
            {
                "role": "system",
                "content": "You are a message router. Determine which domain expert should handle this request. Choose from: sales, service, tech, research. Respond with just the domain name in lowercase.",
            },
            {
                "role": "user",
                "content": f"Recent conversation:\n{formatted_history}\n\nNew message: {message}\n\nWhich domain should handle this?",
            },
        ]

        # Get domain classification
        try:
            domain_response = await self.gateway.generate_chat_completion(
                messages=messages,
                agent_type="coordinator",
                temperature=0.3,  # Lower temperature for more deterministic routing
            )

            # Extract domain from response
            domain = domain_response.get("message", "").strip().lower()

            # Validate domain is one of our experts
            valid_domains = ["sales", "service", "tech", "research"]
            if domain not in valid_domains:
                # Default to research if unclear
                logger.warning(f"Invalid domain classification: {domain}, defaulting to research")
                domain = "research"

            return domain
        except Exception as e:
            logger.error(f"Domain classification failed: {str(e)}")
            # Default to research as fallback
            return "research"
