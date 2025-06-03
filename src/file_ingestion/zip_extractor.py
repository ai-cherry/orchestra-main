#!/usr/bin/env python3
"""ZIP file extraction service"""

import logging
import zipfile
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ZipExtractor:
    """Extract and process ZIP files"""
    
    def __init__(self):
        self.max_extraction_size = 5 * 1024 * 1024 * 1024  # 5GB
    
    async def extract(self, file_path: str, extract_to: str = None) -> Dict[str, Any]:
        """Extract a ZIP file"""
        try:
            path = Path(file_path)
            
            if not zipfile.is_zipfile(path):
                return {"error": "Not a valid ZIP file"}
            
            # Determine extraction directory
            if extract_to:
                extract_dir = Path(extract_to)
            else:
                extract_dir = path.parent / path.stem
            
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract files
            extracted_files = []
            total_size = 0
            
            with zipfile.ZipFile(path, 'r') as zip_file:
                for info in zip_file.infolist():
                    if total_size + info.file_size > self.max_extraction_size:
                        return {"error": "ZIP file too large to extract"}
                    
                    zip_file.extract(info, extract_dir)
                    extracted_files.append(str(extract_dir / info.filename))
                    total_size += info.file_size
            
            return {
                "extracted_to": str(extract_dir),
                "files": extracted_files,
                "total_files": len(extracted_files),
                "total_size": total_size
            }
            
        except Exception as e:
            logger.error(f"ZIP extraction error: {str(e)}")
            return {"error": str(e)}
