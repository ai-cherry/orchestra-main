"""
Pay Ready Query Agent
====================

Natural language query interface for the Pay Ready domain using Weaviate's
Query Agent capabilities.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

import weaviate
from weaviate.classes import Auth
from weaviate.agents.query import QueryAgent

logger = logging.getLogger(__name__)

class PayReadyQueryAgent:
    """
    Provides natural language query capabilities for Pay Ready domain data.

    Uses Weaviate's Query Agent to:
    - Answer questions about customer interactions
    - Generate summaries and reports
    - Find patterns across data sources
    - Create timelines of events
    """

    def __init__(self, weaviate_client: weaviate.Client):
        self.client = weaviate_client
        self.query_agent = None
        self.collections = [
            "PayReadySlackMessage",
            "PayReadyGongCallSegment",
            "PayReadyHubSpotNote",
            "PayReadySalesforceNote",
        ]
        self._initialized = False

    async def initialize(self):
        """Initialize the Query Agent with Pay Ready collections"""
        if self._initialized:
            return

        logger.info("Initializing Pay Ready Query Agent")

        # Initialize Query Agent with our collections
        self.query_agent = QueryAgent(client=self.client, collections=self.collections)

        self._initialized = True
        logger.info("Query Agent initialized successfully")

    async def query(
        self, question: str, context: Optional[Dict[str, Any]] = None, filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a natural language query.

        Args:
            question: Natural language question
            context: Optional context for the query
            filters: Optional filters (date range, source, etc.)

        Returns:
            Query response with answer and metadata
        """
        if not self._initialized:
            await self.initialize()

        logger.info(f"Processing query: {question}")

        # Build context string if provided
        context_str = ""
        if context:
            context_str = f"Context: {context}\n"

        # Apply filters if provided
        if filters:
            # Add date range to question if specified
            if filters.get("start_date") and filters.get("end_date"):
                question += f" between {filters['start_date']} and {filters['end_date']}"
            elif filters.get("start_date"):
                question += f" after {filters['start_date']}"
            elif filters.get("end_date"):
                question += f" before {filters['end_date']}"

            # Add source filter if specified
            if filters.get("sources"):
                sources_str = ", ".join(filters["sources"])
                question += f" from {sources_str}"

        # Execute query
        try:
            response = self.query_agent.run(context_str + question)

            return {
                "question": question,
                "answer": response.get("answer", ""),
                "sources": response.get("sources", []),
                "confidence": response.get("confidence", 0.0),
                "metadata": {"timestamp": datetime.utcnow().isoformat(), "filters": filters, "context": context},
            }
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {
                "question": question,
                "answer": f"I encountered an error processing your query: {str(e)}",
                "error": str(e),
                "metadata": {"timestamp": datetime.utcnow().isoformat(), "filters": filters, "context": context},
            }

    async def generate_summary(
        self, entity_id: str, entity_type: str = "person", time_range_days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate a summary for a specific entity.

        Args:
            entity_id: Unified entity ID
            entity_type: Type of entity (person/company)
            time_range_days: Number of days to include

        Returns:
            Summary with key insights
        """
        # Build appropriate question based on entity type
        if entity_type == "person":
            question = f"Summarize all interactions and activities for person with ID {entity_id} in the last {time_range_days} days"
        else:
            question = f"Summarize all interactions and activities for company with ID {entity_id} in the last {time_range_days} days"

        # Add context about what to include
        context = {
            "include": [
                "Key topics discussed",
                "Important decisions or outcomes",
                "Sentiment trends",
                "Frequency of interactions",
                "Main communication channels used",
            ],
            "entity_type": entity_type,
            "entity_id": entity_id,
        }

        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=time_range_days)

        filters = {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}

        return await self.query(question, context, filters)

    async def find_similar_interactions(
        self, reference_text: str, limit: int = 10, threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Find interactions similar to a reference text.

        Args:
            reference_text: Text to find similar interactions for
            limit: Maximum number of results
            threshold: Similarity threshold (0-1)

        Returns:
            List of similar interactions
        """
        question = f"Find interactions similar to: '{reference_text}'"

        context = {"similarity_threshold": threshold, "max_results": limit, "include_metadata": True}

        response = await self.query(question, context)

        # Extract interactions from response
        # This depends on how the Query Agent formats responses
        interactions = []
        if response.get("sources"):
            for source in response["sources"]:
                interactions.append(
                    {
                        "id": source.get("id"),
                        "text": source.get("text"),
                        "similarity": source.get("score", 0.0),
                        "type": source.get("type"),
                        "metadata": source.get("metadata", {}),
                    }
                )

        return interactions

    async def generate_timeline(
        self,
        entity_id: Optional[str] = None,
        entity_type: str = "person",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sources: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a timeline of interactions.

        Args:
            entity_id: Optional entity to filter by
            entity_type: Type of entity
            start_date: Start date for timeline
            end_date: End date for timeline
            sources: Optional list of sources to include

        Returns:
            Timeline with chronologically ordered events
        """
        # Build question
        if entity_id:
            question = f"Create a timeline of all interactions for {entity_type} with ID {entity_id}"
        else:
            question = "Create a timeline of all interactions"

        # Add source specification
        if sources:
            sources_str = ", ".join(sources)
            question += f" from {sources_str}"

        question += " ordered by date"

        context = {
            "format": "chronological",
            "include": ["date", "time", "source", "summary", "participants"],
            "entity_id": entity_id,
            "entity_type": entity_type,
        }

        filters = {}
        if start_date:
            filters["start_date"] = start_date
        if end_date:
            filters["end_date"] = end_date
        if sources:
            filters["sources"] = sources

        return await self.query(question, context, filters)

    async def analyze_sentiment(
        self, entity_id: Optional[str] = None, time_range_days: int = 30, group_by: str = "day"
    ) -> Dict[str, Any]:
        """
        Analyze sentiment trends over time.

        Args:
            entity_id: Optional entity to analyze
            time_range_days: Number of days to analyze
            group_by: Grouping period (day/week/month)

        Returns:
            Sentiment analysis results
        """
        if entity_id:
            question = f"Analyze sentiment trends for entity {entity_id} over the last {time_range_days} days grouped by {group_by}"
        else:
            question = f"Analyze overall sentiment trends over the last {time_range_days} days grouped by {group_by}"

        context = {
            "analysis_type": "sentiment",
            "metrics": ["positive", "negative", "neutral", "average_score"],
            "group_by": group_by,
            "include_examples": True,
        }

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=time_range_days)

        filters = {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}

        return await self.query(question, context, filters)

    async def identify_topics(
        self, time_range_days: int = 7, min_frequency: int = 3, sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Identify trending topics in recent interactions.

        Args:
            time_range_days: Number of days to analyze
            min_frequency: Minimum frequency for a topic
            sources: Optional sources to analyze

        Returns:
            Identified topics with frequency and examples
        """
        question = f"What are the most frequently discussed topics in the last {time_range_days} days?"

        if sources:
            sources_str = ", ".join(sources)
            question += f" in {sources_str}"

        context = {
            "analysis_type": "topic_extraction",
            "min_frequency": min_frequency,
            "include_examples": True,
            "include_trends": True,
        }

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=time_range_days)

        filters = {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}

        if sources:
            filters["sources"] = sources

        return await self.query(question, context, filters)

    async def generate_coaching_report(self, rep_name: str, period_days: int = 30) -> Dict[str, Any]:
        """
        Generate a coaching report for a sales rep.

        Args:
            rep_name: Name of the sales rep
            period_days: Period to analyze

        Returns:
            Coaching report with insights and recommendations
        """
        question = f"Generate a coaching report for sales rep {rep_name} covering the last {period_days} days"

        context = {
            "report_type": "coaching",
            "include_sections": [
                "Call summary statistics",
                "Key wins and successes",
                "Areas for improvement",
                "Customer sentiment analysis",
                "Talk time ratio",
                "Question asking patterns",
                "Objection handling examples",
                "Recommended focus areas",
            ],
            "rep_name": rep_name,
        }

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)

        filters = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "sources": ["gong"],  # Focus on call data for coaching
        }

        return await self.query(question, context, filters)
