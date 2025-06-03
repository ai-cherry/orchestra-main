"""
"""
    """
    """
        """Initialize the ZIP handler."""
        self.supported_formats = ["zip"]
        self.content_types = ["extracted_file"]
        self.temp_dir = None
        
    async def validate(self, file_content: bytes, filename: str) -> bool:
        """
        """
                    logger.warning(f"Corrupted file in ZIP: {result}")
                    return False
                return True
                
        except Exception:

                
            pass
            return False
        except Exception:

            pass
            logger.error(f"Error validating ZIP file: {e}")
            return False
    
    async def parse(
        self, 
        file_content: bytes, 
        metadata: Dict[str, Any]
    ) -> AsyncIterator[ParsedData]:
        """
        """
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
                    
        except Exception:

                    
            pass
            logger.error(f"Error processing ZIP file: {e}")
            raise
        finally:
            # Cleanup will be handled by the processor after files are parsed
            pass
    
    async def extract_metadata(self, file_content: bytes) -> Dict[str, Any]:
        """
        """
            logger.error(f"Error extracting ZIP metadata: {e}")
            metadata['error'] = str(e)
            
        return metadata
    
    async def _detect_source_type(
        self, 
        file_list: List[str], 
        extract_path: Optional[str]
    ) -> str:
        """
        """
        """Clean up temporary extraction directory."""
            except Exception:

                pass
                logger.error(f"Error cleaning up temp directory: {e}")