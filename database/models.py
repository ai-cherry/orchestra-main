"""
SQLAlchemy Database Models

Defines all database models for the Orchestra AI admin interface.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, JSON, ForeignKey, LargeBinary, Enum, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .connection import Base

# SQLite-compatible UUID type
class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as string.
    """
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            return uuid.UUID(value)

# SQLite-compatible ARRAY type (stored as JSON)
class CompatibleArray(TypeDecorator):
    """Platform-independent ARRAY type.
    Uses PostgreSQL's ARRAY type, otherwise uses JSON.
    """
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(ARRAY(String))
        else:
            return dialect.type_descriptor(JSON)

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            return value  # Store as JSON array

    def process_result_value(self, value, dialect):
        if value is None:
            return value or []
        elif dialect.name == 'postgresql':
            return value or []
        else:
            return value or []

class PersonaType(str, enum.Enum):
    """Enum for persona types"""
    CHERRY = "cherry"
    SOPHIA = "sophia" 
    KAREN = "karen"

class FileStatus(str, enum.Enum):
    """Enum for file processing status"""
    PENDING = "pending"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

class SearchMode(str, enum.Enum):
    """Enum for search modes"""
    BASIC = "basic"
    DEEP = "deep"
    SUPER_DEEP = "super_deep"
    CREATIVE = "creative"
    PRIVATE = "private"
    UNCENSORED = "uncensored"

class User(Base):
    """User model for authentication and preferences"""
    __tablename__ = "users"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    preferences = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    personas = relationship("Persona", back_populates="user", cascade="all, delete-orphan")
    files = relationship("FileRecord", back_populates="user", cascade="all, delete-orphan")
    search_queries = relationship("SearchQuery", back_populates="user", cascade="all, delete-orphan")

class Persona(Base):
    """Persona configuration model"""
    __tablename__ = "personas"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    persona_type = Column(Enum(PersonaType), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Personality Configuration
    communication_style = Column(JSON, default=dict)  # formality, creativity, etc.
    knowledge_domains = Column(CompatibleArray(), default=list)
    preferred_models = Column(JSON, default=dict)
    
    # Behavior Settings
    behavior_config = Column(JSON, default=dict)
    prompt_templates = Column(JSON, default=dict)
    integration_preferences = Column(JSON, default=dict)
    
    # Performance Tracking
    usage_stats = Column(JSON, default=dict)
    performance_metrics = Column(JSON, default=dict)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="personas")
    files = relationship("FileRecord", back_populates="persona")

class FileRecord(Base):
    """File storage and processing tracking"""
    __tablename__ = "file_records"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    persona_id = Column(GUID(), ForeignKey("personas.id"))
    
    # File Information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100))
    file_type = Column(String(50))
    storage_path = Column(String(500), nullable=False)
    checksum = Column(String(64))
    
    # Processing Status
    status = Column(Enum(FileStatus), default=FileStatus.PENDING)
    processing_progress = Column(Float, default=0.0)
    error_message = Column(Text)
    
    # Metadata
    file_metadata = Column(JSON, default=dict)
    extracted_text = Column(Text)
    extracted_metadata = Column(JSON, default=dict)
    
    # Vector Processing
    embedding_model = Column(String(100))
    embedding_dimensions = Column(Integer)
    chunk_count = Column(Integer, default=0)
    
    # Timestamps
    upload_started = Column(DateTime(timezone=True))
    upload_completed = Column(DateTime(timezone=True))
    processing_started = Column(DateTime(timezone=True))
    processing_completed = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="files")
    persona = relationship("Persona", back_populates="files")
    processing_jobs = relationship("ProcessingJob", back_populates="file_record")

class ProcessingJob(Base):
    """Background processing job tracking"""
    __tablename__ = "processing_jobs"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    file_record_id = Column(GUID(), ForeignKey("file_records.id"))
    job_type = Column(String(50), nullable=False)  # embedding, extraction, analysis
    status = Column(String(20), default="pending")
    progress = Column(Float, default=0.0)
    
    # Job Configuration
    config = Column(JSON, default=dict)
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    
    # Error Handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    file_record = relationship("FileRecord", back_populates="processing_jobs")

class SearchQuery(Base):
    """Search query tracking and analytics"""
    __tablename__ = "search_queries"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    
    # Query Information
    query_text = Column(Text, nullable=False)
    search_mode = Column(Enum(SearchMode), nullable=False)
    filters = Column(JSON, default=dict)
    
    # Results
    result_count = Column(Integer, default=0)
    results = Column(JSON, default=list)
    response_time = Column(Float)
    
    # User Interaction
    clicked_results = Column(CompatibleArray(), default=list)
    user_rating = Column(Integer)  # 1-5 scale
    feedback = Column(Text)
    
    # AI Processing
    expanded_query = Column(Text)
    model_used = Column(String(100))
    processing_details = Column(JSON, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="search_queries")

class VectorChunk(Base):
    """Vector embeddings for semantic search"""
    __tablename__ = "vector_chunks"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    file_record_id = Column(GUID(), ForeignKey("file_records.id"), nullable=False)
    
    # Chunk Information
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_size = Column(Integer, nullable=False)
    overlap_size = Column(Integer, default=0)
    
    # Vector Data
    embedding_model = Column(String(100), nullable=False)
    embedding_dimensions = Column(Integer, nullable=False)
    # Note: Actual embedding vectors stored in vector database (Weaviate/Pinecone)
    vector_id = Column(String(255))  # Reference to vector DB
    
    # Metadata
    chunk_metadata = Column(JSON, default=dict)
    context_window = Column(JSON, default=dict)  # surrounding context
    
    # Search Optimization
    keywords = Column(CompatibleArray(), default=list)
    entities = Column(JSON, default=list)
    sentiment_score = Column(Float)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    file_record = relationship("FileRecord")

class ExternalIntegration(Base):
    """External service integration tracking"""
    __tablename__ = "external_integrations"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    
    # Integration Details
    service_name = Column(String(100), nullable=False)  # notion, openrouter, portkey
    service_config = Column(JSON, default=dict)
    credentials_encrypted = Column(LargeBinary)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime(timezone=True))
    sync_status = Column(String(20), default="pending")
    error_message = Column(Text)
    
    # Usage Tracking
    usage_stats = Column(JSON, default=dict)
    rate_limits = Column(JSON, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")

class SystemMetrics(Base):
    """System performance and usage metrics"""
    __tablename__ = "system_metrics"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Metric Information
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20))
    
    # Context
    component = Column(String(50))  # frontend, backend, database, etc.
    environment = Column(String(20))  # development, staging, production
    
    # Additional Data
    metrics_metadata = Column(JSON, default=dict)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

# Create indexes for performance
from sqlalchemy import Index

# Composite indexes for common queries
Index('idx_file_user_status', FileRecord.user_id, FileRecord.status)
Index('idx_search_user_mode', SearchQuery.user_id, SearchQuery.search_mode)
Index('idx_vector_file_chunk', VectorChunk.file_record_id, VectorChunk.chunk_index)
Index('idx_metrics_name_time', SystemMetrics.metric_name, SystemMetrics.timestamp) 