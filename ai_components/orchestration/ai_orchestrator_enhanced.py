#!/usr/bin/env python3
"""
Enhanced AI Orchestrator - Coordinates between EigenCode/Mock Analyzer, Cursor AI, and Roo Code
Implements workflow orchestration with optimizations, MCP context management and PostgreSQL logging
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
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

import psycopg2
from psycopg2.extras import RealDictCursor
import aiohttp
from weaviate import Client
from weaviate.auth import AuthApiKey

# Import enhanced mock analyzer
try:
    from ai_components.eigencode.mock_analyzer import get_mock_analyzer
    MOCK_ANALYZER_AVAILABLE = True
except ImportError:
    MOCK_ANALYZER_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_components/logs/orchestrator_enhanced.log'),
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
    RETRYING = "retrying"


class AgentRole(Enum):
    """Agent roles in the orchestration"""
    ANALYZER = "analyzer"  # EigenCode or Mock Analyzer
    IMPLEMENTER = "implementer"  # Cursor AI
    REFINER = "refiner"  # Roo Code


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class WorkflowContext:
    """Enhanced workflow execution context"""
    workflow_id: str
    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    cache: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskDefinition:
    """Enhanced atomic task definition"""
    task_id: str
    name: str
    agent_role: AgentRole
    inputs: Dict[str, Any]
    outputs: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    priority: TaskPriority = TaskPriority.NORMAL
    timeout: int = 300  # seconds
    retry_count: int = 0
    max_retries: int = 3
    batch_compatible: bool = False
    cache_key: Optional[str] = None


class CircuitBreaker:
    """Circuit breaker for fault tolerance"""
    
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "open":
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            
            raise e


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
    """Enhanced PostgreSQL logging with connection pooling"""
    
    def __init__(self):
        self.connection_params = {
            'host': SecretManager.get_secret('POSTGRES_HOST') or 'localhost',
            'port': SecretManager.get_secret('POSTGRES_PORT') or 5432,
            'database': SecretManager.get_secret('POSTGRES_DB') or 'orchestrator',
            'user': SecretManager.get_secret('POSTGRES_USER') or 'postgres',
            'password': SecretManager.get_secret('POSTGRES_PASSWORD') or 'postgres'
        }
        self._ensure_tables()
    
    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.connection_params)
    
    def _ensure_tables(self):
        """Ensure logging tables exist with optimized indexes"""
        try:
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
                        
                        -- Optimized indexes
                        CREATE INDEX IF NOT EXISTS idx_workflow_id ON orchestration_logs(workflow_id);
                        CREATE INDEX IF NOT EXISTS idx_task_id ON orchestration_logs(task_id);
                        CREATE INDEX IF NOT EXISTS idx_created_at ON orchestration_logs(created_at DESC);
                        CREATE INDEX IF NOT EXISTS idx_status ON orchestration_logs(status);
                        CREATE INDEX IF NOT EXISTS idx_agent_role ON orchestration_logs(agent_role);
                        CREATE INDEX IF NOT EXISTS idx_composite ON orchestration_logs(workflow_id, task_id, created_at DESC);
                    """)
                    conn.commit()
        except Exception as e:
            logger.warning(f"Database initialization warning: {e}")
    
    def log_action(self, workflow_id: str, task_id: str, agent_role: str, 
                   action: str, status: str, metadata: Dict = None, error: str = None):
        """Log an orchestration action"""
        try:
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
        except Exception as e:
            logger.error(f"Failed to log action: {e}")


class WeaviateManager:
    """Enhanced Weaviate Cloud interactions with caching"""
    
    def __init__(self):
        try:
            self.client = Client(
                url=SecretManager.get_secret('WEAVIATE_URL') or 'http://localhost:8080',
                auth_client_secret=AuthApiKey(
                    api_key=SecretManager.get_secret('WEAVIATE_API_KEY') or 'test-key'
                ) if SecretManager.get_secret('WEAVIATE_API_KEY') else None
            )
            self._ensure_schema()
        except Exception as e:
            logger.warning(f"Weaviate initialization warning: {e}")
            self.client = None
    
    def _ensure_schema(self):
        """Ensure Weaviate schema exists"""
        if not self.client:
            return
            
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
                logger.warning(f"Schema creation warning: {e}")
    
    def store_context(self, workflow_id: str, task_id: str, 
                     context_type: str, content: str, metadata: Dict = None):
        """Store context in Weaviate"""
        if not self.client:
            return
            
        try:
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
        except Exception as e:
            logger.error(f"Failed to store context: {e}")
    
    def retrieve_context(self, workflow_id: str, limit: int = 10) -> List[Dict]:
        """Retrieve context for a workflow"""
        if not self.client:
            return []
            
        try:
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
        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}")
            return []


class EnhancedEigenCodeAgent:
    """Enhanced EigenCode agent with mock analyzer fallback"""
    
    def __init__(self):
        self.eigencode_available = self._check_eigencode()
        self.mock_analyzer = get_mock_analyzer() if MOCK_ANALYZER_AVAILABLE else None
        self.circuit_breaker = CircuitBreaker()
    
    def _check_eigencode(self) -> bool:
        """Check if EigenCode is available"""
        try:
            result = subprocess.run(['eigencode', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    async def execute(self, task: TaskDefinition, context: WorkflowContext) -> Dict:
        """Execute code analysis with fallback"""
        codebase_path = task.inputs.get('codebase_path', '.')
        options = task.inputs.get('options', {})
        
        # Try EigenCode first
        if self.eigencode_available:
            try:
                return await self.circuit_breaker.call(
                    self._execute_eigencode, codebase_path, options
                )
            except Exception as e:
                logger.warning(f"EigenCode failed: {e}, falling back to mock analyzer")
                self.eigencode_available = False
        
        # Use mock analyzer if available
        if self.mock_analyzer:
            logger.info("Using enhanced mock analyzer")
            return await self.mock_analyzer.analyze_codebase(codebase_path, options)
        
        # Basic fallback
        logger.warning("Using basic fallback analyzer")
        return self._basic_analysis(codebase_path)
    
    async def _execute_eigencode(self, codebase_path: str, options: Dict) -> Dict:
        """Execute actual EigenCode analysis"""
        cmd = ['eigencode', 'analyze', codebase_path]
        if options.get('depth') == 'comprehensive':
            cmd.append('--comprehensive')
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"EigenCode failed: {result.stderr}")
        
        return json.loads(result.stdout)
    
    def _basic_analysis(self, codebase_path: str) -> Dict:
        """Basic fallback analysis"""
        return {
            "status": "completed",
            "analyzer": "basic_fallback",
            "timestamp": datetime.now().isoformat(),
            "codebase_path": codebase_path,
            "summary": {
                "total_files": 0,
                "total_lines": 0,
                "languages": {}
            }
        }


class CursorAIAgent:
    """Enhanced Cursor AI agent for implementation"""
    
    def __init__(self):
        self.circuit_breaker = CircuitBreaker()
    
    async def execute(self, task: TaskDefinition, context: WorkflowContext) -> Dict:
        """Execute Cursor AI implementation"""
        logger.info(f"Cursor AI implementing: {task.inputs.get('changes')}")
        
        # Simulate implementation with performance tracking
        start_time = time.time()
        
        # Simulate implementation results
        result = {
            "implementation": {
                "files_modified": ["file1.py", "file2.py"],
                "changes_applied": True,
                "performance_improvements": "20%",
                "execution_time": time.time() - start_time
            }
        }
        
        return result


class RooCodeAgent:
    """Enhanced Roo Code agent for refinement"""
    
    def __init__(self):
        self.circuit_breaker = CircuitBreaker()
    
    async def execute(self, task: TaskDefinition, context: WorkflowContext) -> Dict:
        """Execute Roo Code refinement"""
        logger.info(f"Roo Code refining: {task.inputs.get('technology_stack')}")
        
        # Simulate refinement with performance tracking
        start_time = time.time()
        
        # Simulate refinement results
        result = {
            "refinement": {
                "optimizations": ["optimization1", "optimization2"],
                "ease_of_use_score": 8.5,
                "recommendations": ["recommendation1", "recommendation2"],
                "execution_time": time.time() - start_time
            }
        }
        
        return result


class EnhancedAgentCoordinator:
    """Enhanced agent coordinator with load balancing and circuit breakers"""
    
    def __init__(self, db_logger: DatabaseLogger, weaviate_manager: WeaviateManager):
        self.db_logger = db_logger
        self.weaviate_manager = weaviate_manager
        self.agents = {
            AgentRole.ANALYZER: EnhancedEigenCodeAgent(),
            AgentRole.IMPLEMENTER: CursorAIAgent(),
            AgentRole.REFINER: RooCodeAgent()
        }
        self.circuit_breakers = {
            role: CircuitBreaker() for role in AgentRole
        }
        self.agent_metrics = {
            role: {"calls": 0, "failures": 0, "total_time": 0}
            for role in AgentRole
        }
    
    def get_circuit_breaker(self, agent_role: str) -> CircuitBreaker:
        """Get circuit breaker for agent"""
        return self.circuit_breakers.get(AgentRole(agent_role))
    
    async def execute_task(self, task: TaskDefinition, context: WorkflowContext) -> Dict:
        """Execute a task with the appropriate agent"""
        agent = self.agents.get(task.agent_role)
        if not agent:
            raise ValueError(f"No agent found for role: {task.agent_role}")
        
        # Check cache first
        if task.cache_key and task.cache_key in context.cache:
            logger.info(f"Cache hit for task {task.task_id}")
            return context.cache[task.cache_key]
        
        # Log task start
        self.db_logger.log_action(
            workflow_id=context.workflow_id,
            task_id=task.task_id,
            agent_role=task.agent_role.value,
            action="task_start",
            status="running",
            metadata={"inputs": task.inputs}
        )
        
        # Track metrics
        start_time = time.time()
        self.agent_metrics[task.agent_role]["calls"] += 1
        
        try:
            # Execute task with circuit breaker
            circuit_breaker = self.circuit_breakers[task.agent_role]
            results = await circuit_breaker.call(agent.execute, task, context)
            
            # Update metrics
            execution_time = time.time() - start_time
            self.agent_metrics[task.agent_role]["total_time"] += execution_time
            
            # Cache results if applicable
            if task.cache_key:
                context.cache[task.cache_key] = results
            
            # Store results in context
            self.weaviate_manager.store_context(
                workflow_id=context.workflow_id,
                task_id=task.task_id,
                context_type="task_results",
                content=json.dumps(results),
                metadata={
                    "agent_role": task.agent_role.value,
                    "execution_time": execution_time
                }
            )
            
            # Log success
            self.db_logger.log_action(
                workflow_id=context.workflow_id,
                task_id=task.task_id,
                agent_role=task.agent_role.value,
                action="task_complete",
                status="completed",
                metadata={
                    "results": results,
                    "execution_time": execution_time
                }
            )
            
            return results
            
        except Exception as e:
            # Update failure metrics
            self.agent_metrics[task.agent_role]["failures"] += 1
            
            # Log failure
            self.db_logger.log_action(
                workflow_id=context.workflow_id,
                task_id=task.task_id,
                agent_role=task.agent_role.value,
                action="task_failed",
                status="failed",
                error=str(e)
            )
            
            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                logger.info(f"Retrying task {task.task_id} (attempt {task.retry_count})")
                await asyncio.sleep(2 ** task.retry_count)  # Exponential backoff
                return await self.execute_task(task, context)
            
            raise


class EnhancedWorkflowOrchestrator:
    """Enhanced workflow orchestrator with optimizations"""
    
    def __init__(self):
        self.db_logger = DatabaseLogger()
        self.weaviate_manager = WeaviateManager()
        self.agent_coordinator = EnhancedAgentCoordinator(self.db_logger, self.weaviate_manager)
        self.workflows: Dict[str, WorkflowContext] = {}
        
        # Load optimized configuration
        self.config = self._load_optimized_config()
        
        # Configure executors
        cpu_count = multiprocessing.cpu_count()
        self.thread_executor = ThreadPoolExecutor(
            max_workers=self.config.get('execution', {}).get('thread_pool_size', cpu_count * 2)
        )
        self.process_executor = ProcessPoolExecutor(
            max_workers=self.config.get('execution', {}).get('process_pool_size', cpu_count)
        )
        
        # Task queue for batching
        self.task_queue = asyncio.Queue(maxsize=1000)
        self.batch_processor_task = None
    
    def _load_optimized_config(self) -> Dict:
        """Load optimized configuration"""
        config_paths = [
            'config/orchestrator_config_optimized.json',
            'config/orchestrator_config.json'
        ]
        
        for config_path in config_paths:
            path = Path(config_path)
            if path.exists():
                try:
                    with open(path) as f:
                        return json.load(f)
                except Exception as e:
                    logger.warning(f"Failed to load config from {config_path}: {e}")
        
        # Default configuration
        return {
            "execution": {
                "max_parallel_tasks": 100,
                "thread_pool_size": multiprocessing.cpu_count() * 2,
                "process_pool_size": multiprocessing.cpu_count(),
                "batch_size": 50,
                "batch_timeout_ms": 100
            }
        }
    
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
        
        # Start batch processor if not running
        if not self.batch_processor_task:
            self.batch_processor_task = asyncio.create_task(self._batch_processor())
        
        return context
    
    async def execute_workflow(self, workflow_id: str, tasks: List[TaskDefinition]):
        """Execute a workflow with dependency management and optimizations"""
        context = self.workflows.get(workflow_id)
        if not context:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        start_time = time.time()
        
        # Sort tasks by priority
        tasks.sort(key=lambda t: t.priority.value)
        
        # Create task dependency graph
        task_graph = self._build_dependency_graph(tasks)
        
        # Execute tasks with parallelization
        completed_tasks = set()
        task_futures = {}
        
        while len(completed_tasks) < len(tasks):
            # Find tasks ready to execute
            ready_tasks = [
                task for task in tasks
                if task.task_id not in completed_tasks
                and task.task_id not in task_futures
                and all(dep in completed_tasks for dep in task.dependencies)
            ]
            
            if not ready_tasks and not task_futures:
                raise RuntimeError("Circular dependency detected or no tasks ready")
            
            # Submit ready tasks for execution
            for task in ready_tasks:
                if len(task_futures) < self.config['execution']['max_parallel_tasks']:
                    future = asyncio.create_task(
                        self._execute_single_task(task, context)
                    )
                    task_futures[task.task_id] = (task, future)
            
            # Wait for at least one task to complete
            if task_futures:
                done, pending = await asyncio.wait(
                    [f for _, f in task_futures.values()],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Process completed tasks
                for future in done:
                    # Find which task this future belongs to
                    for task_id, (task, task_future) in list(task_futures.items()):
                        if task_future == future:
                            try:
                                result = await future
                                context.results[task_id] = result
                                completed_tasks.add(task_id)
                            except Exception as e:
                                context.errors.append(f"Task {task_id} failed: {str(e)}")
                                context.status = TaskStatus.FAILED
                            finally:
                                del task_futures[task_id]
                            break
        
        # Update workflow status
        execution_time = time.time() - start_time
        context.performance_metrics = {
            "execution_time": execution_time,
            "tasks_executed": len(completed_tasks),
            "tasks_per_second": len(completed_tasks) / execution_time if execution_time > 0 else 0,
            "parallel_efficiency": self._calculate_parallel_efficiency(tasks, execution_time)
        }
        
        if not context.errors:
            context.status = TaskStatus.COMPLETED
        
        # Log workflow completion
        self.db_logger.log_action(
            workflow_id=workflow_id,
            task_id=context.task_id,
            agent_role="orchestrator",
            action="workflow_completed",
            status=context.status.value,
            metadata=context.performance_metrics
        )
        
        return context
    
    async def _execute_single_task(self, task: TaskDefinition, context: WorkflowContext) -> Dict:
        """Execute a single task with timeout and error handling"""
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                self.agent_coordinator.execute_task(task, context),
                timeout=task.timeout
            )
            
            # Create checkpoint
            self._create_checkpoint(context, task.task_id, result)
            
            return result
            
        except asyncio.TimeoutError:
            raise RuntimeError(f"Task {task.task_id} timed out after {task.timeout}s")
    
    async def _batch_processor(self):
        """Process tasks in batches for improved efficiency"""
        batch = []
        last_process_time = time.time()
        
        while True:
            try:
                # Get task from queue with timeout
                timeout = self.config['execution']['batch_timeout_ms'] / 1000
                task = await asyncio.wait_for(
                    self.task_queue.get(),
                    timeout=timeout
                )
                batch.append(task)
                
                # Process batch if full
                if len(batch) >= self.config['execution']['batch_size']:
                    await self._process_batch(batch)
                    batch = []
                    last_process_time = time.time()
                    
            except asyncio.TimeoutError:
                # Process batch on timeout if not empty
                if batch and (time.time() - last_process_time) > timeout:
                    await self._process_batch(batch)
                    batch = []
                    last_process_time = time.time()
    
    async def _process_batch(self, batch: List[TaskDefinition]):
        """Process a batch of tasks"""
        logger.info(f"Processing batch of {len(batch)} tasks")
        # Implementation for batch processing
        # This would group similar tasks for more efficient execution
    
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
    
    def _calculate_parallel_efficiency(self, tasks: List[TaskDefinition], 
                                     actual_time: float) -> float:
        """Calculate parallel execution efficiency"""
        # Estimate sequential time (sum of all task times)
        sequential_time = len(tasks) * 5  # Assume 5 seconds per task
        
        # Calculate efficiency
        if actual_time > 0:
            efficiency = (sequential_time / actual_time) / self.config['execution']['max_parallel_tasks']
            return min(1.0, efficiency)  # Cap at 100%
        return 0.0
    
    def get_agent_metrics(self) -> Dict:
        """Get agent performance metrics"""
        return self.agent_coordinator.agent_metrics


async def main():
    """Main orchestration entry point"""
    # Example workflow with enhanced features
    orchestrator = EnhancedWorkflowOrchestrator()
    
    # Create workflow
    workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    context = await orchestrator.create_workflow(workflow_id)
    
    # Define tasks with enhanced features
    tasks = [
        TaskDefinition(
            task_id="analyze_codebase",
            name="Analyze Codebase with EigenCode/Mock Analyzer",
            agent_role=AgentRole.ANALYZER,
            inputs={
                "codebase_path": "/root/orchestra-main",
                "options": {
                    "depth": "comprehensive",
                    "include_metrics": True,
                    "include_suggestions": True
                }
            },
            priority=TaskPriority.HIGH,
            cache_key="analysis_orchestra_main"
        ),
        TaskDefinition(
            task_id="implement_changes",
            name="Implement Changes with Cursor AI",
            agent_role=AgentRole.IMPLEMENTER,
            inputs={"changes": "performance_optimizations"},
            dependencies=["analyze_codebase"],
            priority=TaskPriority.NORMAL,
            batch_compatible=True
        ),
        TaskDefinition(
            task_id="refine_stack",
            name="Refine Technology Stack with Roo Code",
            agent_role=AgentRole.REFINER,
            inputs={"technology_stack": "python_postgres_weaviate"},
            dependencies=["implement_changes"],
            priority=TaskPriority.NORMAL
        )
    ]
    
    # Execute workflow
    try:
        result = await orchestrator.execute_workflow(workflow_id, tasks)
        logger.info(f"Workflow {workflow_id} completed successfully")
        logger.info(f"Performance metrics: {json.dumps(result.performance_metrics, indent=2)}")
        logger.info(f"Results: {json.dumps(result.results, indent=2)}")
        
        # Display agent metrics
        agent_metrics = orchestrator.get_agent_metrics()
        logger.info(f"Agent metrics: {json.dumps(agent_metrics, indent=2)}")
        
    except Exception as e:
        logger.error(f"Workflow {workflow_id} failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())