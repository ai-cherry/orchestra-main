#!/usr/bin/env python3
"""
AI Orchestrator - Coordinates between EigenCode, Cursor AI, and Roo Code
Implements workflow orchestration with MCP context management and PostgreSQL logging
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import subprocess
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

import psycopg2
from psycopg2.extras import RealDictCursor
import aiohttp
from weaviate import Client
from weaviate.auth import AuthApiKey

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_components/logs/orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRole(Enum):
    """Agent roles in the orchestration"""
    ANALYZER = "analyzer"  # EigenCode
    IMPLEMENTER = "implementer"  # Cursor AI
    REFINER = "refiner"  # Roo Code


@dataclass
class WorkflowContext:
    """Workflow execution context"""
    workflow_id: str
    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class TaskDefinition:
    """Atomic task definition"""
    task_id: str
    name: str
    agent_role: AgentRole
    inputs: Dict[str, Any]
    outputs: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    priority: int = 0
    timeout: int = 300  # seconds


class SecretManager:
    """Manages GitHub Secrets and environment variables"""
    
    @staticmethod
    def get_secret(key: str) -> Optional[str]:
        """Get secret from environment (GitHub Secrets are injected as env vars)"""
        return os.environ.get(key)
    
    @staticmethod
    def get_required_secret(key: str) -> str:
        """Get required secret, raise if not found"""
        value = os.environ.get(key)
        if not value:
            raise ValueError(f"Required secret '{key}' not found in environment")
        return value


class DatabaseLogger:
    """PostgreSQL logging for all orchestration actions"""
    
    def __init__(self):
        self.connection_params = {
            'host': SecretManager.get_required_secret('POSTGRES_HOST'),
            'port': SecretManager.get_secret('POSTGRES_PORT') or 5432,
            'database': SecretManager.get_required_secret('POSTGRES_DB'),
            'user': SecretManager.get_required_secret('POSTGRES_USER'),
            'password': SecretManager.get_required_secret('POSTGRES_PASSWORD')
        }
        self._ensure_tables()
    
    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.connection_params)
    
    def _ensure_tables(self):
        """Ensure logging tables exist"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS orchestration_logs (
                        id SERIAL PRIMARY KEY,
                        workflow_id VARCHAR(255),
                        task_id VARCHAR(255),
                        agent_role VARCHAR(50),
                        action VARCHAR(100),
                        status VARCHAR(50),
                        metadata JSONB,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_workflow_id ON orchestration_logs(workflow_id);
                    CREATE INDEX IF NOT EXISTS idx_task_id ON orchestration_logs(task_id);
                    CREATE INDEX IF NOT EXISTS idx_created_at ON orchestration_logs(created_at);
                """)
                conn.commit()
    
    def log_action(self, workflow_id: str, task_id: str, agent_role: str, 
                   action: str, status: str, metadata: Dict = None, error: str = None):
        """Log an orchestration action"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO orchestration_logs 
                    (workflow_id, task_id, agent_role, action, status, metadata, error_message)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    workflow_id, task_id, agent_role, action, status,
                    json.dumps(metadata or {}), error
                ))
                conn.commit()


class WeaviateManager:
    """Manages Weaviate Cloud interactions for context storage"""
    
    def __init__(self):
        self.client = Client(
            url=SecretManager.get_required_secret('WEAVIATE_URL'),
            auth_client_secret=AuthApiKey(
                api_key=SecretManager.get_required_secret('WEAVIATE_API_KEY')
            )
        )
        self._ensure_schema()
    
    def _ensure_schema(self):
        """Ensure Weaviate schema exists"""
        schema = {
            "class": "OrchestrationContext",
            "properties": [
                {"name": "workflow_id", "dataType": ["string"]},
                {"name": "task_id", "dataType": ["string"]},
                {"name": "context_type", "dataType": ["string"]},
                {"name": "content", "dataType": ["text"]},
                {"name": "metadata", "dataType": ["string"]},
                {"name": "timestamp", "dataType": ["date"]}
            ]
        }
        
        try:
            self.client.schema.create_class(schema)
        except Exception as e:
            if "already exists" not in str(e):
                raise
    
    def store_context(self, workflow_id: str, task_id: str, 
                     context_type: str, content: str, metadata: Dict = None):
        """Store context in Weaviate"""
        data_object = {
            "workflow_id": workflow_id,
            "task_id": task_id,
            "context_type": context_type,
            "content": content,
            "metadata": json.dumps(metadata or {}),
            "timestamp": datetime.now().isoformat()
        }
        
        self.client.data_object.create(
            data_object=data_object,
            class_name="OrchestrationContext"
        )
    
    def retrieve_context(self, workflow_id: str, limit: int = 10) -> List[Dict]:
        """Retrieve context for a workflow"""
        result = (
            self.client.query
            .get("OrchestrationContext", ["workflow_id", "task_id", "context_type", "content", "metadata", "timestamp"])
            .with_where({
                "path": ["workflow_id"],
                "operator": "Equal",
                "valueString": workflow_id
            })
            .with_limit(limit)
            .do()
        )
        
        return result.get("data", {}).get("Get", {}).get("OrchestrationContext", [])


class MCPContextManager:
    """Manages MCP server interactions for task management"""
    
    def __init__(self, mcp_server_url: str = "http://localhost:8080"):
        self.mcp_server_url = mcp_server_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def create_task(self, task: TaskDefinition) -> Dict:
        """Create a task in MCP server"""
        async with self.session.post(
            f"{self.mcp_server_url}/tasks",
            json={
                "task_id": task.task_id,
                "name": task.name,
                "agent_role": task.agent_role.value,
                "inputs": task.inputs,
                "dependencies": task.dependencies,
                "priority": task.priority,
                "timeout": task.timeout
            }
        ) as response:
            return await response.json()
    
    async def update_task_status(self, task_id: str, status: TaskStatus, results: Dict = None):
        """Update task status in MCP server"""
        async with self.session.patch(
            f"{self.mcp_server_url}/tasks/{task_id}",
            json={
                "status": status.value,
                "results": results or {}
            }
        ) as response:
            return await response.json()
    
    async def get_task_status(self, task_id: str) -> Dict:
        """Get task status from MCP server"""
        async with self.session.get(f"{self.mcp_server_url}/tasks/{task_id}") as response:
            return await response.json()


class AgentCoordinator:
    """Coordinates agent interactions"""
    
    def __init__(self, db_logger: DatabaseLogger, weaviate_manager: WeaviateManager):
        self.db_logger = db_logger
        self.weaviate_manager = weaviate_manager
        self.agents = {
            AgentRole.ANALYZER: EigenCodeAgent(),
            AgentRole.IMPLEMENTER: CursorAIAgent(),
            AgentRole.REFINER: RooCodeAgent()
        }
    
    async def execute_task(self, task: TaskDefinition, context: WorkflowContext) -> Dict:
        """Execute a task with the appropriate agent"""
        agent = self.agents.get(task.agent_role)
        if not agent:
            raise ValueError(f"No agent found for role: {task.agent_role}")
        
        # Log task start
        self.db_logger.log_action(
            workflow_id=context.workflow_id,
            task_id=task.task_id,
            agent_role=task.agent_role.value,
            action="task_start",
            status="running",
            metadata={"inputs": task.inputs}
        )
        
        try:
            # Execute task
            results = await agent.execute(task, context)
            
            # Store results in context
            self.weaviate_manager.store_context(
                workflow_id=context.workflow_id,
                task_id=task.task_id,
                context_type="task_results",
                content=json.dumps(results),
                metadata={"agent_role": task.agent_role.value}
            )
            
            # Log success
            self.db_logger.log_action(
                workflow_id=context.workflow_id,
                task_id=task.task_id,
                agent_role=task.agent_role.value,
                action="task_complete",
                status="completed",
                metadata={"results": results}
            )
            
            return results
            
        except Exception as e:
            # Log failure
            self.db_logger.log_action(
                workflow_id=context.workflow_id,
                task_id=task.task_id,
                agent_role=task.agent_role.value,
                action="task_failed",
                status="failed",
                error=str(e)
            )
            raise


class EigenCodeAgent:
    """EigenCode agent for code analysis"""
    
    async def execute(self, task: TaskDefinition, context: WorkflowContext) -> Dict:
        """Execute EigenCode analysis"""
        # Placeholder for EigenCode integration
        # In production, this would call the actual EigenCode CLI/API
        logger.info(f"EigenCode analyzing: {task.inputs.get('codebase_path')}")
        
        # Simulate analysis results
        return {
            "analysis": {
                "structure": "Analyzed project structure",
                "dependencies": ["dependency1", "dependency2"],
                "issues": ["issue1", "issue2"],
                "performance_metrics": {
                    "complexity": "medium",
                    "maintainability": "high"
                }
            }
        }


class CursorAIAgent:
    """Cursor AI agent for implementation"""
    
    async def execute(self, task: TaskDefinition, context: WorkflowContext) -> Dict:
        """Execute Cursor AI implementation"""
        # Placeholder for Cursor AI integration
        logger.info(f"Cursor AI implementing: {task.inputs.get('changes')}")
        
        # Simulate implementation results
        return {
            "implementation": {
                "files_modified": ["file1.py", "file2.py"],
                "changes_applied": True,
                "performance_improvements": "20%"
            }
        }


class RooCodeAgent:
    """Roo Code agent for refinement"""
    
    async def execute(self, task: TaskDefinition, context: WorkflowContext) -> Dict:
        """Execute Roo Code refinement"""
        # Placeholder for Roo Code integration
        logger.info(f"Roo Code refining: {task.inputs.get('technology_stack')}")
        
        # Simulate refinement results
        return {
            "refinement": {
                "optimizations": ["optimization1", "optimization2"],
                "ease_of_use_score": 8.5,
                "recommendations": ["recommendation1", "recommendation2"]
            }
        }


class WorkflowOrchestrator:
    """Main workflow orchestrator"""
    
    def __init__(self):
        self.db_logger = DatabaseLogger()
        self.weaviate_manager = WeaviateManager()
        self.agent_coordinator = AgentCoordinator(self.db_logger, self.weaviate_manager)
        self.workflows: Dict[str, WorkflowContext] = {}
    
    async def create_workflow(self, workflow_id: str) -> WorkflowContext:
        """Create a new workflow"""
        context = WorkflowContext(
            workflow_id=workflow_id,
            task_id=f"{workflow_id}_main"
        )
        self.workflows[workflow_id] = context
        
        # Log workflow creation
        self.db_logger.log_action(
            workflow_id=workflow_id,
            task_id=context.task_id,
            agent_role="orchestrator",
            action="workflow_created",
            status="pending"
        )
        
        return context
    
    async def execute_workflow(self, workflow_id: str, tasks: List[TaskDefinition]):
        """Execute a workflow with dependency management"""
        context = self.workflows.get(workflow_id)
        if not context:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Create task dependency graph
        task_graph = self._build_dependency_graph(tasks)
        
        # Execute tasks in order
        completed_tasks = set()
        
        async with MCPContextManager() as mcp_manager:
            while len(completed_tasks) < len(tasks):
                # Find tasks ready to execute
                ready_tasks = [
                    task for task in tasks
                    if task.task_id not in completed_tasks
                    and all(dep in completed_tasks for dep in task.dependencies)
                ]
                
                if not ready_tasks:
                    raise RuntimeError("Circular dependency detected or no tasks ready")
                
                # Execute ready tasks in parallel
                execution_tasks = []
                for task in ready_tasks:
                    # Create task in MCP
                    await mcp_manager.create_task(task)
                    
                    # Execute task
                    execution_tasks.append(
                        self._execute_single_task(task, context, mcp_manager)
                    )
                
                # Wait for all parallel tasks to complete
                results = await asyncio.gather(*execution_tasks, return_exceptions=True)
                
                # Process results
                for task, result in zip(ready_tasks, results):
                    if isinstance(result, Exception):
                        context.errors.append(f"Task {task.task_id} failed: {str(result)}")
                        context.status = TaskStatus.FAILED
                    else:
                        context.results[task.task_id] = result
                        completed_tasks.add(task.task_id)
        
        # Update workflow status
        if not context.errors:
            context.status = TaskStatus.COMPLETED
        
        return context
    
    async def _execute_single_task(self, task: TaskDefinition, 
                                  context: WorkflowContext, 
                                  mcp_manager: MCPContextManager) -> Dict:
        """Execute a single task with timeout and error handling"""
        try:
            # Update task status to running
            await mcp_manager.update_task_status(task.task_id, TaskStatus.RUNNING)
            
            # Execute with timeout
            result = await asyncio.wait_for(
                self.agent_coordinator.execute_task(task, context),
                timeout=task.timeout
            )
            
            # Update task status to completed
            await mcp_manager.update_task_status(
                task.task_id, TaskStatus.COMPLETED, result
            )
            
            # Create checkpoint
            self._create_checkpoint(context, task.task_id, result)
            
            return result
            
        except asyncio.TimeoutError:
            await mcp_manager.update_task_status(task.task_id, TaskStatus.FAILED)
            raise RuntimeError(f"Task {task.task_id} timed out after {task.timeout}s")
        except Exception as e:
            await mcp_manager.update_task_status(task.task_id, TaskStatus.FAILED)
            raise
    
    def _build_dependency_graph(self, tasks: List[TaskDefinition]) -> Dict[str, List[str]]:
        """Build task dependency graph"""
        graph = {}
        for task in tasks:
            graph[task.task_id] = task.dependencies
        return graph
    
    def _create_checkpoint(self, context: WorkflowContext, task_id: str, result: Dict):
        """Create workflow checkpoint"""
        checkpoint = {
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "result": result,
            "workflow_status": context.status.value
        }
        context.checkpoints.append(checkpoint)
        
        # Store checkpoint in Weaviate
        self.weaviate_manager.store_context(
            workflow_id=context.workflow_id,
            task_id=task_id,
            context_type="checkpoint",
            content=json.dumps(checkpoint)
        )


async def main():
    """Main orchestration entry point"""
    # Example workflow
    orchestrator = WorkflowOrchestrator()
    
    # Create workflow
    workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    context = await orchestrator.create_workflow(workflow_id)
    
    # Define tasks
    tasks = [
        TaskDefinition(
            task_id="analyze_codebase",
            name="Analyze Codebase with EigenCode",
            agent_role=AgentRole.ANALYZER,
            inputs={"codebase_path": "/root/orchestra-main"},
            priority=1
        ),
        TaskDefinition(
            task_id="implement_changes",
            name="Implement Changes with Cursor AI",
            agent_role=AgentRole.IMPLEMENTER,
            inputs={"changes": "performance_optimizations"},
            dependencies=["analyze_codebase"],
            priority=2
        ),
        TaskDefinition(
            task_id="refine_stack",
            name="Refine Technology Stack with Roo Code",
            agent_role=AgentRole.REFINER,
            inputs={"technology_stack": "python_postgres_weaviate"},
            dependencies=["implement_changes"],
            priority=3
        )
    ]
    
    # Execute workflow
    try:
        result = await orchestrator.execute_workflow(workflow_id, tasks)
        logger.info(f"Workflow {workflow_id} completed successfully")
        logger.info(f"Results: {json.dumps(result.results, indent=2)}")
    except Exception as e:
        logger.error(f"Workflow {workflow_id} failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())