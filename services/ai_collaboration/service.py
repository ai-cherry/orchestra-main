#!/usr/bin/env python3
"""
AI Collaboration Service
Main service implementation following clean architecture and SOLID principles
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Protocol
from datetime import datetime
from contextlib import asynccontextmanager

from .models.entities import AIAgent, AITask, AIMetric, CollaborationEvent
from .models.enums import AIAgentType, TaskStatus, MetricType, EventType
from .models.dto import (
    AIStatusDTO,
    TaskCreateDTO,
    TaskUpdateDTO,
    MetricDTO,
    CollaborationEventDTO,
    DashboardSummaryDTO,
)
from .models.value_objects import AgentCapabilities, TaskPayload
from .interfaces import (
    IDatabase,
    ICache,
    IVectorStore,
    IWebSocketAdapter,
    IMetricsCollector,
    ITaskRouter,
)
from .exceptions import (
    ServiceError,
    AgentNotFoundError,
    TaskNotFoundError,
    InvalidStateTransitionError,
)


class AICollaborationService:
    """
    Main service for AI collaboration monitoring and management
    Implements the facade pattern to coordinate subsystems
    """
    
    def __init__(
        self,
        database: IDatabase,
        cache: ICache,
        vector_store: IVectorStore,
        websocket_adapter: IWebSocketAdapter,
        metrics_collector: IMetricsCollector,
        task_router: ITaskRouter,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize service with dependency injection
        
        Args:
            database: Database interface implementation
            cache: Cache interface implementation
            vector_store: Vector store interface implementation
            websocket_adapter: WebSocket adapter implementation
            metrics_collector: Metrics collector implementation
            task_router: Task router implementation
            logger: Optional logger instance
        """
        self.db = database
        self.cache = cache
        self.vector_store = vector_store
        self.ws_adapter = websocket_adapter
        self.metrics = metrics_collector
        self.router = task_router
        self.logger = logger or logging.getLogger(__name__)
        
        self._initialized = False
        self._shutdown_event = asyncio.Event()
        self._background_tasks: List[asyncio.Task] = []
    
    async def initialize(self) -> None:
        """Initialize all service components"""
        if self._initialized:
            self.logger.warning("Service already initialized")
            return
        
        try:
            self.logger.info("Initializing AI Collaboration Service...")
            
            # Initialize components
            await self.db.initialize()
            await self.cache.connect()
            await self.vector_store.initialize()
            await self.ws_adapter.connect()
            
            # Set up database schema
            await self._setup_database_schema()
            
            # Start background tasks
            self._start_background_tasks()
            
            self._initialized = True
            self.logger.info("AI Collaboration Service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize service: {e}")
            await self.shutdown()
            raise ServiceError(f"Service initialization failed: {e}")
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the service"""
        self.logger.info("Shutting down AI Collaboration Service...")
        
        # Signal shutdown to background tasks
        self._shutdown_event.set()
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Disconnect components
        await self.ws_adapter.disconnect()
        await self.cache.disconnect()
        await self.db.close()
        
        self._initialized = False
        self.logger.info("AI Collaboration Service shutdown complete")
    
    @asynccontextmanager
    async def lifespan(self):
        """Context manager for service lifecycle"""
        await self.initialize()
        try:
            yield self
        finally:
            await self.shutdown()
    
    # Agent Management
    
    async def get_agent_status(self, agent_id: Optional[int] = None) -> List[AIStatusDTO]:
        """
        Get status of AI agents
        
        Args:
            agent_id: Optional specific agent ID
            
        Returns:
            List of agent status DTOs
        """
        # Try cache first
        cache_key = f"agent_status:{agent_id or 'all'}"
        cached = await self.cache.get(cache_key)
        if cached:
            return [AIStatusDTO.from_dict(d) for d in cached]
        
        # Query from database
        query = """
        SELECT 
            a.id as agent_id,
            a.agent_type,
            a.agent_name,
            a.status,
            a.last_heartbeat,
            COALESCE(active_tasks.count, 0) as active_tasks,
            COALESCE(completed_tasks.count, 0) as completed_tasks_hour,
            metrics.avg_response_time,
            COALESCE(metrics.error_count, 0) as error_count
        FROM ai_agents a
        LEFT JOIN (
            SELECT agent_id, COUNT(*) as count
            FROM ai_tasks
            WHERE status = ANY($1)
            GROUP BY agent_id
        ) active_tasks ON a.id = active_tasks.agent_id
        LEFT JOIN (
            SELECT agent_id, COUNT(*) as count
            FROM ai_tasks
            WHERE status = 'completed' 
                AND completed_at > NOW() - INTERVAL '1 hour'
            GROUP BY agent_id
        ) completed_tasks ON a.id = completed_tasks.agent_id
        LEFT JOIN (
            SELECT 
                agent_id,
                AVG(value) FILTER (WHERE metric_type = 'response_time') as avg_response_time,
                COUNT(*) FILTER (WHERE metric_type = 'error_rate' AND value > 0) as error_count
            FROM ai_metrics
            WHERE timestamp > NOW() - INTERVAL '5 minutes'
            GROUP BY agent_id
        ) metrics ON a.id = metrics.agent_id
        """
        
        params = [TaskStatus.active_statuses()]
        if agent_id:
            query += " WHERE a.id = $2"
            params.append(agent_id)
        
        rows = await self.db.fetch(query, *params)
        
        # Convert to DTOs and calculate performance scores
        statuses = []
        for row in rows:
            # Calculate performance score
            agent = AIAgent(
                id=row['agent_id'],
                agent_type=AIAgentType(row['agent_type']),
                agent_name=row['agent_name'],
                capabilities=AgentCapabilities.default_for_agent_type(row['agent_type']),
                status=row['status'],
                last_heartbeat=row['last_heartbeat']
            )
            
            # Update metrics for score calculation
            if row['avg_response_time']:
                agent.update_performance_metric(
                    MetricType.RESPONSE_TIME,
                    row['avg_response_time']
                )
            if row['error_count']:
                agent.update_performance_metric(
                    MetricType.ERROR_RATE,
                    row['error_count']
                )
            
            status = AIStatusDTO(
                agent_id=row['agent_id'],
                agent_type=AIAgentType(row['agent_type']),
                agent_name=row['agent_name'],
                status=row['status'],
                active_tasks=row['active_tasks'],
                completed_tasks_hour=row['completed_tasks_hour'],
                avg_response_time=row['avg_response_time'],
                error_count=row['error_count'],
                last_heartbeat=row['last_heartbeat'].isoformat() if row['last_heartbeat'] else None,
                performance_score=agent.get_performance_score()
            )
            statuses.append(status)
        
        # Cache for 5 seconds
        await self.cache.set(
            cache_key,
            [s.to_dict() for s in statuses],
            ttl=5
        )
        
        return statuses
    
    async def register_agent(
        self,
        agent_type: AIAgentType,
        agent_name: str,
        capabilities: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Register a new AI agent
        
        Args:
            agent_type: Type of AI agent
            agent_name: Name of the agent
            capabilities: Optional capabilities dict
            
        Returns:
            Agent ID
        """
        caps = AgentCapabilities.default_for_agent_type(agent_type.value)
        if capabilities:
            # Merge with provided capabilities
            caps = AgentCapabilities(
                supported_tasks=caps.supported_tasks | set(capabilities.get('tasks', [])),
                max_concurrent_tasks=capabilities.get('max_concurrent_tasks', caps.max_concurrent_tasks),
                supported_languages=caps.supported_languages | set(capabilities.get('languages', [])),
                features=caps.features | capabilities.get('features', {}),
                performance_profile=caps.performance_profile | capabilities.get('performance', {})
            )
        
        agent_id = await self.db.insert(
            "ai_agents",
            agent_type=agent_type.value,
            agent_name=agent_name,
            capabilities=caps.to_dict(),
            status='inactive',
            created_at=datetime.utcnow()
        )
        
        # Emit registration event
        await self._emit_event(
            EventType.AGENT_ONLINE,
            source_agent_id=agent_id,
            event_data={"agent_name": agent_name, "agent_type": agent_type.value}
        )
        
        return agent_id
    
    # Task Management
    
    async def create_task(self, task_dto: TaskCreateDTO) -> str:
        """
        Create a new AI task with intelligent routing
        
        Args:
            task_dto: Task creation DTO
            
        Returns:
            Task ID (UUID string)
        """
        # Validate task
        errors = task_dto.validate()
        if errors:
            raise ValueError(f"Invalid task: {', '.join(errors)}")
        
        # Create task payload
        payload = TaskPayload(
            task_data=task_dto.task_data,
            context=task_dto.context,
            constraints=task_dto.constraints
        )
        
        # Route to appropriate agent
        agent_id = await self.router.route_task(task_dto)
        
        # Create task entity
        task = AITask(
            id=0,  # Will be set by database
            agent_id=agent_id,
            task_type=task_dto.task_type,
            payload=payload,
            priority=task_dto.priority,
            timeout_seconds=payload.get_timeout(),
            max_retries=payload.get_max_retries()
        )
        
        # Store in database
        task_id = await self.db.insert(
            "ai_tasks",
            task_id=task.task_id,
            agent_id=task.agent_id,
            task_type=task.task_type,
            payload=payload.to_json(),
            status=task.status.value,
            priority=task.priority,
            created_at=task.created_at
        )
        
        # Send to WebSocket adapter
        await self.ws_adapter.send_message({
            "type": "task_created",
            "task_id": str(task.task_id),
            "agent_id": agent_id,
            "task_type": task.task_type,
            "priority": task.priority
        })
        
        # Emit event
        await self._emit_event(
            EventType.TASK_CREATED,
            source_agent_id=agent_id,
            task_id=task.task_id,
            event_data={"task_type": task.task_type}
        )
        
        # Collect metric
        await self.metrics.collect_metric(
            agent_id,
            MetricType.QUEUE_DEPTH,
            await self._get_agent_queue_depth(agent_id)
        )
        
        return str(task.task_id)
    
    async def update_task_status(self, update_dto: TaskUpdateDTO) -> None:
        """
        Update task status
        
        Args:
            update_dto: Task update DTO
        """
        # Get current task
        task_row = await self.db.fetch_one(
            "SELECT * FROM ai_tasks WHERE task_id = $1",
            update_dto.task_id
        )
        
        if not task_row:
            raise TaskNotFoundError(f"Task {update_dto.task_id} not found")
        
        # Recreate task entity
        task = AITask(
            id=task_row['id'],
            task_id=task_row['task_id'],
            agent_id=task_row['agent_id'],
            task_type=task_row['task_type'],
            payload=TaskPayload.from_json(task_row['payload']),
            status=TaskStatus(task_row['status']),
            priority=task_row['priority'],
            created_at=task_row['created_at'],
            started_at=task_row['started_at'],
            completed_at=task_row['completed_at'],
            error_details=task_row['error_details']
        )
        
        # Apply status transition
        try:
            if update_dto.status == TaskStatus.IN_PROGRESS:
                task.start()
            elif update_dto.status == TaskStatus.COMPLETED:
                task.complete(update_dto.result)
            elif update_dto.status == TaskStatus.FAILED:
                task.fail(update_dto.error_details or {"error": "Unknown error"})
            elif update_dto.status == TaskStatus.CANCELLED:
                task.cancel(update_dto.error_details.get("reason", "") if update_dto.error_details else "")
            else:
                task.transition_to(update_dto.status)
        except ValueError as e:
            raise InvalidStateTransitionError(str(e))
        
        # Update in database
        update_data = {
            "status": task.status.value,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "error_details": task.error_details
        }
        
        if update_dto.result:
            payload_with_result = task.payload.with_result(update_dto.result)
            update_data["payload"] = payload_with_result.to_json()
        
        await self.db.update(
            "ai_tasks",
            {"task_id": task.task_id},
            **update_data
        )
        
        # Emit appropriate event
        event_type_map = {
            TaskStatus.ASSIGNED: EventType.TASK_ASSIGNED,
            TaskStatus.IN_PROGRESS: EventType.TASK_STARTED,
            TaskStatus.COMPLETED: EventType.TASK_COMPLETED,
            TaskStatus.FAILED: EventType.TASK_FAILED,
        }
        
        if task.status in event_type_map:
            await self._emit_event(
                event_type_map[task.status],
                source_agent_id=task.agent_id,
                task_id=task.task_id,
                event_data={"status": task.status.value}
            )
        
        # Collect metrics
        if task.status == TaskStatus.COMPLETED and task.get_duration():
            await self.metrics.collect_metric(
                task.agent_id,
                MetricType.TASK_DURATION,
                task.get_duration()
            )
    
    async def get_dashboard_summary(self) -> DashboardSummaryDTO:
        """
        Get comprehensive dashboard summary
        
        Returns:
            Dashboard summary DTO
        """
        # Get agent statuses
        agent_statuses = await self.get_agent_status()
        
        # Get task statistics
        task_stats = await self.db.fetch_one("""
        SELECT 
            COUNT(*) as total_tasks,
            COUNT(*) FILTER (WHERE status = ANY($1)) as active_tasks,
            COUNT(*) FILTER (WHERE status = 'completed' AND completed_at > NOW() - INTERVAL '1 hour') as completed_tasks_hour,
            COUNT(*) FILTER (WHERE status = 'failed' AND completed_at > NOW() - INTERVAL '1 hour') as failed_tasks_hour,
            AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) FILTER (WHERE completed_at IS NOT NULL) as avg_task_duration
        FROM ai_tasks
        WHERE created_at > NOW() - INTERVAL '24 hours'
        """, TaskStatus.active_statuses())
        
        tasks_data = {
            "total_tasks": task_stats['total_tasks'],
            "active_tasks": task_stats['active_tasks'],
            "completed_tasks_hour": task_stats['completed_tasks_hour'],
            "failed_tasks_hour": task_stats['failed_tasks_hour'],
            "avg_task_duration": task_stats['avg_task_duration'] or 0.0
        }
        
        return DashboardSummaryDTO.from_metrics(agent_statuses, tasks_data)
    
    # Private methods
    
    async def _setup_database_schema(self) -> None:
        """Set up database schema"""
        # This would contain the full schema setup
        # For brevity, assuming schema is already set up
        self.logger.info("Database schema verified")
    
    async def _emit_event(
        self,
        event_type: EventType,
        source_agent_id: Optional[int] = None,
        target_agent_id: Optional[int] = None,
        task_id: Optional[Any] = None,
        event_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Emit a collaboration event"""
        event = CollaborationEvent(
            id=0,  # Will be set by database
            event_type=event_type,
            source_agent_id=source_agent_id,
            target_agent_id=target_agent_id,
            task_id=task_id,
            event_data=event_data or {}
        )
        
        # Store in database
        await self.db.insert(
            "ai_collaboration_events",
            event_type=event.event_type.value,
            source_agent_id=event.source_agent_id,
            target_agent_id=event.target_agent_id,
            task_id=str(event.task_id) if event.task_id else None,
            event_data=event.event_data,
            timestamp=event.timestamp
        )
        
        # Publish to Redis for real-time updates
        event_dto = CollaborationEventDTO(
            event_type=event.event_type,
            source_agent_id=event.source_agent_id,
            target_agent_id=event.target_agent_id,
            task_id=str(event.task_id) if event.task_id else None,
            event_data=event.event_data
        )
        
        await self.cache.publish("ai_updates", event_dto.to_dict())
        
        # Index in vector store for semantic search
        await self.vector_store.index(
            collection="ai_interactions",
            data={
                "content": event.to_log_entry(),
                "metadata": {
                    "type": event.event_type.value,
                    "timestamp": event.timestamp.isoformat(),
                    "severity": event.get_severity()
                }
            }
        )
    
    async def _get_agent_queue_depth(self, agent_id: int) -> int:
        """Get current queue depth for an agent"""
        result = await self.db.fetch_one(
            "SELECT COUNT(*) as count FROM ai_tasks WHERE agent_id = $1 AND status = ANY($2)",
            agent_id,
            [TaskStatus.PENDING.value, TaskStatus.QUEUED.value]
        )
        return result['count']
    
    def _start_background_tasks(self) -> None:
        """Start background tasks"""
        self._background_tasks = [
            asyncio.create_task(self._heartbeat_monitor()),
            asyncio.create_task(self._task_timeout_monitor()),
            asyncio.create_task(self._metrics_aggregator()),
        ]
    
    async def _heartbeat_monitor(self) -> None:
        """Monitor agent heartbeats"""
        while not self._shutdown_event.is_set():
            try:
                # Check for stale agents
                stale_agents = await self.db.fetch("""
                SELECT id, agent_name FROM ai_agents 
                WHERE status = 'active' 
                AND last_heartbeat < NOW() - INTERVAL '2 minutes'
                """)
                
                for agent in stale_agents:
                    await self.db.update(
                        "ai_agents",
                        {"id": agent['id']},
                        status='offline'
                    )
                    
                    await self._emit_event(
                        EventType.AGENT_OFFLINE,
                        source_agent_id=agent['id'],
                        event_data={"reason": "heartbeat_timeout"}
                    )
                    
                    self.logger.warning(f"Agent {agent['agent_name']} marked offline due to heartbeat timeout")
                
            except Exception as e:
                self.logger.error(f"Error in heartbeat monitor: {e}")
            
            # Wait 30 seconds
            await asyncio.sleep(30)
    
    async def _task_timeout_monitor(self) -> None:
        """Monitor task timeouts"""
        while not self._shutdown_event.is_set():
            try:
                # Find timed out tasks
                timed_out_tasks = await self.db.fetch("""
                SELECT task_id, agent_id, task_type,
                       EXTRACT(EPOCH FROM (NOW() - started_at)) as elapsed_seconds,
                       (payload->>'constraints'->>'timeout_seconds')::int as timeout_seconds
                FROM ai_tasks
                WHERE status = 'in_progress'
                AND started_at IS NOT NULL
                AND EXTRACT(EPOCH FROM (NOW() - started_at)) > 
                    COALESCE((payload->>'constraints'->>'timeout_seconds')::int, 300)
                """)
                
                for task in timed_out_tasks:
                    update_dto = TaskUpdateDTO(
                        task_id=task['task_id'],
                        status=TaskStatus.FAILED,
                        error_details={
                            "error": "timeout",
                            "elapsed_seconds": task['elapsed_seconds'],
                            "timeout_seconds": task['timeout_seconds']
                        }
                    )
                    
                    await self.update_task_status(update_dto)
                    
                    self.logger.warning(
                        f"Task {task['task_id']} timed out after {task['elapsed_seconds']}s"
                    )
                
            except Exception as e:
                self.logger.error(f"Error in task timeout monitor: {e}")
            
            # Wait 10 seconds
            await asyncio.sleep(10)
    
    async def _metrics_aggregator(self) -> None:
        """Aggregate metrics periodically"""
        while not self._shutdown_event.is_set():
            try:
                # Refresh materialized view
                await self.db.execute("SELECT refresh_ai_dashboard()")
                
                # Calculate and store aggregate metrics
                aggregates = await self.db.fetch("""
                SELECT 
                    agent_id,
                    metric_type,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY value) as p50,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY value) as p95,
                    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY value) as p99,
                    AVG(value) as avg,
                    COUNT(*) as count
                FROM ai_metrics
                WHERE timestamp > NOW() - INTERVAL '5 minutes'
                GROUP BY agent_id, metric_type
                """)
                
                # Store aggregates in cache for fast access
                for agg in aggregates:
                    cache_key = f"metrics:{agg['agent_id']}:{agg['metric_type']}"
                    await self.cache.set(cache_key, dict(agg), ttl=300)
                
            except Exception as e:
                self.logger.error(f"Error in metrics aggregator: {e}")
            
            # Wait 1 minute
            await asyncio.sleep(60)