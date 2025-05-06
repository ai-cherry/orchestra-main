"""
Memory Chunker for AI Orchestra Memory System.

This module provides functionality to split large documents into semantic chunks
for more efficient storage and retrieval.
"""

import logging
import re
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union, TypeVar

from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)


class ChunkingStrategy(str, Enum):
    """Strategies for chunking memory items."""
    PARAGRAPH = "paragraph"     # Split by paragraphs
    SENTENCE = "sentence"       # Split by sentences
    FIXED_SIZE = "fixed_size"   # Split by fixed token/character count
    SEMANTIC = "semantic"       # Split by semantic boundaries using AI
    HYBRID = "hybrid"           # Combine multiple strategies


class ChunkMetadata(BaseModel):
    """
    Metadata for a memory chunk.
    
    This class encapsulates metadata about a chunk, including its
    position in the original document and relationships to other chunks.
    """
    # Chunk identifiers
    chunk_id: str
    parent_id: str  # ID of the original document
    
    # Position information
    sequence_num: int
    total_chunks: int
    
    # Content information
    chunk_type: str = "text"
    content_start_idx: int
    content_end_idx: int
    
    # Relationship information
    previous_chunk_id: Optional[str] = None
    next_chunk_id: Optional[str] = None
    
    # Semantic information
    heading: Optional[str] = None
    summary: Optional[str] = None
    
    # Additional metadata
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)


class Chunk(BaseModel):
    """
    A chunk of a memory item.
    
    This class represents a chunk of a larger memory item,
    including the chunk content and metadata.
    """
    # Chunk content
    content: str
    
    # Chunk metadata
    metadata: ChunkMetadata
    
    # Optional embedding for semantic search
    embedding: Optional[List[float]] = None


class ChunkerConfig(BaseModel):
    """
    Configuration for memory chunker.
    
    This class encapsulates the configuration parameters for the
    memory chunking algorithm.
    """
    # Default chunking strategy
    default_strategy: ChunkingStrategy = ChunkingStrategy.PARAGRAPH
    
    # Paragraph chunking parameters
    min_paragraph_length: int = 100
    max_paragraph_length: int = 1000
    
    # Sentence chunking parameters
    min_sentences_per_chunk: int = 3
    max_sentences_per_chunk: int = 10
    
    # Fixed size chunking parameters
    chunk_size_chars: int = 500
    chunk_overlap_chars: int = 50
    
    # Semantic chunking parameters
    use_vertex_ai: bool = True
    vertex_ai_config: Dict[str, Any] = Field(default_factory=dict)
    
    # Hybrid chunking parameters
    hybrid_strategies: List[ChunkingStrategy] = Field(
        default_factory=lambda: [
            ChunkingStrategy.PARAGRAPH,
            ChunkingStrategy.SENTENCE
        ]
    )
    
    # General parameters
    preserve_headings: bool = True
    generate_summaries: bool = False
    min_chunk_length: int = 50
    max_chunks_per_item: int = 100


class MemoryChunker:
    """
    Splits large documents into semantic chunks.
    
    This class provides functionality to split large memory items into
    smaller chunks for more efficient storage and retrieval.
    """
    
    def __init__(self, config: Optional[ChunkerConfig] = None):
        """
        Initialize memory chunker.
        
        Args:
            config: Optional configuration for memory chunking
        """
        self.config = config or ChunkerConfig()
        self.vertex_ai_client = None
        
        # Initialize Vertex AI client if enabled
        if self.config.use_vertex_ai:
            self._init_vertex_ai()
        
        logger.info(f"MemoryChunker initialized (strategy: {self.config.default_strategy})")
    
    def _init_vertex_ai(self) -> None:
        """
        Initialize Vertex AI client for semantic chunking.
        
        This method sets up the Vertex AI client for text analysis.
        """
        try:
            from google.cloud import aiplatform
            
            # Extract configuration
            project = self.config.vertex_ai_config.get("project", "cherry-ai-project")
            location = self.config.vertex_ai_config.get("location", "us-central1")
            
            # Initialize Vertex AI
            aiplatform.init(project=project, location=location)
            
            # Set up endpoint for text analysis
            endpoint_name = self.config.vertex_ai_config.get("endpoint_name")
            if endpoint_name:
                self.vertex_ai_client = aiplatform.Endpoint(endpoint_name)
                logger.info(f"Vertex AI endpoint initialized: {endpoint_name}")
            else:
                # Use foundation model for text analysis
                self.vertex_ai_client = aiplatform.TextGenerationModel.from_pretrained("text-bison@latest")
                logger.info("Vertex AI foundation model initialized for text analysis")
                
        except ImportError:
            logger.warning("google-cloud-aiplatform package not installed. Falling back to rule-based chunking.")
            self.config.use_vertex_ai = False
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            self.config.use_vertex_ai = False
    
    async def chunk_item(
        self,
        item_id: str,
        content: str,
        strategy: Optional[ChunkingStrategy] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """
        Split a memory item into chunks.
        
        Args:
            item_id: ID of the memory item
            content: Content to chunk
            strategy: Optional chunking strategy (defaults to config)
            metadata: Optional metadata about the content
            
        Returns:
            List of chunks
        """
        # Use default strategy if not specified
        if strategy is None:
            strategy = self.config.default_strategy
        
        # Select chunking method based on strategy
        if strategy == ChunkingStrategy.PARAGRAPH:
            chunks = self._chunk_by_paragraph(item_id, content)
        elif strategy == ChunkingStrategy.SENTENCE:
            chunks = self._chunk_by_sentence(item_id, content)
        elif strategy == ChunkingStrategy.FIXED_SIZE:
            chunks = self._chunk_by_fixed_size(item_id, content)
        elif strategy == ChunkingStrategy.SEMANTIC:
            chunks = await self._chunk_by_semantic(item_id, content)
        elif strategy == ChunkingStrategy.HYBRID:
            chunks = await self._chunk_by_hybrid(item_id, content)
        else:
            logger.warning(f"Unknown chunking strategy: {strategy}, falling back to paragraph")
            chunks = self._chunk_by_paragraph(item_id, content)
        
        # Apply post-processing
        chunks = self._post_process_chunks(chunks, metadata)
        
        # Limit number of chunks if needed
        if len(chunks) > self.config.max_chunks_per_item:
            logger.warning(
                f"Too many chunks generated ({len(chunks)}), "
                f"limiting to {self.config.max_chunks_per_item}"
            )
            chunks = chunks[:self.config.max_chunks_per_item]
        
        # Update chunk metadata with total count
        total_chunks = len(chunks)
        for i, chunk in enumerate(chunks):
            chunk.metadata.total_chunks = total_chunks
            chunk.metadata.sequence_num = i
            
            # Set previous/next chunk IDs
            if i > 0:
                chunk.metadata.previous_chunk_id = chunks[i-1].metadata.chunk_id
            if i < total_chunks - 1:
                chunk.metadata.next_chunk_id = chunks[i+1].metadata.chunk_id
        
        return chunks
    
    def _chunk_by_paragraph(self, item_id: str, content: str) -> List[Chunk]:
        """
        Split content by paragraphs.
        
        Args:
            item_id: ID of the memory item
            content: Content to chunk
            
        Returns:
            List of chunks
        """
        # Split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', content)
        
        # Filter out empty paragraphs
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        # Create chunks
        chunks = []
        current_chunk = ""
        current_start_idx = 0
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed max length, create a new chunk
            if len(current_chunk) + len(paragraph) > self.config.max_paragraph_length and len(current_chunk) >= self.config.min_paragraph_length:
                # Create chunk
                chunk_id = f"{item_id}_chunk_{len(chunks)}"
                chunk = Chunk(
                    content=current_chunk,
                    metadata=ChunkMetadata(
                        chunk_id=chunk_id,
                        parent_id=item_id,
                        sequence_num=len(chunks),
                        total_chunks=0,  # Will be updated later
                        content_start_idx=current_start_idx,
                        content_end_idx=current_start_idx + len(current_chunk)
                    )
                )
                chunks.append(chunk)
                
                # Reset current chunk
                current_chunk = paragraph
                current_start_idx = content.find(paragraph, current_start_idx + 1)
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                    current_start_idx = content.find(paragraph)
        
        # Add the last chunk if not empty
        if current_chunk:
            chunk_id = f"{item_id}_chunk_{len(chunks)}"
            chunk = Chunk(
                content=current_chunk,
                metadata=ChunkMetadata(
                    chunk_id=chunk_id,
                    parent_id=item_id,
                    sequence_num=len(chunks),
                    total_chunks=0,  # Will be updated later
                    content_start_idx=current_start_idx,
                    content_end_idx=current_start_idx + len(current_chunk)
                )
            )
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_by_sentence(self, item_id: str, content: str) -> List[Chunk]:
        """
        Split content by sentences.
        
        Args:
            item_id: ID of the memory item
            content: Content to chunk
            
        Returns:
            List of chunks
        """
        # Split by sentences
        sentences = re.split(r'(?<=[.!?])\s+', content)
        
        # Filter out empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Create chunks
        chunks = []
        current_sentences = []
        current_start_idx = 0
        
        for sentence in sentences:
            # If adding this sentence would exceed max sentences, create a new chunk
            if len(current_sentences) >= self.config.max_sentences_per_chunk:
                # Create chunk
                chunk_content = " ".join(current_sentences)
                chunk_id = f"{item_id}_chunk_{len(chunks)}"
                chunk = Chunk(
                    content=chunk_content,
                    metadata=ChunkMetadata(
                        chunk_id=chunk_id,
                        parent_id=item_id,
                        sequence_num=len(chunks),
                        total_chunks=0,  # Will be updated later
                        content_start_idx=current_start_idx,
                        content_end_idx=current_start_idx + len(chunk_content)
                    )
                )
                chunks.append(chunk)
                
                # Reset current sentences
                current_sentences = [sentence]
                current_start_idx = content.find(sentence, current_start_idx + 1)
            else:
                # Add sentence to current chunk
                if not current_sentences:
                    current_start_idx = content.find(sentence)
                current_sentences.append(sentence)
        
        # Add the last chunk if not empty
        if current_sentences:
            chunk_content = " ".join(current_sentences)
            chunk_id = f"{item_id}_chunk_{len(chunks)}"
            chunk = Chunk(
                content=chunk_content,
                metadata=ChunkMetadata(
                    chunk_id=chunk_id,
                    parent_id=item_id,
                    sequence_num=len(chunks),
                    total_chunks=0,  # Will be updated later
                    content_start_idx=current_start_idx,
                    content_end_idx=current_start_idx + len(chunk_content)
                )
            )
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_by_fixed_size(self, item_id: str, content: str) -> List[Chunk]:
        """
        Split content by fixed size chunks.
        
        Args:
            item_id: ID of the memory item
            content: Content to chunk
            
        Returns:
            List of chunks
        """
        chunks = []
        chunk_size = self.config.chunk_size_chars
        overlap = self.config.chunk_overlap_chars
        
        # Create chunks with overlap
        for i in range(0, len(content), chunk_size - overlap):
            # Get chunk content
            chunk_content = content[i:i + chunk_size]
            
            # Skip if chunk is too small
            if len(chunk_content) < self.config.min_chunk_length:
                continue
            
            # Create chunk
            chunk_id = f"{item_id}_chunk_{len(chunks)}"
            chunk = Chunk(
                content=chunk_content,
                metadata=ChunkMetadata(
                    chunk_id=chunk_id,
                    parent_id=item_id,
                    sequence_num=len(chunks),
                    total_chunks=0,  # Will be updated later
                    content_start_idx=i,
                    content_end_idx=i + len(chunk_content)
                )
            )
            chunks.append(chunk)
        
        return chunks
    
    async def _chunk_by_semantic(self, item_id: str, content: str) -> List[Chunk]:
        """
        Split content by semantic boundaries using AI.
        
        Args:
            item_id: ID of the memory item
            content: Content to chunk
            
        Returns:
            List of chunks
        """
        # If Vertex AI is not available, fall back to paragraph chunking
        if not self.config.use_vertex_ai or not self.vertex_ai_client:
            logger.warning("Semantic chunking not available, falling back to paragraph chunking")
            return self._chunk_by_paragraph(item_id, content)
        
        try:
            # Create prompt for semantic chunking
            prompt = f"""
            Split the following text into coherent semantic chunks. Each chunk should be a self-contained unit of information.
            
            Rules for chunking:
            1. Each chunk should be coherent and self-contained
            2. Preserve paragraph boundaries when possible
            3. Keep related information together
            4. Split at natural semantic boundaries
            5. Aim for chunks of roughly similar length
            
            Format your response as a JSON array of chunks, where each chunk is a string.
            
            Text to chunk:
            {content}
            
            Chunks:
            """
            
            # Call Vertex AI
            if hasattr(self.vertex_ai_client, "predict"):
                # Using custom endpoint
                response = await self.vertex_ai_client.predict_async(
                    instances=[{"prompt": prompt}]
                )
                
                # Extract chunks from response
                try:
                    import json
                    chunks_text = response[0].get("content", "[]")
                    chunks_list = json.loads(chunks_text)
                except (json.JSONDecodeError, IndexError, KeyError):
                    logger.error("Failed to parse semantic chunks from response")
                    return self._chunk_by_paragraph(item_id, content)
                
            else:
                # Using foundation model
                response = await self.vertex_ai_client.predict_async(
                    prompt=prompt,
                    max_output_tokens=1024,
                    temperature=0.2
                )
                
                # Extract chunks from response
                try:
                    import json
                    chunks_text = response.text
                    # Extract JSON array from response
                    json_match = re.search(r'\[.*\]', chunks_text, re.DOTALL)
                    if json_match:
                        chunks_list = json.loads(json_match.group(0))
                    else:
                        raise ValueError("No JSON array found in response")
                except (json.JSONDecodeError, ValueError):
                    logger.error("Failed to parse semantic chunks from response")
                    return self._chunk_by_paragraph(item_id, content)
            
            # Create chunks
            chunks = []
            current_start_idx = 0
            
            for chunk_text in chunks_list:
                # Find position in original content
                chunk_text = chunk_text.strip()
                if not chunk_text:
                    continue
                    
                # Find position in original content
                chunk_start = content.find(chunk_text, current_start_idx)
                if chunk_start == -1:
                    # If exact match not found, use current position
                    chunk_start = current_start_idx
                
                # Create chunk
                chunk_id = f"{item_id}_chunk_{len(chunks)}"
                chunk = Chunk(
                    content=chunk_text,
                    metadata=ChunkMetadata(
                        chunk_id=chunk_id,
                        parent_id=item_id,
                        sequence_num=len(chunks),
                        total_chunks=0,  # Will be updated later
                        content_start_idx=chunk_start,
                        content_end_idx=chunk_start + len(chunk_text)
                    )
                )
                chunks.append(chunk)
                
                # Update current position
                current_start_idx = chunk_start + len(chunk_text)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Semantic chunking failed: {e}")
            return self._chunk_by_paragraph(item_id, content)
    
    async def _chunk_by_hybrid(self, item_id: str, content: str) -> List[Chunk]:
        """
        Split content using a hybrid of multiple strategies.
        
        Args:
            item_id: ID of the memory item
            content: Content to chunk
            
        Returns:
            List of chunks
        """
        # Use the first strategy as primary
        primary_strategy = self.config.hybrid_strategies[0] if self.config.hybrid_strategies else ChunkingStrategy.PARAGRAPH
        
        # Get chunks using primary strategy
        if primary_strategy == ChunkingStrategy.SEMANTIC:
            chunks = await self._chunk_by_semantic(item_id, content)
        elif primary_strategy == ChunkingStrategy.PARAGRAPH:
            chunks = self._chunk_by_paragraph(item_id, content)
        elif primary_strategy == ChunkingStrategy.SENTENCE:
            chunks = self._chunk_by_sentence(item_id, content)
        elif primary_strategy == ChunkingStrategy.FIXED_SIZE:
            chunks = self._chunk_by_fixed_size(item_id, content)
        else:
            chunks = self._chunk_by_paragraph(item_id, content)
        
        # If we have multiple strategies, refine chunks using secondary strategy
        if len(self.config.hybrid_strategies) > 1:
            secondary_strategy = self.config.hybrid_strategies[1]
            
            # Refine large chunks using secondary strategy
            refined_chunks = []
            for chunk in chunks:
                # If chunk is too large, refine it
                if len(chunk.content) > self.config.max_paragraph_length:
                    # Create a temporary ID for sub-chunking
                    temp_id = f"{chunk.metadata.chunk_id}_sub"
                    
                    # Apply secondary strategy
                    if secondary_strategy == ChunkingStrategy.SEMANTIC:
                        sub_chunks = await self._chunk_by_semantic(temp_id, chunk.content)
                    elif secondary_strategy == ChunkingStrategy.PARAGRAPH:
                        sub_chunks = self._chunk_by_paragraph(temp_id, chunk.content)
                    elif secondary_strategy == ChunkingStrategy.SENTENCE:
                        sub_chunks = self._chunk_by_sentence(temp_id, chunk.content)
                    elif secondary_strategy == ChunkingStrategy.FIXED_SIZE:
                        sub_chunks = self._chunk_by_fixed_size(temp_id, chunk.content)
                    else:
                        sub_chunks = [chunk]
                    
                    # Add refined chunks
                    for sub_chunk in sub_chunks:
                        # Adjust metadata to maintain parent relationship
                        sub_chunk.metadata.parent_id = item_id
                        refined_chunks.append(sub_chunk)
                else:
                    # Keep chunk as is
                    refined_chunks.append(chunk)
            
            # Replace original chunks with refined chunks
            chunks = refined_chunks
        
        return chunks
    
    def _post_process_chunks(
        self,
        chunks: List[Chunk],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """
        Apply post-processing to chunks.
        
        Args:
            chunks: List of chunks to process
            metadata: Optional metadata about the content
            
        Returns:
            Processed chunks
        """
        # Skip if no chunks
        if not chunks:
            return chunks
        
        # Extract headings if enabled
        if self.config.preserve_headings:
            chunks = self._extract_headings(chunks)
        
        # Generate summaries if enabled
        if self.config.generate_summaries:
            chunks = self._generate_summaries(chunks)
        
        # Add custom metadata if provided
        if metadata:
            for chunk in chunks:
                chunk.metadata.custom_metadata.update(metadata)
        
        return chunks
    
    def _extract_headings(self, chunks: List[Chunk]) -> List[Chunk]:
        """
        Extract headings from chunks.
        
        Args:
            chunks: List of chunks to process
            
        Returns:
            Processed chunks with headings
        """
        # Simple heading extraction using regex
        heading_pattern = r'^#+\s+(.+)$|^(.+)\n[=\-]{3,}$'
        
        for chunk in chunks:
            # Look for Markdown or reStructuredText style headings
            match = re.search(heading_pattern, chunk.content, re.MULTILINE)
            if match:
                # Extract heading text
                heading = match.group(1) or match.group(2)
                chunk.metadata.heading = heading.strip()
        
        return chunks
    
    def _generate_summaries(self, chunks: List[Chunk]) -> List[Chunk]:
        """
        Generate summaries for chunks.
        
        Args:
            chunks: List of chunks to process
            
        Returns:
            Processed chunks with summaries
        """
        # Simple summary generation (first sentence)
        for chunk in chunks:
            # Extract first sentence
            match = re.search(r'^(.+?[.!?])(?:\s|$)', chunk.content)
            if match:
                summary = match.group(1).strip()
                # Truncate if too long
                if len(summary) > 100:
                    summary = summary[:97] + "..."
                chunk.metadata.summary = summary
        
        return chunks


# Import datetime here to avoid circular import
from datetime import datetime