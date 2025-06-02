"""
FastAPI router for data ingestion endpoints.

This module provides REST API endpoints for file upload, processing status,
and querying across ingested data sources.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import asyncio
import uuid
from datetime import datetime
import aiofiles
import os
from pathlib import Path
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel, Field

from ...core.database import get_db
from ...core.auth import get_current_user
from ....core.data_ingestion.parsers import get_parser
from ....core.data_ingestion.interfaces.processor import ProcessingStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/data-ingestion", tags=["data-ingestion"])

# Pydantic models for request/response
class FileUploadResponse(BaseModel):
    """Response model for file upload."""
    file_id: str
    filename: str
    source_type: str
    status: str
    message: str

class ProcessingStatusResponse(BaseModel):
    """Response model for processing status."""
    file_id: str
    filename: str
    source_type: str
    status: ProcessingStatus
    progress: Optional[float] = None
    total_records: Optional[int] = None
    processed_records: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class QueryRequest(BaseModel):
    """Request model for data queries."""
    query: str = Field(..., min_length=1, max_length=1000)
    sources: Optional[List[str]] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    use_cache: bool = True

class QueryResponse(BaseModel):
    """Response model for query results."""
    query: str
    sources: List[str]
    results: List[Dict[str, Any]]
    total_count: int
    response_time_ms: int
    from_cache: bool

# Configuration
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
    Upload files for ingestion.
    
    Accepts multiple files and queues them for processing.
    Supports Slack, Gong.io, Salesforce, Looker, and HubSpot exports.
    """
    responses = []
    
    for file in files:
        try:
            # Validate file size
            file_size = 0
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
                INSERT INTO data_ingestion.file_imports 
                (id, filename, source_type, file_size, mime_type, created_by)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """
            
            await db.execute(
                insert_query,
                file_id,
                file.filename,
                source_type,
                file_size,
                file.content_type,
                current_user["id"]
            )
            
            # Queue for processing if requested
            if process_immediately:
                # Add to processing queue
                queue_query = """
                    INSERT INTO data_ingestion.processing_queue
                    (file_import_id, priority)
                    VALUES ($1, $2)
                """
                await db.execute(queue_query, file_id, 5)  # Default priority
                
                # Trigger background processing
                background_tasks.add_task(
                    process_file_async,
                    file_id,
                    str(temp_file_path),
                    source_type
                )
            
            await db.commit()
            
            responses.append(FileUploadResponse(
                file_id=file_id,
                filename=file.filename,
                source_type=source_type,
                status="queued" if process_immediately else "uploaded",
                message=f"File uploaded successfully"
            ))
            
        except HTTPException:
            raise
        except Exception as e:
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
    Upload a ZIP file containing multiple data sources.
    
    The system will automatically detect and process files from different sources
    within the ZIP archive.
    """
    # Validate file is ZIP
    if not file.filename.lower().endswith('.zip'):
        raise HTTPException(
            status_code=400,
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
        SELECT 
            fi.id,
            fi.filename,
            fi.source_type,
            fi.processing_status,
            fi.error_message,
            fi.created_at,
            fi.updated_at,
            COUNT(pc.id) as processed_records,
            fi.metadata->>'total_records' as total_records
        FROM data_ingestion.file_imports fi
        LEFT JOIN data_ingestion.parsed_content pc ON fi.id = pc.file_import_id
        WHERE fi.id = $1 AND fi.created_by = $2
        GROUP BY fi.id
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
        SELECT 
            fi.id,
            fi.filename,
            fi.source_type,
            fi.processing_status,
            fi.error_message,
            fi.created_at,
            fi.updated_at,
            COUNT(pc.id) as processed_records,
            fi.metadata->>'total_records' as total_records
        FROM data_ingestion.file_imports fi
        LEFT JOIN data_ingestion.parsed_content pc ON fi.id = pc.file_import_id
        WHERE fi.created_by = $1
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
        GROUP BY fi.id
        ORDER BY fi.created_at DESC
        LIMIT ${param_count + 1} OFFSET ${param_count + 2}
    """
    params.extend([limit, offset])
    
    results = await db.fetch_all(query, *params)
    
    return [
        ProcessingStatusResponse(
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
    Query across all ingested data sources.
    
    Performs semantic search using vector embeddings and returns
    relevant results from all specified sources.
    """
    start_time = datetime.utcnow()
    
    # Check cache first if enabled
    if request.use_cache:
        cache_result = await check_query_cache(
            db, 
            request.query, 
            request.sources
        )
        if cache_result:
            return QueryResponse(
                query=request.query,
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
        WITH search_results AS (
            SELECT 
                pc.id,
                pc.content,
                pc.content_type,
                pc.source_id,
                pc.metadata,
                fi.source_type,
                fi.filename,
                ts_rank(
                    to_tsvector('english', pc.content),
                    plainto_tsquery('english', $1)
                ) as rank
            FROM data_ingestion.parsed_content pc
            JOIN data_ingestion.file_imports fi ON pc.file_import_id = fi.id
            WHERE fi.created_by = $2
                AND to_tsvector('english', pc.content) @@ plainto_tsquery('english', $1)
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
            ORDER BY rank DESC
            LIMIT ${param_count + 1} OFFSET ${param_count + 2}
        )
        SELECT * FROM search_results
    """
    params.extend([request.limit, request.offset])
    
    results = await db.fetch_all(search_query, *params)
    
    # Format results
    formatted_results = [
        {
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
    # This would be implemented to use the processor interface
    # For now, it's a placeholder
    logger.info(f"Processing file {file_id} of type {source_type}")

async def check_query_cache(
    db: AsyncSession, 
    query: str, 
    sources: Optional[List[str]]
) -> Optional[Dict[str, Any]]:
    """Check if query results are cached."""
    # Implementation would check the query_cache table
    return None

async def cache_query_results(
    db: AsyncSession,
    query: str,
    sources: Optional[List[str]],
    results: List[Dict[str, Any]],
    response_time: int
):
    """Cache query results for future use."""
    # Implementation would insert into query_cache table
    pass