"""
"""
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
    """Request for natural language data upload."""
    query: str = Field(..., description="Natural language description of data to upload")
    content: str = Field(..., description="The actual content to ingest")
    auto_detect_source: bool = True

class StreamingUploadResponse(BaseModel):
    """Response for streaming upload progress."""
@router.post("/upload/sync", response_model=List[UploadResponseV2])
async def upload_files_sync(
    files: List[UploadFile] = File(...),
    request_data: UploadRequestV2 = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    """
                user_id=current_user["id"],
                metadata={"filename": file.filename}
            )
            
            # Read file content
            content = await file.read()
            
            # Check for existing similar content
            existing_query = """
            """
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
                """
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
    """
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
    Example: "Upload this Slack conversation about the Q4 planning meeting"
    """
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
    """
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
    
    except Exception:

    
        pass
        manager.disconnect(client_id)

# Streaming endpoint

@router.post("/upload/stream")
async def upload_stream(
    request: UploadRequestV2 = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    """
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
    """
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
            "tracking_id": tracking_id,
            "status": "processing",
            "progress": 0.5
        }),
        tracking_id
    )

async def get_upload_status(tracking_id: str, db: AsyncSession) -> Dict[str, Any]:
    """Get current status of an upload."""
        "tracking_id": tracking_id,
        "status": "processing",
        "progress": 0.75,
        "message": "Checking for duplicates..."
    }