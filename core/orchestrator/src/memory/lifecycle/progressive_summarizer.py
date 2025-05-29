"""
Progressive Summarizer for AI Orchestra Memory System.

This module provides functionality to create multi-level summaries of memory items
for efficient storage while preserving context.
"""

import logging
import re
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from google.cloud import aiplatform
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)


class SummaryLevel(str, Enum):
    """Summary levels for progressive summarization."""

    FULL = "full"  # Original full content
    CONDENSED = "condensed"  # Condensed highlights (about 30-40% of original)
    KEY_POINTS = "key_points"  # Key points and entities (about 10-20% of original)
    HEADLINE = "headline"  # Single sentence headline (about 5% of original)


class SummaryResult(BaseModel):
    """
    Result of a summarization operation.

    This class encapsulates the result of summarizing content,
    including the summary text and metadata.
    """

    # Original content reference
    original_id: str
    original_length: int

    # Summary content
    summary_text: str
    summary_level: SummaryLevel
    compression_ratio: float  # Original length / Summary length

    # Metadata
    preserved_entities: List[str] = Field(default_factory=list)
    preserved_keywords: List[str] = Field(default_factory=list)

    # Quality metrics
    estimated_quality: float = 0.0  # 0.0 to 1.0

    # Timestamp
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ProgressiveSummarizerConfig(BaseModel):
    """
    Configuration for progressive summarizer.

    This class encapsulates the configuration parameters for the
    progressive summarization algorithm.
    """

    # Target compression ratios for each level
    condensed_ratio: float = 0.35  # Target 35% of original length
    key_points_ratio: float = 0.15  # Target 15% of original length
    headline_ratio: float = 0.05  # Target 5% of original length

    # Minimum content lengths for summarization
    min_length_for_condensed: int = 100
    min_length_for_key_points: int = 200
    min_length_for_headline: int = 500

    # Maximum token limits
    max_input_tokens: int = 4000

    # Entity and keyword preservation
    preserve_entities: bool = True
    preserve_keywords: bool = True
    max_entities_to_preserve: int = 10
    max_keywords_to_preserve: int = 15

    # Use Vertex AI for summarization
    use_openai: bool = True
    openai_config: Dict[str, Any] = Field(default_factory=dict)

    # Fallback to rule-based summarization if AI fails
    enable_fallback: bool = True


class ProgressiveSummarizer:
    """
    Creates multi-level summaries of memory items.

    This class provides functionality to create summaries at different levels
    of compression, from condensed highlights to single-sentence headlines.
    """

    def __init__(self, config: Optional[ProgressiveSummarizerConfig] = None):
        """
        Initialize progressive summarizer.

        Args:
            config: Optional configuration for progressive summarization
        """
        self.config = config or ProgressiveSummarizerConfig()
        self.openai_client = None

        # Initialize Vertex AI client if enabled
        if self.config.use_openai:
            self._init_openai()

        logger.info(f"ProgressiveSummarizer initialized (Vertex AI: {self.config.use_openai})")

    def _init_openai(self) -> None:
        """
        Initialize Vertex AI client for summarization.

        This method sets up the Vertex AI client for text summarization.
        """
        try:

            # Extract configuration
            project = self.config.openai_config.get("project", "cherry-ai-project")
            location = self.config.openai_config.get("location", "us-central1")

            # Initialize Vertex AI
            aiplatform.init(project=project, location=location)

            # Set up endpoint for text generation
            endpoint_name = self.config.openai_config.get("endpoint_name")
            if endpoint_name:
                self.openai_client = aiplatform.Endpoint(endpoint_name)
                logger.info(f"Vertex AI endpoint initialized: {endpoint_name}")
            else:
                # Use foundation model for summarization
                self.openai_client = aiplatform.TextGenerationModel.from_pretrained("text-bison@latest")
                logger.info("Vertex AI foundation model initialized for summarization")

        except ImportError:
            logger.warning("google-cloud-aiplatform package not installed. Falling back to rule-based summarization.")
            self.config.use_openai = False
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            self.config.use_openai = False

    async def summarize(
        self,
        content: str,
        item_id: str,
        level: SummaryLevel,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SummaryResult:
        """
        Summarize content to the specified level.

        Args:
            content: The content to summarize
            item_id: ID of the original item
            level: The desired summary level
            metadata: Optional metadata about the content

        Returns:
            Summary result
        """
        if level == SummaryLevel.FULL:
            # No summarization needed
            return SummaryResult(
                original_id=item_id,
                original_length=len(content),
                summary_text=content,
                summary_level=SummaryLevel.FULL,
                compression_ratio=1.0,
                estimated_quality=1.0,
            )

        # Check minimum length requirements
        content_length = len(content)
        if level == SummaryLevel.CONDENSED and content_length < self.config.min_length_for_condensed:
            logger.info(f"Content too short for {level} summarization, returning full content")
            return SummaryResult(
                original_id=item_id,
                original_length=content_length,
                summary_text=content,
                summary_level=SummaryLevel.FULL,
                compression_ratio=1.0,
                estimated_quality=1.0,
            )

        if level == SummaryLevel.KEY_POINTS and content_length < self.config.min_length_for_key_points:
            # Fall back to condensed if available
            if content_length >= self.config.min_length_for_condensed:
                level = SummaryLevel.CONDENSED
            else:
                return SummaryResult(
                    original_id=item_id,
                    original_length=content_length,
                    summary_text=content,
                    summary_level=SummaryLevel.FULL,
                    compression_ratio=1.0,
                    estimated_quality=1.0,
                )

        if level == SummaryLevel.HEADLINE and content_length < self.config.min_length_for_headline:
            # Fall back to key points or condensed if available
            if content_length >= self.config.min_length_for_key_points:
                level = SummaryLevel.KEY_POINTS
            elif content_length >= self.config.min_length_for_condensed:
                level = SummaryLevel.CONDENSED
            else:
                return SummaryResult(
                    original_id=item_id,
                    original_length=content_length,
                    summary_text=content,
                    summary_level=SummaryLevel.FULL,
                    compression_ratio=1.0,
                    estimated_quality=1.0,
                )

        # Extract entities and keywords if needed
        entities = []
        keywords = []
        if self.config.preserve_entities or self.config.preserve_keywords:
            entities, keywords = await self._extract_entities_and_keywords(content, metadata)

        # Truncate content if too long
        if content_length > self.config.max_input_tokens * 4:  # Approximate chars to tokens
            content = content[: self.config.max_input_tokens * 4]
            logger.warning(f"Content truncated to {self.config.max_input_tokens} tokens")

        # Perform summarization
        try:
            if self.config.use_openai and self.openai_client:
                summary_text = await self._summarize_with_openai(content, level)
            else:
                summary_text = self._summarize_with_rules(content, level)

            # Ensure entities and keywords are preserved
            if self.config.preserve_entities and entities:
                summary_text = self._ensure_entities_preserved(summary_text, entities)

            if self.config.preserve_keywords and keywords:
                summary_text = self._ensure_keywords_preserved(summary_text, keywords)

            # Calculate compression ratio
            compression_ratio = content_length / max(1, len(summary_text))

            # Estimate quality (simple heuristic)
            estimated_quality = min(1.0, len(summary_text) / (content_length * 0.5))

            return SummaryResult(
                original_id=item_id,
                original_length=content_length,
                summary_text=summary_text,
                summary_level=level,
                compression_ratio=compression_ratio,
                preserved_entities=entities[: self.config.max_entities_to_preserve],
                preserved_keywords=keywords[: self.config.max_keywords_to_preserve],
                estimated_quality=estimated_quality,
            )

        except Exception as e:
            logger.error(f"Summarization failed: {e}")

            # Fall back to rule-based summarization if AI fails
            if self.config.enable_fallback and self.config.use_openai:
                logger.info("Falling back to rule-based summarization")
                return await self.summarize(content, item_id, level, metadata)

            # If all else fails, return the original content
            return SummaryResult(
                original_id=item_id,
                original_length=content_length,
                summary_text=content,
                summary_level=SummaryLevel.FULL,
                compression_ratio=1.0,
                estimated_quality=0.5,
            )

    async def _summarize_with_openai(self, content: str, level: SummaryLevel) -> str:
        """
        Summarize content using Vertex AI.

        Args:
            content: The content to summarize
            level: The desired summary level

        Returns:
            Summarized text
        """
        # Determine target length based on level
        if level == SummaryLevel.CONDENSED:
            target_ratio = self.config.condensed_ratio
            instruction = "Create a condensed summary that preserves the main points and important details."
        elif level == SummaryLevel.KEY_POINTS:
            target_ratio = self.config.key_points_ratio
            instruction = "Extract only the key points and important entities as a concise summary."
        elif level == SummaryLevel.HEADLINE:
            target_ratio = self.config.headline_ratio
            instruction = "Create a single-sentence headline that captures the essence of the content."
        else:
            raise ValueError(f"Unsupported summary level: {level}")

        target_length = int(len(content) * target_ratio)

        # Create prompt for summarization
        prompt = f"""
        {instruction}

        Target length: approximately {target_length} characters.

        Original content:
        {content}

        Summary:
        """

        # Call Vertex AI
        if hasattr(self.openai_client, "predict"):
            # Using custom endpoint
            response = await self.openai_client.predict_async(instances=[{"prompt": prompt}])

            # Extract summary from response
            summary = response[0].get("content", "")

        else:
            # Using foundation model
            response = await self.openai_client.predict_async(
                prompt=prompt,
                max_output_tokens=1024,
                temperature=0.2,
                top_p=0.8,
                top_k=40,
            )

            summary = response.text

        return summary.strip()

    def _summarize_with_rules(self, content: str, level: SummaryLevel) -> str:
        """
        Summarize content using rule-based approaches.

        This is a fallback method when AI summarization is not available.

        Args:
            content: The content to summarize
            level: The desired summary level

        Returns:
            Summarized text
        """
        # Determine target length based on level
        if level == SummaryLevel.CONDENSED:
            target_ratio = self.config.condensed_ratio
        elif level == SummaryLevel.KEY_POINTS:
            target_ratio = self.config.key_points_ratio
        elif level == SummaryLevel.HEADLINE:
            target_ratio = self.config.headline_ratio
        else:
            raise ValueError(f"Unsupported summary level: {level}")

        target_length = int(len(content) * target_ratio)

        # Split into sentences
        sentences = re.split(r"(?<=[.!?])\s+", content)

        if level == SummaryLevel.HEADLINE:
            # For headline, just return the first sentence
            return sentences[0] if sentences else content[:target_length]

        # Calculate sentence importance (simple heuristic)
        sentence_scores = []
        for i, sentence in enumerate(sentences):
            # Position score (earlier sentences more important)
            position_score = 1.0 - (i / len(sentences))

            # Length score (longer sentences might have more info)
            length_score = min(1.0, len(sentence) / 100)

            # Keyword score (placeholder - would check for important keywords)
            keyword_score = 0.5

            # Combined score
            score = position_score * 0.5 + length_score * 0.3 + keyword_score * 0.2
            sentence_scores.append((sentence, score))

        # Sort by score
        sentence_scores.sort(key=lambda x: x[1], reverse=True)

        # Select top sentences to meet target length
        selected_sentences = []
        current_length = 0

        for sentence, _ in sentence_scores:
            if current_length + len(sentence) <= target_length:
                selected_sentences.append(sentence)
                current_length += len(sentence) + 1  # +1 for space
            else:
                break

        # Reorder sentences to maintain original flow
        original_order = []
        for sentence in sentences:
            if sentence in selected_sentences:
                original_order.append(sentence)

        # Join sentences
        return " ".join(original_order)

    async def _extract_entities_and_keywords(
        self, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[str], List[str]]:
        """
        Extract entities and keywords from content.

        Args:
            content: The content to extract from
            metadata: Optional metadata that might contain entities/keywords

        Returns:
            Tuple of (entities, keywords)
        """
        # Use metadata if available
        entities = []
        keywords = []

        if metadata:
            entities = metadata.get("entities", [])
            keywords = metadata.get("keywords", [])

        # If we have both, return them
        if entities and keywords:
            return entities, keywords

        # Simple extraction based on capitalization and frequency
        # In a real implementation, this would use NLP techniques

        # Extract potential entities (capitalized words)
        words = re.findall(r"\b[A-Z][a-z]+\b", content)
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1

        # Sort by frequency
        sorted_entities = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        entities = [word for word, _ in sorted_entities[: self.config.max_entities_to_preserve]]

        # Extract keywords (most frequent words, excluding stopwords)
        stopwords = {
            "the",
            "and",
            "a",
            "an",
            "in",
            "on",
            "at",
            "to",
            "for",
            "with",
            "by",
            "of",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
        }

        words = re.findall(r"\b[a-z]{3,}\b", content.lower())
        word_counts = {}
        for word in words:
            if word not in stopwords:
                word_counts[word] = word_counts.get(word, 0) + 1

        # Sort by frequency
        sorted_keywords = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, _ in sorted_keywords[: self.config.max_keywords_to_preserve]]

        return entities, keywords

    def _ensure_entities_preserved(self, summary: str, entities: List[str]) -> str:
        """
        Ensure entities are preserved in the summary.

        Args:
            summary: The summary text
            entities: List of entities to preserve

        Returns:
            Updated summary with entities preserved
        """
        # Check which entities are missing
        missing_entities = []
        for entity in entities[: self.config.max_entities_to_preserve]:
            if entity.lower() not in summary.lower():
                missing_entities.append(entity)

        # If no missing entities, return original summary
        if not missing_entities:
            return summary

        # Add missing entities as a postscript
        if len(missing_entities) > 0:
            entity_str = ", ".join(missing_entities)
            return f"{summary}\n\nKey entities: {entity_str}"

        return summary

    def _ensure_keywords_preserved(self, summary: str, keywords: List[str]) -> str:
        """
        Ensure keywords are preserved in the summary.

        Args:
            summary: The summary text
            keywords: List of keywords to preserve

        Returns:
            Updated summary with keywords preserved
        """
        # Check which keywords are missing
        missing_keywords = []
        for keyword in keywords[: self.config.max_keywords_to_preserve]:
            if keyword.lower() not in summary.lower():
                missing_keywords.append(keyword)

        # If no missing keywords, return original summary
        if not missing_keywords:
            return summary

        # Add missing keywords as a postscript
        if len(missing_keywords) > 0:
            keyword_str = ", ".join(missing_keywords)

            # Check if we already added entities
            if "Key entities:" in summary:
                return f"{summary}\n\nKey topics: {keyword_str}"
            else:
                return f"{summary}\n\nKey topics: {keyword_str}"

        return summary

    async def create_progressive_summaries(
        self, content: str, item_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[SummaryLevel, SummaryResult]:
        """
        Create summaries at all levels for a memory item.

        Args:
            content: The content to summarize
            item_id: ID of the original item
            metadata: Optional metadata about the content

        Returns:
            Dictionary mapping summary levels to summary results
        """
        # Create summaries for each level
        results = {}

        # Always include full content
        results[SummaryLevel.FULL] = SummaryResult(
            original_id=item_id,
            original_length=len(content),
            summary_text=content,
            summary_level=SummaryLevel.FULL,
            compression_ratio=1.0,
            estimated_quality=1.0,
        )

        # Check if content is long enough for condensed summary
        if len(content) >= self.config.min_length_for_condensed:
            condensed = await self.summarize(content, item_id, SummaryLevel.CONDENSED, metadata)
            results[SummaryLevel.CONDENSED] = condensed

        # Check if content is long enough for key points
        if len(content) >= self.config.min_length_for_key_points:
            key_points = await self.summarize(content, item_id, SummaryLevel.KEY_POINTS, metadata)
            results[SummaryLevel.KEY_POINTS] = key_points

        # Check if content is long enough for headline
        if len(content) >= self.config.min_length_for_headline:
            headline = await self.summarize(content, item_id, SummaryLevel.HEADLINE, metadata)
            results[SummaryLevel.HEADLINE] = headline

        return results


# Import datetime here to avoid circular import
from datetime import datetime
