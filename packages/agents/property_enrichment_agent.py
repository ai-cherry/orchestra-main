"""
Property Enrichment Agent

Handles property data ingestion, address normalization, deduplication, and initial web search.
Integrates with Firestore for data storage and Google Maps API for address normalization.

Author: AI Orchestrator Team
"""

import logging
import os
from typing import Dict, List, Optional

import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PropertyEnrichmentAgent")


class PropertyEnrichmentAgent:
    def __init__(self, firestore_collection: str, google_maps_api_key: str):
        """
        Args:
            firestore_collection: Name of the Firestore collection for properties.
            google_maps_api_key: API key for Google Maps Geocoding API.
        """
        self.db = firestore.Client()
        self.collection = firestore_collection
        self.maps_api_key = google_maps_api_key

    def ingest_properties(self, properties: List[Dict]) -> None:
        """
        Ingests a list of property records, normalizes addresses, deduplicates, and stores them in Firestore.

        Args:
            properties: List of property dicts with at least 'address' field.
        """
        for prop in properties:
            normalized = self.normalize_address(prop.get("address", ""))
            if not normalized:
                logger.warning(f"Could not normalize address: {prop.get('address')}")
                continue

            prop["normalized_address"] = normalized
            prop["status"] = "ingested"

            # Deduplication: check if property already exists by normalized address
            existing = (
                self.db.collection(self.collection)
                .where("normalized_address", "==", normalized)
                .get()
            )
            if existing:
                logger.info(f"Duplicate property found for address: {normalized}")
                continue

            # Store in Firestore
            self.db.collection(self.collection).add(prop)
            logger.info(f"Ingested property: {normalized}")

    def normalize_address(self, address: str) -> Optional[str]:
        """
        Uses Google Maps Geocoding API to normalize an address.

        Args:
            address: Raw address string.

        Returns:
            Normalized address string or None if normalization fails.
        """
        if not address:
            return None
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": address, "key": self.maps_api_key}
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "OK" and data["results"]:
                return data["results"][0]["formatted_address"]
            else:
                logger.warning(
                    f"Geocoding failed for address: {address} - {data.get('status')}"
                )
                return None
        except Exception as e:
            logger.error(f"Error normalizing address '{address}': {e}")
            return None

    def run_initial_web_search(self, property_record: Dict) -> Dict:
        """
        Placeholder for initial web search logic (e.g., SerpAPI integration).

        Args:
            property_record: Property dict.

        Returns:
            Updated property dict with web search results.
        """
        # TODO: Integrate SerpAPI or other web search here.
        property_record["web_search_status"] = "pending"
        return property_record


# Example usage (to be replaced with n8n or orchestrator triggers)
if __name__ == "__main__":
    GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    agent = PropertyEnrichmentAgent(
        firestore_collection="properties",
        google_maps_api_key=GOOGLE_MAPS_API_KEY,
    )
    # Example property list
    properties = [
        {"address": "1600 Amphitheatre Parkway, Mountain View, CA"},
        {"address": "1 Infinite Loop, Cupertino, CA"},
    ]
    agent.ingest_properties(properties)
