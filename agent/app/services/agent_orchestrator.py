"""
Agent Orchestrator for Managing Multi-Agent Workflows

This module implements the orchestration layer that coordinates:
- Inter-agent communication
- Parallel task execution
- Shared knowledge bases
- Workflow state management
- Performance monitoring
"""

import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict
import networkx as nx

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from agent.app.services.specialized_agents import (
    get_specialized_agent,
    AgentType,
    BaseSpecializedAgent
)
from core.llm_intelligent_router import get_intelligent_llm_router
from agent.app.core.database import get_db

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TaskStatus(Enum):
    """Individual task status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


@dataclass
class WorkflowTask:
    """Individual task in a workflow"""
    id: str
    agent_type: AgentType
    task_data: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class Workflow:
    """Workflow definition and state"""
    id: str
    name: str
    tasks: Dict[str, WorkflowTask]
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    context: Dict[str, Any] = field(default_factory=dict)
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)


class CircuitBreaker:
    """Circuit breaker for external service calls"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.is_open = False
    
    def record_success(self):
        """Record successful call"""
        self.failure_count = 0
        self.is_open = False
    
    def record_failure(self):
        """Record failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.is_open = True
    
    def can_execute(self) -> bool:
        """Check if circuit allows execution"""
        if not self.is_open:
            return True
        
        # Check if recovery timeout has passed
        if self.last_failure_time:
            time_since_failure = (datetime.utcnow() - self.last_failure_time).seconds
            if time_since_failure > self.recovery_timeout:
                self.is_open = False
                self.failure_count = 0
                return True
        
        return False


class AgentOrchestrator:
    """
    Main orchestrator for coordinating multi-agent workflows
    """
    
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.agent_pool: Dict[AgentType, List[BaseSpecializedAgent]] = defaultdict(list)
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.shared_context: Dict[str, Any] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.llm_router = get_intelligent_llm_router()
        
        # Redis for distributed state
        self.redis_client = None
        self._init_redis()
        
        # Performance metrics
        self.metrics = {
            "workflows_completed": 0,
            "tasks_completed": 0,
            "average_task_duration": 0,
            "agent_utilization": defaultdict(float)
        }
        
        # Start background workers
        asyncio.create_task(self._message_processor())
        asyncio.create_task(self._health_monitor())
    
    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                decode_responses=True
            )
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
    
    async def create_workflow(
        self,
        name: str,
        tasks: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Workflow:
        """Create a new workflow with dependency resolution"""
        
        workflow_id = str(uuid.uuid4())
        workflow_tasks = {}
        
        # Create task objects
        for task_def in tasks:
            task = WorkflowTask(
                id=task_def["id"],
                agent_type=AgentType(task_def["agent_type"]),
                task_data=task_def["data"],
                dependencies=task_def.get("dependencies", [])
            )
            workflow_tasks[task.id] = task
        
        # Validate dependencies
        self._validate_dependencies(workflow_tasks)
        
        # Create workflow
        workflow = Workflow(
            id=workflow_id,
            name=name,
            tasks=workflow_tasks,
            context=context or {}
        )
        
        self.workflows[workflow_id] = workflow
        
        # Store in Redis
        if self.redis_client:
            await self.redis_client.hset(
                "workflows",
                workflow_id,
                json.dumps({
                    "name": workflow.name,
                    "status": workflow.status.value,
                    "created_at": workflow.created_at.isoformat(),
                    "task_count": len(workflow.tasks)
                })
            )
        
        return workflow
    
    def _validate_dependencies(self, tasks: Dict[str, WorkflowTask]):
        """Validate task dependencies form a DAG"""
        
        # Build dependency graph
        graph = nx.DiGraph()
        for task_id, task in tasks.items():
            graph.add_node(task_id)
            for dep in task.dependencies:
                if dep not in tasks:
                    raise ValueError(f"Task {task_id} depends on unknown task {dep}")
                graph.add_edge(dep, task_id)
        
        # Check for cycles
        if not nx.is_directed_acyclic_graph(graph):
            raise ValueError("Task dependencies contain cycles")
    
    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute a workflow with parallel task execution"""
        
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.utcnow()
        
        try:
            # Build execution plan
            execution_plan = self._build_execution_plan(workflow)
            
            # Execute tasks in parallel batches
            for batch in execution_plan:
                await self._execute_task_batch(workflow, batch)
                
                # Create checkpoint after each batch
                await self._create_checkpoint(workflow)
            
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.utcnow()
            
            # Update metrics
            self.metrics["workflows_completed"] += 1
            
            return {
                "workflow_id": workflow_id,
                "status": "completed",
                "duration": (workflow.completed_at - workflow.started_at).total_seconds(),
                "results": {
                    task_id: task.result
                    for task_id, task in workflow.tasks.items()
                    if task.result
                }
            }
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            logger.error(f"Workflow {workflow_id} failed: {e}")
            raise
    
    def _build_execution_plan(self, workflow: Workflow) -> List[List[str]]:
        """Build parallel execution plan based on dependencies"""
        
        # Build dependency graph
        graph = nx.DiGraph()
        for task_id, task in workflow.tasks.items():
            graph.add_node(task_id)
            for dep in task.dependencies:
                graph.add_edge(dep, task_id)
        
        # Topological sort to get execution order
        execution_order = list(nx.topological_sort(graph))
        
        # Group tasks that can run in parallel
        batches = []
        processed = set()
        
        for task_id in execution_order:
            if task_id in processed:
                continue
            
            # Find all tasks that can run in parallel with this one
            batch = [task_id]
            processed.add(task_id)
            
            for other_id in execution_order:
                if other_id in processed:
                    continue
                
                # Check if all dependencies are satisfied
                task = workflow.tasks[other_id]
                if all(dep in processed or dep in batch for dep in task.dependencies):
                    batch.append(other_id)
                    processed.add(other_id)
            
            batches.append(batch)
        
        return batches
    
    async def _execute_task_batch(
        self,
        workflow: Workflow,
        task_ids: List[str]
    ):
        """Execute a batch of tasks in parallel"""
        
        tasks = []
        for task_id in task_ids:
            task = workflow.tasks[task_id]
            if task.status == TaskStatus.COMPLETED:
                continue
            
            tasks.append(self._execute_single_task(workflow, task))
        
        # Execute all tasks in parallel
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_single_task(
        self,
        workflow: Workflow,
        task: WorkflowTask
    ):
        """Execute a single task with retry logic"""
        
        # Check circuit breaker
        breaker_key = f"{task.agent_type.value}:{task.task_data.get('type', 'default')}"
        breaker = self.circuit_breakers.get(breaker_key)
        if not breaker:
            breaker = CircuitBreaker()
            self.circuit_breakers[breaker_key] = breaker
        
        if not breaker.can_execute():
            task.status = TaskStatus.FAILED
            task.error = "Circuit breaker open"
            return
        
        # Execute with retries
        for attempt in range(task.max_retries + 1):
            try:
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.utcnow()
                
                # Get agent
                agent = await get_specialized_agent(task.agent_type.value)
                
                # Inject workflow context
                task_data_with_context = {
                    **task.task_data,
                    "workflow_context": workflow.context,
                    "shared_context": self.shared_context
                }
                
                # Execute task
                result = await agent.process_task(task_data_with_context)
                
                # Record success
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.completed_at = datetime.utcnow()
                breaker.record_success()
                
                # Update metrics
                self.metrics["tasks_completed"] += 1
                task_duration = (task.completed_at - task.started_at).total_seconds()
                self._update_average_duration(task_duration)
                
                # Send completion message
                await self.message_queue.put({
                    "type": "task_completed",
                    "workflow_id": workflow.id,
                    "task_id": task.id,
                    "result": result
                })
                
                return
                
            except Exception as e:
                task.retry_count = attempt + 1
                task.error = str(e)
                breaker.record_failure()
                
                if attempt < task.max_retries:
                    task.status = TaskStatus.RETRYING
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    task.status = TaskStatus.FAILED
                    logger.error(f"Task {task.id} failed after {task.retry_count} attempts: {e}")
    
    def _update_average_duration(self, new_duration: float):
        """Update rolling average task duration"""
        current_avg = self.metrics["average_task_duration"]
        total_tasks = self.metrics["tasks_completed"]
        
        if total_tasks == 1:
            self.metrics["average_task_duration"] = new_duration
        else:
            self.metrics["average_task_duration"] = (
                (current_avg * (total_tasks - 1) + new_duration) / total_tasks
            )
    
    async def _create_checkpoint(self, workflow: Workflow):
        """Create workflow checkpoint for recovery"""
        
        checkpoint = {
            "timestamp": datetime.utcnow().isoformat(),
            "task_states": {
                task_id: {
                    "status": task.status.value,
                    "result": task.result,
                    "error": task.error
                }
                for task_id, task in workflow.tasks.items()
            },
            "context": workflow.context
        }
        
        workflow.checkpoints.append(checkpoint)
        
        # Store in Redis
        if self.redis_client:
            await self.redis_client.hset(
                f"workflow_checkpoints:{workflow.id}",
                checkpoint["timestamp"],
                json.dumps(checkpoint)
            )
    
    async def recover_workflow(
        self,
        workflow_id: str,
        checkpoint_timestamp: Optional[str] = None
    ) -> Workflow:
        """Recover workflow from checkpoint"""
        
        if not self.redis_client:
            raise RuntimeError("Redis not available for recovery")
        
        # Get workflow metadata
        workflow_data = await self.redis_client.hget("workflows", workflow_id)
        if not workflow_data:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Get checkpoints
        checkpoints = await self.redis_client.hgetall(f"workflow_checkpoints:{workflow_id}")
        if not checkpoints:
            raise ValueError(f"No checkpoints found for workflow {workflow_id}")
        
        # Select checkpoint
        if checkpoint_timestamp:
            checkpoint_data = checkpoints.get(checkpoint_timestamp)
        else:
            # Get latest checkpoint
            latest_timestamp = max(checkpoints.keys())
            checkpoint_data = checkpoints[latest_timestamp]
        
        checkpoint = json.loads(checkpoint_data)
        
        # Reconstruct workflow
        # (Implementation would restore full workflow state)
        
        logger.info(f"Recovered workflow {workflow_id} from checkpoint {checkpoint['timestamp']}")
    
    async def _message_processor(self):
        """Process inter-agent messages"""
        
        while True:
            try:
                message = await self.message_queue.get()
                
                # Route message based on type
                if message["type"] == "task_completed":
                    # Update shared context with results
                    task_id = message["task_id"]
                    result = message["result"]
                    
                    if isinstance(result, dict) and "shared_data" in result:
                        self.shared_context.update(result["shared_data"])
                
                elif message["type"] == "agent_communication":
                    # Forward message to target agent
                    target_agent = message["target"]
                    data = message["data"]
                    # Implementation for agent-to-agent messaging
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
            
            await asyncio.sleep(0.1)
    
    async def _health_monitor(self):
        """Monitor agent health and performance"""
        
        while True:
            try:
                # Check all agents
                for agent_type in AgentType:
                    agent = await get_specialized_agent(agent_type.value)
                    status = await agent.get_status()
                    
                    # Update utilization metrics
                    if status["status"] == "active":
                        self.metrics["agent_utilization"][agent_type.value] += 1
                
                # Check circuit breakers
                for key, breaker in self.circuit_breakers.items():
                    if breaker.is_open:
                        logger.warning(f"Circuit breaker {key} is open")
                
                # Log metrics
                logger.info(f"Orchestrator metrics: {self.metrics}")
                
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get detailed workflow status"""
        
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Calculate progress
        total_tasks = len(workflow.tasks)
        completed_tasks = sum(
            1 for task in workflow.tasks.values()
            if task.status == TaskStatus.COMPLETED
        )
        
        return {
            "workflow_id": workflow_id,
            "name": workflow.name,
            "status": workflow.status.value,
            "progress": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "created_at": workflow.created_at.isoformat(),
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "tasks": {
                task_id: {
                    "status": task.status.value,
                    "agent_type": task.agent_type.value,
                    "error": task.error,
                    "retry_count": task.retry_count
                }
                for task_id, task in workflow.tasks.items()
            },
            "checkpoints": len(workflow.checkpoints)
        }
    
    async def cancel_workflow(self, workflow_id: str):
        """Cancel a running workflow"""
        
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        if workflow.status != WorkflowStatus.RUNNING:
            raise ValueError(f"Workflow {workflow_id} is not running")
        
        workflow.status = WorkflowStatus.CANCELLED
        
        # Cancel all pending tasks
        for task in workflow.tasks.values():
            if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                task.status = TaskStatus.SKIPPED
        
        logger.info(f"Cancelled workflow {workflow_id}")


# Singleton instance
_orchestrator_instance: Optional[AgentOrchestrator] = None


def get_agent_orchestrator() -> AgentOrchestrator:
    """Get or create the singleton orchestrator instance"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = AgentOrchestrator()
    return _orchestrator_instance


# Example workflow definitions

async def create_comprehensive_search_workflow(
    user_id: str,
    search_query: str,
    include_medical: bool = False
) -> Workflow:
    """Create a comprehensive search workflow using multiple agents"""
    
    orchestrator = get_agent_orchestrator()
    
    tasks = [
        {
            "id": "personal_search",
            "agent_type": "personal",
            "data": {
                "type": "search",
                "user_id": user_id,
                "query": search_query,
                "search_type": "comprehensive"
            },
            "dependencies": []
        }
    ]
    
    if include_medical:
        tasks.append({
            "id": "medical_search",
            "agent_type": "paragon_medical",
            "data": {
                "type": "search_literature",
                "query": search_query,
                "filters": {"recent": True}
            },
            "dependencies": []
        })
    
    # Analysis task depends on search results
    tasks.append({
        "id": "analyze_results",
        "agent_type": "personal",
        "data": {
            "type": "analyze",
            "user_id": user_id,
            "analyze_type": "search_synthesis"
        },
        "dependencies": ["personal_search"] + (["medical_search"] if include_medical else [])
    })
    
    workflow = await orchestrator.create_workflow(
        name=f"Comprehensive Search: {search_query[:50]}",
        tasks=tasks,
        context={"user_id": user_id, "original_query": search_query}
    )
    
    return workflow