"""
Context Pruner for Memory Management.

This module provides mechanisms for automatically pruning non-essential
context from conversation history using Gemini AI-generated summaries.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from packages.shared.src.models.base_models import MemoryItem, AgentData, PersonaConfig
from packages.shared.src.storage.exceptions import StorageError, ConnectionError, OperationError
from agent.core.vertex_operations import generate_text

# Set up logger
logger = logging.getLogger(__name__)


class ContextPruner:
    """
    Context pruner for memory management.
    
    This class provides mechanisms for automatically pruning non-essential
    context from conversation history using Gemini AI-generated summaries.
    It helps maintain high-quality context while reducing token usage.
    """
    
    def __init__(
        self,
        max_context_items: int = 15,
        max_context_tokens: int = 4000,
        summarization_threshold: int = 25,
        summary_max_tokens: int = 1000,
        gemini_model: str = "gemini-1.5-pro",
        gemini_project: str = "your-project-id",
        gemini_location: str = "us-central1",
        summary_prompt_template: Optional[str] = None,
    ):
        """
        Initialize the context pruner.
        
        Args:
            max_context_items: Maximum number of history items to keep before pruning
            max_context_tokens: Maximum token budget for context
            summarization_threshold: Minimum number of items before summarization
            summary_max_tokens: Maximum token budget for summaries
            gemini_model: Gemini model to use for summarization
            gemini_project: GCP project ID
            gemini_location: GCP location
            summary_prompt_template: Optional custom prompt template for summarization
        """
        self._max_context_items = max_context_items
        self._max_context_tokens = max_context_tokens
        self._summarization_threshold = summarization_threshold
        self._summary_max_tokens = summary_max_tokens
        self._gemini_model = gemini_model
        self._gemini_project = gemini_project
        self._gemini_location = gemini_location
        
        # Default summarization prompt template
        self._summary_prompt_template = summary_prompt_template or """
            Summarize the following conversation history to extract the most important information.
            Focus on key facts, decisions, user preferences, and critical context.
            Include any specific details mentioned by the user that might be important later.
            Omit pleasantries, acknowledgments, and generic information.
            
            CONVERSATION HISTORY:
            {conversation_history}
            
            SUMMARY (be concise but comprehensive, focus on facts and context):
        """
    
    async def prune_conversation_history(
        self,
        history: List[MemoryItem],
        user_id: str,
        session_id: Optional[str] = None,
        important_keys: Optional[List[str]] = None,
    ) -> List[MemoryItem]:
        """
        Prune conversation history by summarizing non-essential context.
        
        Args:
            history: List of memory items representing conversation history
            user_id: User ID
            session_id: Optional session ID
            important_keys: Optional list of item IDs to preserve (never summarize)
            
        Returns:
            Pruned conversation history
        """
        if len(history) <= self._max_context_items:
            # No pruning needed
            return history
            
        # Sort by timestamp
        sorted_history = sorted(history, key=lambda x: x.timestamp)
        
        # Prepare important keys set (these items won't be summarized)
        important_items = set(important_keys or [])
        
        # Always keep the most recent items
        recent_items = sorted_history[-self._max_context_items // 2:]
        recent_item_ids = {item.id for item in recent_items if item.id}
        
        # Items that can be summarized (older items not in important_items)
        summarizable_items = []
        for item in sorted_history[:-self._max_context_items // 2]:
            if item.id and (item.id in important_items or item.id in recent_item_ids):
                # Keep important items as-is
                recent_items.append(item)
            else:
                # Candidate for summarization
                summarizable_items.append(item)
                
        # Check if we have enough items to summarize
        if len(summarizable_items) < self._summarization_threshold:
            # Not enough items to summarize, just return the important and recent items
            return sorted(recent_items + summarizable_items, key=lambda x: x.timestamp)
            
        # Generate summary of older conversation
        summary_text = await self._generate_summary(summarizable_items, user_id)
        
        # Create a new memory item containing the summary
        summary_item = MemoryItem(
            user_id=user_id,
            session_id=session_id,
            content=summary_text,
            content_type="summary",
            metadata={
                "summary_of": len(summarizable_items),
                "timestamp_range": [
                    summarizable_items[0].timestamp.isoformat() if summarizable_items[0].timestamp else "",
                    summarizable_items[-1].timestamp.isoformat() if summarizable_items[-1].timestamp else ""
                ]
            },
            timestamp=datetime.now(),
        )
        
        # Return pruned history: summary item + recent/important items
        pruned_history = [summary_item] + recent_items
        return sorted(pruned_history, key=lambda x: x.timestamp)
    
    async def prune_by_token_budget(
        self,
        history: List[MemoryItem],
        token_budget: int,
        important_keys: Optional[List[str]] = None,
    ) -> List[MemoryItem]:
        """
        Prune conversation history to fit within a token budget.
        
        Args:
            history: List of memory items representing conversation history
            token_budget: Maximum tokens to allocate for history
            important_keys: Optional list of item IDs to preserve (highest priority)
            
        Returns:
            Pruned conversation history
        """
        if not history:
            return []
            
        # Sort by timestamp (newest first)
        sorted_history = sorted(history, key=lambda x: x.timestamp, reverse=True)
        
        # Calculate approximate token count for each item
        # Rule of thumb: ~4 chars per token for English text
        item_tokens = []
        for item in sorted_history:
            token_estimate = len(item.content) // 4
            item_tokens.append((item, token_estimate))
            
        # Identify important items
        important_items = set(important_keys or [])
        
        # Create buckets: important, recent, and older items
        important_bucket = []
        recent_bucket = []
        older_bucket = []
        
        # First pass: separate items into buckets
        for item, tokens in item_tokens:
            if item.id and item.id in important_items:
                important_bucket.append((item, tokens))
            elif len(recent_bucket) < 5:  # Always keep 5 most recent items
                recent_bucket.append((item, tokens))
            else:
                older_bucket.append((item, tokens))
                
        # Second pass: calculate total tokens for each bucket
        important_tokens = sum(tokens for _, tokens in important_bucket)
        recent_tokens = sum(tokens for _, tokens in recent_bucket)
        
        # If important and recent items already exceed the budget, summarize them
        if important_tokens + recent_tokens > token_budget:
            # Sort important items by timestamp (oldest first)
            important_bucket.sort(key=lambda x: x[0].timestamp)
            
            # Keep adding items until we hit the budget
            kept_items = []
            current_tokens = 0
            
            # First add the most recent items
            for item, tokens in recent_bucket:
                if current_tokens + tokens <= token_budget * 0.8:  # Reserve 20% for summary
                    kept_items.append(item)
                    current_tokens += tokens
                else:
                    # Recent item doesn't fit, will be summarized
                    older_bucket.append((item, tokens))
            
            # Then add important items in order of recency
            for item, tokens in reversed(important_bucket):
                if current_tokens + tokens <= token_budget * 0.8:
                    kept_items.append(item)
                    current_tokens += tokens
                else:
                    # Important but too large, will be summarized
                    older_bucket.append((item, tokens))
                    
            # Extract just the items for summarization
            to_summarize = [item for item, _ in older_bucket]
            
            # Generate summary if we have items to summarize
            if to_summarize:
                user_id = to_summarize[0].user_id
                summary_text = await self._generate_summary(to_summarize, user_id)
                
                # Create a new memory item containing the summary
                summary_item = MemoryItem(
                    user_id=user_id,
                    session_id=to_summarize[0].session_id,
                    content=summary_text,
                    content_type="summary",
                    metadata={
                        "summary_of": len(to_summarize),
                        "token_budget": token_budget,
                        "timestamp_range": [
                            to_summarize[0].timestamp.isoformat() if to_summarize[0].timestamp else "",
                            to_summarize[-1].timestamp.isoformat() if to_summarize[-1].timestamp else ""
                        ]
                    },
                    timestamp=datetime.now(),
                )
                
                # Add summary item to kept items
                kept_items.append(summary_item)
                
            # Return the kept items sorted by timestamp
            return sorted(kept_items, key=lambda x: x.timestamp)
            
        else:
            # We have enough budget for important and recent items, now add older items
            remaining_budget = token_budget - (important_tokens + recent_tokens)
            
            # Sort older items by recency
            older_bucket.sort(key=lambda x: x[0].timestamp, reverse=True)
            
            # Add older items until we hit the budget
            kept_older = []
            older_to_summarize = []
            current_tokens = 0
            
            for item, tokens in older_bucket:
                if current_tokens + tokens <= remaining_budget * 0.8:  # Reserve 20% for summary
                    kept_older.append(item)
                    current_tokens += tokens
                else:
                    older_to_summarize.append(item)
            
            # Create the result list with kept items
            result = [item for item, _ in important_bucket] + [item for item, _ in recent_bucket] + kept_older
            
            # Generate summary for remaining older items if needed
            if older_to_summarize and remaining_budget - current_tokens >= 100:  # Only if we have at least 100 tokens left
                user_id = older_to_summarize[0].user_id
                summary_text = await self._generate_summary(older_to_summarize, user_id)
                
                # Create a new memory item containing the summary
                summary_item = MemoryItem(
                    user_id=user_id,
                    session_id=older_to_summarize[0].session_id,
                    content=summary_text,
                    content_type="summary",
                    metadata={
                        "summary_of": len(older_to_summarize),
                        "token_budget": token_budget,
                        "timestamp_range": [
                            older_to_summarize[0].timestamp.isoformat() if older_to_summarize[0].timestamp else "",
                            older_to_summarize[-1].timestamp.isoformat() if older_to_summarize[-1].timestamp else ""
                        ]
                    },
                    timestamp=datetime.now(),
                )
                
                # Add summary item to result
                result.append(summary_item)
                
            # Return items sorted by timestamp
            return sorted(result, key=lambda x: x.timestamp)
    
    async def _generate_summary(
        self,
        items: List[MemoryItem],
        user_id: str,
    ) -> str:
        """
        Generate a summary of conversation items using Gemini.
        
        Args:
            items: List of memory items to summarize
            user_id: User ID for the conversation
            
        Returns:
            Generated summary text
        """
        # Sort items by timestamp
        sorted_items = sorted(items, key=lambda x: x.timestamp)
        
        # Format conversation history
        conversation_text = ""
        for item in sorted_items:
            # Skip existing summaries
            if item.content_type == "summary":
                continue
                
            # Format based on content type
            if item.content_type == "user_message":
                conversation_text += f"User: {item.content}\n\n"
            elif item.content_type == "assistant_message":
                conversation_text += f"Assistant: {item.content}\n\n"
            else:
                conversation_text += f"{item.content_type}: {item.content}\n\n"
        
        # Prepare the prompt
        prompt = self._summary_prompt_template.format(
            conversation_history=conversation_text,
            user_id=user_id,
        )
        
        try:
            # Call Gemini API to generate summary
            summary = await generate_text(
                prompt=prompt,
                model=self._gemini_model,
                project_id=self._gemini_project,
                location=self._gemini_location,
                max_output_tokens=self._summary_max_tokens,
                temperature=0.1,  # Low temperature for factual summaries
            )
            
            # Clean up the summary
            summary = summary.strip()
            
            # Log summary generation
            logger.info(f"Generated summary for {len(items)} items, {len(summary)} chars")
            
            return f"CONVERSATION SUMMARY: {summary}"
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            # Fallback summary
            return f"CONVERSATION SUMMARY: This summarizes {len(items)} previous messages in the conversation with {user_id}."
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text string.
        
        Args:
            text: The text to analyze
            
        Returns:
            Estimated token count
        """
        # Simple estimation: ~4 characters per token for English text
        return len(text) // 4
