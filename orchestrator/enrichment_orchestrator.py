"""
Enrichment Orchestrator

Coordinates Property, Company, and Contact Enrichment Agents.
Tracks status, handles retries/errors, and exposes controls for workflow automation and admin interface.

Author: AI Orchestrator Team
"""

import logging
from typing import List, Optional

from packages.agents.company_enrichment_agent import CompanyEnrichmentAgent
from packages.agents.contact_enrichment_agent import ContactEnrichmentAgent
from packages.agents.property_enrichment_agent import PropertyEnrichmentAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EnrichmentOrchestrator")


class EnrichmentOrchestrator:
    def __init__(
        self,
        property_agent: PropertyEnrichmentAgent,
        company_agent: CompanyEnrichmentAgent,
        contact_agent: ContactEnrichmentAgent,
    ):
        self.property_agent = property_agent
        self.company_agent = company_agent
        self.contact_agent = contact_agent

    def run_full_enrichment(self, property_records: List[dict]) -> None:
        """
        Runs the full enrichment pipeline for a list of property records.

        Args:
            property_records: List of property dicts to ingest and enrich.
        """
        logger.info("Starting property ingestion and normalization...")
        self.property_agent.ingest_properties(property_records)

        # Fetch all ingested properties (could be optimized for batch processing)
        # For demo, assume property_records now have Firestore doc IDs
        for prop in property_records:
            doc_id = prop.get("doc_id")
            if not doc_id:
                logger.warning(f"Property missing doc_id: {prop}")
                continue

            logger.info(f"Enriching company for property {doc_id}...")
            self.company_agent.enrich_property(doc_id)

            logger.info(f"Enriching contacts for property/company {doc_id}...")
            self.contact_agent.enrich_company_contacts(doc_id)

    def run_enrichment_for_property(self, property_doc_id: str) -> None:
        """
        Runs company and contact enrichment for a single property by Firestore doc ID.

        Args:
            property_doc_id: Firestore document ID for the property.
        """
        logger.info(f"Enriching company for property {property_doc_id}...")
        self.company_agent.enrich_property(property_doc_id)

        logger.info(f"Enriching contacts for property/company {property_doc_id}...")
        self.contact_agent.enrich_company_contacts(property_doc_id)

    # Additional methods for status tracking, retries, error handling, and admin interface integration can be added here.


# Example usage (to be replaced with n8n/Pipedream or admin interface triggers)
if __name__ == "__main__":
    import os

    # Instantiate agents with environment variables for credentials/config
    property_agent = PropertyEnrichmentAgent(
        firestore_collection="properties",
        google_maps_api_key=os.environ.get("GOOGLE_MAPS_API_KEY", ""),
    )
    company_agent = CompanyEnrichmentAgent(
        firestore_collection="properties",
        serpapi_key=os.environ.get("SERPAPI_KEY", ""),
        claude_max_webhook=os.environ.get("CLAUDE_MAX_WEBHOOK", ""),
    )
    contact_agent = ContactEnrichmentAgent(
        firestore_collection="companies",
        apollo_api_key=os.environ.get("APOLLO_API_KEY", ""),
        phantombuster_api_key=os.environ.get("PHANTOMBUSTER_API_KEY", ""),
        browser_use_endpoint=os.environ.get("BROWSER_USE_ENDPOINT", ""),
        claude_max_webhook=os.environ.get("CLAUDE_MAX_WEBHOOK", ""),
    )

    orchestrator = EnrichmentOrchestrator(property_agent, company_agent, contact_agent)

    # Example: Run enrichment for a batch of properties
    properties = [
        {
            "address": "1600 Amphitheatre Parkway, Mountain View, CA",
            "doc_id": "property_doc_id_1",
        },
        {"address": "1 Infinite Loop, Cupertino, CA", "doc_id": "property_doc_id_2"},
    ]
    orchestrator.run_full_enrichment(properties)
