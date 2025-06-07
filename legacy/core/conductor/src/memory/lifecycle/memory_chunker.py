"""
"""
    """Strategies for chunking memory items."""
    PARAGRAPH = "paragraph"  # Split by paragraphs
    SENTENCE = "sentence"  # Split by sentences
    FIXED_SIZE = "fixed_size"  # Split by fixed token/character count
    SEMANTIC = "semantic"  # Split by semantic boundaries using AI
    HYBRID = "hybrid"  # Combine multiple strategies

class ChunkMetadata(BaseModel):
    """
    """
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
    """
    """
    """
    """
    """
        """
        """
        logger.info(f"MemoryChunker initialized (strategy: {self.config.default_strategy})")

    async def chunk_item(
        self,
        item_id: str,
        content: str,
        strategy: Optional[ChunkingStrategy] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Chunk]:
        """
        """
            logger.warning(f"Unknown chunking strategy: {strategy}, falling back to paragraph")
            chunks = self._chunk_by_paragraph(item_id, content)

        # Apply post-processing
        chunks = self._post_process_chunks(chunks, metadata)

        # Limit number of chunks if needed
        if len(chunks) > self.config.max_chunks_per_item:
            logger.warning(
                f"Too many chunks generated ({len(chunks)}), " f"limiting to {self.config.max_chunks_per_item}"
            )
            chunks = chunks[: self.config.max_chunks_per_item]

        # Update chunk metadata with total count
        total_chunks = len(chunks)
        for i, chunk in enumerate(chunks):
            chunk.metadata.total_chunks = total_chunks
            chunk.metadata.sequence_num = i

            # Set previous/next chunk IDs
            if i > 0:
                chunk.metadata.previous_chunk_id = chunks[i - 1].metadata.chunk_id
            if i < total_chunks - 1:
                chunk.metadata.next_chunk_id = chunks[i + 1].metadata.chunk_id

        return chunks

    def _chunk_by_paragraph(self, item_id: str, content: str) -> List[Chunk]:
        """
        """
        paragraphs = re.split(r"\n\s*\n", content)

        # Filter out empty paragraphs
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        # Create chunks
        chunks = []
        current_chunk = ""
        current_start_idx = 0

        for paragraph in paragraphs:
            # If adding this paragraph would exceed max length, create a new chunk
            if (
                len(current_chunk) + len(paragraph) > self.config.max_paragraph_length
                and len(current_chunk) >= self.config.min_paragraph_length
            ):
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
                        content_end_idx=current_start_idx + len(current_chunk),
                    ),
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
                    content_end_idx=current_start_idx + len(current_chunk),
                ),
            )
            chunks.append(chunk)

        return chunks

    def _chunk_by_sentence(self, item_id: str, content: str) -> List[Chunk]:
        """
        """
        sentences = re.split(r"(?<=[.!?])\s+", content)

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
                        content_end_idx=current_start_idx + len(chunk_content),
                    ),
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
                    content_end_idx=current_start_idx + len(chunk_content),
                ),
            )
            chunks.append(chunk)

        return chunks

    def _chunk_by_fixed_size(self, item_id: str, content: str) -> List[Chunk]:
        """
        """
            chunk_id = f"{item_id}_chunk_{len(chunks)}"
            chunk = Chunk(
                content=chunk_content,
                metadata=ChunkMetadata(
                    chunk_id=chunk_id,
                    parent_id=item_id,
                    sequence_num=len(chunks),
                    total_chunks=0,  # Will be updated later
                    content_start_idx=i,
                    content_end_idx=i + len(chunk_content),
                ),
            )
            chunks.append(chunk)

        return chunks

    async def _chunk_by_semantic(self, item_id: str, content: str) -> List[Chunk]:
        """
        """
            logger.warning("Semantic chunking not available, falling back to paragraph chunking")
            return self._chunk_by_paragraph(item_id, content)

        try:


            pass
            # Create prompt for semantic chunking
            prompt = f"""
            """
            if hasattr(self.config.openai_client, "predict"):
                # Using custom endpoint
                response = await self.config.openai_client.predict_async(instances=[{"prompt": prompt}])

                # Extract chunks from response
                try:

                    pass
                    import json

                    chunks_text = response[0].get("content", "[]")
                    chunks_list = json.loads(chunks_text)
                except Exception:

                    pass
                    logger.error("Failed to parse semantic chunks from response")
                    return self._chunk_by_paragraph(item_id, content)

            else:
                # Using foundation model
                response = await self.config.openai_client.predict_async(
                    prompt=prompt, max_output_tokens=1024, temperature=0.2
                )

                # Extract chunks from response
                try:

                    pass
                    import json

                    chunks_text = response.text
                    # Extract JSON array from response
                    json_match = re.search(r"\[.*\]", chunks_text, re.DOTALL)
                    if json_match:
                        chunks_list = json.loads(json_match.group(0))
                    else:
                        raise ValueError("No JSON array found in response")
                except Exception:

                    pass
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
                        content_end_idx=chunk_start + len(chunk_text),
                    ),
                )
                chunks.append(chunk)

                # Update current position
                current_start_idx = chunk_start + len(chunk_text)

            return chunks

        except Exception:


            pass
            logger.error(f"Semantic chunking failed: {e}")
            return self._chunk_by_paragraph(item_id, content)

    async def _chunk_by_hybrid(self, item_id: str, content: str) -> List[Chunk]:
        """
        """
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

    def _post_process_chunks(self, chunks: List[Chunk], metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """
        """
        """
        """
        heading_pattern = r"^#+\s+(.+)$|^(.+)\n[=\-]{3,}$"

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
        """
            match = re.search(r"^(.+?[.!?])(?:\s|$)", chunk.content)
            if match:
                summary = match.group(1).strip()
                # Truncate if too long
                if len(summary) > 100:
                    summary = summary[:97] + "..."
                chunk.metadata.summary = summary

        return chunks

# Import datetime here to avoid circular import
