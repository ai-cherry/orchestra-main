"""
Contact Enrichment Agent

Finds and verifies executive contacts for companies, enriches CRM records.
Integrates with mongodb for data storage, Apollo.io and PhantomBuster for contact search,
and supports Browser Use for LinkedIn scraping and Claude Max for validation.

Author: AI Orchestrator Team
"""

import logging
import os
from typing import Dict, List, Optional

import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ContactEnrichmentAgent")


class ContactEnrichmentAgent:
    def __init__(
        self,
        firestore_collection: str,
        apollo_api_key: str,
        phantombuster_api_key: str,
        browser_use_endpoint: str,
        claude_max_webhook: str,
    ):
        """
        Args:
            firestore_collection: Name of the mongodb collection for companies/contacts.
            apollo_api_key: API key for Apollo.io.
            phantombuster_api_key: API key for PhantomBuster.
            browser_use_endpoint: HTTP endpoint for Browser Use automation.
            claude_max_webhook: Webhook URL for Claude Max validation.
        """
        self.db = mongodb.Client()
        self.collection = firestore_collection
        self.apollo_api_key = apollo_api_key
        self.phantombuster_api_key = phantombuster_api_key
        self.browser_use_endpoint = browser_use_endpoint
        self.claude_max_webhook = claude_max_webhook

    def enrich_company_contacts(self, company_doc_id: str) -> None:
        """
        Enriches executive contacts for a company and updates mongodb.

        Args:
            company_doc_id: mongodb document ID for the company.
        """
        doc_ref = self.db.collection(self.collection).document(company_doc_id)
        company = doc_ref.get().to_dict()
        if not company or "company_name" not in company:
            logger.warning(f"Company {company_doc_id} missing company_name.")
            return

        contacts = self.search_contacts_apollo(company["company_name"])
        if not contacts:
            contacts = self.search_contacts_phantombuster(company["company_name"])
        if not contacts:
            contacts = self.scrape_contacts_browser_use(
                company["company_name"], company.get("website")
            )

        validated_contacts = self.validate_contacts_claude(contacts)
        if validated_contacts:
            doc_ref.update(
                {
                    "contacts": validated_contacts,
                    "contact_enrichment_status": "enriched",
                }
            )
            logger.info(
                f"Enriched company {company_doc_id} with {len(validated_contacts)} contacts."
            )
        else:
            doc_ref.update({"contact_enrichment_status": "not_found"})
            logger.warning(f"No valid contacts found for company: {company_doc_id}")

    def search_contacts_apollo(self, company_name: str) -> Optional[List[Dict]]:
        """
        Uses Apollo.io API to search for executive contacts.

        Args:
            company_name: Name of the company.

        Returns:
            List of contact dicts or None.
        """
        url = "https://api.apollo.io/v1/mixed_people/search"
        headers = {"Authorization": f"Bearer {self.apollo_api_key}"}
        params = {
            "q_organization_names": company_name,
            "person_titles": "CEO,President,Owner,Principal,Executive",
        }
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            if data.get("people"):
                return data["people"]
            return None
        except Exception as e:
            logger.error(f"Apollo.io contact search failed for {company_name}: {e}")
            return None

    def search_contacts_phantombuster(self, company_name: str) -> Optional[List[Dict]]:
        """
        Uses PhantomBuster API to search for contacts (e.g., LinkedIn scraping).

        Args:
            company_name: Name of the company.

        Returns:
            List of contact dicts or None.
        """
        url = "https://api.phantombuster.com/api/v2/agent/launch"
        headers = {"X-Phantombuster-Key-1": self.phantombuster_api_key}
        payload = {"argument": {"company": company_name}}
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            # Extract contacts from PhantomBuster output (simplified)
            return data.get("contacts")
        except Exception as e:
            logger.error(f"PhantomBuster contact search failed for {company_name}: {e}")
            return None

    def scrape_contacts_browser_use(
        self, company_name: str, website: Optional[str]
    ) -> Optional[List[Dict]]:
        """
        Uses Browser Use automation to scrape executive contacts from LinkedIn or company website.

        Args:
            company_name: Name of the company.
            website: Company website URL.

        Returns:
            List of contact dicts or None.
        """
        payload = {"company_name": company_name, "website": website}
        try:
            response = requests.post(
                self.browser_use_endpoint, json=payload, timeout=60
            )
            response.raise_for_status()
            data = response.json()
            return data.get("contacts")
        except Exception as e:
            logger.error(f"Browser Use scraping failed for {company_name}: {e}")
            return None

    def validate_contacts_claude(
        self, contacts: Optional[List[Dict]]
    ) -> Optional[List[Dict]]:
        """
        Uses Claude Max to validate and deduplicate contacts.

        Args:
            contacts: List of contact dicts.

        Returns:
            List of validated contact dicts or None.
        """
        if not contacts:
            return None
        try:
            payload = {
                "prompt": (
                    "Given the following list of contacts, deduplicate and validate executive roles. "
                    "Return only valid, unique executive contacts as a JSON list.\n"
                    f"{contacts}"
                )
            }
            response = requests.post(self.claude_max_webhook, json=payload, timeout=20)
            response.raise_for_status()
            data = response.json()
            return data.get("validated_contacts")
        except Exception as e:
            logger.error(f"Claude Max contact validation failed: {e}")
            return None


# Example usage (to be replaced with orchestrator triggers)
if __name__ == "__main__":
    APOLLO_API_KEY = os.environ.get("APOLLO_API_KEY", "")
    PHANTOMBUSTER_API_KEY = os.environ.get("PHANTOMBUSTER_API_KEY", "")
    BROWSER_USE_ENDPOINT = os.environ.get("BROWSER_USE_ENDPOINT", "")
    CLAUDE_MAX_WEBHOOK = os.environ.get("CLAUDE_MAX_WEBHOOK", "")
    agent = ContactEnrichmentAgent(
        firestore_collection="companies",
        apollo_api_key=APOLLO_API_KEY,
        phantombuster_api_key=PHANTOMBUSTER_API_KEY,
        browser_use_endpoint=BROWSER_USE_ENDPOINT,
        claude_max_webhook=CLAUDE_MAX_WEBHOOK,
    )
    # Example: Enrich contacts for a company by mongodb doc ID
    agent.enrich_company_contacts("example_company_doc_id")
