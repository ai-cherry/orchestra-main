"""
Configuration Settings for File Ingestion System.

This module provides centralized configuration settings for the
ingestion system, including service connections, file size limits,
and other operational parameters.
"""

import os
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field, validator


class GCSSettings(BaseModel):
    """Google Cloud Storage settings."""
    raw_bucket_name: str
    processed_text_bucket_name: str
    project_id: Optional[str] = None


class PubSubSettings(BaseModel):
    """Google Cloud Pub/Sub settings."""
    project_id: Optional[str] = None
    ingestion_topic: str
    ingestion_subscription: str


class VertexAISettings(BaseModel):
    """Vertex AI settings for embeddings."""
    project_id: Optional[str] = None
    location: str = "us-central1"
    embedding_model: str = "textembedding-gecko@latest"


class FirestoreSettings(BaseModel):
    """Firestore settings."""
    project_id: Optional[str] = None
    ingestion_tasks_collection: str = "ingestion_tasks"
    processed_files_collection: str = "processed_files"


class PostgresSettings(BaseModel):
    """PostgreSQL database settings."""
    dsn: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = 5432
    database: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    embedding_table: str = "orchestra_embeddings"
    embedding_dimension: int = 768  # May differ based on embedding model


class IngestionSettings(BaseModel):
    """Main ingestion system settings."""
    # Service settings
    environment: str = "dev"
    project_id: str = Field(
        default_factory=lambda: os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    )
    
    # GCS settings
    gcs: GCSSettings = Field(
        default_factory=lambda: GCSSettings(
            project_id=os.environ.get("GOOGLE_CLOUD_PROJECT", ""),
            raw_bucket_name=f"orchestra-ingestion-raw-{os.environ.get('ENVIRONMENT', 'dev')}",
            processed_text_bucket_name=f"orchestra-ingestion-processed-text-{os.environ.get('ENVIRONMENT', 'dev')}"
        )
    )
    
    # Pub/Sub settings
    pubsub: PubSubSettings = Field(
        default_factory=lambda: PubSubSettings(
            project_id=os.environ.get("GOOGLE_CLOUD_PROJECT", ""),
            ingestion_topic=f"file-ingestion-queue-{os.environ.get('ENVIRONMENT', 'dev')}",
            ingestion_subscription=f"file-ingestion-subscription-{os.environ.get('ENVIRONMENT', 'dev')}"
        )
    )
    
    # Vertex AI settings
    vertex_ai: VertexAISettings = Field(
        default_factory=lambda: VertexAISettings(
            project_id=os.environ.get("GOOGLE_CLOUD_PROJECT", "")
        )
    )
    
    # Firestore settings
    firestore: FirestoreSettings = Field(
        default_factory=lambda: FirestoreSettings(
            project_id=os.environ.get("GOOGLE_CLOUD_PROJECT", "")
        )
    )
    
    # PostgreSQL settings
    postgres: PostgresSettings = Field(
        default_factory=lambda: PostgresSettings(
            dsn=os.environ.get("POSTGRES_DSN", "")
        )
    )
    
    # Ingestion limits and settings
    max_file_size_mb: int = 500  # Maximum file size in MB
    max_chunk_size: int = 1000  # Maximum text chunk size in characters
    chunk_overlap: int = 100  # Overlap between chunks in characters
    max_parallel_downloads: int = 10  # Maximum parallel downloads
    upload_chunk_size: int = 8 * 1024 * 1024  # 8MB chunks for uploads
    allowed_file_types: List[str] = [
        "pdf", "docx", "xlsx", "csv", "txt", "json", "html", 
        "zip", "tar.gz", "jpg", "png", "eml", "msg"
    ]
    
    # Notification settings
    send_notifications: bool = True
    notification_types: List[str] = ["completion", "failure"]


# Create a global settings instance
def get_settings() -> IngestionSettings:
    """Get the current settings."""
    return IngestionSettings()
