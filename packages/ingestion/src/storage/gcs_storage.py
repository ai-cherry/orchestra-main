"""
Google Cloud Storage (GCS) Module for File Ingestion System.

This module provides functionality for uploading, downloading, and
managing files in Google Cloud Storage buckets.
"""

import os
import logging
import tempfile
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, BinaryIO, Tuple
from urllib.parse import urlparse
import mimetypes

import aiohttp
from google.cloud import storage
from google.cloud.storage.blob import Blob
from google.api_core.exceptions import NotFound, GoogleAPIError
from tenacity import retry, stop_after_attempt, wait_exponential

from packages.ingestion.src.config.settings import get_settings

# Configure logging
logger = logging.getLogger(__name__)


class GCSStorageError(Exception):
    """Exception for GCS storage-related errors."""
    pass


class GCSStorage:
    """
    Google Cloud Storage implementation for file storage.
    
    This class provides methods for uploading, downloading, and
    managing files in Google Cloud Storage buckets.
    """
    
    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize the GCS storage.
        
        Args:
            project_id: Optional Google Cloud project ID. If not provided,
                      will be read from settings or environment.
        """
        settings = get_settings()
        self.project_id = project_id or settings.gcs.project_id
        self.raw_bucket_name = settings.gcs.raw_bucket_name
        self.processed_text_bucket_name = settings.gcs.processed_text_bucket_name
        self.upload_chunk_size = settings.upload_chunk_size
        self._client = None
        self._raw_bucket = None
        self._processed_text_bucket = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the GCS client and create buckets if they don't exist."""
        if self._initialized:
            return
            
        try:
            # Create synchronous client for GCS (no async client available)
            self._client = storage.Client(project=self.project_id)
            
            # Ensure raw bucket exists
            try:
                self._raw_bucket = self._client.get_bucket(self.raw_bucket_name)
            except NotFound:
                logger.info(f"Creating raw bucket: {self.raw_bucket_name}")
                self._raw_bucket = self._client.create_bucket(
                    self.raw_bucket_name, 
                    location="us-central1"
                )
            
            # Ensure processed text bucket exists
            try:
                self._processed_text_bucket = self._client.get_bucket(self.processed_text_bucket_name)
            except NotFound:
                logger.info(f"Creating processed text bucket: {self.processed_text_bucket_name}")
                self._processed_text_bucket = self._client.create_bucket(
                    self.processed_text_bucket_name,
                    location="us-central1"
                )
                
            self._initialized = True
            logger.info("GCS storage initialized")
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}")
            raise GCSStorageError(f"Failed to initialize GCS: {e}")
    
    def _check_initialized(self) -> None:
        """Check if the client is initialized and raise error if not."""
        if not self._initialized or not self._client:
            raise GCSStorageError("GCS client not initialized")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry_error_callback=lambda retry_state: None
    )
    async def download_from_url(
        self,
        url: str,
        task_id: str,
        max_size_mb: int = 500
    ) -> Tuple[str, str]:
        """
        Download a file from a URL to a temporary location.
        
        Args:
            url: The URL of the file to download
            task_id: The ID of the ingestion task
            max_size_mb: Maximum allowed file size in MB
            
        Returns:
            Tuple of (local file path, filename)
            
        Raises:
            GCSStorageError: If download fails or file is too large
        """
        max_size = max_size_mb * 1024 * 1024  # Convert to bytes
        
        # Parse the URL to extract the filename
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        if not filename:
            filename = f"file_{task_id}"
            
        # Create a temporary file
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, filename)
        
        try:
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes timeout
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, allow_redirects=True) as response:
                    if response.status != 200:
                        raise GCSStorageError(
                            f"Failed to download file from URL: {url}, "
                            f"Status: {response.status}"
                        )
                        
                    # Check content length if available
                    content_length = response.headers.get("Content-Length")
                    if content_length and int(content_length) > max_size:
                        raise GCSStorageError(
                            f"File size ({int(content_length) / 1024 / 1024:.1f} MB) "
                            f"exceeds maximum allowed size ({max_size_mb} MB)"
                        )
                        
                    # Get content type and update filename if needed
                    content_type = response.headers.get("Content-Type", "")
                    if content_type and "." not in filename:
                        ext = mimetypes.guess_extension(content_type)
                        if ext:
                            filename = f"{filename}{ext}"
                            temp_path = os.path.join(temp_dir, filename)
                            
                    # Stream download to file
                    total_size = 0
                    with open(temp_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(8192):
                            total_size += len(chunk)
                            if total_size > max_size:
                                raise GCSStorageError(
                                    f"File size exceeds maximum allowed size "
                                    f"({max_size_mb} MB)"
                                )
                            f.write(chunk)
            
            logger.info(f"Downloaded file from {url} to {temp_path} ({total_size / 1024 / 1024:.1f} MB)")
            return temp_path, filename
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error downloading file from {url}: {e}")
            raise GCSStorageError(f"Failed to download file: {e}")
        except Exception as e:
            logger.error(f"Error downloading file from {url}: {e}")
            raise GCSStorageError(f"Failed to download file: {e}")
    
    async def upload_raw_file(
        self,
        file_path: str,
        task_id: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Upload a file to the raw files bucket.
        
        Args:
            file_path: Path to the local file
            task_id: The ID of the ingestion task
            filename: Optional custom filename (defaults to the basename of file_path)
            
        Returns:
            The GCS object path in format 'gs://bucket-name/path/to/file'
            
        Raises:
            GCSStorageError: If upload fails
        """
        self._check_initialized()
        
        # Use provided filename or extract from path
        if not filename:
            filename = os.path.basename(file_path)
            
        # Define GCS path: task_id/original_filename
        gcs_path = f"{task_id}/{filename}"
        
        try:
            # Get blob reference
            blob = self._raw_bucket.blob(gcs_path)
            
            # Set content type based on file extension
            content_type = mimetypes.guess_type(filename)[0]
            if content_type:
                blob.content_type = content_type
                
            # Upload file
            blob.upload_from_filename(file_path)
            
            # Create gs:// URI
            gcs_uri = f"gs://{self.raw_bucket_name}/{gcs_path}"
            logger.info(f"Uploaded raw file to {gcs_uri}")
            return gcs_uri
        except Exception as e:
            logger.error(f"Failed to upload raw file to GCS: {e}")
            raise GCSStorageError(f"Failed to upload raw file: {e}")
    
    async def upload_text_content(
        self,
        text_content: str,
        task_id: str,
        filename: str
    ) -> str:
        """
        Upload extracted text content to the processed text bucket.
        
        Args:
            text_content: The text content to upload
            task_id: The ID of the ingestion task
            filename: Base filename for the text content
            
        Returns:
            The GCS object path in format 'gs://bucket-name/path/to/file'
            
        Raises:
            GCSStorageError: If upload fails
        """
        self._check_initialized()
        
        # Define GCS path: task_id/filename.txt
        if not filename.endswith(".txt"):
            filename = f"{filename}.txt"
        gcs_path = f"{task_id}/{filename}"
        
        try:
            # Get blob reference
            blob = self._processed_text_bucket.blob(gcs_path)
            
            # Set content type
            blob.content_type = "text/plain"
            
            # Upload content
            blob.upload_from_string(text_content)
            
            # Create gs:// URI
            gcs_uri = f"gs://{self.processed_text_bucket_name}/{gcs_path}"
            logger.info(f"Uploaded text content to {gcs_uri}")
            return gcs_uri
        except Exception as e:
            logger.error(f"Failed to upload text content to GCS: {e}")
            raise GCSStorageError(f"Failed to upload text content: {e}")
    
    async def get_download_url(
        self,
        gcs_uri: str,
        expiration_minutes: int = 60
    ) -> str:
        """
        Generate a signed URL for downloading a file from GCS.
        
        Args:
            gcs_uri: The GCS URI in format 'gs://bucket-name/path/to/file'
            expiration_minutes: URL expiration time in minutes
            
        Returns:
            Signed download URL
            
        Raises:
            GCSStorageError: If URL generation fails
        """
        self._check_initialized()
        
        try:
            # Parse URI to get bucket and blob path
            if not gcs_uri.startswith("gs://"):
                raise ValueError(f"Invalid GCS URI format: {gcs_uri}")
                
            parts = gcs_uri[5:].split("/", 1)
            if len(parts) != 2:
                raise ValueError(f"Invalid GCS URI format: {gcs_uri}")
                
            bucket_name, blob_path = parts
            
            # Get bucket and blob
            bucket = self._client.bucket(bucket_name)
            blob = bucket.blob(blob_path)
            
            # Generate signed URL
            expiration = datetime.utcnow() + timedelta(minutes=expiration_minutes)
            url = blob.generate_signed_url(expiration=expiration)
            
            logger.debug(f"Generated signed URL for {gcs_uri}, expires in {expiration_minutes} minutes")
            return url
        except Exception as e:
            logger.error(f"Failed to generate signed URL for {gcs_uri}: {e}")
            raise GCSStorageError(f"Failed to generate signed URL: {e}")
    
    async def download_to_memory(self, gcs_uri: str) -> bytes:
        """
        Download a file from GCS to memory.
        
        Args:
            gcs_uri: The GCS URI in format 'gs://bucket-name/path/to/file'
            
        Returns:
            File content as bytes
            
        Raises:
            GCSStorageError: If download fails
        """
        self._check_initialized()
        
        try:
            # Parse URI to get bucket and blob path
            if not gcs_uri.startswith("gs://"):
                raise ValueError(f"Invalid GCS URI format: {gcs_uri}")
                
            parts = gcs_uri[5:].split("/", 1)
            if len(parts) != 2:
                raise ValueError(f"Invalid GCS URI format: {gcs_uri}")
                
            bucket_name, blob_path = parts
            
            # Get bucket and blob
            bucket = self._client.bucket(bucket_name)
            blob = bucket.blob(blob_path)
            
            # Download content
            content = blob.download_as_bytes()
            
            logger.debug(f"Downloaded {gcs_uri} to memory ({len(content)} bytes)")
            return content
        except Exception as e:
            logger.error(f"Failed to download {gcs_uri} to memory: {e}")
            raise GCSStorageError(f"Failed to download file: {e}")
    
    async def delete_file(self, gcs_uri: str) -> None:
        """
        Delete a file from GCS.
        
        Args:
            gcs_uri: The GCS URI in format 'gs://bucket-name/path/to/file'
            
        Raises:
            GCSStorageError: If deletion fails
        """
        self._check_initialized()
        
        try:
            # Parse URI to get bucket and blob path
            if not gcs_uri.startswith("gs://"):
                raise ValueError(f"Invalid GCS URI format: {gcs_uri}")
                
            parts = gcs_uri[5:].split("/", 1)
            if len(parts) != 2:
                raise ValueError(f"Invalid GCS URI format: {gcs_uri}")
                
            bucket_name, blob_path = parts
            
            # Get bucket and blob
            bucket = self._client.bucket(bucket_name)
            blob = bucket.blob(blob_path)
            
            # Delete blob
            blob.delete()
            
            logger.info(f"Deleted file {gcs_uri}")
        except Exception as e:
            logger.error(f"Failed to delete {gcs_uri}: {e}")
            raise GCSStorageError(f"Failed to delete file: {e}")
    
    async def list_task_files(self, task_id: str, bucket_name: Optional[str] = None) -> List[str]:
        """
        List all files for a specific task.
        
        Args:
            task_id: The ID of the ingestion task
            bucket_name: Optional bucket name (defaults to raw files bucket)
            
        Returns:
            List of GCS URIs
            
        Raises:
            GCSStorageError: If listing fails
        """
        self._check_initialized()
        
        if not bucket_name:
            bucket_name = self.raw_bucket_name
            
        try:
            # Get bucket
            bucket = self._client.bucket(bucket_name)
            
            # List blobs with prefix
            blobs = bucket.list_blobs(prefix=f"{task_id}/")
            
            # Create GCS URIs
            uris = [f"gs://{bucket_name}/{blob.name}" for blob in blobs]
            
            return uris
        except Exception as e:
            logger.error(f"Failed to list task files for {task_id}: {e}")
            raise GCSStorageError(f"Failed to list task files: {e}")
