"""
Company Enrichment Agent

Matches properties to management/owner companies, enriches company profiles.
Integrates with mongodb for data storage, SerpAPI for web search, and Claude Max for reasoning.

Author: AI Orchestrator Team
"""

import logging
import os
from typing import Dict, Optional

import requests
from google.cloud import firestore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CompanyEnrichmentAgent")


class CompanyEnrichmentAgent:
    def __init__(self, firestore_collection: str, serpapi_key: str, claude_max_webhook: str):
        """
        Args:
            firestore_collection: Name of the mongodb collection for properties/companies.
            serpapi_key: API key for SerpAPI.
            claude_max_webhook: Webhook URL for Claude Max reasoning.
        """
        self.db = firestore.Client()
        self.collection = firestore_collection
        self.serpapi_key = serpapi_key
        self.claude_max_webhook = claude_max_webhook

    def enrich_property(self, property_doc_id: str) -> None:
        """
        Enriches a property by searching for its management/owner company and updating mongodb.

        Args:
            property_doc_id: mongodb document ID for the property.
        """
        doc_ref = self.db.collection(self.collection).document(property_doc_id)
        prop = doc_ref.get().to_dict()
        if not prop or "normalized_address" not in prop:
            logger.warning(f"Property {property_doc_id} missing normalized address.")
            return

        search_result = self.search_company(prop["normalized_address"])
        if not search_result:
            logger.warning(f"No company found for property: {property_doc_id}")
            doc_ref.update({"company_enrichment_status": "not_found"})
            return

        # Use Claude Max for reasoning if ambiguous
        company_name = self.resolve_company_with_claude(search_result)
        if not company_name:
            logger.warning(f"Claude Max could not resolve company for property: {property_doc_id}")
            doc_ref.update({"company_enrichment_status": "ambiguous"})
            return

        # Update mongodb with company info
        doc_ref.update({"company_name": company_name, "company_enrichment_status": "enriched"})
        logger.info(f"Enriched property {property_doc_id} with company: {company_name}")

    def search_company(self, address: str) -> Optional[Dict]:
        """
        Uses SerpAPI to search for property management/owner company.

        Args:
            address: Normalized property address.

        Returns:
            Search result dict or None.
        """
        url = "https://serpapi.com/search"
        params = {
            "engine": "google_maps",
            "q": address,
            "type": "search",
            "api_key": self.serpapi_key,
        }
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            # Extract company info from results (simplified)
            if "local_results" in data and data["local_results"]:
                return data["local_results"][0]
            return None
        except Exception as e:
            logger.error(f"Error searching company for address '{address}': {e}")
            return None

    def resolve_company_with_claude(self, search_result: Dict) -> Optional[str]:
        """
        Uses Claude Max (via webhook) to reason over search results and extract company name.

        Args:
            search_result: Dict from SerpAPI.

        Returns:
            Company name string or None.
        """
        try:
            payload = {
                "prompt": (
                    "Given the following Google Maps search result, extract the most likely property management or owner company name:\n"
                    f"{search_result}"
                )
            }
            response = requests.post(self.claude_max_webhook, json=payload, timeout=20)
            response.raise_for_status()
            data = response.json()
            return data.get("company_name")
        except Exception as e:
            logger.error(f"Error resolving company with Claude Max: {e}")
            return None


# Example usage (to be replaced with orchestrator triggers)
if __name__ == "__main__":
    SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")
    CLAUDE_MAX_WEBHOOK = os.environ.get("CLAUDE_MAX_WEBHOOK", "")
    agent = CompanyEnrichmentAgent(
        firestore_collection="properties",
        serpapi_key=SERPAPI_KEY,
        claude_max_webhook=CLAUDE_MAX_WEBHOOK,
    )
    # Example: Enrich a property by mongodb doc ID
    agent.enrich_property("example_property_doc_id")
