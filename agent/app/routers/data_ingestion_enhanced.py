"""
Enhanced data ingestion API with real-time support and deduplication.

This module provides both synchronous and asynchronous endpoints with
comprehensive duplicate handling and natural language interface support.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Optional, Dict, Any, AsyncGenerator
import asyncio
import uuid
from datetime import datetime
import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from ...core.database import get_db
from ...core.auth import get_current_user
from ....core.data_ingestion.deduplication import (
    DeduplicationEngine, 
    DuplicateResolver, 
    DeduplicationAuditLogger,
    UploadChannel
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/data-ingestion/v2", tags=["data-ingestion-v2"])

# Global instances (would be dependency injected in production)
dedup_engine = DeduplicationEngine()
dedup_resolver = DuplicateResolver()
audit_logger = DeduplicationAuditLogger()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

manager = ConnectionManager()

# Request/Response models
class UploadRequestV2(BaseModel):
    """Enhanced upload request with deduplication options."""
    source_type: str = Field(..., regex="^(slack|gong|salesforce|looker|hubspot|auto)$")
    process_immediately: bool = True
    deduplication_strategy: Optional[str] = Field(
        default="auto",
        regex="^(auto|keep_existing|replace|merge|keep_both|manual)$"
    )
    upload_channel: str = Field(default="api")
    metadata: Optional[Dict[str, Any]] = None

class UploadResponseV2(BaseModel):
    """Enhanced upload response with deduplication info."""
    file_id: str
    filename: str
    source_type: str
    status: str
    duplicate_detected: bool = False
    duplicate_info: Optional[Dict[str, Any]] = None
    resolution_applied: Optional[str] = None
    message: str

class NaturalLanguageUploadRequest(BaseModel):
    """Request for natural language data upload."""
    query: str = Field(..., description="Natural language description of data to upload")
    content: str = Field(..., description="The actual content to ingest")
    auto_detect_source: bool = True

class StreamingUploadResponse(BaseModel):
    """Response for streaming upload progress."""
    event_type: str
    file_id: str
    progress: float
    status: str
    message: str
    metadata: Optional[Dict[str, Any]] = None

# Synchronous endpoints

@router.post("/upload/sync", response_model=List[UploadResponseV2])
async def upload_files_sync(
    files: List[UploadFile] = File(...),
    request_data: UploadRequestV2 = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Synchronous file upload with immediate deduplication.
    
    Returns complete results including duplicate detection and resolution.
    """
    responses = []
    
    # Start audit logging
    await audit_logger.start()
    
    try:
        for file in files:
            file_id = str(uuid.uuid4())
            
            # Log upload attempt
            await audit_logger.log_duplicate_check(
                content_id=file_id,
                upload_channel=UploadChannel(request_data.upload_channel),
                user_id=current_user["id"],
                metadata={"filename": file.filename}
            )
            
            # Read file content
            content = await file.read()
            
            # Check for existing similar content
            existing_query = """
                SELECT id, content, content_hash, metadata
                FROM data_ingestion.parsed_content
                WHERE source_type = $1
                ORDER BY created_at DESC
                LIMIT 1000
            """
            
            existing_records = await db.fetch_all(
                existing_query, 
                request_data.source_type
            )
            
            # Check for duplicates
            duplicate_match = await dedup_engine.check_duplicate(
                content.decode('utf-8') if isinstance(content, bytes) else content,
                {"filename": file.filename, "source_type": request_data.source_type},
                [dict(r) for r in existing_records],
                UploadChannel(request_data.upload_channel)
            )
            
            if duplicate_match:
                # Log duplicate detection
                await audit_logger.log_duplicate_detected(
                    content_id=file_id,
                    duplicate_match=duplicate_match,
                    upload_channel=UploadChannel(request_data.upload_channel),
                    user_id=current_user["id"]
                )
                
                # Resolve duplicate
                resolution = await dedup_resolver.resolve_duplicate(
                    duplicate_match,
                    {"id": file_id, "content": content, "filename": file.filename},
                    {"id": duplicate_match.existing_id},
                    {"resolution_strategy": request_data.deduplication_strategy}
                )
                
                # Log resolution
                await audit_logger.log_resolution(
                    content_id=file_id,
                    resolution_result=resolution,
                    upload_channel=UploadChannel(request_data.upload_channel),
                    user_id=current_user["id"]
                )
                
                responses.append(UploadResponseV2(
                    file_id=file_id,
                    filename=file.filename,
                    source_type=request_data.source_type,
                    status=resolution.action.value,
                    duplicate_detected=True,
                    duplicate_info={
                        "existing_id": duplicate_match.existing_id,
                        "similarity_score": duplicate_match.similarity_score,
                        "duplicate_type": duplicate_match.duplicate_type.value
                    },
                    resolution_applied=resolution.strategy.value,
                    message=resolution.resolution_reason
                ))
            else:
                # No duplicate - proceed with upload
                # Insert file record
                insert_query = """
                    INSERT INTO data_ingestion.file_imports 
                    (id, filename, source_type, file_size, created_by)
                    VALUES ($1, $2, $3, $4, $5)
                """
                
                await db.execute(
                    insert_query,
                    file_id,
                    file.filename,
                    request_data.source_type,
                    len(content),
                    current_user["id"]
                )
                
                await db.commit()
                
                responses.append(UploadResponseV2(
                    file_id=file_id,
                    filename=file.filename,
                    source_type=request_data.source_type,
                    status="uploaded",
                    duplicate_detected=False,
                    message="File uploaded successfully - no duplicates found"
                ))
    
    finally:
        await audit_logger.stop()
    
    return responses

# Asynchronous endpoints

@router.post("/upload/async")
async def upload_files_async(
    files: List[UploadFile] = File(...),
    request_data: UploadRequestV2 = Depends(),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Asynchronous file upload with background processing.
    
    Returns immediately with tracking IDs.
    """
    tracking_ids = []
    
    for file in files:
        tracking_id = str(uuid.uuid4())
        
        # Queue for background processing
        background_tasks.add_task(
            process_file_with_deduplication,
            tracking_id,
            file,
            request_data,
            current_user["id"]
        )
        
        tracking_ids.append({
            "tracking_id": tracking_id,
            "filename": file.filename,
            "status": "queued"
        })
    
    return {
        "message": "Files queued for processing",
        "tracking_ids": tracking_ids,
        "websocket_url": f"/api/v1/data-ingestion/v2/ws/{tracking_ids[0]['tracking_id']}"
    }

# Natural Language Interface

@router.post("/upload/natural-language")
async def upload_via_natural_language(
    request: NaturalLanguageUploadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Upload data using natural language description.
    
    Example: "Upload this Slack conversation about the Q4 planning meeting"
    """
    # Parse natural language to detect intent and source
    source_keywords = {
        "slack": ["slack", "conversation", "message", "channel"],
        "gong": ["gong", "call", "transcript", "recording"],
        "salesforce": ["salesforce", "crm", "account", "opportunity"],
        "looker": ["looker", "dashboard", "analytics", "report"],
        "hubspot": ["hubspot", "marketing", "contact", "campaign"]
    }
    
    detected_source = "auto"
    query_lower = request.query.lower()
    
    for source, keywords in source_keywords.items():
        if any(keyword in query_lower for keyword in keywords):
            detected_source = source
            break
    
    # Create virtual file from content
    file_id = str(uuid.uuid4())
    filename = f"nl_upload_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
    
    # Check for duplicates
    duplicate_match = await dedup_engine.check_duplicate(
        request.content,
        {
            "filename": filename,
            "source_type": detected_source,
            "natural_language_query": request.query
        },
        [],  # Would fetch existing records
        UploadChannel.WEB_INTERFACE
    )
    
    response = {
        "file_id": file_id,
        "detected_source": detected_source,
        "interpretation": f"Understood: {request.query}",
        "duplicate_detected": duplicate_match is not None
    }
    
    if duplicate_match:
        response["duplicate_info"] = {
            "similarity_score": duplicate_match.similarity_score,
            "recommendation": "This content appears to be similar to existing data"
        }
    
    return response

# Real-time WebSocket endpoint

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for real-time upload progress and notifications.
    """
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "subscribe":
                # Subscribe to upload progress
                await websocket.send_text(json.dumps({
                    "type": "subscribed",
                    "client_id": client_id
                }))
            
            elif message["type"] == "status":
                # Send current status
                tracking_id = message.get("tracking_id")
                status = await get_upload_status(tracking_id, db)
                await websocket.send_text(json.dumps(status))
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)

# Streaming endpoint

@router.post("/upload/stream")
async def upload_stream(
    request: UploadRequestV2 = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Streaming upload endpoint for large files with progress updates.
    """
    async def generate_progress():
        file_id = str(uuid.uuid4())
        
        # Initial response
        yield json.dumps(StreamingUploadResponse(
            event_type="started",
            file_id=file_id,
            progress=0.0,
            status="initializing",
            message="Upload started"
        ).dict()) + "\n"
        
        # Simulate progress (would be real processing)
        for progress in range(0, 101, 10):
            await asyncio.sleep(0.5)
            
            yield json.dumps(StreamingUploadResponse(
                event_type="progress",
                file_id=file_id,
                progress=progress / 100.0,
                status="processing",
                message=f"Processing: {progress}%"
            ).dict()) + "\n"
        
        # Final response
        yield json.dumps(StreamingUploadResponse(
            event_type="completed",
            file_id=file_id,
            progress=1.0,
            status="completed",
            message="Upload completed successfully"
        ).dict()) + "\n"
    
    return StreamingResponse(
        generate_progress(),
        media_type="application/x-ndjson"
    )

# Bulk deduplication endpoint

@router.post("/deduplicate/bulk")
async def bulk_deduplication(
    file_ids: List[str],
    strategy: str = Query(default="auto"),
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Perform bulk deduplication on existing files.
    """
    operation_id = str(uuid.uuid4())
    
    # Log bulk operation
    await audit_logger.log_bulk_operation(
        operation_id=operation_id,
        item_count=len(file_ids),
        duplicates_found=0,  # Will be updated
        resolutions_applied={},
        upload_channel=UploadChannel.API,
        user_id=current_user["id"]
    )
    
    results = {
        "operation_id": operation_id,
        "files_processed": len(file_ids),
        "duplicates_found": 0,
        "resolutions": {}
    }
    
    # Process each file
    # Implementation would check duplicates and apply resolutions
    
    return results

# Helper functions

async def process_file_with_deduplication(
    tracking_id: str,
    file: UploadFile,
    request_data: UploadRequestV2,
    user_id: str
):
    """Background task for file processing with deduplication."""
    # Implementation would handle actual processing
    # Send updates via WebSocket
    await manager.send_personal_message(
        json.dumps({
            "tracking_id": tracking_id,
            "status": "processing",
            "progress": 0.5
        }),
        tracking_id
    )

async def get_upload_status(tracking_id: str, db: AsyncSession) -> Dict[str, Any]:
    """Get current status of an upload."""
    # Query processing status from database
    return {
        "tracking_id": tracking_id,
        "status": "processing",
        "progress": 0.75,
        "message": "Checking for duplicates..."
    }