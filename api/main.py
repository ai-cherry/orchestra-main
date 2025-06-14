from fastapi import FastAPI, Depends, HTTPException, Request

"""
Orchestra AI Admin API - Phase 2

Enhanced API with comprehensive database integration, file processing,
vector search, and advanced persona management capabilities.
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, UploadFile, File, Form, WebSocket, WebSocketDisconnect, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
import psutil
import os
import subprocess
import logging
from pathlib import Path
import structlog

# Import Phase 2 services
from api.database.connection import init_database, close_database, get_db, db_manager
from api.health_monitor import router as health_router
from database.models import (
    User, Persona, FileRecord, FileStatus, PersonaType, 
    SearchQuery, SearchMode, ProcessingJob
)
from database.vector_store import vector_store
from services.file_service import (
    enhanced_file_service, 
    FileUploadRequest, 
    FileUploadResponse,
    FileProcessingStatus,
    FileSearchRequest,
    FileSearchResult
)
from services.file_processor import file_processor
from services.websocket_service import websocket_service, heartbeat_task
from sqlalchemy.ext.asyncio import AsyncSession

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Security
security = HTTPBearer()

# Background task to update metrics
async def update_metrics():
    """Background task to update agent metrics"""
    while True:
        try:
            for agent in agents_db.values():
                if agent.status == "active":
                    # Simulate some activity
                    agent.requests_count += int(psutil.cpu_percent() / 10)
                    agent.memory_usage = min(90.0, agent.memory_usage + (psutil.cpu_percent() - 50) * 0.1)
                    agent.cpu_usage = max(0.0, min(100.0, psutil.cpu_percent() + (agent.requests_count % 10)))
                    agent.last_activity = datetime.now()
            
            await asyncio.sleep(10)  # Update every 10 seconds
        except Exception as e:
            logger.error("Error updating metrics", error=str(e))
            await asyncio.sleep(10)

# Background tasks
async def simulate_backup(backup_id: str):
    """Simulate backup process"""
    await asyncio.sleep(30)  # Simulate backup time
    
    activity_logs.append(ActivityLog(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        type="success",
        title="System backup completed",
        description=f"Backup {backup_id} completed successfully",
        component="backup-service",
        user=None
    ))

# Startup event
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the application"""
    try:
        # Initialize database
        await init_database()
        
        # Initialize services
        await enhanced_file_service.initialize()
        await vector_store.initialize()
        
        # Initialize sample data
        initialize_sample_data()
        
        # Start background tasks
        asyncio.create_task(update_metrics())
        asyncio.create_task(heartbeat_task())
        
        logger.info("Orchestra AI Admin API Phase 2 started successfully")
        yield
        
    except Exception as e:
        logger.error("Failed to initialize application", error=str(e))
        raise
    finally:
        # Cleanup
        await close_database()
        logger.info("Orchestra AI Admin API shutting down")

# Create FastAPI app
app = FastAPI(
    title="Orchestra AI Admin API - Phase 2",
    description="Enhanced admin API with comprehensive data integration and AI capabilities",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data Models for legacy compatibility
class AgentStatus(BaseModel):
    id: str
    name: str
    status: str  # active, idle, error, stopped
    requests_count: int
    success_rate: float
    avg_response_time: float
    last_activity: datetime
    memory_usage: float
    cpu_usage: float

class SystemMetrics(BaseModel):
    active_agents: int
    api_requests_per_minute: int
    memory_usage_percent: float
    cpu_usage_percent: float
    success_rate: float
    uptime_hours: float
    disk_usage_percent: float
    network_io: Dict[str, float]
    # Phase 2 additions
    database_status: str
    vector_store_status: str
    file_processing_queue: int
    total_files_processed: int

class WorkflowStatus(BaseModel):
    id: str
    name: str
    status: str  # active, paused, error, completed
    executions_today: int
    success_rate: float
    avg_execution_time: float
    last_run: datetime
    next_run: Optional[datetime]

class ActivityLog(BaseModel):
    id: str
    timestamp: datetime
    type: str  # info, warning, error, success
    title: str
    description: str
    component: str
    user: Optional[str]

class DeploymentRequest(BaseModel):
    agent_type: str
    name: str
    config: Dict[str, Any]

# Phase 2 API Models
class PersonaConfigRequest(BaseModel):
    persona_type: PersonaType
    name: str
    description: Optional[str] = None
    communication_style: Dict[str, Any]
    knowledge_domains: List[str]
    preferred_models: Dict[str, Any]
    behavior_config: Dict[str, Any]
    prompt_templates: Dict[str, Any]
    integration_preferences: Dict[str, Any]

class PersonaResponse(BaseModel):
    id: str
    persona_type: PersonaType
    name: str
    description: Optional[str]
    communication_style: Dict[str, Any]
    knowledge_domains: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class SearchRequest(BaseModel):
    query: str
    search_mode: SearchMode
    filters: Optional[Dict[str, Any]] = None
    limit: int = 10

class SearchResponse(BaseModel):
    query: str
    search_mode: SearchMode
    results: List[Dict[str, Any]]
    total_results: int
    response_time: float
    model_used: str

# In-memory storage (replace with real database for production)
agents_db: Dict[str, AgentStatus] = {}
workflows_db: Dict[str, WorkflowStatus] = {}
activity_logs: List[ActivityLog] = []
system_start_time = time.time()

# Initialize sample data
def initialize_sample_data():
    global agents_db, workflows_db, activity_logs
    
    # Sample agents (keeping existing for compatibility)
    agents_db = {
        "agent-001": AgentStatus(
            id="agent-001",
            name="Customer Support Agent",
            status="active",
            requests_count=247,
            success_rate=98.5,
            avg_response_time=1.2,
            last_activity=datetime.now(),
            memory_usage=45.2,
            cpu_usage=12.3
        ),
        "agent-002": AgentStatus(
            id="agent-002",
            name="Data Analysis Agent",
            status="active",
            requests_count=89,
            success_rate=94.1,
            avg_response_time=3.7,
            last_activity=datetime.now() - timedelta(minutes=5),
            memory_usage=67.8,
            cpu_usage=23.1
        ),
        "agent-003": AgentStatus(
            id="agent-003",
            name="Content Generator",
            status="idle",
            requests_count=12,
            success_rate=100.0,
            avg_response_time=5.1,
            last_activity=datetime.now() - timedelta(hours=2),
            memory_usage=23.4,
            cpu_usage=2.1
        )
    }
    
    # Sample workflows
    workflows_db = {
        "workflow-001": WorkflowStatus(
            id="workflow-001",
            name="Customer Onboarding",
            status="active",
            executions_today=142,
            success_rate=98.2,
            avg_execution_time=2.3,
            last_run=datetime.now() - timedelta(minutes=2),
            next_run=datetime.now() + timedelta(minutes=5)
        ),
        "workflow-002": WorkflowStatus(
            id="workflow-002",
            name="Lead Qualification",
            status="active",
            executions_today=89,
            success_rate=94.7,
            avg_execution_time=1.8,
            last_run=datetime.now() - timedelta(minutes=8),
            next_run=datetime.now() + timedelta(minutes=12)
        )
    }
    
    # Sample activity logs
    activity_logs = [
        ActivityLog(
            id=str(uuid.uuid4()),
            timestamp=datetime.now() - timedelta(minutes=2),
            type="success",
            title="Phase 2 system initialized",
            description="Enhanced file processing and vector search capabilities activated",
            component="system-init",
            user="system"
        ),
        ActivityLog(
            id=str(uuid.uuid4()),
            timestamp=datetime.now() - timedelta(minutes=5),
            type="info",
            title="Database connection established",
            description="PostgreSQL and vector store connections active",
            component="database",
            user="system"
        )
    ]

# Utility functions
async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract user ID from token (simplified for demo)"""
    # In production, this would validate JWT token and extract user ID
    return "demo-user-001"

# === CORE API ENDPOINTS ===

# Include health monitoring router
app.include_router(health_router)

@app.get("/")
async def root():
    return {
        "message": "Orchestra AI Admin API - Phase 2", 
        "status": "operational", 
        "version": "2.0.0",
        "features": [
            "Enhanced file processing",
            "Vector search capabilities", 
            "Advanced persona management",
            "Database integration",
            "Real-time notifications",
            "Health monitoring"
        ]
    }

@app.get("/api/system/status", response_model=SystemMetrics)
async def get_system_status():
    """Get enhanced system metrics and status"""
    try:
        # Get real system metrics
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        # Calculate derived metrics
        active_agents = len([a for a in agents_db.values() if a.status == "active"])
        total_requests = sum(a.requests_count for a in agents_db.values())
        avg_success_rate = sum(a.success_rate for a in agents_db.values()) / len(agents_db) if agents_db else 0
        uptime = (time.time() - system_start_time) / 3600  # hours
        
        # Phase 2 metrics
        db_status = "healthy" if await db_manager.health_check() else "error"
        vector_status = "healthy" if await vector_store.health_check() else "error"
        
        return SystemMetrics(
            active_agents=active_agents,
            api_requests_per_minute=total_requests // 60 if total_requests > 0 else 0,
            memory_usage_percent=memory.percent,
            cpu_usage_percent=cpu_percent,
            success_rate=avg_success_rate,
            uptime_hours=uptime,
            disk_usage_percent=(disk.used / disk.total) * 100,
            network_io={
                "bytes_sent": float(network.bytes_sent),
                "bytes_recv": float(network.bytes_recv)
            },
            database_status=db_status,
            vector_store_status=vector_status,
            file_processing_queue=len(enhanced_file_service.active_uploads),
            total_files_processed=0  # Would query from database
        )
    except Exception as e:
        logger.error("Error getting system status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get system status")

# === FILE MANAGEMENT ENDPOINTS ===

@app.post("/api/files/upload/initiate", response_model=FileUploadResponse)
async def initiate_file_upload(
    request: FileUploadRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Initiate a new file upload with enhanced processing"""
    try:
        response = await enhanced_file_service.initiate_upload(request, user_id, db)
        logger.info("File upload initiated", file_id=response.file_id, filename=request.filename)
        return response
    except Exception as e:
        logger.error("File upload initiation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/files/{file_id}/upload")
async def upload_file_chunk(
    file_id: str,
    chunk: UploadFile = File(...),
    chunk_offset: int = Form(0),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Upload file chunk with progress tracking"""
    try:
        chunk_data = await chunk.read()
        result = await enhanced_file_service.upload_chunk(file_id, chunk_data, chunk_offset, db)
        return result
    except Exception as e:
        logger.error("Chunk upload failed", file_id=file_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files/{file_id}/status", response_model=FileProcessingStatus)
async def get_file_status(
    file_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get file processing status"""
    try:
        return await enhanced_file_service.get_file_status(file_id, db)
    except Exception as e:
        logger.error("Failed to get file status", file_id=file_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/files/search", response_model=List[FileSearchResult])
async def search_files(
    request: FileSearchRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Search files using vector similarity and metadata filters"""
    try:
        results = await enhanced_file_service.search_files(request, user_id, db)
        logger.info("File search completed", query=request.query, results=len(results))
        return results
    except Exception as e:
        logger.error("File search failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files/{file_id}/content")
async def get_file_content(
    file_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get file content and metadata"""
    try:
        return await enhanced_file_service.get_file_content(file_id, user_id, db)
    except Exception as e:
        logger.error("Failed to get file content", file_id=file_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/files/{file_id}")
async def delete_file(
    file_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Delete a file and its associated data"""
    try:
        success = await enhanced_file_service.delete_file(file_id, user_id, db)
        if success:
            return {"message": "File deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="File deletion failed")
    except Exception as e:
        logger.error("File deletion failed", file_id=file_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# === PERSONA MANAGEMENT ENDPOINTS ===

@app.post("/api/personas", response_model=PersonaResponse)
async def create_persona(
    request: PersonaConfigRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new persona configuration"""
    try:
        from sqlalchemy import select
        
        # Check if persona already exists
        result = await db.execute(
            select(Persona).where(
                Persona.user_id == user_id,
                Persona.persona_type == request.persona_type
            )
        )
        existing_persona = result.scalar_one_or_none()
        
        if existing_persona:
            raise HTTPException(
                status_code=400, 
                detail=f"Persona {request.persona_type.value} already exists"
            )
        
        # Create new persona
        persona = Persona(
            user_id=user_id,
            persona_type=request.persona_type,
            name=request.name,
            description=request.description,
            communication_style=request.communication_style,
            knowledge_domains=request.knowledge_domains,
            preferred_models=request.preferred_models,
            behavior_config=request.behavior_config,
            prompt_templates=request.prompt_templates,
            integration_preferences=request.integration_preferences
        )
        
        db.add(persona)
        await db.commit()
        await db.refresh(persona)
        
        logger.info("Persona created", persona_id=str(persona.id), type=request.persona_type.value)
        
        return PersonaResponse(
            id=str(persona.id),
            persona_type=persona.persona_type,
            name=persona.name,
            description=persona.description,
            communication_style=persona.communication_style,
            knowledge_domains=persona.knowledge_domains,
            is_active=persona.is_active,
            created_at=persona.created_at,
            updated_at=persona.updated_at
        )
        
    except Exception as e:
        logger.error("Persona creation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/personas", response_model=List[PersonaResponse])
async def get_personas(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get all personas for the current user"""
    try:
        from sqlalchemy import select
        
        result = await db.execute(
            select(Persona).where(Persona.user_id == user_id)
        )
        personas = result.scalars().all()
        
        return [
            PersonaResponse(
                id=str(p.id),
                persona_type=p.persona_type,
                name=p.name,
                description=p.description,
                communication_style=p.communication_style,
                knowledge_domains=p.knowledge_domains,
                is_active=p.is_active,
                created_at=p.created_at,
                updated_at=p.updated_at
            )
            for p in personas
        ]
        
    except Exception as e:
        logger.error("Failed to get personas", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/personas/{persona_id}", response_model=PersonaResponse)
async def update_persona(
    persona_id: str,
    request: PersonaConfigRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update persona configuration"""
    try:
        from sqlalchemy import select, update
        
        # Get existing persona
        result = await db.execute(
            select(Persona).where(
                Persona.id == persona_id,
                Persona.user_id == user_id
            )
        )
        persona = result.scalar_one_or_none()
        
        if not persona:
            raise HTTPException(status_code=404, detail="Persona not found")
        
        # Update persona
        await db.execute(
            update(Persona)
            .where(Persona.id == persona_id)
            .values(
                name=request.name,
                description=request.description,
                communication_style=request.communication_style,
                knowledge_domains=request.knowledge_domains,
                preferred_models=request.preferred_models,
                behavior_config=request.behavior_config,
                prompt_templates=request.prompt_templates,
                integration_preferences=request.integration_preferences,
                updated_at=datetime.utcnow()
            )
        )
        await db.commit()
        
        # Refresh persona
        await db.refresh(persona)
        
        logger.info("Persona updated", persona_id=persona_id)
        
        return PersonaResponse(
            id=str(persona.id),
            persona_type=persona.persona_type,
            name=persona.name,
            description=persona.description,
            communication_style=persona.communication_style,
            knowledge_domains=persona.knowledge_domains,
            is_active=persona.is_active,
            created_at=persona.created_at,
            updated_at=persona.updated_at
        )
        
    except Exception as e:
        logger.error("Persona update failed", persona_id=persona_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# === SEARCH ENDPOINTS ===

@app.post("/api/search", response_model=SearchResponse)
async def multi_modal_search(
    request: SearchRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Multi-modal search across different modes"""
    try:
        start_time = time.time()
        
        # Create search query record
        search_query = SearchQuery(
            user_id=user_id,
            query_text=request.query,
            search_mode=request.search_mode,
            filters=request.filters or {}
        )
        
        db.add(search_query)
        await db.commit()
        
        # Perform search based on mode
        if request.search_mode == SearchMode.BASIC:
            results = await _basic_search(request, user_id, db)
        elif request.search_mode == SearchMode.DEEP:
            results = await _deep_search(request, user_id, db)
        elif request.search_mode == SearchMode.SUPER_DEEP:
            results = await _super_deep_search(request, user_id, db)
        elif request.search_mode == SearchMode.CREATIVE:
            results = await _creative_search(request, user_id, db)
        elif request.search_mode == SearchMode.PRIVATE:
            results = await _private_search(request, user_id, db)
        elif request.search_mode == SearchMode.UNCENSORED:
            results = await _uncensored_search(request, user_id, db)
        else:
            results = await _basic_search(request, user_id, db)
        
        response_time = time.time() - start_time
        
        # Update search query with results
        search_query.result_count = len(results)
        search_query.results = results
        search_query.response_time = response_time
        search_query.model_used = "sentence-transformers/all-MiniLM-L6-v2"  # Default model
        await db.commit()
        
        logger.info(
            "Search completed", 
            mode=request.search_mode.value,
            query=request.query,
            results=len(results),
            response_time=response_time
        )
        
        return SearchResponse(
            query=request.query,
            search_mode=request.search_mode,
            results=results,
            total_results=len(results),
            response_time=response_time,
            model_used="sentence-transformers/all-MiniLM-L6-v2"
        )
        
    except Exception as e:
        logger.error("Search failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Search implementations
async def _basic_search(request: SearchRequest, user_id: str, db) -> List[Dict[str, Any]]:
    """Basic search implementation"""
    file_search_request = FileSearchRequest(
        query=request.query,
        limit=request.limit
    )
    results = await enhanced_file_service.search_files(file_search_request, user_id, db)
    
    return [
        {
            "id": r.file_id,
            "title": r.filename,
            "content": r.snippet,
            "relevance_score": r.relevance_score,
            "metadata": r.metadata,
            "source": "files"
        }
        for r in results
    ]

async def _deep_search(request: SearchRequest, user_id: str, db) -> List[Dict[str, Any]]:
    """Deep search with comprehensive analysis"""
    # Start with basic file search
    basic_results = await _basic_search(request, user_id, db)
    
    # TODO: Add AI analysis and synthesis
    # For now, return enhanced basic results
    return basic_results

async def _super_deep_search(request: SearchRequest, user_id: str, db) -> List[Dict[str, Any]]:
    """Super deep search with multi-step reasoning"""
    # Start with deep search
    deep_results = await _deep_search(request, user_id, db)
    
    # TODO: Add multi-step reasoning and cross-reference analysis
    return deep_results

async def _creative_search(request: SearchRequest, user_id: str, db) -> List[Dict[str, Any]]:
    """Creative search for inspiration and ideation"""
    # Start with basic search
    results = await _basic_search(request, user_id, db)
    
    # TODO: Add creative connections and novel insights
    return results

async def _private_search(request: SearchRequest, user_id: str, db) -> List[Dict[str, Any]]:
    """Private search with enhanced security"""
    # Same as basic search but with additional security measures
    results = await _basic_search(request, user_id, db)
    
    # TODO: Add privacy protections and access controls
    return results

async def _uncensored_search(request: SearchRequest, user_id: str, db) -> List[Dict[str, Any]]:
    """Uncensored search for comprehensive coverage"""
    # Same as basic search but without content filtering
    results = await _basic_search(request, user_id, db)
    
    # TODO: Add unrestricted information access
    return results

# === LEGACY ENDPOINTS (for compatibility) ===

@app.get("/api/agents", response_model=List[AgentStatus])
async def get_agents():
    """Get all AI agents and their status"""
    return list(agents_db.values())

@app.get("/api/agents/{agent_id}", response_model=AgentStatus)
async def get_agent(agent_id: str):
    """Get specific agent details"""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agents_db[agent_id]

@app.post("/api/agents/{agent_id}/start")
async def start_agent(agent_id: str):
    """Start an agent"""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agents_db[agent_id].status = "active"
    agents_db[agent_id].last_activity = datetime.now()
    return {"message": f"Agent {agent_id} started successfully"}

@app.get("/api/workflows", response_model=List[WorkflowStatus])
async def get_workflows():
    """Get all workflows and their status"""
    return list(workflows_db.values())

@app.get("/api/activity", response_model=List[ActivityLog])
async def get_activity_logs(limit: int = 50):
    """Get recent activity logs"""
    return sorted(activity_logs, key=lambda x: x.timestamp, reverse=True)[:limit]

# === WEBSOCKET ENDPOINTS ===

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time communication"""
    try:
        await websocket_service.connect(websocket, user_id)
        
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message.get("type") == "file_upload_progress":
                    # File upload progress updates are handled by the file service
                    pass
                elif message.get("type") == "search_query":
                    # Real-time search results could be sent here
                    pass
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error("WebSocket message handling failed", user_id=user_id, error=str(e))
                break
                
    except Exception as e:
        logger.error("WebSocket connection failed", user_id=user_id, error=str(e))
    finally:
        await websocket_service.disconnect(user_id)

# === HEALTH CHECK ENDPOINTS ===

@app.get("/api/health")
async def health_check():
    """Comprehensive health check"""
    try:
        # Check database
        db_healthy = await db_manager.health_check()
        
        # Check vector store
        vector_healthy = await vector_store.health_check()
        
        # Check file service
        file_service_healthy = True  # Could add specific health check
        
        health_status = {
            "status": "healthy" if all([db_healthy, vector_healthy, file_service_healthy]) else "unhealthy",
            "database": "healthy" if db_healthy else "unhealthy",
            "vector_store": "healthy" if vector_healthy else "unhealthy", 
            "file_service": "healthy" if file_service_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0"
        }
        
        return health_status
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 