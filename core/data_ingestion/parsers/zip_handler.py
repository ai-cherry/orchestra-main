"""
ZIP file handler for data ingestion.

This module handles extraction and processing of ZIP files containing
data exports from various sources.
"""

import zipfile
import io
import logging
from typing import Dict, Any, List, AsyncIterator, Optional, Tuple
from pathlib import Path
import tempfile
import shutil

from ..interfaces.parser import ParserInterface, ParsedData

logger = logging.getLogger(__name__)

class ZipHandler(ParserInterface):
    """
    Handler for ZIP files containing data exports.
    
    This handler extracts ZIP files and delegates parsing to appropriate
    source-specific parsers based on file content and structure.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the ZIP handler."""
        super().__init__(config)
        self.supported_formats = ["zip"]
        self.content_types = ["extracted_file"]
        self.temp_dir = None
        
    async def validate(self, file_content: bytes, filename: str) -> bool:
        """
        Validate if the file is a valid ZIP archive.
        
        Args:
            file_content: Raw file content
            filename: Name of the file
            
        Returns:
            True if valid ZIP file
        """
        try:
            # Check if it's a valid ZIP file
            with zipfile.ZipFile(io.BytesIO(file_content)) as zf:
                # Test the ZIP file integrity
                result = zf.testzip()
                if result is not None:
                    logger.warning(f"Corrupted file in ZIP: {result}")
                    return False
                return True
                
        except zipfile.BadZipFile:
            logger.debug(f"Not a valid ZIP file: {filename}")
            return False
        except Exception as e:
            logger.error(f"Error validating ZIP file: {e}")
            return False
    
    async def parse(
        self, 
        file_content: bytes, 
        metadata: Dict[str, Any]
    ) -> AsyncIterator[ParsedData]:
        """
        Extract and process files from ZIP archive.
        
        This method extracts files and attempts to identify their source type
        based on file structure and content.
        
        Args:
            file_content: Raw ZIP file content
            metadata: File metadata
            
        Yields:
            ParsedData objects for extracted file metadata
        """
        try:
            # Create temporary directory for extraction
            self.temp_dir = tempfile.mkdtemp(prefix="data_ingestion_")
            
            with zipfile.ZipFile(io.BytesIO(file_content)) as zf:
                # Extract all files
                zf.extractall(self.temp_dir)
                
                # Get file list and detect source type
                file_list = zf.namelist()
                source_type = await self._detect_source_type(file_list, self.temp_dir)
                
                # Yield metadata about the ZIP contents
                yield ParsedData(
                    content_type='extracted_file',
                    source_id=f"zip_{metadata.get('filename', 'unknown')}",
                    content=f"ZIP archive containing {len(file_list)} files",
                    metadata={
                        'source_type': source_type,
                        'file_count': len(file_list),
                        'file_list': file_list[:100],  # Limit to first 100 files
                        'total_size': sum(zf.getinfo(name).file_size for name in file_list),
                        'extraction_path': self.temp_dir
                    },
                    file_import_id=metadata.get('file_import_id')
                )
                
                # Process each file based on detected source type
                for file_info in zf.infolist():
                    if file_info.is_dir():
                        continue
                        
                    # Read file content
                    file_path = Path(self.temp_dir) / file_info.filename
                    
                    # Yield file metadata
                    yield ParsedData(
                        content_type='extracted_file',
                        source_id=file_info.filename,
                        content=f"File: {file_info.filename}",
                        metadata={
                            'filename': file_info.filename,
                            'file_size': file_info.file_size,
                            'compress_size': file_info.compress_size,
                            'date_time': file_info.date_time,
                            'source_type': source_type,
                            'file_path': str(file_path)
                        },
                        file_import_id=metadata.get('file_import_id')
                    )
                    
        except Exception as e:
            logger.error(f"Error processing ZIP file: {e}")
            raise
        finally:
            # Cleanup will be handled by the processor after files are parsed
            pass
    
    async def extract_metadata(self, file_content: bytes) -> Dict[str, Any]:
        """
        Extract metadata from ZIP archive.
        
        Args:
            file_content: Raw ZIP file content
            
        Returns:
            Dictionary containing ZIP metadata
        """
        metadata = {
            'source_type': 'zip',
            'format': 'zip'
        }
        
        try:
            with zipfile.ZipFile(io.BytesIO(file_content)) as zf:
                # Get file list
                file_list = zf.namelist()
                metadata['file_count'] = len(file_list)
                
                # Calculate sizes
                total_uncompressed = 0
                total_compressed = 0
                file_types = {}
                
                for info in zf.infolist():
                    if not info.is_dir():
                        total_uncompressed += info.file_size
                        total_compressed += info.compress_size
                        
                        # Track file types
                        ext = Path(info.filename).suffix.lower()
                        file_types[ext] = file_types.get(ext, 0) + 1
                
                metadata['total_size_uncompressed'] = total_uncompressed
                metadata['total_size_compressed'] = total_compressed
                metadata['compression_ratio'] = (
                    1 - (total_compressed / total_uncompressed) 
                    if total_uncompressed > 0 else 0
                )
                metadata['file_types'] = file_types
                
                # Detect likely source type
                source_type = await self._detect_source_type(file_list, None)
                metadata['detected_source'] = source_type
                
                # Sample file list (first 20 files)
                metadata['sample_files'] = file_list[:20]
                
        except Exception as e:
            logger.error(f"Error extracting ZIP metadata: {e}")
            metadata['error'] = str(e)
            
        return metadata
    
    async def _detect_source_type(
        self, 
        file_list: List[str], 
        extract_path: Optional[str]
    ) -> str:
        """
        Detect the source type based on file structure.
        
        Args:
            file_list: List of files in the ZIP
            extract_path: Path where files are extracted (optional)
            
        Returns:
            Detected source type or 'unknown'
        """
        # Convert to lowercase for comparison
        lower_files = [f.lower() for f in file_list]
        
        # Slack detection
        slack_indicators = ['users.json', 'channels.json', 'integration_logs.json']
        if any(indicator in lower_files for indicator in slack_indicators):
            return 'slack'
        
        # Check for Slack channel folders
        if any('/' in f and f.endswith('.json') for f in file_list):
            # Check if structure matches Slack export (channel_name/YYYY-MM-DD.json)
            channel_pattern = any(
                len(Path(f).parts) == 2 and Path(f).suffix == '.json'
                for f in file_list
            )
            if channel_pattern:
                return 'slack'
        
        # Salesforce detection
        if any('salesforce' in f or '.soql' in f for f in lower_files):
            return 'salesforce'
        
        # Gong detection
        if any('gong' in f or 'transcript' in f for f in lower_files):
            return 'gong'
        
        # Looker detection
        if any('looker' in f or 'dashboard' in f for f in lower_files):
            return 'looker'
        
        # HubSpot detection
        if any('hubspot' in f or 'contacts' in f for f in lower_files):
            return 'hubspot'
        
        # Check file extensions for hints
        extensions = [Path(f).suffix.lower() for f in file_list]
        if '.csv' in extensions and any('report' in f for f in lower_files):
            return 'salesforce'  # Likely Salesforce reports
        
        return 'unknown'
    
    def cleanup(self) -> None:
        """Clean up temporary extraction directory."""
        if self.temp_dir and Path(self.temp_dir).exists():
            try:
                shutil.rmtree(self.temp_dir)
                logger.debug(f"Cleaned up temp directory: {self.temp_dir}")
            except Exception as e:
                logger.error(f"Error cleaning up temp directory: {e}")