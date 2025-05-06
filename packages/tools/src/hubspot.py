"""Tool for interacting with HubSpot CRM API for contact and deal management."""

import os
from typing import Dict, Any, Optional, List
from functools import wraps

from agno.tool import tool
from orchestra.tools.base import OrchestraTool

try:
    from hubspot import HubSpot
    from hubspot.crm.contacts import ApiException as ContactsApiException
    from hubspot.crm.deals import ApiException as DealsApiException
except ImportError:
    raise ImportError(
        "hubspot-api-client package is required. "
        "Install it with 'pip install hubspot-api-client'"
    )


def _get_hubspot_client() -> HubSpot:
    """Create and return an authenticated HubSpot client."""
    api_key = os.environ.get("HUBSPOT_API_KEY")
    if not api_key:
        raise ValueError("Missing HUBSPOT_API_KEY in environment variables.")
    
    return HubSpot(api_key=api_key)


@tool
def get_contact_by_email(email: str) -> Dict[str, Any]:
    """
    Retrieve a HubSpot contact by email address.
    
    Args:
        email: The email address of the contact
        
    Returns:
        Dictionary containing the contact details
    """
    client = _get_hubspot_client()
    
    try:
        # Search for the contact by email
        filter_dict = {"propertyName": "email", "operator": "EQ", "value": email}
        response = client.crm.contacts.search_api.do_search(
            {"filters": [filter_dict], "properties": ["*"]}
        )
        
        if response.results and len(response.results) > 0:
            contact = response.results[0].to_dict()
            # Formatting the response for better readability
            return {
                "id": contact.get("id", ""),
                "created_at": contact.get("created_at", ""),
                "updated_at": contact.get("updated_at", ""),
                "archived": contact.get("archived", False),
                "properties": contact.get("properties", {}),
                "associations": contact.get("associations", {})
            }
        else:
            return {"error": f"No contact found with email {email}"}
    
    except ContactsApiException as e:
        return {"error": f"HubSpot API error: {str(e)}"}


@tool
def get_deal_details(deal_id: str) -> Dict[str, Any]:
    """
    Retrieve details for a specific HubSpot deal.
    
    Args:
        deal_id: The HubSpot deal identifier
        
    Returns:
        Dictionary containing the deal details
    """
    client = _get_hubspot_client()
    
    try:
        # Get deal by ID with all properties
        deal = client.crm.deals.basic_api.get_by_id(
            deal_id=deal_id, 
            properties=["*"],
            archived=False
        )
        
        deal_dict = deal.to_dict()
        
        # Get associated contacts for the deal
        associated_contacts = client.crm.deals.associations_api.get_all(
            deal_id=deal_id,
            to_object_type="contacts"
        )
        
        # Get associated company for the deal
        associated_companies = client.crm.deals.associations_api.get_all(
            deal_id=deal_id,
            to_object_type="companies"
        )
        
        # Format the response
        return {
            "id": deal_dict.get("id", ""),
            "created_at": deal_dict.get("created_at", ""),
            "updated_at": deal_dict.get("updated_at", ""),
            "archived": deal_dict.get("archived", False),
            "properties": deal_dict.get("properties", {}),
            "associated_contacts": [r.to_dict() for r in associated_contacts.results] if associated_contacts.results else [],
            "associated_companies": [r.to_dict() for r in associated_companies.results] if associated_companies.results else [],
        }
    
    except DealsApiException as e:
        return {"error": f"HubSpot API error: {str(e)}"}


@tool
def update_deal_stage(deal_id: str, stage: str) -> Dict[str, Any]:
    """
    Update the stage of a HubSpot deal.
    
    Args:
        deal_id: The HubSpot deal identifier
        stage: The new stage to set for the deal
        
    Returns:
        Dictionary containing the updated deal details
    """
    client = _get_hubspot_client()
    
    try:
        # Get current deal to verify it exists
        current_deal = client.crm.deals.basic_api.get_by_id(
            deal_id=deal_id, 
            properties=["dealstage"],
            archived=False
        )
        
        # Prepare properties to update
        properties = {
            "dealstage": stage
        }
        
        # Update the deal
        client.crm.deals.basic_api.update(
            deal_id=deal_id, 
            simple_public_object_input={"properties": properties}
        )
        
        # Get the updated deal to return
        return get_deal_details(deal_id)
    
    except DealsApiException as e:
        return {"error": f"HubSpot API error: {str(e)}"}


@tool
def enrich_contact(contact_id: str, enrichment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich a HubSpot contact with additional data.
    
    Args:
        contact_id: The HubSpot contact identifier
        enrichment_data: Dictionary of properties to update or add
        
    Returns:
        Dictionary containing the enriched contact details
    """
    client = _get_hubspot_client()
    
    try:
        # Update the contact with enrichment data
        client.crm.contacts.basic_api.update(
            contact_id=contact_id, 
            simple_public_object_input={"properties": enrichment_data}
        )
        
        # Get the updated contact
        contact = client.crm.contacts.basic_api.get_by_id(
            contact_id=contact_id,
            properties=["*"],
            archived=False
        )
        
        contact_dict = contact.to_dict()
        return {
            "id": contact_dict.get("id", ""),
            "created_at": contact_dict.get("created_at", ""),
            "updated_at": contact_dict.get("updated_at", ""),
            "properties": contact_dict.get("properties", {}),
            "enriched_fields": list(enrichment_data.keys()),
        }
    
    except ContactsApiException as e:
        return {"error": f"HubSpot API error: {str(e)}"}


class HubSpotTool(OrchestraTool):
    """
    Tool for interacting with HubSpot CRM API for contact and deal management.
    Implements the OrchestraTool interface.
    """
    
    def __init__(self):
        """Initialize the HubSpotTool."""
        super().__init__(
            name="HubSpotTool",
            description="Manage HubSpot CRM contacts and deals",
        )
    
    def get_contact_by_email(self, email: str) -> Dict[str, Any]:
        """
        Retrieve a HubSpot contact by email address.
        
        Args:
            email: The email address of the contact
            
        Returns:
            Dictionary containing the contact details
        """
        return get_contact_by_email(email)
    
    def get_deal_details(self, deal_id: str) -> Dict[str, Any]:
        """
        Retrieve details for a specific HubSpot deal.
        
        Args:
            deal_id: The HubSpot deal identifier
            
        Returns:
            Dictionary containing the deal details
        """
        return get_deal_details(deal_id)
    
    def update_deal_stage(self, deal_id: str, stage: str) -> Dict[str, Any]:
        """
        Update the stage of a HubSpot deal.
        
        Args:
            deal_id: The HubSpot deal identifier
            stage: The new stage to set for the deal
            
        Returns:
            Dictionary containing the updated deal details
        """
        return update_deal_stage(deal_id, stage)
    
    def enrich_contact(self, contact_id: str, enrichment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a HubSpot contact with additional data.
        
        Args:
            contact_id: The HubSpot contact identifier
            enrichment_data: Dictionary of properties to update or add
            
        Returns:
            Dictionary containing the enriched contact details
        """
        return enrich_contact(contact_id, enrichment_data)
