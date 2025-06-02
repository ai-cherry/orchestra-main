import logging
import requests
import json
import time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class ContactEnrichmentAgent:
    """
    Agent for enriching contact data using Apollo.io API.

    This agent retrieves additional information about contacts such as:
    - Email addresses
    - Phone numbers
    - Social media profiles
    - Job history
    - Education
    """

    def __init__(
        self,
        apollo_api_key: str,
        firestore_collection: str,
        claude_max_webhook: Optional[str] = None,
    ):
        """
        Initialize the Contact Enrichment Agent.

        Args:
            apollo_api_key: API key for Apollo.io.
            firestore_collection: Firestore collection for storing enriched data.
            claude_max_webhook: Webhook URL for Claude Max validation.
        """
        self.apollo_api_key = apollo_api_key
        self.claude_webhook = claude_max_webhook
        self.api_base_url = "https://api.apollo.io/v1"

    def enrich_contact(self, contact_data: Dict) -> Dict:
        """
        Enrich a contact with additional information from Apollo.io.

        Args:
            contact_data: Basic contact information including at least one of:
                         name, email, company, linkedin_url.

        Returns:
            Dict containing the original data plus enriched fields.
        """
        # Prepare search parameters
        search_params = {}

        if contact_data.get("email"):
            search_params["email"] = contact_data["email"]
        elif contact_data.get("linkedin_url"):
            search_params["linkedin_url"] = contact_data["linkedin_url"]
        elif contact_data.get("name") and contact_data.get("company_name"):
            search_params["name"] = contact_data["name"]
            search_params["organization_name"] = contact_data["company_name"]
        else:
            logger.error("Insufficient data for contact enrichment")
            return contact_data

        # Call Apollo API
        try:
            response = self._call_apollo_api("people/search", search_params)
            if not response or "people" not in response:
                return contact_data

            # Process and merge data
            if response["people"] and len(response["people"]) > 0:
                person = response["people"][0]  # Take best match
                enriched_data = self._process_apollo_person(person)

                # Merge with original data, keeping original values if present
                for key, value in enriched_data.items():
                    if key not in contact_data or not contact_data[key]:
                        contact_data[key] = value

                # Store enriched data
                self._store_enriched_contact(contact_data)

            return contact_data

        except Exception as e:
            logger.error(f"Error enriching contact: {str(e)}")
            return contact_data

    def _call_apollo_api(self, endpoint: str, params: Dict) -> Dict:
        """Call Apollo.io API with rate limiting and error handling."""
        url = f"{self.api_base_url}/{endpoint}"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.apollo_api_key}"}

        try:
            response = requests.post(url, headers=headers, json=params)

            if response.status_code == 429:  # Rate limited
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning(f"Rate limited by Apollo API. Retrying after {retry_after}s")
                time.sleep(retry_after)
                return self._call_apollo_api(endpoint, params)

            if response.status_code != 200:
                logger.error(f"Apollo API error: {response.status_code} - {response.text}")
                return {}

            return response.json()

        except Exception as e:
            logger.error(f"Error calling Apollo API: {str(e)}")
            return {}

    def _process_apollo_person(self, person: Dict) -> Dict:
        """Process and normalize Apollo.io person data."""
        result = {}

        # Basic info
        result["full_name"] = person.get("name", "")
        result["first_name"] = person.get("first_name", "")
        result["last_name"] = person.get("last_name", "")
        result["email"] = person.get("email", "")
        result["linkedin_url"] = person.get("linkedin_url", "")

        # Contact info
        if "phone_numbers" in person and person["phone_numbers"]:
            result["phone"] = person["phone_numbers"][0]

        # Employment info
        if "organization" in person and person["organization"]:
            result["company_name"] = person["organization"].get("name", "")
            result["company_website"] = person["organization"].get("website_url", "")
            result["company_linkedin"] = person["organization"].get("linkedin_url", "")

        result["title"] = person.get("title", "")
        result["seniority"] = person.get("seniority", "")

        # Location info
        if "city" in person and person["city"]:
            result["city"] = person["city"]
        if "state" in person and person["state"]:
            result["state"] = person["state"]
        if "country" in person and person["country"]:
            result["country"] = person["country"]

        return result

    def _store_enriched_contact(self, contact_data: Dict) -> None:
        """Store enriched contact data in the database."""
        try:
            logger.info(f"Contact data enriched: {contact_data.get('id', 'unknown')}")
            pass
        except Exception as e:
            logger.error(f"Error storing enriched contact: {str(e)}")

    def validate_with_claude(self, contact_data: Dict) -> Dict:
        """
        Validate and enhance contact data using Claude.

        This is a premium feature that uses Claude to:
        1. Validate the accuracy of Apollo data
        2. Add additional insights about the contact
        3. Suggest personalized outreach strategies
        """
        if not self.claude_webhook:
            return contact_data

        try:
            prompt = self._generate_claude_prompt(contact_data)
            response = requests.post(
                self.claude_webhook, headers={"Content-Type": "application/json"}, json={"prompt": prompt}
            )

            if response.status_code == 200:
                claude_data = response.json()
                if "insights" in claude_data:
                    contact_data["ai_insights"] = claude_data["insights"]
                if "outreach_suggestions" in claude_data:
                    contact_data["outreach_suggestions"] = claude_data["outreach_suggestions"]

            return contact_data

        except Exception as e:
            logger.error(f"Error validating with Claude: {str(e)}")
            return contact_data

    def _generate_claude_prompt(self, contact_data: Dict) -> str:
        """Generate a prompt for Claude to analyze contact data."""
        prompt = f"""
        Please analyze this contact information and provide:
        1. Validation of the data accuracy
        2. Additional insights about this person
        3. Personalized outreach strategy suggestions
        
        Contact Information:
        {json.dumps(contact_data, indent=2)}
        
        Format your response as JSON with these keys:
        - validation: object with accuracy scores for each field
        - insights: array of insights about the person
        - outreach_suggestions: array of personalized outreach strategies
        """
        return prompt
