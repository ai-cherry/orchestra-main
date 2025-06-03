# TODO: Consider adding connection pooling configuration
"""
"""
router = APIRouter(prefix="/api/v1/data-ingestion", tags=["data-ingestion"])

# Pydantic models for request/response
class FileUploadResponse(BaseModel):
    """Response model for file upload."""
    """Response model for processing status."""
    """Request model for data queries."""
    """Response model for query results."""
UPLOAD_DIR = Path("/tmp/data_ingestion_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

@router.post("/upload", response_model=List[FileUploadResponse])
async def upload_files(
    files: List[UploadFile] = File(...),
    source_type: str = Query(..., regex="^(slack|gong|salesforce|looker|hubspot)$"),
    process_immediately: bool = Query(default=True),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    """
            temp_file_path = UPLOAD_DIR / f"{uuid.uuid4()}_{file.filename}"
            
            # Save uploaded file
            async with aiofiles.open(temp_file_path, 'wb') as f:
                while chunk := await file.read(8192):  # Read in 8KB chunks
                    file_size += len(chunk)
                    if file_size > MAX_FILE_SIZE:
                        await f.close()
                        os.unlink(temp_file_path)
                        raise HTTPException(
                            status_code=413,
                            detail=f"File {file.filename} exceeds maximum size of 500MB"
                        )
                    await f.write(chunk)
            
            # Create database record
            file_id = str(uuid.uuid4())
            
            # Insert into file_imports table
            insert_query = """
            """
                current_user["id"]
            )
            
            # Queue for processing if requested
            if process_immediately:
                # Add to processing queue
                queue_query = """
                """
                status="queued" if process_immediately else "uploaded",
                message=f"File uploaded successfully"
            ))
            
        except Exception:

            
            pass
            raise
        except Exception:

            pass
            logger.error(f"Error uploading file {file.filename}: {e}")
            responses.append(FileUploadResponse(
                file_id="",
                filename=file.filename,
                source_type=source_type,
                status="error",
                message=str(e)
            ))
    
    return responses

@router.post("/upload-zip", response_model=FileUploadResponse)
async def upload_zip(
    file: UploadFile = File(...),
    auto_detect_sources: bool = Query(default=True),
    process_immediately: bool = Query(default=True),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    """
            detail="File must be a ZIP archive"
        )
    
    # Process similar to regular upload but with source_type="zip"
    # The ZIP handler will extract and identify individual sources
    return await upload_files(
        files=[file],
        source_type="zip" if auto_detect_sources else "unknown",
        process_immediately=process_immediately,
        background_tasks=background_tasks,
        db=db,
        current_user=current_user
    )[0]

@router.get("/status/{file_id}", response_model=ProcessingStatusResponse)
async def get_processing_status(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get processing status for an uploaded file."""
    query = """
    """
    result = await db.fetch_one(query, file_id, current_user["id"])
    
    if not result:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Calculate progress
    progress = None
    if result["total_records"] and result["processed_records"]:
        progress = (result["processed_records"] / int(result["total_records"])) * 100
    
    return ProcessingStatusResponse(
        file_id=result["id"],
        filename=result["filename"],
        source_type=result["source_type"],
        status=ProcessingStatus(result["processing_status"]),
        progress=progress,
        total_records=int(result["total_records"]) if result["total_records"] else None,
        processed_records=result["processed_records"],
        error_message=result["error_message"],
        created_at=result["created_at"],
        updated_at=result["updated_at"]
    )

@router.get("/status", response_model=List[ProcessingStatusResponse])
async def list_processing_status(
    source_type: Optional[str] = Query(None),
    status: Optional[ProcessingStatus] = Query(None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """List processing status for all uploaded files."""
    query = """
    """
    params = [current_user["id"]]
    param_count = 1
    
    if source_type:
        param_count += 1
        query += f" AND fi.source_type = ${param_count}"
        params.append(source_type)
    
    if status:
        param_count += 1
        query += f" AND fi.processing_status = ${param_count}"
        params.append(status.value)
    
    query += f"""
    """
            file_id=row["id"],
            filename=row["filename"],
            source_type=row["source_type"],
            status=ProcessingStatus(row["processing_status"]),
            progress=(row["processed_records"] / int(row["total_records"]) * 100) 
                    if row["total_records"] else None,
            total_records=int(row["total_records"]) if row["total_records"] else None,
            processed_records=row["processed_records"],
            error_message=row["error_message"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
        for row in results
    ]

@router.post("/query", response_model=QueryResponse)
async def query_data(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    """
                sources=request.sources or ["all"],
                results=cache_result["results"],
                total_count=cache_result["total_count"],
                response_time_ms=cache_result["response_time_ms"],
                from_cache=True
            )
    
    # Perform vector search
    # This would integrate with Weaviate for semantic search
    # For now, we'll do a simple text search in PostgreSQL
    
    search_query = """
    """
    params = [request.query, current_user["id"]]
    param_count = 2
    
    if request.sources:
        param_count += 1
        placeholders = ','.join([f'${i}' for i in range(param_count, param_count + len(request.sources))])
        search_query += f" AND fi.source_type IN ({placeholders})"
        params.extend(request.sources)
        param_count += len(request.sources) - 1
    
    search_query += f"""
    """
            "id": str(row["id"]),
            "content": row["content"],
            "content_type": row["content_type"],
            "source_type": row["source_type"],
            "source_id": row["source_id"],
            "filename": row["filename"],
            "metadata": row["metadata"],
            "relevance_score": float(row["rank"])
        }
        for row in results
    ]
    
    # Calculate response time
    response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
    
    # Cache results if enabled
    if request.use_cache and formatted_results:
        await cache_query_results(
            db,
            request.query,
            request.sources,
            formatted_results,
            response_time
        )
    
    return QueryResponse(
        query=request.query,
        sources=request.sources or ["all"],
        results=formatted_results,
        total_count=len(formatted_results),  # Would need separate count query for accurate total
        response_time_ms=response_time,
        from_cache=False
    )

# Helper functions
async def process_file_async(file_id: str, file_path: str, source_type: str):
    """Background task to process uploaded file."""
    logger.info(f"Processing file {file_id} of type {source_type}")

async def check_query_cache(
    db: AsyncSession, 
    query: str, 
    sources: Optional[List[str]]
) -> Optional[Dict[str, Any]]:
    """Check if query results are cached."""
    """Cache query results for future use."""