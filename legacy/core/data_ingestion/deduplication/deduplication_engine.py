"""
"""
    """Types of duplicates detected."""
    EXACT = "exact"  # Exact content match
    NEAR = "near"    # Similar content (fuzzy match)
    SEMANTIC = "semantic"  # Same meaning, different words
    PARTIAL = "partial"  # Subset of existing content

class UploadChannel(Enum):
    """Data upload channels."""
    MANUAL = "manual"
    API = "api"
    WEB_INTERFACE = "web_interface"
    WEBHOOK = "webhook"
    SYNC = "sync"

@dataclass
class DuplicateMatch:
    """Represents a duplicate match found."""
    detection_method: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
            "existing_id": self.existing_id,
            "new_content_hash": self.new_content_hash,
            "existing_content_hash": self.existing_content_hash,
            "duplicate_type": self.duplicate_type.value,
            "similarity_score": self.similarity_score,
            "existing_metadata": self.existing_metadata,
            "detection_timestamp": self.detection_timestamp.isoformat(),
            "detection_method": self.detection_method
        }

class DeduplicationEngine:
    """
    """
        """
        """
        self.near_threshold = self.config.get("near_threshold", 0.95)
        self.semantic_threshold = self.config.get("semantic_threshold", 0.85)
        self.partial_threshold = self.config.get("partial_threshold", 0.7)
        
        # TF-IDF vectorizer for text similarity
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 3),
            stop_words='english'
        )
        
        # Cache for performance
        self._hash_cache: Dict[str, str] = {}
        self._vector_cache: Dict[str, np.ndarray] = {}
        
    async def check_duplicate(
        self,
        content: str,
        metadata: Dict[str, Any],
        existing_records: List[Dict[str, Any]],
        upload_channel: UploadChannel
    ) -> Optional[DuplicateMatch]:
        """
        """
        """
        """
        all_content = [item.get("content", "") for item in items]
        all_content.extend([
            record.get("content", "") for record in existing_records
        ])
        
        if all_content:
            # Fit vectorizer on all content
            self.vectorizer.fit(all_content)
        
        # Check each item
        tasks = []
        for item in items:
            task = self.check_duplicate(
                item.get("content", ""),
                item.get("metadata", {}),
                existing_records,
                UploadChannel(item.get("upload_channel", "manual"))
            )
            tasks.append(task)
        
        # Run checks in parallel
        matches = await asyncio.gather(*tasks)
        
        # Map results
        for item, match in zip(items, matches):
            results[item.get("id", str(hash(item["content"])))] = match
        
        return results
    
    def _generate_content_hash(
        self,
        content: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        """
        cache_key = f"{content}:{json.dumps(metadata, sort_keys=True)}"
        if cache_key in self._hash_cache:
            return self._hash_cache[cache_key]
        
        # Include key metadata in hash for better duplicate detection
        hash_input = content
        
        # Add source-specific identifiers
        if "source_id" in metadata:
            hash_input += f"|source_id:{metadata['source_id']}"
        if "timestamp" in metadata:
            hash_input += f"|timestamp:{metadata['timestamp']}"
        if "source_type" in metadata:
            hash_input += f"|source_type:{metadata['source_type']}"
        
        # Generate hash
        content_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
        
        # Cache result
        self._hash_cache[cache_key] = content_hash
        
        return content_hash
    
    async def _check_exact_match(
        self,
        content_hash: str,
        existing_records: List[Dict[str, Any]]
    ) -> Optional[DuplicateMatch]:
        """Check for exact content match."""
            existing_hash = record.get("content_hash")
            if existing_hash == content_hash:
                return DuplicateMatch(
                    existing_id=record["id"],
                    new_content_hash=content_hash,
                    existing_content_hash=existing_hash,
                    duplicate_type=DuplicateType.EXACT,
                    similarity_score=1.0,
                    existing_metadata=record.get("metadata", {}),
                    detection_method="hash_match"
                )
        return None
    
    async def _check_near_match(
        self,
        content: str,
        existing_records: List[Dict[str, Any]]
    ) -> Optional[DuplicateMatch]:
        """Check for near duplicates using fuzzy matching."""
            existing_content = record.get("content", "")
            if not existing_content:
                continue
            
            # Get or compute vector
            record_id = record["id"]
            if record_id in self._vector_cache:
                existing_vector = self._vector_cache[record_id]
            else:
                existing_vector = self.vectorizer.transform([existing_content])
                self._vector_cache[record_id] = existing_vector
            
            # Calculate similarity
            similarity = cosine_similarity(new_vector, existing_vector)[0][0]
            
            if similarity >= self.near_threshold and similarity > best_score:
                best_score = similarity
                best_match = record
        
        if best_match:
            return DuplicateMatch(
                existing_id=best_match["id"],
                new_content_hash=self._generate_content_hash(content, {}),
                existing_content_hash=best_match.get("content_hash", ""),
                duplicate_type=DuplicateType.NEAR,
                similarity_score=best_score,
                existing_metadata=best_match.get("metadata", {}),
                detection_method="fuzzy_match"
            )
        
        return None
    
    async def _check_semantic_match(
        self,
        content: str,
        existing_records: List[Dict[str, Any]]
    ) -> Optional[DuplicateMatch]:
        """
        """
            existing_content = record.get("content", "")
            if not existing_content:
                continue
            
            existing_vector = self.vectorizer.transform([existing_content])
            similarity = cosine_similarity(new_vector, existing_vector)[0][0]
            
            if (similarity >= self.semantic_threshold and 
                similarity < self.near_threshold and 
                similarity > best_score):
                best_score = similarity
                best_match = record
        
        if best_match:
            return DuplicateMatch(
                existing_id=best_match["id"],
                new_content_hash=self._generate_content_hash(content, {}),
                existing_content_hash=best_match.get("content_hash", ""),
                duplicate_type=DuplicateType.SEMANTIC,
                similarity_score=best_score,
                existing_metadata=best_match.get("metadata", {}),
                detection_method="semantic_match"
            )
        
        return None
    
    async def _check_partial_match(
        self,
        content: str,
        existing_records: List[Dict[str, Any]]
    ) -> Optional[DuplicateMatch]:
        """Check if content is subset of existing content."""
            existing_content = record.get("content", "").lower().strip()
            if not existing_content:
                continue
            
            # Check if new content is substring of existing
            if content_lower in existing_content:
                similarity = content_length / len(existing_content)
                if similarity >= self.partial_threshold:
                    return DuplicateMatch(
                        existing_id=record["id"],
                        new_content_hash=self._generate_content_hash(content, {}),
                        existing_content_hash=record.get("content_hash", ""),
                        duplicate_type=DuplicateType.PARTIAL,
                        similarity_score=similarity,
                        existing_metadata=record.get("metadata", {}),
                        detection_method="substring_match"
                    )
            
            # Check if existing content is substring of new
            elif existing_content in content_lower:
                similarity = len(existing_content) / content_length
                if similarity >= self.partial_threshold:
                    return DuplicateMatch(
                        existing_id=record["id"],
                        new_content_hash=self._generate_content_hash(content, {}),
                        existing_content_hash=record.get("content_hash", ""),
                        duplicate_type=DuplicateType.PARTIAL,
                        similarity_score=similarity,
                        existing_metadata=record.get("metadata", {}),
                        detection_method="substring_match"
                    )
        
        return None
    
    def clear_cache(self):
        """Clear internal caches."""