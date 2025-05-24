#!/usr/bin/env python3
"""
Data Source Integrations for Orchestra AI MVP
Comprehensive integrations for Gong.io, Salesforce, HubSpot, Slack, and Looker.
"""

import asyncio
import base64
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp

from enhanced_vector_memory_system import EnhancedVectorMemorySystem

logger = logging.getLogger(__name__)


@dataclass
class DataSourceConfig:
    """Configuration for data source connections."""

    name: str
    api_key: str
    base_url: str
    rate_limit: float = 1.0  # requests per second
    additional_headers: Dict[str, str] = None


class BaseDataSourceIntegration:
    """Base class for all data source integrations."""

    def __init__(self, config: DataSourceConfig, memory_system: EnhancedVectorMemorySystem, user_id: str):
        self.config = config
        self.memory_system = memory_system
        self.user_id = user_id
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_request_time = 0.0

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if not self._session or self._session.closed:
            headers = {"User-Agent": "Orchestra-AI/1.0"}
            if self.config.additional_headers:
                headers.update(self.config.additional_headers)

            self._session = aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=30))
        return self._session

    async def _rate_limit(self) -> None:
        """Apply rate limiting."""
        if self.config.rate_limit > 0:
            elapsed = asyncio.get_event_loop().time() - self._last_request_time
            sleep_time = (1.0 / self.config.rate_limit) - elapsed
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        self._last_request_time = asyncio.get_event_loop().time()

    async def close(self) -> None:
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def sync_data(self, since: Optional[datetime] = None) -> int:
        """Sync data from source. To be implemented by subclasses."""
        raise NotImplementedError


class GongIntegration(BaseDataSourceIntegration):
    """Integration for Gong.io call intelligence platform."""

    async def sync_data(self, since: Optional[datetime] = None) -> int:
        """Sync calls, meetings, and insights from Gong."""
        session = await self._get_session()
        synced_count = 0

        # Default to last 30 days if no since date
        if not since:
            since = datetime.utcnow() - timedelta(days=30)

        # Sync call recordings and transcripts
        synced_count += await self._sync_calls(session, since)

        # Sync meeting insights and analytics
        synced_count += await self._sync_insights(session, since)

        # Sync deal intelligence
        synced_count += await self._sync_deals(session, since)

        return synced_count

    async def _sync_calls(self, session: aiohttp.ClientSession, since: datetime) -> int:
        """Sync call recordings and transcripts."""
        await self._rate_limit()

        # Gong API v2 call list endpoint
        url = f"{self.config.base_url}/v2/calls"

        headers = {
            "Authorization": f"Basic {base64.b64encode(f'{self.config.api_key}:'.encode()).decode()}",
            "Content-Type": "application/json",
        }

        params = {"fromDateTime": since.isoformat(), "limit": 100}

        count = 0
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()

                for call in data.get("calls", []):
                    # Process call transcript
                    if call.get("transcript"):
                        transcript_content = " ".join(
                            [
                                f"{speaker['speakerId']}: {sentence['text']}"
                                for speaker in call.get("speakers", [])
                                for sentence in speaker.get("sentences", [])
                            ]
                        )

                        await self.memory_system.add_memory(
                            user_id=self.user_id,
                            content=transcript_content,
                            source="gong",
                            source_metadata={
                                "type": "call_transcript",
                                "call_id": call.get("id"),
                                "title": call.get("title"),
                                "duration": call.get("duration"),
                                "participants": [p.get("emailAddress") for p in call.get("participants", [])],
                                "date": call.get("actualStart"),
                                "deal_id": call.get("dealId"),
                            },
                            context_tags=["sales_call", "gong", "transcript"],
                        )
                        count += 1

                    # Process call insights
                    if call.get("insights"):
                        insights_content = json.dumps(call["insights"], indent=2)

                        await self.memory_system.add_memory(
                            user_id=self.user_id,
                            content=f"Call Insights: {insights_content}",
                            source="gong",
                            source_metadata={
                                "type": "call_insights",
                                "call_id": call.get("id"),
                                "insights": call["insights"],
                            },
                            context_tags=["sales_insights", "gong", "analytics"],
                        )
                        count += 1

        return count

    async def _sync_insights(self, session: aiohttp.ClientSession, since: datetime) -> int:
        """Sync meeting insights and analytics."""
        # Implementation for Gong insights API
        return 0

    async def _sync_deals(self, session: aiohttp.ClientSession, since: datetime) -> int:
        """Sync deal intelligence."""
        # Implementation for Gong deals API
        return 0


class SalesforceIntegration(BaseDataSourceIntegration):
    """Integration for Salesforce CRM."""

    def __init__(self, config: DataSourceConfig, memory_system: EnhancedVectorMemorySystem, user_id: str):
        super().__init__(config, memory_system, user_id)
        self._access_token: Optional[str] = None
        self._instance_url: Optional[str] = None

    async def _authenticate(self) -> None:
        """Authenticate with Salesforce using OAuth."""
        session = await self._get_session()

        # OAuth endpoint
        auth_url = f"{self.config.base_url}/services/oauth2/token"

        data = {
            "grant_type": "client_credentials",
            "client_id": self.config.api_key,
            "client_secret": self.config.additional_headers.get("client_secret"),
        }

        async with session.post(auth_url, data=data) as response:
            if response.status == 200:
                auth_data = await response.json()
                self._access_token = auth_data["access_token"]
                self._instance_url = auth_data["instance_url"]

    async def sync_data(self, since: Optional[datetime] = None) -> int:
        """Sync accounts, contacts, opportunities, and activities from Salesforce."""
        await self._authenticate()

        if not self._access_token:
            logger.error("Failed to authenticate with Salesforce")
            return 0

        session = await self._get_session()
        synced_count = 0

        if not since:
            since = datetime.utcnow() - timedelta(days=30)

        # Sync different Salesforce objects
        synced_count += await self._sync_accounts(session, since)
        synced_count += await self._sync_opportunities(session, since)
        synced_count += await self._sync_contacts(session, since)
        synced_count += await self._sync_activities(session, since)

        return synced_count

    async def _sync_accounts(self, session: aiohttp.ClientSession, since: datetime) -> int:
        """Sync Salesforce accounts."""
        await self._rate_limit()

        # SOQL query for accounts
        soql = f"""
        SELECT Id, Name, Type, Industry, Description, Website, Phone,
               BillingAddress, LastModifiedDate, Owner.Name
        FROM Account
        WHERE LastModifiedDate >= {since.isoformat()}
        LIMIT 200
        """

        headers = {"Authorization": f"Bearer {self._access_token}"}
        url = f"{self._instance_url}/services/data/v57.0/query"

        count = 0
        async with session.get(url, headers=headers, params={"q": soql}) as response:
            if response.status == 200:
                data = await response.json()

                for record in data.get("records", []):
                    content = f"""
                    Account: {record.get('Name')}
                    Type: {record.get('Type')}
                    Industry: {record.get('Industry')}
                    Description: {record.get('Description')}
                    Website: {record.get('Website')}
                    Phone: {record.get('Phone')}
                    Owner: {record.get('Owner', {}).get('Name')}
                    """

                    await self.memory_system.add_memory(
                        user_id=self.user_id,
                        content=content.strip(),
                        source="salesforce",
                        source_metadata={
                            "type": "account",
                            "account_id": record.get("Id"),
                            "industry": record.get("Industry"),
                            "account_type": record.get("Type"),
                            "last_modified": record.get("LastModifiedDate"),
                        },
                        context_tags=["crm", "salesforce", "account"],
                    )
                    count += 1

        return count

    async def _sync_opportunities(self, session: aiohttp.ClientSession, since: datetime) -> int:
        """Sync Salesforce opportunities."""
        await self._rate_limit()

        soql = f"""
        SELECT Id, Name, StageName, Amount, CloseDate, Probability,
               Description, Account.Name, Owner.Name, LastModifiedDate
        FROM Opportunity
        WHERE LastModifiedDate >= {since.isoformat()}
        LIMIT 200
        """

        headers = {"Authorization": f"Bearer {self._access_token}"}
        url = f"{self._instance_url}/services/data/v57.0/query"

        count = 0
        async with session.get(url, headers=headers, params={"q": soql}) as response:
            if response.status == 200:
                data = await response.json()

                for record in data.get("records", []):
                    content = f"""
                    Opportunity: {record.get('Name')}
                    Stage: {record.get('StageName')}
                    Amount: ${record.get('Amount', 0):,.2f}
                    Close Date: {record.get('CloseDate')}
                    Probability: {record.get('Probability')}%
                    Account: {record.get('Account', {}).get('Name')}
                    Owner: {record.get('Owner', {}).get('Name')}
                    Description: {record.get('Description')}
                    """

                    await self.memory_system.add_memory(
                        user_id=self.user_id,
                        content=content.strip(),
                        source="salesforce",
                        source_metadata={
                            "type": "opportunity",
                            "opportunity_id": record.get("Id"),
                            "stage": record.get("StageName"),
                            "amount": record.get("Amount"),
                            "close_date": record.get("CloseDate"),
                            "probability": record.get("Probability"),
                        },
                        context_tags=["crm", "salesforce", "opportunity", "pipeline"],
                    )
                    count += 1

        return count

    async def _sync_contacts(self, session: aiohttp.ClientSession, since: datetime) -> int:
        """Sync Salesforce contacts."""
        # Similar implementation to accounts
        return 0

    async def _sync_activities(self, session: aiohttp.ClientSession, since: datetime) -> int:
        """Sync Salesforce activities (tasks, events)."""
        # Implementation for activities
        return 0


class HubSpotIntegration(BaseDataSourceIntegration):
    """Integration for HubSpot CRM and marketing platform."""

    async def sync_data(self, since: Optional[datetime] = None) -> int:
        """Sync contacts, companies, deals, and activities from HubSpot."""
        session = await self._get_session()
        synced_count = 0

        if not since:
            since = datetime.utcnow() - timedelta(days=30)

        # HubSpot API v3
        headers = {"Authorization": f"Bearer {self.config.api_key}"}

        # Sync different HubSpot objects
        synced_count += await self._sync_contacts(session, headers, since)
        synced_count += await self._sync_companies(session, headers, since)
        synced_count += await self._sync_deals(session, headers, since)

        return synced_count

    async def _sync_contacts(self, session: aiohttp.ClientSession, headers: Dict[str, str], since: datetime) -> int:
        """Sync HubSpot contacts."""
        await self._rate_limit()

        url = f"{self.config.base_url}/crm/v3/objects/contacts"

        params = {"properties": "firstname,lastname,email,company,jobtitle,phone,notes", "limit": 100}

        count = 0
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()

                for contact in data.get("results", []):
                    props = contact.get("properties", {})
                    content = f"""
                    Contact: {props.get('firstname', '')} {props.get('lastname', '')}
                    Email: {props.get('email')}
                    Company: {props.get('company')}
                    Job Title: {props.get('jobtitle')}
                    Phone: {props.get('phone')}
                    Notes: {props.get('notes')}
                    """

                    await self.memory_system.add_memory(
                        user_id=self.user_id,
                        content=content.strip(),
                        source="hubspot",
                        source_metadata={
                            "type": "contact",
                            "contact_id": contact.get("id"),
                            "email": props.get("email"),
                            "company": props.get("company"),
                            "created_at": contact.get("createdAt"),
                            "updated_at": contact.get("updatedAt"),
                        },
                        context_tags=["crm", "hubspot", "contact"],
                    )
                    count += 1

        return count

    async def _sync_companies(self, session: aiohttp.ClientSession, headers: Dict[str, str], since: datetime) -> int:
        """Sync HubSpot companies."""
        # Similar implementation to contacts
        return 0

    async def _sync_deals(self, session: aiohttp.ClientSession, headers: Dict[str, str], since: datetime) -> int:
        """Sync HubSpot deals."""
        # Similar implementation to contacts
        return 0


class SlackIntegration(BaseDataSourceIntegration):
    """Integration for Slack workspace communications."""

    async def sync_data(self, since: Optional[datetime] = None) -> int:
        """Sync messages, channels, and user data from Slack."""
        session = await self._get_session()
        synced_count = 0

        if not since:
            since = datetime.utcnow() - timedelta(days=7)  # Shorter window for chat

        headers = {"Authorization": f"Bearer {self.config.api_key}"}

        # Sync channels and their messages
        channels = await self._get_channels(session, headers)

        for channel in channels:
            synced_count += await self._sync_channel_messages(session, headers, channel, since)

        return synced_count

    async def _get_channels(self, session: aiohttp.ClientSession, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """Get list of Slack channels."""
        await self._rate_limit()

        url = f"{self.config.base_url}/conversations.list"

        params = {"types": "public_channel,private_channel", "limit": 200}

        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("channels", [])

        return []

    async def _sync_channel_messages(
        self, session: aiohttp.ClientSession, headers: Dict[str, str], channel: Dict[str, Any], since: datetime
    ) -> int:
        """Sync messages from a specific channel."""
        await self._rate_limit()

        url = f"{self.config.base_url}/conversations.history"

        # Convert to Slack timestamp
        oldest = str(int(since.timestamp()))

        params = {"channel": channel["id"], "oldest": oldest, "limit": 200}

        count = 0
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()

                for message in data.get("messages", []):
                    if message.get("text"):
                        content = f"""
                        Channel: #{channel.get('name')}
                        User: {message.get('user')}
                        Message: {message.get('text')}
                        Timestamp: {datetime.fromtimestamp(float(message.get('ts', 0)))}
                        """

                        # Check for thread replies
                        if message.get("thread_ts"):
                            replies = await self._get_thread_replies(
                                session, headers, channel["id"], message["thread_ts"]
                            )
                            if replies:
                                content += f"\nThread Replies: {len(replies)} messages"

                        await self.memory_system.add_memory(
                            user_id=self.user_id,
                            content=content.strip(),
                            source="slack",
                            source_metadata={
                                "type": "message",
                                "channel_id": channel["id"],
                                "channel_name": channel.get("name"),
                                "user_id": message.get("user"),
                                "timestamp": message.get("ts"),
                                "thread_ts": message.get("thread_ts"),
                            },
                            context_tags=["communication", "slack", "message"],
                        )
                        count += 1

        return count

    async def _get_thread_replies(
        self, session: aiohttp.ClientSession, headers: Dict[str, str], channel_id: str, thread_ts: str
    ) -> List[Dict[str, Any]]:
        """Get replies to a thread."""
        await self._rate_limit()

        url = f"{self.config.base_url}/conversations.replies"

        params = {"channel": channel_id, "ts": thread_ts}

        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("messages", [])

        return []


class LookerIntegration(BaseDataSourceIntegration):
    """Integration for Looker business intelligence platform."""

    def __init__(self, config: DataSourceConfig, memory_system: EnhancedVectorMemorySystem, user_id: str):
        super().__init__(config, memory_system, user_id)
        self._access_token: Optional[str] = None

    async def _authenticate(self) -> None:
        """Authenticate with Looker API."""
        session = await self._get_session()

        # Looker OAuth
        auth_url = f"{self.config.base_url}/api/4.0/login"

        auth_data = {
            "client_id": self.config.api_key,
            "client_secret": self.config.additional_headers.get("client_secret"),
        }

        async with session.post(auth_url, json=auth_data) as response:
            if response.status == 200:
                auth_response = await response.json()
                self._access_token = auth_response["access_token"]

    async def sync_data(self, since: Optional[datetime] = None) -> int:
        """Sync dashboards, looks, and data from Looker."""
        await self._authenticate()

        if not self._access_token:
            logger.error("Failed to authenticate with Looker")
            return 0

        session = await self._get_session()
        synced_count = 0

        # Sync different Looker objects
        synced_count += await self._sync_dashboards(session)
        synced_count += await self._sync_looks(session)
        synced_count += await self._sync_explores(session)

        return synced_count

    async def _sync_dashboards(self, session: aiohttp.ClientSession) -> int:
        """Sync Looker dashboards."""
        await self._rate_limit()

        headers = {"Authorization": f"Bearer {self._access_token}"}
        url = f"{self.config.base_url}/api/4.0/dashboards"

        count = 0
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                dashboards = await response.json()

                for dashboard in dashboards:
                    content = f"""
                    Dashboard: {dashboard.get('title')}
                    Description: {dashboard.get('description')}
                    Folder: {dashboard.get('folder', {}).get('name')}
                    Created: {dashboard.get('created_at')}
                    Updated: {dashboard.get('updated_at')}
                    """

                    await self.memory_system.add_memory(
                        user_id=self.user_id,
                        content=content.strip(),
                        source="looker",
                        source_metadata={
                            "type": "dashboard",
                            "dashboard_id": dashboard.get("id"),
                            "title": dashboard.get("title"),
                            "folder_id": dashboard.get("folder", {}).get("id"),
                            "created_at": dashboard.get("created_at"),
                            "updated_at": dashboard.get("updated_at"),
                        },
                        context_tags=["analytics", "looker", "dashboard", "business_intelligence"],
                    )
                    count += 1

        return count

    async def _sync_looks(self, session: aiohttp.ClientSession) -> int:
        """Sync Looker looks (saved queries)."""
        # Similar implementation to dashboards
        return 0

    async def _sync_explores(self, session: aiohttp.ClientSession) -> int:
        """Sync Looker explores and data models."""
        # Implementation for explores
        return 0


class DataAggregationOrchestrator:
    """Orchestrates data collection from all sources."""

    def __init__(self, memory_system: EnhancedVectorMemorySystem, user_id: str):
        self.memory_system = memory_system
        self.user_id = user_id
        self.integrations: Dict[str, BaseDataSourceIntegration] = {}

    def add_integration(self, name: str, integration: BaseDataSourceIntegration) -> None:
        """Add a data source integration."""
        self.integrations[name] = integration

    async def sync_all_sources(self, since: Optional[datetime] = None) -> Dict[str, int]:
        """Sync data from all configured sources."""
        results = {}

        for name, integration in self.integrations.items():
            try:
                logger.info(f"Starting sync for {name}")
                count = await integration.sync_data(since)
                results[name] = count
                logger.info(f"Synced {count} items from {name}")
            except Exception as e:
                logger.error(f"Failed to sync {name}: {e}")
                results[name] = -1
            finally:
                await integration.close()

        return results

    async def setup_default_integrations(self, configs: Dict[str, DataSourceConfig]) -> None:
        """Set up all default integrations."""
        if "gong" in configs:
            self.add_integration("gong", GongIntegration(configs["gong"], self.memory_system, self.user_id))

        if "salesforce" in configs:
            self.add_integration(
                "salesforce", SalesforceIntegration(configs["salesforce"], self.memory_system, self.user_id)
            )

        if "hubspot" in configs:
            self.add_integration("hubspot", HubSpotIntegration(configs["hubspot"], self.memory_system, self.user_id))

        if "slack" in configs:
            self.add_integration("slack", SlackIntegration(configs["slack"], self.memory_system, self.user_id))

        if "looker" in configs:
            self.add_integration("looker", LookerIntegration(configs["looker"], self.memory_system, self.user_id))
