"""Tool for interacting with Gong API to retrieve call transcripts and insights."""

import os
import requests
from typing import Dict, Any, Optional, List
from functools import wraps

from agno.tool import tool
from orchestra.tools.base import OrchestraTool


def _check_gong_auth():
    """Check if Gong API credentials are available."""
    if not os.environ.get("GONG_API_KEY"):
        raise ValueError("Missing GONG_API_KEY in environment variables.")
    if not os.environ.get("GONG_API_BASE_URL"):
        raise ValueError("Missing GONG_API_BASE_URL in environment variables.")


def _get_api_headers() -> Dict[str, str]:
    """Get Gong API headers with authentication."""
    _check_gong_auth()
    return {
        "Authorization": f"Bearer {os.environ['GONG_API_KEY']}",
        "Content-Type": "application/json",
    }


@tool
def get_call_transcript(call_id: str) -> Dict[str, Any]:
    """
    Retrieve transcript for a specific Gong call.
    
    Args:
        call_id: The Gong call identifier
        
    Returns:
        Dictionary containing the call transcript and metadata
    """
    _check_gong_auth()
    
    url = f"{os.environ['GONG_API_BASE_URL']}/calls/{call_id}/transcript"
    response = requests.get(url, headers=_get_api_headers())
    
    if response.status_code != 200:
        raise Exception(
            f"Failed to retrieve Gong call transcript. Status: {response.status_code}, "
            f"Response: {response.text}"
        )
    
    return response.json()


@tool
def get_call_insights(call_id: str) -> Dict[str, Any]:
    """
    Retrieve insights for a specific Gong call, including topics, trackers, and competitor mentions.
    
    Args:
        call_id: The Gong call identifier
        
    Returns:
        Dictionary containing call insights data
    """
    _check_gong_auth()
    
    url = f"{os.environ['GONG_API_BASE_URL']}/calls/{call_id}/insights"
    response = requests.get(url, headers=_get_api_headers())
    
    if response.status_code != 200:
        raise Exception(
            f"Failed to retrieve Gong call insights. Status: {response.status_code}, "
            f"Response: {response.text}"
        )
    
    data = response.json()
    
    # Process and structure the insights
    insights = {
        "topics": _extract_topics(data),
        "trackers": _extract_trackers(data),
        "competitor_mentions": _extract_competitor_mentions(data),
        "call_metadata": _extract_metadata(data),
    }
    
    return insights


def _extract_topics(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract and format topics from Gong response."""
    topics = []
    if "topics" in data:
        for topic in data["topics"]:
            topics.append({
                "name": topic.get("name", ""),
                "duration": topic.get("duration", 0),
                "start_time": topic.get("startTime", 0),
                "end_time": topic.get("endTime", 0),
            })
    return topics


def _extract_trackers(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract and format trackers from Gong response."""
    trackers = []
    if "trackers" in data:
        for tracker in data["trackers"]:
            trackers.append({
                "name": tracker.get("name", ""),
                "occurrences": tracker.get("occurrenceCount", 0),
                "timestamps": tracker.get("timestamps", []),
            })
    return trackers


def _extract_competitor_mentions(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract and format competitor mentions from Gong response."""
    mentions = []
    if "competitorMentions" in data:
        for mention in data["competitorMentions"]:
            mentions.append({
                "competitor": mention.get("competitor", ""),
                "count": mention.get("mentionCount", 0),
                "timestamps": mention.get("timestamps", []),
            })
    return mentions


def _extract_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and format call metadata."""
    return {
        "call_id": data.get("callId", ""),
        "duration": data.get("callDuration", 0),
        "date": data.get("callDate", ""),
        "title": data.get("title", ""),
        "participants": data.get("participants", []),
    }


class GongTool(OrchestraTool):
    """
    Tool for interacting with Gong API to retrieve call transcripts and insights.
    Implements the OrchestraTool interface.
    """
    
    def __init__(self):
        """Initialize the GongTool."""
        super().__init__(
            name="GongTool",
            description="Retrieve and analyze Gong call recordings, transcripts, and insights",
        )
    
    def get_call_transcript(self, call_id: str) -> Dict[str, Any]:
        """
        Retrieve transcript for a specific Gong call.
        
        Args:
            call_id: The Gong call identifier
            
        Returns:
            Dictionary containing the call transcript and metadata
        """
        return get_call_transcript(call_id)
    
    def get_call_insights(self, call_id: str) -> Dict[str, Any]:
        """
        Retrieve insights for a specific Gong call, including topics, trackers, and competitor mentions.
        
        Args:
            call_id: The Gong call identifier
            
        Returns:
            Dictionary containing call insights data
        """
        return get_call_insights(call_id)
