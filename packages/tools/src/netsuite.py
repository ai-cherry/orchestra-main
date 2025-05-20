"""Tool for interacting with NetSuite API to retrieve and update inventory data."""

import os
import json
import time
import hmac
import base64
import hashlib
import requests
from typing import Dict, Any, Optional, List
from urllib.parse import quote_plus, urlencode

from agno.tool import tool
from orchestra.tools.base import OrchestraTool


def _check_netsuite_auth() -> None:
    """Check if NetSuite API credentials are available."""
    required_env_vars = [
        "NETSUITE_ACCOUNT_ID",
        "NETSUITE_CONSUMER_KEY",
        "NETSUITE_CONSUMER_SECRET",
        "NETSUITE_TOKEN_ID",
        "NETSUITE_TOKEN_SECRET",
    ]

    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    if missing_vars:
        raise ValueError(
            f"Missing required NetSuite credentials: {', '.join(missing_vars)}"
        )


def _generate_netsuite_signature(url: str, http_method: str) -> Dict[str, str]:
    """
    Generate the OAuth 1.0 signature for NetSuite API calls.

    Args:
        url: The API endpoint URL
        http_method: HTTP method (GET, POST, PUT, etc.)

    Returns:
        Dictionary containing the OAuth headers
    """
    _check_netsuite_auth()

    account_id = os.environ["NETSUITE_ACCOUNT_ID"]
    consumer_key = os.environ["NETSUITE_CONSUMER_KEY"]
    consumer_secret = os.environ["NETSUITE_CONSUMER_SECRET"]
    token_id = os.environ["NETSUITE_TOKEN_ID"]
    token_secret = os.environ["NETSUITE_TOKEN_SECRET"]

    # Generate timestamp and nonce
    oauth_timestamp = str(int(time.time()))
    oauth_nonce = base64.b64encode(os.urandom(32)).decode("utf-8")

    # Create parameter string
    params = {
        "oauth_consumer_key": consumer_key,
        "oauth_token": token_id,
        "oauth_signature_method": "HMAC-SHA256",
        "oauth_timestamp": oauth_timestamp,
        "oauth_nonce": oauth_nonce,
        "oauth_version": "1.0",
        "realm": account_id,
    }

    # Create signature base string
    param_string = "&".join(
        [
            f"{quote_plus(key)}={quote_plus(params[key])}"
            for key in sorted(params.keys())
            if key != "realm"
        ]
    )
    signature_base = (
        f"{http_method.upper()}&{quote_plus(url)}&{quote_plus(param_string)}"
    )

    # Create signing key and generate signature
    signing_key = f"{quote_plus(consumer_secret)}&{quote_plus(token_secret)}"
    signature = base64.b64encode(
        hmac.new(
            signing_key.encode("utf-8"), signature_base.encode("utf-8"), hashlib.sha256
        ).digest()
    ).decode("utf-8")

    # Create Authorization header
    oauth_header = "OAuth "
    oauth_header += f'realm="{account_id}", '
    oauth_header += f'oauth_consumer_key="{consumer_key}", '
    oauth_header += f'oauth_token="{token_id}", '
    oauth_header += 'oauth_signature_method="HMAC-SHA256", '
    oauth_header += f'oauth_timestamp="{oauth_timestamp}", '
    oauth_header += f'oauth_nonce="{oauth_nonce}", '
    oauth_header += 'oauth_version="1.0", '
    oauth_header += f'oauth_signature="{quote_plus(signature)}"'

    return {"Authorization": oauth_header}


def _get_netsuite_api_url(endpoint: str) -> str:
    """
    Construct the full NetSuite API URL.

    Args:
        endpoint: The API endpoint path

    Returns:
        The full URL for the API request
    """
    _check_netsuite_auth()
    account_id = os.environ["NETSUITE_ACCOUNT_ID"]
    # Base URL format for NetSuite REST API
    return f"https://{account_id}.suitetalk.api.netsuite.com/services/rest{endpoint}"


@tool
def get_inventory_levels(sku: str) -> Dict[str, Any]:
    """
    Retrieve inventory levels for a specific SKU.

    Args:
        sku: The Stock Keeping Unit identifier

    Returns:
        Dictionary containing inventory level details for the SKU
    """
    _check_netsuite_auth()

    # Construct the API URL for inventory item lookup
    url = _get_netsuite_api_url(f"/record/v1/inventoryItem?q=sku EQUALS '{sku}'")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        **_generate_netsuite_signature(url, "GET"),
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        inventory_data = response.json()
        if (
            not inventory_data
            or "items" not in inventory_data
            or not inventory_data["items"]
        ):
            return {"error": f"No inventory item found for SKU: {sku}"}

        item = inventory_data["items"][0]
        item_id = item.get("id")

        # Get detailed inventory information including quantities
        detail_url = _get_netsuite_api_url(f"/record/v1/inventoryItem/{item_id}")
        detail_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **_generate_netsuite_signature(detail_url, "GET"),
        }

        detail_response = requests.get(detail_url, headers=detail_headers)
        detail_response.raise_for_status()

        inventory_details = detail_response.json()

        # Format and return the inventory information
        return {
            "item_id": inventory_details.get("id"),
            "sku": sku,
            "name": inventory_details.get("displayName"),
            "description": inventory_details.get("description", ""),
            "inventory_levels": {
                "on_hand": inventory_details.get("quantityOnHand", 0),
                "available": inventory_details.get("quantityAvailable", 0),
                "committed": inventory_details.get("quantityCommitted", 0),
                "back_ordered": inventory_details.get("quantityBackOrdered", 0),
                "on_order": inventory_details.get("quantityOnOrder", 0),
            },
            "locations": inventory_details.get("locationQuantityOnHand", []),
            "last_updated": inventory_details.get("lastModifiedDate"),
        }
    except requests.RequestException as e:
        return {"error": f"NetSuite API error: {str(e)}"}


@tool
def update_inventory_record(
    item_id: str, update_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update inventory record fields in NetSuite.

    Args:
        item_id: The NetSuite internal ID of the inventory item
        update_data: Dictionary of fields to update

    Returns:
        Dictionary containing the updated inventory record data
    """
    _check_netsuite_auth()

    # Construct the API URL for inventory item update
    url = _get_netsuite_api_url(f"/record/v1/inventoryItem/{item_id}")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        **_generate_netsuite_signature(url, "PATCH"),
    }

    try:
        # Send PATCH request to update the inventory record
        response = requests.patch(url, headers=headers, data=json.dumps(update_data))
        response.raise_for_status()

        # Get the updated inventory item
        get_url = url
        get_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **_generate_netsuite_signature(get_url, "GET"),
        }

        get_response = requests.get(get_url, headers=get_headers)
        get_response.raise_for_status()

        updated_data = get_response.json()

        # Format and return the updated inventory information
        return {
            "item_id": updated_data.get("id"),
            "name": updated_data.get("displayName"),
            "updated_fields": list(update_data.keys()),
            "inventory_levels": {
                "on_hand": updated_data.get("quantityOnHand", 0),
                "available": updated_data.get("quantityAvailable", 0),
            },
            "last_updated": updated_data.get("lastModifiedDate"),
        }
    except requests.RequestException as e:
        return {"error": f"NetSuite API error: {str(e)}"}


class NetSuiteTool(OrchestraTool):
    """
    Tool for interacting with NetSuite API to retrieve and update inventory data.
    Implements the OrchestraTool interface.
    """

    def __init__(self):
        """Initialize the NetSuiteTool."""
        super().__init__(
            name="NetSuiteTool",
            description="Retrieve and update NetSuite inventory data",
        )

    def get_inventory_levels(self, sku: str) -> Dict[str, Any]:
        """
        Retrieve inventory levels for a specific SKU.

        Args:
            sku: The Stock Keeping Unit identifier

        Returns:
            Dictionary containing inventory level details for the SKU
        """
        return get_inventory_levels(sku)

    def update_inventory_record(
        self, item_id: str, update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update inventory record fields in NetSuite.

        Args:
            item_id: The NetSuite internal ID of the inventory item
            update_data: Dictionary of fields to update

        Returns:
            Dictionary containing the updated inventory record data
        """
        return update_inventory_record(item_id, update_data)
