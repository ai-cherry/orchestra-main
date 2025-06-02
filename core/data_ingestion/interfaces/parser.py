"""
Parser interface for data ingestion system.

This module defines the base interface that all source-specific parsers must implement.
The interface ensures consistent behavior across different data sources while allowing
for source-specific customization.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, AsyncIterator
from datetime import datetime
import hashlib

@dataclass
class ParsedData:
    """
    Represents a single parsed data item from any source.
    
    Attributes:
        content_type: Type of content (e.g., 'message', 'transcript', 'record')
        source_id: Original ID from the source system
        content: The actual text content
        metadata: Additional metadata specific to the source
        timestamp: When the content was created (if available)
        file_import_id: Reference to the file import record
        content_hash: SHA-256 hash of the content for deduplication
    """
    content_type: str
    source_id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    file_import_id: Optional[str] = None
    content_hash: Optional[str] = None
    
    def __post_init__(self):
        """Generate content hash if not provided."""
        if not self.content_hash and self.content:
            self.content_hash = hashlib.sha256(
                self.content.encode('utf-8')
            ).hexdigest()

class ParserInterface(ABC):
    """
    Abstract base class for all data source parsers.
    
    This interface defines the contract that all parsers must implement,
    ensuring consistency while allowing for source-specific behavior.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the parser with optional configuration.
        
        Args:
            config: Optional configuration dictionary for parser-specific settings
        """
        self.config = config or {}
        self.supported_formats: List[str] = []
        self.content_types: List[str] = []
    
    @abstractmethod
    async def validate(self, file_content: bytes, filename: str) -> bool:
        """
        Validate if the file content is in the expected format.
        
        Args:
            file_content: Raw file content as bytes
            filename: Name of the file being validated
            
        Returns:
            True if the file is valid for this parser, False otherwise
        """
        pass
    
    @abstractmethod
    async def parse(
        self, 
        file_content: bytes, 
        metadata: Dict[str, Any]
    ) -> AsyncIterator[ParsedData]:
        """
        Parse the file content and yield parsed data items.
        
        This method should yield ParsedData objects as they are parsed,
        allowing for streaming processing of large files.
        
        Args:
            file_content: Raw file content as bytes
            metadata: Additional metadata about the file
            
        Yields:
            ParsedData objects representing individual data items
        """
        pass
    
    @abstractmethod
    async def extract_metadata(
        self, 
        file_content: bytes
    ) -> Dict[str, Any]:
        """
        Extract high-level metadata from the file.
        
        This method should extract metadata about the file itself,
        such as date ranges, number of records, etc.
        
        Args:
            file_content: Raw file content as bytes
            
        Returns:
            Dictionary containing file-level metadata
        """
        pass
    
    async def preprocess(self, file_content: bytes) -> bytes:
        """
        Optional preprocessing step for file content.
        
        Override this method if the parser needs to perform any
        preprocessing on the raw file content before parsing.
        
        Args:
            file_content: Raw file content as bytes
            
        Returns:
            Preprocessed file content
        """
        return file_content
    
    async def postprocess(self, parsed_data: ParsedData) -> ParsedData:
        """
        Optional postprocessing step for parsed data.
        
        Override this method if the parser needs to perform any
        postprocessing on individual parsed data items.
        
        Args:
            parsed_data: A parsed data item
            
        Returns:
            Postprocessed parsed data item
        """
        return parsed_data
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats."""
        return self.supported_formats
    
    def get_content_types(self) -> List[str]:
        """Get list of content types this parser produces."""
        return self.content_types