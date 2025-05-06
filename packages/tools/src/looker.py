"""Tool for interacting with Looker API to run analytics queries and access looks."""

import os
import json
import time
import hmac
import base64
import hashlib
import requests
from typing import Dict, Any, Optional, List, Union

from agno.tool import tool
from orchestra.tools.base import OrchestraTool


def _check_looker_auth() -> None:
    """Check if Looker API credentials are available."""
    required_env_vars = [
        "LOOKER_API_URL",
        "LOOKER_CLIENT_ID", 
        "LOOKER_CLIENT_SECRET"
    ]
    
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    if missing_vars:
        raise ValueError(f"Missing required Looker credentials: {', '.join(missing_vars)}")


def _get_looker_auth_token() -> str:
    """Get Looker API authentication token."""
    _check_looker_auth()
    
    api_url = os.environ["LOOKER_API_URL"]
    client_id = os.environ["LOOKER_CLIENT_ID"]
    client_secret = os.environ["LOOKER_CLIENT_SECRET"]
    
    # Get authentication token
    auth_url = f"{api_url}/login"
    auth_data = {
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    try:
        response = requests.post(auth_url, json=auth_data)
        response.raise_for_status()
        token_data = response.json()
        
        return token_data.get("access_token")
    except requests.RequestException as e:
        raise ValueError(f"Failed to authenticate with Looker API: {str(e)}")


def _get_looker_headers() -> Dict[str, str]:
    """Get headers for Looker API requests with authentication."""
    token = _get_looker_auth_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


@tool
def run_look(look_id: str, result_format: str = "json") -> Dict[str, Any]:
    """
    Run a saved Look and retrieve the results.
    
    Args:
        look_id: The Looker Look identifier
        result_format: Format for results (json, csv, xlsx, html, etc.)
        
    Returns:
        Dictionary containing the Look results
    """
    _check_looker_auth()
    
    api_url = os.environ["LOOKER_API_URL"]
    url = f"{api_url}/looks/{look_id}/run/{result_format}"
    headers = _get_looker_headers()
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # For JSON responses, parse the data
        if result_format.lower() == "json":
            data = response.json()
            return {
                "look_id": look_id,
                "data": data
            }
        # For other formats, return metadata and raw content
        else:
            return {
                "look_id": look_id,
                "format": result_format,
                "content_type": response.headers.get("Content-Type"),
                "content_length": len(response.content),
                "raw_data": base64.b64encode(response.content).decode("utf-8")
            }
    
    except requests.RequestException as e:
        return {"error": f"Looker API error: {str(e)}"}


@tool
def run_query(query_body: Dict[str, Any], result_format: str = "json") -> Dict[str, Any]:
    """
    Run a Looker query and retrieve the results.
    
    Args:
        query_body: The Looker query specification
        result_format: Format for results (json, csv, xlsx, html, etc.)
        
    Returns:
        Dictionary containing the query results
    """
    _check_looker_auth()
    
    api_url = os.environ["LOOKER_API_URL"]
    url = f"{api_url}/queries/run/{result_format}"
    headers = _get_looker_headers()
    
    try:
        response = requests.post(url, headers=headers, json=query_body)
        response.raise_for_status()
        
        # For JSON responses, parse the data
        if result_format.lower() == "json":
            data = response.json()
            return {
                "query": query_body,
                "data": data
            }
        # For other formats, return metadata and raw content
        else:
            return {
                "query": query_body,
                "format": result_format,
                "content_type": response.headers.get("Content-Type"),
                "content_length": len(response.content),
                "raw_data": base64.b64encode(response.content).decode("utf-8")
            }
    
    except requests.RequestException as e:
        return {"error": f"Looker API error: {str(e)}"}


@tool
def get_look_info(look_id: str) -> Dict[str, Any]:
    """
    Get information about a saved Look.
    
    Args:
        look_id: The Looker Look identifier
        
    Returns:
        Dictionary containing Look metadata
    """
    _check_looker_auth()
    
    api_url = os.environ["LOOKER_API_URL"]
    url = f"{api_url}/looks/{look_id}"
    headers = _get_looker_headers()
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        look_data = response.json()
        
        # Extract relevant fields
        return {
            "id": look_data.get("id"),
            "title": look_data.get("title"),
            "description": look_data.get("description"),
            "folder": look_data.get("folder", {}),
            "model": look_data.get("model", {}).get("name"),
            "view": look_data.get("query", {}).get("view"),
            "fields": look_data.get("query", {}).get("fields", []),
            "filters": look_data.get("query", {}).get("filters", {}),
            "pivots": look_data.get("query", {}).get("pivots", []),
            "sorts": look_data.get("query", {}).get("sorts", []),
            "last_updated_at": look_data.get("updated_at")
        }
    
    except requests.RequestException as e:
        return {"error": f"Looker API error: {str(e)}"}


@tool
def list_dashboards(folder_id: Optional[str] = None) -> Dict[str, Any]:
    """
    List available dashboards, optionally filtering by folder.
    
    Args:
        folder_id: Optional folder ID to filter by
        
    Returns:
        Dictionary containing dashboard information
    """
    _check_looker_auth()
    
    api_url = os.environ["LOOKER_API_URL"]
    url = f"{api_url}/dashboards"
    
    if folder_id:
        url += f"?folder_id={folder_id}"
        
    headers = _get_looker_headers()
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        dashboards = response.json()
        
        # Format the response
        formatted_dashboards = []
        for dashboard in dashboards:
            formatted_dashboards.append({
                "id": dashboard.get("id"),
                "title": dashboard.get("title"),
                "description": dashboard.get("description"),
                "folder": dashboard.get("folder", {}),
                "created_at": dashboard.get("created_at"),
                "updated_at": dashboard.get("updated_at"),
                "looks_count": len(dashboard.get("dashboard_elements", []))
            })
        
        return {
            "dashboards": formatted_dashboards,
            "count": len(formatted_dashboards)
        }
    
    except requests.RequestException as e:
        return {"error": f"Looker API error: {str(e)}"}


class LookerTool(OrchestraTool):
    """
    Tool for interacting with Looker API to run analytics queries and access looks.
    Implements the OrchestraTool interface.
    """
    
    def __init__(self):
        """Initialize the LookerTool."""
        super().__init__(
            name="LookerTool",
            description="Run analytics queries and access looks in Looker",
        )
    
    def run_look(self, look_id: str, result_format: str = "json") -> Dict[str, Any]:
        """
        Run a saved Look and retrieve the results.
        
        Args:
            look_id: The Looker Look identifier
            result_format: Format for results (json, csv, xlsx, html, etc.)
            
        Returns:
            Dictionary containing the Look results
        """
        return run_look(look_id, result_format)
    
    def run_query(self, query_body: Dict[str, Any], result_format: str = "json") -> Dict[str, Any]:
        """
        Run a Looker query and retrieve the results.
        
        Args:
            query_body: The Looker query specification
            result_format: Format for results (json, csv, xlsx, html, etc.)
            
        Returns:
            Dictionary containing the query results
        """
        return run_query(query_body, result_format)
    
    def get_look_info(self, look_id: str) -> Dict[str, Any]:
        """
        Get information about a saved Look.
        
        Args:
            look_id: The Looker Look identifier
            
        Returns:
            Dictionary containing Look metadata
        """
        return get_look_info(look_id)
    
    def list_dashboards(self, folder_id: Optional[str] = None) -> Dict[str, Any]:
        """
        List available dashboards, optionally filtering by folder.
        
        Args:
            folder_id: Optional folder ID to filter by
            
        Returns:
            Dictionary containing dashboard information
        """
        return list_dashboards(folder_id)
