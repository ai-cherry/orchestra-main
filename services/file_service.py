"""
Enhanced File Service

Comprehensive file service with database integration, vector processing,
and persona-specific processing capabilities for Phase 2.
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any, BinaryIO
import asyncio
import aiofiles
import os
import hashlib
import json
import uuid
from datetime import datetime, timedelta
from pydantic import BaseModel
import mimetypes
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import structlog

# Use absolute imports that work when running directly
try:
    # When running as a module
    from database.models import FileRecord, FileStatus, PersonaType, ProcessingJob, VectorChunk, User
    from database.connection import get_db
except ImportError:
    # Fallback for relative imports
    from ..database.models import FileRecord, FileStatus, PersonaType, ProcessingJob, VectorChunk, User
    from ..database.connection import get_db

# Make file_processor import optional to avoid dependency issues
file_processor = None
try:
    from services.file_processor import file_processor
except ImportError:
    try:
        from .file_processor import file_processor
    except ImportError:
        # Create a mock file processor for development
        class MockFileProcessor:
            async def process_file(self, file_path: str, metadata: dict) -> dict:
                """Mock file processor that just returns basic metadata"""
                return {
                    "processed": True,
                    "text_extracted": f"Mock processed content from {file_path}",
                    "embedding": [0.1] * 384,  # Mock embedding
                    "metadata": metadata
                }
        file_processor = MockFileProcessor()

logger = structlog.get_logger(__name__)

class FileMetadata(BaseModel):
    persona: str
    file_type: str
    processing_intent: str
    custom_metadata: Dict[str, Any]
    tags: List[str]
    
class FileInfo(BaseModel):
    id: str
    filename: str
    file_size: int
    file_type: str
    mime_type: str
    upload_date: datetime
    status: str
    persona: str
    metadata: Optional[FileMetadata]
    processing_log: List[Dict[str, Any]]
    checksum: Optional[str]
    storage_path: str

class ChunkInfo(BaseModel):
    file_id: str
    chunk_number: int
    chunk_size: int
    chunk_hash: str
    uploaded: bool

class FileUploadRequest(BaseModel):
    filename: str
    file_size: int
    persona_type: PersonaType
    metadata: Dict[str, Any]

class FileUploadResponse(BaseModel):
    file_id: str
    upload_url: str
    chunk_size: int
    max_file_size: int
    status: str

class FileProcessingStatus(BaseModel):
    file_id: str
    status: FileStatus
    progress: float
    error_message: Optional[str] = None
    processing_started: Optional[datetime] = None
    processing_completed: Optional[datetime] = None

class FileSearchRequest(BaseModel):
    query: str
    file_types: Optional[List[str]] = None
    persona_types: Optional[List[PersonaType]] = None
    date_range: Optional[Dict[str, datetime]] = None
    limit: int = 10

class FileSearchResult(BaseModel):
    file_id: str
    filename: str
    file_type: str
    persona_type: Optional[PersonaType]
    relevance_score: float
    snippet: str
    metadata: Dict[str, Any]
    created_at: datetime

class EnhancedFileService:
    """Enhanced file service with comprehensive functionality"""
    
    def __init__(self):
        self.upload_dir = Path(os.getenv("UPLOAD_DIR", "./uploads"))
        self.upload_dir.mkdir(exist_ok=True)
        self.temp_dir = self.upload_dir / "temp"
        self.temp_dir.mkdir(exist_ok=True)
        self.processed_dir = self.upload_dir / "processed"
        self.processed_dir.mkdir(exist_ok=True)
        
        self.chunk_size = 8 * 1024 * 1024  # 8MB chunks
        self.max_file_size = 2 * 1024 * 1024 * 1024  # 2GB max
        
        # Active uploads tracking
        self.active_uploads: Dict[str, Dict[str, Any]] = {}
    
    async def initialize(self):
        """Initialize the file service"""
        await file_processor.initialize()
        logger.info("Enhanced file service initialized")
    
    async def initiate_upload(
        self, 
        request: FileUploadRequest,
        user_id: str,
        db: AsyncSession
    ) -> FileUploadResponse:
        """Initiate a new file upload"""
        try:
            # Validate file size
            if request.file_size > self.max_file_size:
                raise HTTPException(
                    status_code=413, 
                    detail=f"File too large. Maximum size: {self.max_file_size} bytes"
                )
            
            # Create file record
            file_record = FileRecord(
                user_id=user_id,
                filename=self._generate_unique_filename(request.filename),
                original_filename=request.filename,
                file_size=request.file_size,
                status=FileStatus.PENDING,
                file_metadata=request.metadata,
                upload_started=datetime.utcnow()
            )
            
            # Save to database
            db.add(file_record)
            await db.commit()
            await db.refresh(file_record)
            
            # Create temporary upload tracking
            self.active_uploads[str(file_record.id)] = {
                'expected_size': request.file_size,
                'received_size': 0,
                'persona_type': request.persona_type,
                'temp_path': self.temp_dir / f"{file_record.id}.tmp"
            }
            
            logger.info(
                "File upload initiated",
                file_id=str(file_record.id),
                filename=request.filename,
                size=request.file_size
            )
            
            return FileUploadResponse(
                file_id=str(file_record.id),
                upload_url=f"/api/files/{file_record.id}/upload",
                chunk_size=self.chunk_size,
                max_file_size=self.max_file_size,
                status="pending"
            )
            
        except Exception as e:
            logger.error("Failed to initiate upload", error=str(e))
            raise HTTPException(status_code=500, detail=f"Upload initiation failed: {str(e)}")
    
    async def upload_chunk(
        self,
        file_id: str,
        chunk_data: bytes,
        chunk_offset: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Upload a chunk of file data"""
        try:
            # Get file record
            result = await db.execute(
                select(FileRecord).where(FileRecord.id == file_id)
            )
            file_record = result.scalar_one_or_none()
            
            if not file_record:
                raise HTTPException(status_code=404, detail="File not found")
            
            if file_record.status not in [FileStatus.PENDING, FileStatus.UPLOADING]:
                raise HTTPException(status_code=400, detail="File is not in uploadable state")
            
            # Get upload tracking info
            if file_id not in self.active_uploads:
                raise HTTPException(status_code=400, detail="Upload not initiated")
            
            upload_info = self.active_uploads[file_id]
            temp_path = upload_info['temp_path']
            
            # Update status to uploading if not already
            if file_record.status == FileStatus.PENDING:
                file_record.status = FileStatus.UPLOADING
                await db.commit()
            
            # Append chunk to temporary file
            async with aiofiles.open(temp_path, 'ab') as f:
                await f.write(chunk_data)
            
            # Update received size
            upload_info['received_size'] += len(chunk_data)
            
            # Calculate progress
            progress = upload_info['received_size'] / upload_info['expected_size']
            
            logger.debug(
                "Chunk uploaded",
                file_id=file_id,
                chunk_size=len(chunk_data),
                progress=progress
            )
            
            # Check if upload is complete
            if upload_info['received_size'] >= upload_info['expected_size']:
                await self._complete_upload(file_id, file_record, upload_info, db)
                return {
                    'status': 'completed',
                    'progress': 1.0,
                    'message': 'Upload completed successfully'
                }
            
            return {
                'status': 'uploading',
                'progress': progress,
                'received_bytes': upload_info['received_size'],
                'total_bytes': upload_info['expected_size']
            }
            
        except Exception as e:
            logger.error("Chunk upload failed", file_id=file_id, error=str(e))
            # Update file status to error
            if file_id in self.active_uploads:
                await self._mark_upload_error(file_id, str(e), db)
            raise HTTPException(status_code=500, detail=f"Chunk upload failed: {str(e)}")
    
    async def _complete_upload(
        self,
        file_id: str,
        file_record: FileRecord,
        upload_info: Dict[str, Any],
        db: AsyncSession
    ):
        """Complete file upload and start processing"""
        try:
            temp_path = upload_info['temp_path']
            
            # Calculate checksum
            file_record.checksum = await self._calculate_checksum(temp_path)
            
            # Move to permanent storage
            storage_path = self.processed_dir / f"{file_record.id}_{file_record.original_filename}"
            temp_path.rename(storage_path)
            file_record.storage_path = str(storage_path)
            
            # Update status
            file_record.status = FileStatus.UPLOADED
            file_record.upload_completed = datetime.utcnow()
            
            # Detect file type and MIME type
            file_record.mime_type = mimetypes.guess_type(file_record.original_filename)[0]
            file_record.file_type = self._detect_file_type(storage_path)
            
            await db.commit()
            
            # Clean up upload tracking
            del self.active_uploads[file_id]
            
            # Start background processing
            persona_type = upload_info['persona_type']
            asyncio.create_task(self._process_file_background(file_record, persona_type, db))
            
            logger.info(
                "Upload completed",
                file_id=file_id,
                filename=file_record.original_filename,
                size=file_record.file_size
            )
            
        except Exception as e:
            logger.error("Upload completion failed", file_id=file_id, error=str(e))
            await self._mark_upload_error(file_id, str(e), db)
            raise
    
    async def _process_file_background(
        self,
        file_record: FileRecord,
        persona_type: PersonaType,
        db: AsyncSession
    ):
        """Background file processing task"""
        try:
            # Update status
            file_record.status = FileStatus.PROCESSING
            file_record.processing_started = datetime.utcnow()
            await db.commit()
            
            # Process with file processor
            with open(file_record.storage_path, 'rb') as file_data:
                processed_record = await file_processor.process_upload(
                    file_data=file_data,
                    filename=file_record.original_filename,
                    file_size=file_record.file_size,
                    persona_type=persona_type,
                    metadata=file_record.file_metadata
                )
            
            # Update file record with processed information
            file_record.extracted_text = processed_record.extracted_text
            file_record.extracted_metadata = processed_record.extracted_metadata
            file_record.embedding_model = processed_record.embedding_model
            file_record.embedding_dimensions = processed_record.embedding_dimensions
            file_record.chunk_count = processed_record.chunk_count
            file_record.status = FileStatus.COMPLETED
            file_record.processing_completed = datetime.utcnow()
            file_record.processing_progress = 1.0
            
            await db.commit()
            
            logger.info(
                "File processing completed",
                file_id=str(file_record.id),
                filename=file_record.original_filename,
                chunks=file_record.chunk_count
            )
            
        except Exception as e:
            logger.error(
                "File processing failed",
                file_id=str(file_record.id),
                error=str(e)
            )
            
            file_record.status = FileStatus.ERROR
            file_record.error_message = str(e)
            await db.commit()
    
    async def get_file_status(self, file_id: str, db: AsyncSession) -> FileProcessingStatus:
        """Get file processing status"""
        try:
            result = await db.execute(
                select(FileRecord).where(FileRecord.id == file_id)
            )
            file_record = result.scalar_one_or_none()
            
            if not file_record:
                raise HTTPException(status_code=404, detail="File not found")
            
            return FileProcessingStatus(
                file_id=str(file_record.id),
                status=file_record.status,
                progress=file_record.processing_progress,
                error_message=file_record.error_message,
                processing_started=file_record.processing_started,
                processing_completed=file_record.processing_completed
            )
            
        except Exception as e:
            logger.error("Failed to get file status", file_id=file_id, error=str(e))
            raise HTTPException(status_code=500, detail=f"Status retrieval failed: {str(e)}")
    
    async def search_files(
        self,
        request: FileSearchRequest,
        user_id: str,
        db: AsyncSession
    ) -> List[FileSearchResult]:
        """Search files using vector similarity and metadata filters"""
        try:
            # Build database query
            query = select(FileRecord).where(
                FileRecord.user_id == user_id,
                FileRecord.status == FileStatus.COMPLETED
            )
            
            # Apply filters
            if request.file_types:
                query = query.where(FileRecord.file_type.in_(request.file_types))
            
            if request.date_range:
                if 'start' in request.date_range:
                    query = query.where(FileRecord.created_at >= request.date_range['start'])
                if 'end' in request.date_range:
                    query = query.where(FileRecord.created_at <= request.date_range['end'])
            
            # Execute query
            result = await db.execute(query)
            files = result.scalars().all()
            
            if not files:
                return []
            
            # If we have a search query, use vector search
            if request.query.strip():
                # Generate query embedding
                query_embedding = file_processor.embedding_model.encode([request.query])[0]
                
                # Search vector store
                vector_results = await file_processor.vector_store.search_vectors(
                    collection_name="documents",
                    query_vector=query_embedding.tolist(),
                    top_k=request.limit * 2,  # Get more results for better filtering
                    filters=None
                )
                
                # Match vector results with database files
                results = []
                file_dict = {str(f.id): f for f in files}
                
                for vector_result in vector_results:
                    file_id = vector_result['metadata'].get('file_id')
                    if file_id in file_dict:
                        file_record = file_dict[file_id]
                        
                        # Apply persona filter if specified
                        if request.persona_types and file_record.persona_id:
                            # Would need to check persona type from persona table
                            pass
                        
                        results.append(FileSearchResult(
                            file_id=str(file_record.id),
                            filename=file_record.original_filename,
                            file_type=file_record.file_type,
                            persona_type=None,  # Would need to join with persona table
                            relevance_score=vector_result['score'],
                            snippet=vector_result['metadata'].get('content', '')[:200],
                            metadata=file_record.file_metadata,
                            created_at=file_record.created_at
                        ))
                
                return results[:request.limit]
            
            else:
                # Return recent files without vector search
                results = []
                for file_record in files[:request.limit]:
                    results.append(FileSearchResult(
                        file_id=str(file_record.id),
                        filename=file_record.original_filename,
                        file_type=file_record.file_type,
                        persona_type=None,
                        relevance_score=1.0,
                        snippet=file_record.extracted_text[:200] if file_record.extracted_text else '',
                        metadata=file_record.file_metadata,
                        created_at=file_record.created_at
                    ))
                
                return results
            
        except Exception as e:
            logger.error("File search failed", error=str(e))
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
    
    async def delete_file(self, file_id: str, user_id: str, db: AsyncSession) -> bool:
        """Delete a file and its associated data"""
        try:
            # Get file record
            result = await db.execute(
                select(FileRecord).where(
                    FileRecord.id == file_id,
                    FileRecord.user_id == user_id
                )
            )
            file_record = result.scalar_one_or_none()
            
            if not file_record:
                raise HTTPException(status_code=404, detail="File not found")
            
            # Delete from vector store
            if file_record.chunk_count > 0:
                chunk_ids = [f"{file_id}_{i}" for i in range(file_record.chunk_count)]
                await file_processor.vector_store.delete_vectors("documents", chunk_ids)
            
            # Delete physical file
            if file_record.storage_path and os.path.exists(file_record.storage_path):
                os.remove(file_record.storage_path)
            
            # Delete from database (cascading deletes will handle related records)
            await db.delete(file_record)
            await db.commit()
            
            logger.info("File deleted", file_id=file_id, filename=file_record.original_filename)
            return True
            
        except Exception as e:
            logger.error("File deletion failed", file_id=file_id, error=str(e))
            raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")
    
    async def _mark_upload_error(self, file_id: str, error_message: str, db: AsyncSession):
        """Mark upload as failed"""
        try:
            await db.execute(
                update(FileRecord)
                .where(FileRecord.id == file_id)
                .values(status=FileStatus.ERROR, error_message=error_message)
            )
            await db.commit()
            
            # Clean up upload tracking
            if file_id in self.active_uploads:
                upload_info = self.active_uploads[file_id]
                if upload_info['temp_path'].exists():
                    upload_info['temp_path'].unlink()
                del self.active_uploads[file_id]
                
        except Exception as e:
            logger.error("Failed to mark upload error", file_id=file_id, error=str(e))
    
    async def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file"""
        hash_sha256 = hashlib.sha256()
        async with aiofiles.open(file_path, 'rb') as f:
            while True:
                chunk = await f.read(8192)
                if not chunk:
                    break
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _generate_unique_filename(self, original_filename: str) -> str:
        """Generate unique filename with timestamp"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(original_filename)
        # Clean filename for safety
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        return f"{timestamp}_{safe_name}{ext}"
    
    def _detect_file_type(self, file_path: Path) -> str:
        """Detect file type from extension"""
        ext = file_path.suffix.lower()
        
        type_mapping = {
            '.pdf': 'pdf',
            '.docx': 'docx', '.doc': 'docx',
            '.txt': 'txt',
            '.md': 'md',
            '.html': 'html', '.htm': 'html',
            '.xml': 'xml',
            '.json': 'json',
            '.csv': 'csv',
            '.xlsx': 'xlsx', '.xls': 'xlsx',
            '.zip': 'zip',
            '.tar': 'tar', '.gz': 'tar',
            '.7z': '7z',
            '.jpg': 'jpg', '.jpeg': 'jpg',
            '.png': 'png',
            '.gif': 'gif',
            '.bmp': 'bmp',
            '.mp3': 'mp3',
            '.wav': 'wav',
            '.mp4': 'mp4',
            '.avi': 'avi',
            '.py': 'py',
            '.js': 'js',
            '.ts': 'ts',
            '.css': 'css',
            '.sql': 'sql'
        }
        
        return type_mapping.get(ext, 'unknown')
    
    async def get_file_content(self, file_id: str, user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Get file content and metadata"""
        try:
            result = await db.execute(
                select(FileRecord).where(
                    FileRecord.id == file_id,
                    FileRecord.user_id == user_id
                )
            )
            file_record = result.scalar_one_or_none()
            
            if not file_record:
                raise HTTPException(status_code=404, detail="File not found")
            
            return {
                'id': str(file_record.id),
                'filename': file_record.original_filename,
                'file_type': file_record.file_type,
                'file_size': file_record.file_size,
                'status': file_record.status.value,
                'extracted_text': file_record.extracted_text,
                'extracted_metadata': file_record.extracted_metadata,
                'metadata': file_record.file_metadata,
                'chunk_count': file_record.chunk_count,
                'created_at': file_record.created_at.isoformat(),
                'processing_completed': file_record.processing_completed.isoformat() if file_record.processing_completed else None
            }
            
        except Exception as e:
            logger.error("Failed to get file content", file_id=file_id, error=str(e))
            raise HTTPException(status_code=500, detail=f"Content retrieval failed: {str(e)}")

# Global enhanced file service instance
enhanced_file_service = EnhancedFileService() 