#!/usr/bin/env python3
"""
Enterprise File Ingestion Pipeline
Handles large file uploads, processing, chunking, and multi-database storage

Supports:
- ZIP file extraction and processing
- Multiple file formats (PDF, DOCX, CSV, JSON, TXT, Slack exports)
- Intelligent chunking with context preservation
- Parallel storage in Pinecone, Weaviate, Redis, PostgreSQL
- Metadata extraction and enrichment

Author: Cherry AI Team
Version: 1.0.0
"""

import os
import json
import asyncio
import hashlib
import zipfile
import tempfile
import mimetypes
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
from pathlib import Path

# File processing imports
try:
    import PyPDF2
    import docx
    import pandas as pd
    from bs4 import BeautifulSoup
    FILE_PROCESSING_AVAILABLE = True
except ImportError:
    FILE_PROCESSING_AVAILABLE = False
    print("Warning: File processing libraries not available. Install with: pip install PyPDF2 python-docx pandas beautifulsoup4")

# Text processing imports
try:
    import tiktoken
    from sentence_transformers import SentenceTransformer
    import nltk
    TEXT_PROCESSING_AVAILABLE = True
except ImportError:
    TEXT_PROCESSING_AVAILABLE = False
    print("Warning: Text processing libraries not available. Install with: pip install tiktoken sentence-transformers nltk")

from .enterprise_db_manager import EnterpriseDatabaseManager

logger = logging.getLogger(__name__)

class FileProcessor:
    """Handles different file format processing"""
    
    def __init__(self):
        self.supported_formats = {
            '.pdf': self._process_pdf,
            '.docx': self._process_docx,
            '.doc': self._process_docx,
            '.txt': self._process_text,
            '.csv': self._process_csv,
            '.json': self._process_json,
            '.html': self._process_html,
            '.htm': self._process_html,
            '.md': self._process_text,
            '.zip': self._process_zip
        }
    
    async def process_file(self, file_path: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a file and return chunks with metadata"""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext not in self.supported_formats:
            logger.warning(f"Unsupported file format: {file_ext}")
            return []
        
        try:
            processor = self.supported_formats[file_ext]
            return await processor(file_path, metadata)
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return []
    
    async def _process_pdf(self, file_path: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process PDF files"""
        if not FILE_PROCESSING_AVAILABLE:
            return []
        
        chunks = []
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    if text.strip():
                        chunk_metadata = {
                            **metadata,
                            'page_number': page_num + 1,
                            'total_pages': len(pdf_reader.pages)
                        }
                        chunks.append({
                            'content': text,
                            'metadata': chunk_metadata
                        })
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {e}")
        
        return chunks
    
    async def _process_docx(self, file_path: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process DOCX files"""
        if not FILE_PROCESSING_AVAILABLE:
            return []
        
        chunks = []
        try:
            doc = docx.Document(file_path)
            content = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    content.append(paragraph.text)
            
            full_text = '\n'.join(content)
            if full_text.strip():
                chunks.append({
                    'content': full_text,
                    'metadata': {
                        **metadata,
                        'paragraphs': len(content)
                    }
                })
        except Exception as e:
            logger.error(f"Error processing DOCX {file_path}: {e}")
        
        return chunks
    
    async def _process_text(self, file_path: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process text files"""
        chunks = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                if content.strip():
                    chunks.append({
                        'content': content,
                        'metadata': metadata
                    })
        except Exception as e:
            logger.error(f"Error processing text file {file_path}: {e}")
        
        return chunks
    
    async def _process_csv(self, file_path: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process CSV files"""
        if not FILE_PROCESSING_AVAILABLE:
            return []
        
        chunks = []
        try:
            df = pd.read_csv(file_path)
            
            # Convert to structured text
            content = f"CSV Data Summary:\n"
            content += f"Columns: {', '.join(df.columns)}\n"
            content += f"Rows: {len(df)}\n\n"
            
            # Add sample data
            content += "Sample Data:\n"
            content += df.head(10).to_string(index=False)
            
            # Add column statistics if numeric
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                content += "\n\nNumeric Column Statistics:\n"
                content += df[numeric_cols].describe().to_string()
            
            chunks.append({
                'content': content,
                'metadata': {
                    **metadata,
                    'rows': len(df),
                    'columns': list(df.columns),
                    'numeric_columns': list(numeric_cols)
                }
            })
            
        except Exception as e:
            logger.error(f"Error processing CSV {file_path}: {e}")
        
        return chunks
    
    async def _process_json(self, file_path: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process JSON files"""
        chunks = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                # Convert JSON to readable text
                content = json.dumps(data, indent=2, ensure_ascii=False)
                
                chunks.append({
                    'content': content,
                    'metadata': {
                        **metadata,
                        'json_keys': list(data.keys()) if isinstance(data, dict) else None,
                        'json_type': type(data).__name__
                    }
                })
                
        except Exception as e:
            logger.error(f"Error processing JSON {file_path}: {e}")
        
        return chunks
    
    async def _process_html(self, file_path: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process HTML files"""
        if not FILE_PROCESSING_AVAILABLE:
            return []
        
        chunks = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                html_content = file.read()
                
                soup = BeautifulSoup(html_content, 'html.parser')
                text = soup.get_text()
                
                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                text = '\n'.join(line for line in lines if line)
                
                if text.strip():
                    chunks.append({
                        'content': text,
                        'metadata': {
                            **metadata,
                            'title': soup.title.string if soup.title else None
                        }
                    })
                    
        except Exception as e:
            logger.error(f"Error processing HTML {file_path}: {e}")
        
        return chunks
    
    async def _process_zip(self, file_path: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process ZIP files by extracting and processing contents"""
        all_chunks = []
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Create temporary directory for extraction
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)
                    
                    # Process each extracted file
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            extracted_path = os.path.join(root, file)
                            relative_path = os.path.relpath(extracted_path, temp_dir)
                            
                            # Create metadata for extracted file
                            extracted_metadata = {
                                **metadata,
                                'extracted_from': os.path.basename(file_path),
                                'relative_path': relative_path,
                                'original_file': file
                            }
                            
                            # Process the extracted file
                            file_chunks = await self.process_file(extracted_path, extracted_metadata)
                            all_chunks.extend(file_chunks)
                            
        except Exception as e:
            logger.error(f"Error processing ZIP {file_path}: {e}")
        
        return all_chunks

class TextChunker:
    """Intelligent text chunking with context preservation"""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap
        
        # Initialize tokenizer
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except:
            self.tokenizer = None
            logger.warning("Tiktoken not available, using character-based chunking")
    
    async def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split text into chunks with overlap and context preservation"""
        if not text.strip():
            return []
        
        chunks = []
        
        if self.tokenizer:
            chunks = await self._chunk_by_tokens(text, metadata)
        else:
            chunks = await self._chunk_by_characters(text, metadata)
        
        return chunks
    
    async def _chunk_by_tokens(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk text by token count"""
        tokens = self.tokenizer.encode(text)
        chunks = []
        
        for i in range(0, len(tokens), self.chunk_size - self.overlap):
            chunk_tokens = tokens[i:i + self.chunk_size]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            
            chunk_metadata = {
                **metadata,
                'chunk_index': len(chunks),
                'token_count': len(chunk_tokens),
                'start_token': i,
                'end_token': i + len(chunk_tokens)
            }
            
            chunks.append({
                'content': chunk_text,
                'metadata': chunk_metadata
            })
        
        return chunks
    
    async def _chunk_by_characters(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk text by character count"""
        chunks = []
        char_chunk_size = self.chunk_size * 4  # Approximate 4 chars per token
        char_overlap = self.overlap * 4
        
        for i in range(0, len(text), char_chunk_size - char_overlap):
            chunk_text = text[i:i + char_chunk_size]
            
            chunk_metadata = {
                **metadata,
                'chunk_index': len(chunks),
                'char_count': len(chunk_text),
                'start_char': i,
                'end_char': i + len(chunk_text)
            }
            
            chunks.append({
                'content': chunk_text,
                'metadata': chunk_metadata
            })
        
        return chunks

class IngestionPipeline:
    """Main ingestion pipeline coordinating file processing and database storage"""
    
    def __init__(self, db_manager: EnterpriseDatabaseManager):
        self.db_manager = db_manager
        self.file_processor = FileProcessor()
        self.text_chunker = TextChunker()
    
    async def ingest_file(self, file_path: str, persona: str, 
                         source: str = "upload", additional_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Main ingestion method for a single file"""
        start_time = datetime.now()
        
        # Calculate file hash
        file_hash = await self._calculate_file_hash(file_path)
        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)
        file_type = mimetypes.guess_type(file_path)[0] or 'unknown'
        
        # Check if file already processed
        if await self._is_file_processed(file_hash):
            logger.info(f"File {filename} already processed, skipping")
            return {
                'status': 'skipped',
                'reason': 'already_processed',
                'file_hash': file_hash
            }
        
        # Record ingestion start
        ingestion_id = await self._record_ingestion_start(
            filename, file_hash, file_size, file_type, persona
        )
        
        try:
            # Base metadata
            base_metadata = {
                'filename': filename,
                'file_hash': file_hash,
                'file_size': file_size,
                'file_type': file_type,
                'persona': persona,
                'source': source,
                'ingestion_id': ingestion_id,
                'timestamp': start_time.isoformat(),
                **(additional_metadata or {})
            }
            
            # Process file
            logger.info(f"Processing file: {filename}")
            file_chunks = await self.file_processor.process_file(file_path, base_metadata)
            
            if not file_chunks:
                await self._record_ingestion_error(ingestion_id, "No content extracted from file")
                return {
                    'status': 'error',
                    'reason': 'no_content',
                    'file_hash': file_hash
                }
            
            # Chunk text content
            all_chunks = []
            for file_chunk in file_chunks:
                text_chunks = await self.text_chunker.chunk_text(
                    file_chunk['content'], 
                    file_chunk['metadata']
                )
                all_chunks.extend(text_chunks)
            
            logger.info(f"Created {len(all_chunks)} chunks from {filename}")
            
            # Generate embeddings and store in databases
            await self._store_chunks(all_chunks, persona)
            
            # Record successful completion
            await self._record_ingestion_completion(ingestion_id, len(all_chunks))
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            return {
                'status': 'success',
                'file_hash': file_hash,
                'chunks_created': len(all_chunks),
                'processing_time': processing_time,
                'ingestion_id': ingestion_id
            }
            
        except Exception as e:
            logger.error(f"Error ingesting file {filename}: {e}")
            await self._record_ingestion_error(ingestion_id, str(e))
            return {
                'status': 'error',
                'reason': str(e),
                'file_hash': file_hash,
                'ingestion_id': ingestion_id
            }
    
    async def ingest_directory(self, directory_path: str, persona: str, 
                             recursive: bool = True) -> Dict[str, Any]:
        """Ingest all files in a directory"""
        results = []
        total_files = 0
        successful = 0
        
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                total_files += 1
                
                result = await self.ingest_file(file_path, persona, source="directory")
                results.append(result)
                
                if result['status'] == 'success':
                    successful += 1
            
            if not recursive:
                break
        
        return {
            'total_files': total_files,
            'successful': successful,
            'failed': total_files - successful,
            'results': results
        }
    
    async def _store_chunks(self, chunks: List[Dict[str, Any]], persona: str):
        """Store chunks in all database systems"""
        if not chunks:
            return
        
        # Generate embeddings
        texts = [chunk['content'] for chunk in chunks]
        embeddings = []
        
        if self.db_manager.embedding_manager:
            embeddings = await self.db_manager.embedding_manager.embed_texts(texts)
        
        # Prepare data for each database
        pinecone_vectors = []
        weaviate_objects = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{chunk['metadata']['file_hash']}_{chunk['metadata'].get('chunk_index', i)}"
            embedding = embeddings[i] if embeddings else None
            
            # Pinecone format
            if embedding and self.db_manager.pinecone_manager:
                pinecone_vectors.append({
                    'id': chunk_id,
                    'values': embedding,
                    'metadata': {
                        'content': chunk['content'][:1000],  # Limit metadata size
                        'source': chunk['metadata'].get('filename', ''),
                        'timestamp': chunk['metadata'].get('timestamp', ''),
                        'file_type': chunk['metadata'].get('file_type', ''),
                        'chunk_index': chunk['metadata'].get('chunk_index', 0)
                    }
                })
            
            # Weaviate format
            if self.db_manager.weaviate_manager:
                weaviate_objects.append({
                    'content': chunk['content'],
                    'source': chunk['metadata'].get('filename', ''),
                    'timestamp': chunk['metadata'].get('timestamp', ''),
                    'metadata': chunk['metadata'],
                    'persona': persona,
                    'file_type': chunk['metadata'].get('file_type', ''),
                    'chunk_index': chunk['metadata'].get('chunk_index', 0)
                })
        
        # Store in databases
        try:
            # Store in Pinecone
            if pinecone_vectors and self.db_manager.pinecone_manager:
                await self.db_manager.pinecone_manager.upsert_vectors(persona, pinecone_vectors)
            
            # Store in Weaviate
            if weaviate_objects and self.db_manager.weaviate_manager:
                await self.db_manager.weaviate_manager.add_objects(persona, weaviate_objects)
            
            # Cache embeddings in Redis
            if embeddings and self.db_manager.redis_manager:
                for i, text in enumerate(texts):
                    await self.db_manager.redis_manager.cache_embedding(text, embeddings[i])
            
            logger.info(f"Stored {len(chunks)} chunks in databases for persona {persona}")
            
        except Exception as e:
            logger.error(f"Error storing chunks in databases: {e}")
            raise
    
    async def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    async def _is_file_processed(self, file_hash: str) -> bool:
        """Check if file has already been processed"""
        if not self.db_manager.postgresql_manager:
            return False
        
        query = "SELECT id FROM file_ingestion WHERE file_hash = %s AND status = 'completed'"
        results = await self.db_manager.postgresql_manager.execute_query(query, (file_hash,))
        return len(results) > 0
    
    async def _record_ingestion_start(self, filename: str, file_hash: str, 
                                    file_size: int, file_type: str, persona: str) -> int:
        """Record the start of file ingestion"""
        if not self.db_manager.postgresql_manager:
            return 0
        
        query = """
        INSERT INTO file_ingestion (filename, file_hash, file_size, file_type, persona, status)
        VALUES (%s, %s, %s, %s, %s, 'processing')
        RETURNING id
        """
        
        results = await self.db_manager.postgresql_manager.execute_query(
            query, (filename, file_hash, file_size, file_type, persona)
        )
        
        return results[0]['id'] if results else 0
    
    async def _record_ingestion_completion(self, ingestion_id: int, chunks_created: int):
        """Record successful completion of ingestion"""
        if not self.db_manager.postgresql_manager:
            return
        
        query = """
        UPDATE file_ingestion 
        SET status = 'completed', chunks_created = %s, completed_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        
        await self.db_manager.postgresql_manager.execute_update(
            query, (chunks_created, ingestion_id)
        )
    
    async def _record_ingestion_error(self, ingestion_id: int, error_message: str):
        """Record ingestion error"""
        if not self.db_manager.postgresql_manager:
            return
        
        query = """
        UPDATE file_ingestion 
        SET status = 'error', metadata = jsonb_build_object('error', %s), completed_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        
        await self.db_manager.postgresql_manager.execute_update(
            query, (error_message, ingestion_id)
        )

# Example usage
async def main():
    """Test the ingestion pipeline"""
    db_manager = EnterpriseDatabaseManager()
    await db_manager.initialize_all()
    
    pipeline = IngestionPipeline(db_manager)
    
    # Test file ingestion
    test_file = "/path/to/test/file.pdf"
    if os.path.exists(test_file):
        result = await pipeline.ingest_file(test_file, "sophia", "test")
        print(f"Ingestion result: {result}")

if __name__ == "__main__":
    asyncio.run(main())

