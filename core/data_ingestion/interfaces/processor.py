"""
Processor interface for data ingestion system.

This module defines the base interface for data processors that orchestrate
the parsing, transformation, and storage of ingested data.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, AsyncIterator
from datetime import datetime
from enum import Enum
import uuid

class ProcessingStatus(Enum):
    """Status of a processing operation."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ProcessingResult:
    """
    Result of a processing operation.
    
    Attributes:
        file_id: Unique identifier for the processed file
        status: Current status of the processing
        total_records: Total number of records processed
        successful_records: Number of successfully processed records
        failed_records: Number of failed records
        processing_time_ms: Time taken to process in milliseconds
        error_messages: List of error messages encountered
        metadata: Additional processing metadata
    """
    file_id: str
    status: ProcessingStatus
    total_records: int = 0
    successful_records: int = 0
    failed_records: int = 0
    processing_time_ms: int = 0
    error_messages: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Ensure file_id is set."""
        if not self.file_id:
            self.file_id = str(uuid.uuid4())
    
    @property
    def success_rate(self) -> float:
        """Calculate the success rate of processing."""
        if self.total_records == 0:
            return 0.0
        return self.successful_records / self.total_records
    
    def add_error(self, error: str) -> None:
        """Add an error message to the result."""
        self.error_messages.append(f"[{datetime.utcnow().isoformat()}] {error}")

class ProcessorInterface(ABC):
    """
    Abstract base class for data processors.
    
    Processors orchestrate the entire data ingestion pipeline including
    parsing, transformation, vector embedding, and storage.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the processor with configuration.
        
        Args:
            config: Configuration dictionary containing processor settings
        """
        self.config = config
        self.parsers: Dict[str, Any] = {}
        self.storage_adapters: Dict[str, Any] = {}
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the processor and its dependencies.
        
        This method should set up parsers, storage adapters, and any
        other required components.
        
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def process_file(
        self,
        file_path: str,
        source_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProcessingResult:
        """
        Process a single file through the ingestion pipeline.
        
        Args:
            file_path: Path to the file to process
            source_type: Type of source (slack, gong, salesforce, etc.)
            metadata: Optional metadata about the file
            
        Returns:
            ProcessingResult with details of the operation
        """
        pass
    
    @abstractmethod
    async def process_stream(
        self,
        data_stream: AsyncIterator[bytes],
        source_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[ProcessingResult]:
        """
        Process a stream of data through the ingestion pipeline.
        
        This method supports streaming processing for large files or
        real-time data feeds.
        
        Args:
            data_stream: Async iterator yielding data chunks
            source_type: Type of source
            metadata: Optional metadata about the stream
            
        Yields:
            ProcessingResult objects as data is processed
        """
        pass
    
    @abstractmethod
    async def validate_source(
        self,
        file_path: str,
        source_type: str
    ) -> bool:
        """
        Validate if a file can be processed by this processor.
        
        Args:
            file_path: Path to the file to validate
            source_type: Claimed source type
            
        Returns:
            True if the file can be processed, False otherwise
        """
        pass
    
    async def preprocess_file(
        self,
        file_path: str,
        source_type: str
    ) -> Dict[str, Any]:
        """
        Optional preprocessing step before main processing.
        
        Override this method to perform any preprocessing such as
        file extraction, format conversion, etc.
        
        Args:
            file_path: Path to the file
            source_type: Type of source
            
        Returns:
            Dictionary with preprocessing results
        """
        return {"preprocessed": False}
    
    async def postprocess_results(
        self,
        result: ProcessingResult
    ) -> ProcessingResult:
        """
        Optional postprocessing step after main processing.
        
        Override this method to perform any postprocessing such as
        notifications, cleanup, etc.
        
        Args:
            result: The processing result
            
        Returns:
            Updated processing result
        """
        return result
    
    async def get_processing_status(
        self,
        file_id: str
    ) -> Optional[ProcessingResult]:
        """
        Get the current status of a processing operation.
        
        Args:
            file_id: The file ID to check
            
        Returns:
            ProcessingResult if found, None otherwise
        """
        # Default implementation - override for persistent status tracking
        return None
    
    async def cancel_processing(
        self,
        file_id: str
    ) -> bool:
        """
        Cancel an ongoing processing operation.
        
        Args:
            file_id: The file ID to cancel
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        # Default implementation - override for cancellation support
        return False
    
    async def cleanup(self) -> None:
        """
        Cleanup resources used by the processor.
        
        This method should close connections, clear caches, etc.
        """
        pass
    
    def register_parser(self, source_type: str, parser: Any) -> None:
        """Register a parser for a specific source type."""
        self.parsers[source_type] = parser
    
    def register_storage(self, storage_type: str, adapter: Any) -> None:
        """Register a storage adapter."""
        self.storage_adapters[storage_type] = adapter
    
    def get_supported_sources(self) -> List[str]:
        """Get list of supported source types."""
        return list(self.parsers.keys())
    
    def is_initialized(self) -> bool:
        """Check if the processor is initialized."""
        return self._initialized