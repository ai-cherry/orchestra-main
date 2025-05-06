"""Tool for interacting with Salesforce CRM to query and update data."""

import os
from typing import Dict, Any, Optional, List, Union

from agno.tool import tool
from orchestra.tools.base import OrchestraTool

try:
    from simple_salesforce import Salesforce, SalesforceError
except ImportError:
    raise ImportError(
        "simple-salesforce package is required. "
        "Install it with 'pip install simple-salesforce'"
    )


def _get_salesforce_client() -> Salesforce:
    """Create and return an authenticated Salesforce client."""
    # Check for required credentials
    required_env_vars = [
        "SALESFORCE_USERNAME",
        "SALESFORCE_PASSWORD",
        "SALESFORCE_SECURITY_TOKEN",
        "SALESFORCE_DOMAIN"
    ]
    
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    if missing_vars:
        raise ValueError(f"Missing required Salesforce credentials: {', '.join(missing_vars)}")
    
    # Create client with credentials
    return Salesforce(
        username=os.environ["SALESFORCE_USERNAME"],
        password=os.environ["SALESFORCE_PASSWORD"],
        security_token=os.environ["SALESFORCE_SECURITY_TOKEN"],
        domain=os.environ["SALESFORCE_DOMAIN"]
    )


@tool
def query_salesforce(soql_query: str) -> Dict[str, Any]:
    """
    Execute a SOQL query against Salesforce.
    
    Args:
        soql_query: The SOQL query string to execute
        
    Returns:
        Dictionary containing query results
    """
    client = _get_salesforce_client()
    
    try:
        # Execute the query
        result = client.query(soql_query)
        
        # Format the response
        formatted_result = {
            "total_size": result.get("totalSize", 0),
            "done": result.get("done", False),
            "records": [],
        }
        
        # Process records
        if "records" in result:
            formatted_result["records"] = [
                {k: v for k, v in record.items() if k != "attributes"} 
                for record in result["records"]
            ]
        
        return formatted_result
    
    except SalesforceError as e:
        return {"error": f"Salesforce API error: {str(e)}"}


@tool
def get_salesforce_record(
    object_name: str, 
    record_id: str
) -> Dict[str, Any]:
    """
    Retrieve a specific record from Salesforce by ID.
    
    Args:
        object_name: The Salesforce object name (e.g., Account, Opportunity)
        record_id: The record ID to retrieve
        
    Returns:
        Dictionary containing the record data
    """
    client = _get_salesforce_client()
    
    try:
        # Get the object
        sf_object = getattr(client, object_name)
        
        # Retrieve the record
        record = sf_object.get(record_id)
        
        # Format and return the record data
        return {k: v for k, v in record.items() if k != "attributes"}
    
    except (SalesforceError, AttributeError) as e:
        return {"error": f"Salesforce API error: {str(e)}"}


@tool
def update_salesforce_record(
    object_name: str, 
    record_id: str,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update a specific record in Salesforce.
    
    Args:
        object_name: The Salesforce object name (e.g., Account, Opportunity)
        record_id: The record ID to update
        data: Dictionary of fields to update and their new values
        
    Returns:
        Dictionary containing the update status
    """
    client = _get_salesforce_client()
    
    try:
        # Get the object
        sf_object = getattr(client, object_name)
        
        # Update the record
        sf_object.update(record_id, data)
        
        # Retrieve the updated record to confirm changes
        return {
            "success": True,
            "record_id": record_id,
            "object": object_name,
            "updated_fields": list(data.keys()),
            "updated_record": get_salesforce_record(object_name, record_id)
        }
    
    except (SalesforceError, AttributeError) as e:
        return {
            "success": False,
            "error": f"Salesforce API error: {str(e)}"
        }


@tool
def create_salesforce_record(
    object_name: str,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a new record in Salesforce.
    
    Args:
        object_name: The Salesforce object name (e.g., Account, Opportunity)
        data: Dictionary of field values for the new record
        
    Returns:
        Dictionary containing the creation status and new record ID
    """
    client = _get_salesforce_client()
    
    try:
        # Get the object
        sf_object = getattr(client, object_name)
        
        # Create the record
        result = sf_object.create(data)
        
        if result.get("success", False):
            record_id = result.get("id")
            return {
                "success": True,
                "record_id": record_id,
                "object": object_name,
                "created_record": get_salesforce_record(object_name, record_id)
            }
        else:
            return {
                "success": False,
                "errors": result.get("errors", [])
            }
    
    except (SalesforceError, AttributeError) as e:
        return {
            "success": False,
            "error": f"Salesforce API error: {str(e)}"
        }


@tool
def search_salesforce(search_query: str) -> Dict[str, Any]:
    """
    Execute a SOSL search query against Salesforce.
    
    Args:
        search_query: The SOSL search query to execute
        
    Returns:
        Dictionary containing search results
    """
    client = _get_salesforce_client()
    
    try:
        # Execute the search
        result = client.search(search_query)
        
        # Process and return search results
        return {
            "search_records": result.get("searchRecords", []),
            "metadata": {
                "query": search_query
            }
        }
    
    except SalesforceError as e:
        return {"error": f"Salesforce API error: {str(e)}"}


class SalesforceTool(OrchestraTool):
    """
    Tool for interacting with Salesforce CRM to query and update data.
    Implements the OrchestraTool interface.
    """
    
    def __init__(self):
        """Initialize the SalesforceTool."""
        super().__init__(
            name="SalesforceTool",
            description="Query and update data in Salesforce CRM",
        )
    
    def query(self, soql_query: str) -> Dict[str, Any]:
        """
        Execute a SOQL query against Salesforce.
        
        Args:
            soql_query: The SOQL query string to execute
            
        Returns:
            Dictionary containing query results
        """
        return query_salesforce(soql_query)
    
    def get_record(self, object_name: str, record_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific record from Salesforce by ID.
        
        Args:
            object_name: The Salesforce object name (e.g., Account, Opportunity)
            record_id: The record ID to retrieve
            
        Returns:
            Dictionary containing the record data
        """
        return get_salesforce_record(object_name, record_id)
    
    def update_record(self, object_name: str, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a specific record in Salesforce.
        
        Args:
            object_name: The Salesforce object name (e.g., Account, Opportunity)
            record_id: The record ID to update
            data: Dictionary of fields to update and their new values
            
        Returns:
            Dictionary containing the update status
        """
        return update_salesforce_record(object_name, record_id, data)
    
    def create_record(self, object_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new record in Salesforce.
        
        Args:
            object_name: The Salesforce object name (e.g., Account, Opportunity)
            data: Dictionary of field values for the new record
            
        Returns:
            Dictionary containing the creation status and new record ID
        """
        return create_salesforce_record(object_name, data)
    
    def search(self, search_query: str) -> Dict[str, Any]:
        """
        Execute a SOSL search query against Salesforce.
        
        Args:
            search_query: The SOSL search query to execute
            
        Returns:
            Dictionary containing search results
        """
        return search_salesforce(search_query)
