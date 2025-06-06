#!/usr/bin/env python3
"""
AI Collaboration Dashboard API Endpoints
FastAPI implementation with WebSocket support and comprehensive error handling
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import uuid

from ..service import AICollaborationService
from ..models.dto import (
    CreateAgentRequest, CreateAgentResponse,
    CreateTaskRequest, CreateTaskResponse,
    UpdateTaskRequest, TaskResponse,
    MetricRequest, MetricResponse,
    CollaborationEventResponse
)
from ..models.enums import TaskStatus, MetricType, EventType, AIAgentType
from ..exceptions import (
    AICollaborationError, ValidationError, ResourceNotFoundError,
    ResourceConflictError, ServiceUnavailableError
)


logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/ai-collaboration",
    tags=["ai-collaboration"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, str] = {}


class DashboardStats(BaseModel):
    """Dashboard statistics response"""
    total_agents: int
    active_agents: int
    total_tasks: int
    tasks_by_status: Dict[str, int]
    avg_completion_time: float
    success_rate: float
    events_last_hour: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WebSocketManager:
    """Manage WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.connection_metadata[client_id] = {
            "connected_at": datetime.utcnow(),
            "subscriptions": set()
        }
        logger.info(f"WebSocket client {client_id} connected")
    
    def disconnect(self, client_id: str):
        """Remove WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            del self.connection_metadata[client_id]
            logger.info(f"WebSocket client {client_id} disconnected")
    
    async def send_personal_message(self, message: str, client_id: str):
        """Send message to specific client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: str, event_type: Optional[str] = None):
        """Broadcast message to all connected clients"""
        disconnected_clients = []
        
        for client_id, websocket in self.active_connections.items():
            try:
                # Check if client is subscribed to this event type
                if event_type:
                    subscriptions = self.connection_metadata[client_id].get("subscriptions", set())
                    if event_type not in subscriptions and "*" not in subscriptions:
                        continue
                
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    def subscribe(self, client_id: str, event_types: List[str]):
        """Subscribe client to specific event types"""
        if client_id in self.connection_metadata:
            self.connection_metadata[client_id]["subscriptions"].update(event_types)


# Global WebSocket manager
ws_manager = WebSocketManager()

# Dependency to get service instance
async def get_service() -> AICollaborationService:
    """Get AI Collaboration Service instance"""
    # In production, this would be properly injected
    # For now, return a placeholder
    return None  # Will be injected by the application


# Health endpoints
@router.get("/health", response_model=HealthResponse)
async def health_check(service: AICollaborationService = Depends(get_service)):
    """Check service health"""
    try:
        # Check service components
        services = {}
        
        # Database health
        try:
            await service.database.fetch_one("SELECT 1")
            services["database"] = "healthy"
        except Exception:
            services["database"] = "unhealthy"
        
        # Cache health
        try:
            await service.cache.set("health_check", "ok", ttl=1)
            services["cache"] = "healthy"
        except Exception:
            services["cache"] = "unhealthy"
        
        # Vector store health
        try:
            await service.vector_store.health_check()
            services["vector_store"] = "healthy"
        except Exception:
            services["vector_store"] = "unhealthy"
        
        # Overall status
        all_healthy = all(status == "healthy" for status in services.values())
        
        return HealthResponse(
            status="healthy" if all_healthy else "degraded",
            services=services
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@router.get("/status", response_model=DashboardStats)
async def get_dashboard_status(
    service: AICollaborationService = Depends(get_service)
):
    """Get dashboard statistics"""
    try:
        # Get agent stats
        agents = await service.get_agents()
        active_agents = [a for a in agents if a.status == "active"]
        
        # Get task stats
        tasks = await service.get_tasks(limit=1000)
        tasks_by_status = defaultdict(int)
        completion_times = []
        
        for task in tasks:
            tasks_by_status[task.status.value] += 1
            if task.status == TaskStatus.COMPLETED and task.metadata.get("completion_time"):
                completion_times.append(task.metadata["completion_time"])
        
        # Calculate metrics
        avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0
        total_completed = tasks_by_status.get(TaskStatus.COMPLETED.value, 0)
        total_failed = tasks_by_status.get(TaskStatus.FAILED.value, 0)
        success_rate = total_completed / (total_completed + total_failed) if (total_completed + total_failed) > 0 else 0
        
        # Get recent events
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_events = await service.get_events(start_time=one_hour_ago)
        
        return DashboardStats(
            total_agents=len(agents),
            active_agents=len(active_agents),
            total_tasks=len(tasks),
            tasks_by_status=dict(tasks_by_status),
            avg_completion_time=avg_completion_time,
            success_rate=success_rate,
            events_last_hour=len(recent_events)
        )
        
    except Exception as e:
        logger.error(f"Error getting dashboard status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Agent endpoints
@router.post("/agents", response_model=CreateAgentResponse)
async def create_agent(
    request: CreateAgentRequest,
    service: AICollaborationService = Depends(get_service)
):
    """Create a new AI agent"""
    try:
        agent = await service.create_agent(
            name=request.name,
            agent_type=request.type,
            capabilities=request.capabilities,
            metadata=request.metadata
        )
        
        # Broadcast new agent event
        event = {
            "type": "agent_created",
            "data": {
                "id": agent.id,
                "name": agent.name,
                "type": agent.type.value
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        await ws_manager.broadcast(json.dumps(event), "agent_created")
        
        return CreateAgentResponse(
            id=agent.id,
            name=agent.name,
            type=agent.type,
            status=agent.status,
            capabilities=agent.capabilities,
            created_at=agent.created_at
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents", response_model=List[CreateAgentResponse])
async def list_agents(
    agent_type: Optional[AIAgentType] = None,
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    service: AICollaborationService = Depends(get_service)
):
    """List AI agents with optional filtering"""
    try:
        agents = await service.get_agents(
            agent_type=agent_type,
            status=status,
            limit=limit
        )
        
        return [
            CreateAgentResponse(
                id=agent.id,
                name=agent.name,
                type=agent.type,
                status=agent.status,
                capabilities=agent.capabilities,
                created_at=agent.created_at
            )
            for agent in agents
        ]
        
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}", response_model=CreateAgentResponse)
async def get_agent(
    agent_id: str,
    service: AICollaborationService = Depends(get_service)
):
    """Get specific agent details"""
    try:
        agents = await service.get_agents(limit=1000)
        agent = next((a for a in agents if a.id == agent_id), None)
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return CreateAgentResponse(
            id=agent.id,
            name=agent.name,
            type=agent.type,
            status=agent.status,
            capabilities=agent.capabilities,
            created_at=agent.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Task endpoints
@router.post("/tasks", response_model=CreateTaskResponse)
async def create_task(
    request: CreateTaskRequest,
    background_tasks: BackgroundTasks,
    service: AICollaborationService = Depends(get_service)
):
    """Create a new task"""
    try:
        task = await service.create_task(
            title=request.title,
            description=request.description,
            agent_type=request.agent_type,
            priority=request.priority,
            payload=request.payload,
            metadata=request.metadata
        )
        
        # Schedule task assignment in background
        background_tasks.add_task(
            service.assign_task,
            task.id
        )
        
        # Broadcast new task event
        event = {
            "type": "task_created",
            "data": {
                "id": task.id,
                "title": task.title,
                "agent_type": task.agent_type.value,
                "priority": task.priority
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        await ws_manager.broadcast(json.dumps(event), "task_created")
        
        return CreateTaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            agent_type=task.agent_type,
            status=task.status,
            priority=task.priority,
            created_at=task.created_at
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    status: Optional[TaskStatus] = None,
    agent_type: Optional[AIAgentType] = None,
    assigned_to: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    service: AICollaborationService = Depends(get_service)
):
    """List tasks with optional filtering"""
    try:
        tasks = await service.get_tasks(
            status=status,
            agent_type=agent_type,
            assigned_to=assigned_to,
            limit=limit
        )
        
        return [
            TaskResponse(
                id=task.id,
                title=task.title,
                description=task.description,
                agent_type=task.agent_type,
                status=task.status,
                priority=task.priority,
                assigned_to=task.assigned_to,
                created_at=task.created_at,
                updated_at=task.updated_at,
                metadata=task.metadata
            )
            for task in tasks
        ]
        
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    service: AICollaborationService = Depends(get_service)
):
    """Get specific task details"""
    try:
        tasks = await service.get_tasks(limit=1000)
        task = next((t for t in tasks if t.id == task_id), None)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            agent_type=task.agent_type,
            status=task.status,
            priority=task.priority,
            assigned_to=task.assigned_to,
            created_at=task.created_at,
            updated_at=task.updated_at,
            metadata=task.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    request: UpdateTaskRequest,
    service: AICollaborationService = Depends(get_service)
):
    """Update task status or metadata"""
    try:
        task = await service.update_task_status(
            task_id=task_id,
            status=request.status,
            metadata=request.metadata
        )
        
        # Broadcast task update event
        event = {
            "type": "task_updated",
            "data": {
                "id": task.id,
                "status": task.status.value,
                "assigned_to": task.assigned_to
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        await ws_manager.broadcast(json.dumps(event), "task_updated")
        
        return TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            agent_type=task.agent_type,
            status=task.status,
            priority=task.priority,
            assigned_to=task.assigned_to,
            created_at=task.created_at,
            updated_at=task.updated_at,
            metadata=task.metadata
        )
        
    except ResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Task not found")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Metrics endpoints
@router.post("/metrics", response_model=MetricResponse)
async def record_metric(
    request: MetricRequest,
    service: AICollaborationService = Depends(get_service)
):
    """Record a new metric"""
    try:
        metric = await service.record_metric(
            agent_id=request.agent_id,
            metric_type=request.type,
            value=request.value,
            metadata=request.metadata
        )
        
        return MetricResponse(
            id=metric.id,
            agent_id=metric.agent_id,
            type=metric.type,
            value=metric.value,
            timestamp=metric.timestamp
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error recording metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=List[MetricResponse])
async def list_metrics(
    agent_id: Optional[str] = None,
    metric_type: Optional[MetricType] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000),
    service: AICollaborationService = Depends(get_service)
):
    """List metrics with optional filtering"""
    try:
        metrics = await service.get_metrics(
            agent_id=agent_id,
            metric_type=metric_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        return [
            MetricResponse(
                id=metric.id,
                agent_id=metric.agent_id,
                type=metric.type,
                value=metric.value,
                timestamp=metric.timestamp
            )
            for metric in metrics
        ]
        
    except Exception as e:
        logger.error(f"Error listing metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/aggregated")
async def get_aggregated_metrics(
    agent_id: str,
    metric_type: MetricType,
    window: str = "hour",
    service: AICollaborationService = Depends(get_service)
):
    """Get aggregated metrics for an agent"""
    try:
        # Map window string to enum
        from ..metrics.collector import AggregationWindow
        window_map = {
            "minute": AggregationWindow.MINUTE,
            "5minutes": AggregationWindow.FIVE_MINUTES,
            "hour": AggregationWindow.HOUR,
            "day": AggregationWindow.DAY
        }
        
        if window not in window_map:
            raise HTTPException(status_code=400, detail="Invalid aggregation window")
        
        stats = await service.metrics_collector.get_aggregated_metrics(
            agent_id=agent_id,
            metric_type=metric_type,
            window=window_map[window]
        )
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting aggregated metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Events endpoints
@router.get("/events", response_model=List[CollaborationEventResponse])
async def list_events(
    event_type: Optional[EventType] = None,
    agent_id: Optional[str] = None,
    task_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000),
    service: AICollaborationService = Depends(get_service)
):
    """List collaboration events with optional filtering"""
    try:
        events = await service.get_events(
            event_type=event_type,
            agent_id=agent_id,
            task_id=task_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        return [
            CollaborationEventResponse(
                id=event.id,
                type=event.type,
                agent_id=event.agent_id,
                task_id=event.task_id,
                data=event.data,
                timestamp=event.timestamp
            )
            for event in events
        ]
        
    except Exception as e:
        logger.error(f"Error listing events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint
@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    service: AICollaborationService = Depends(get_service)
):
    """WebSocket endpoint for real-time updates"""
    await ws_manager.connect(websocket, client_id)
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        while True:
            # Receive messages from client
            data = await websocket.receive_json()
            
            # Handle different message types
            if data.get("type") == "subscribe":
                # Subscribe to specific event types
                event_types = data.get("events", ["*"])
                ws_manager.subscribe(client_id, event_types)
                
                await websocket.send_json({
                    "type": "subscription",
                    "status": "subscribed",
                    "events": event_types,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            elif data.get("type") == "ping":
                # Respond to ping
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            else:
                # Echo unknown messages
                await websocket.send_json({
                    "type": "error",
                    "message": "Unknown message type",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    except WebSocketDisconnect:
        ws_manager.disconnect(client_id)
        logger.info(f"WebSocket client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        ws_manager.disconnect(client_id)


# Utility endpoints
@router.get("/agent-types")
async def get_agent_types():
    """Get available agent types"""
    return [
        {
            "value": agent_type.value,
            "name": agent_type.name,
            "description": f"{agent_type.value.replace('_', ' ').title()} Agent"
        }
        for agent_type in AIAgentType
    ]


@router.get("/task-statuses")
async def get_task_statuses():
    """Get available task statuses"""
    return [
        {
            "value": status.value,
            "name": status.name,
            "description": status.value.replace('_', ' ').title()
        }
        for status in TaskStatus
    ]


@router.get("/metric-types")
async def get_metric_types():
    """Get available metric types"""
    return [
        {
            "value": metric_type.value,
            "name": metric_type.name,
            "description": metric_type.value.replace('_', ' ').title()
        }
        for metric_type in MetricType
    ]


@router.get("/event-types")
async def get_event_types():
    """Get available event types"""
    return [
        {
            "value": event_type.value,
            "name": event_type.name,
            "description": event_type.value.replace('_', ' ').title()
        }
        for event_type in EventType
    ]