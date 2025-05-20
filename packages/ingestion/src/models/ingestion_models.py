"""
Ingestion Models for Orchestra File Ingestion System.

This module defines the data models used for file ingestion,
including task tracking, file metadata, and chunk information.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union

from pydantic import BaseModel, Field, HttpUrl, validator


class IngestionStatus(str, Enum):
    """Status of an ingestion task."""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class FileType(str, Enum):
    """Supported file types for ingestion."""

    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    CSV = "csv"
    TXT = "txt"
    JSON = "json"
    HTML = "html"
    ZIP = "zip"
    TAR_GZ = "tar.gz"
    JPG = "jpg"
    PNG = "png"
    EML = "eml"
    MSG = "msg"
    UNKNOWN = "unknown"


class IngestionTask(BaseModel):
    """
    Model for tracking ingestion tasks.

    This represents a top-level ingestion request, potentially
    involving multiple files (e.g., if the source is an archive).
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_id: Optional[str] = None
    source_url: HttpUrl
    status: IngestionStatus = IngestionStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class ProcessedFile(BaseModel):
    """
    Model for tracking processed files.

    This represents an individual file that has been processed,
    which may be part of a larger ingestion task.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    user_id: str
    original_filename: str
    detected_type: Union[FileType, str] = FileType.UNKNOWN
    size_bytes: int = 0
    status: IngestionStatus = IngestionStatus.PENDING
    gcs_raw_path: Optional[str] = None
    gcs_text_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class TextChunk(BaseModel):
    """
    Model for text chunks extracted from a file.

    This represents a segment of text extracted from a processed file,
    which will be embedded and stored in the vector database.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file_id: str
    task_id: str
    user_id: str
    chunk_number: int
    text_content: str
    embedding: Optional[List[float]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class IngestionResult(BaseModel):
    """
    Model for returning ingestion task results.

    This is used for API responses to provide information
    about an ingestion task's status and details.
    """

    task_id: str
    status: IngestionStatus
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class PubSubMessage(BaseModel):
    """
    Model for PubSub message data.

    This represents the structure of messages sent through Pub/Sub
    for asynchronous processing of ingestion tasks.
    """

    task_id: str
    user_id: str
    session_id: Optional[str] = None
    source_url: HttpUrl
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
