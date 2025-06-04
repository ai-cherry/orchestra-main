#!/usr/bin/env python3
"""
Enterprise API Integration Manager
Comprehensive integration with business systems for Cherry AI Orchestrator

Supported APIs:
- Salesforce: CRM data, opportunities, accounts
- HubSpot: Marketing, contacts, deals
- Apollo.io: Prospecting, sequences, analytics
- Gong.io: Call data, transcripts, coaching
- Slack: Messages, channels, files
- Looker: Reports, dashboards, analytics

Author: Cherry AI Team
Version: 1.0.0
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import aiohttp
import base64
from urllib.parse import urlencode

# Database integration
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'database_layer'))
from enterprise_db_manager import EnterpriseDatabaseManager

logger = logging.getLogger(__name__)

class APIConfig:
    """Configuration management for all API integrations"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), 'api_config.json')
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load API configuration from file or environment"""
        default_config = {
            "salesforce": {
                "client_id": os.getenv("SALESFORCE_CLIENT_ID", ""),
                "client_secret": os.getenv("SALESFORCE_CLIENT_SECRET", ""),
                "username": os.getenv("SALESFORCE_USERNAME", ""),
                "password": os.getenv("SALESFORCE_PASSWORD", ""),
                "security_token": os.getenv("SALESFORCE_SECURITY_TOKEN", ""),
                "domain": os.getenv("SALESFORCE_DOMAIN", "login"),  # or your custom domain
                "api_version": "v59.0",
                "enabled": False
            },
            "hubspot": {
                "api_key": os.getenv("HUBSPOT_API_KEY", ""),
                "access_token": os.getenv("HUBSPOT_ACCESS_TOKEN", ""),
                "portal_id": os.getenv("HUBSPOT_PORTAL_ID", ""),
                "api_version": "v3",
                "enabled": False
            },
            "apollo": {
                "api_key": os.getenv("APOLLO_API_KEY", ""),
                "base_url": "https://api.apollo.io/v1",
                "enabled": False
            },
            "gong": {
                "access_key": os.getenv("GONG_ACCESS_KEY", ""),
                "access_key_secret": os.getenv("GONG_ACCESS_KEY_SECRET", ""),
                "base_url": "https://api.gong.io/v2",
                "enabled": False
            },
            "slack": {
                "bot_token": os.getenv("SLACK_BOT_TOKEN", ""),
                "app_token": os.getenv("SLACK_APP_TOKEN", ""),
                "signing_secret": os.getenv("SLACK_SIGNING_SECRET", ""),
                "workspace_id": os.getenv("SLACK_WORKSPACE_ID", ""),
                "enabled": False
            },
            "looker": {
                "base_url": os.getenv("LOOKER_BASE_URL", ""),
                "client_id": os.getenv("LOOKER_CLIENT_ID", ""),
                "client_secret": os.getenv("LOOKER_CLIENT_SECRET", ""),
                "api_version": "4.0",
                "enabled": False
            },
            "automation": {
                "n8n_webhook_url": os.getenv("N8N_WEBHOOK_URL", ""),
                "zapier_webhook_url": os.getenv("ZAPIER_WEBHOOK_URL", ""),
                "sync_frequency": 3600,  # seconds
                "batch_size": 100
            }
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    file_config = json.load(f)
                    # Merge with defaults
                    for key, value in file_config.items():
                        if key in default_config and isinstance(value, dict):
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
            except Exception as e:
                logger.warning(f"Error loading API config file: {e}")
        
        return default_config

class SalesforceIntegration:
    """Salesforce CRM integration"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.access_token = None
        self.instance_url = None
        self.session = None
    
    async def authenticate(self) -> bool:
        """Authenticate with Salesforce using OAuth2"""
        if not self.config.get("enabled", False):
            return False
        
        auth_url = f"https://{self.config['domain']}.salesforce.com/services/oauth2/token"
        
        data = {
            'grant_type': 'password',
            'client_id': self.config['client_id'],
            'client_secret': self.config['client_secret'],
            'username': self.config['username'],
            'password': self.config['password'] + self.config['security_token']
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(auth_url, data=data) as response:
                    if response.status == 200:
                        auth_data = await response.json()
                        self.access_token = auth_data['access_token']
                        self.instance_url = auth_data['instance_url']
                        logger.info("Salesforce authentication successful")
                        return True
                    else:
                        logger.error(f"Salesforce authentication failed: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Salesforce authentication error: {e}")
            return False
    
    async def get_accounts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve Salesforce accounts"""
        if not self.access_token:
            await self.authenticate()
        
        query = f"SELECT Id, Name, Type, Industry, BillingCity, BillingState, BillingCountry, Phone, Website, Description FROM Account LIMIT {limit}"
        return await self._execute_soql(query)
    
    async def get_opportunities(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve Salesforce opportunities"""
        if not self.access_token:
            await self.authenticate()
        
        query = f"SELECT Id, Name, StageName, Amount, CloseDate, Probability, AccountId, Account.Name, OwnerId, Owner.Name FROM Opportunity LIMIT {limit}"
        return await self._execute_soql(query)
    
    async def get_contacts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve Salesforce contacts"""
        if not self.access_token:
            await self.authenticate()
        
        query = f"SELECT Id, FirstName, LastName, Email, Phone, Title, AccountId, Account.Name FROM Contact LIMIT {limit}"
        return await self._execute_soql(query)
    
    async def _execute_soql(self, query: str) -> List[Dict[str, Any]]:
        """Execute SOQL query"""
        if not self.access_token:
            return []
        
        url = f"{self.instance_url}/services/data/{self.config['api_version']}/query"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        params = {'q': query}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('records', [])
                    else:
                        logger.error(f"Salesforce query failed: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Salesforce query error: {e}")
            return []

class HubSpotIntegration:
    """HubSpot CRM and Marketing integration"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = f"https://api.hubapi.com/crm/{config['api_version']}"
    
    async def get_contacts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve HubSpot contacts"""
        if not self.config.get("enabled", False):
            return []
        
        url = f"{self.base_url}/objects/contacts"
        headers = self._get_headers()
        params = {
            'limit': limit,
            'properties': 'firstname,lastname,email,phone,company,jobtitle,lifecyclestage'
        }
        
        return await self._make_request(url, headers, params)
    
    async def get_deals(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve HubSpot deals"""
        if not self.config.get("enabled", False):
            return []
        
        url = f"{self.base_url}/objects/deals"
        headers = self._get_headers()
        params = {
            'limit': limit,
            'properties': 'dealname,amount,dealstage,closedate,pipeline,dealtype'
        }
        
        return await self._make_request(url, headers, params)
    
    async def get_companies(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve HubSpot companies"""
        if not self.config.get("enabled", False):
            return []
        
        url = f"{self.base_url}/objects/companies"
        headers = self._get_headers()
        params = {
            'limit': limit,
            'properties': 'name,domain,industry,city,state,country,phone,website'
        }
        
        return await self._make_request(url, headers, params)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HubSpot API headers"""
        if self.config.get('access_token'):
            return {
                'Authorization': f'Bearer {self.config["access_token"]}',
                'Content-Type': 'application/json'
            }
        else:
            return {
                'Authorization': f'Bearer {self.config["api_key"]}',
                'Content-Type': 'application/json'
            }
    
    async def _make_request(self, url: str, headers: Dict[str, str], params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Make HubSpot API request"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('results', [])
                    else:
                        logger.error(f"HubSpot request failed: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"HubSpot request error: {e}")
            return []

class ApolloIntegration:
    """Apollo.io prospecting and sales intelligence integration"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config['base_url']
    
    async def search_people(self, query: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        """Search for people in Apollo"""
        if not self.config.get("enabled", False):
            return []
        
        url = f"{self.base_url}/mixed_people/search"
        headers = self._get_headers()
        data = {
            **query,
            'page': 1,
            'per_page': min(limit, 200)  # Apollo max is 200
        }
        
        return await self._make_request(url, headers, data, method='POST')
    
    async def search_organizations(self, query: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        """Search for organizations in Apollo"""
        if not self.config.get("enabled", False):
            return []
        
        url = f"{self.base_url}/mixed_companies/search"
        headers = self._get_headers()
        data = {
            **query,
            'page': 1,
            'per_page': min(limit, 200)
        }
        
        return await self._make_request(url, headers, data, method='POST')
    
    async def get_sequences(self) -> List[Dict[str, Any]]:
        """Get Apollo sequences"""
        if not self.config.get("enabled", False):
            return []
        
        url = f"{self.base_url}/emailer_campaigns"
        headers = self._get_headers()
        
        return await self._make_request(url, headers, method='GET')
    
    def _get_headers(self) -> Dict[str, str]:
        """Get Apollo API headers"""
        return {
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/json',
            'X-Api-Key': self.config['api_key']
        }
    
    async def _make_request(self, url: str, headers: Dict[str, str], 
                          data: Optional[Dict[str, Any]] = None, method: str = 'GET') -> List[Dict[str, Any]]:
        """Make Apollo API request"""
        try:
            async with aiohttp.ClientSession() as session:
                if method == 'POST':
                    async with session.post(url, headers=headers, json=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            return result.get('people', result.get('organizations', result.get('emailer_campaigns', [])))
                        else:
                            logger.error(f"Apollo request failed: {response.status}")
                            return []
                else:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            result = await response.json()
                            return result.get('emailer_campaigns', [])
                        else:
                            logger.error(f"Apollo request failed: {response.status}")
                            return []
        except Exception as e:
            logger.error(f"Apollo request error: {e}")
            return []

class GongIntegration:
    """Gong.io call intelligence and coaching integration"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config['base_url']
    
    async def get_calls(self, from_date: Optional[datetime] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve Gong calls"""
        if not self.config.get("enabled", False):
            return []
        
        if not from_date:
            from_date = datetime.now() - timedelta(days=30)
        
        url = f"{self.base_url}/calls"
        headers = self._get_headers()
        data = {
            'filter': {
                'fromDateTime': from_date.isoformat(),
                'toDateTime': datetime.now().isoformat()
            },
            'cursor': {
                'limit': limit
            }
        }
        
        return await self._make_request(url, headers, data)
    
    async def get_call_transcripts(self, call_id: str) -> Dict[str, Any]:
        """Get transcript for a specific call"""
        if not self.config.get("enabled", False):
            return {}
        
        url = f"{self.base_url}/calls/transcript"
        headers = self._get_headers()
        data = {'filter': {'callIds': [call_id]}}
        
        result = await self._make_request(url, headers, data)
        return result[0] if result else {}
    
    async def get_users(self) -> List[Dict[str, Any]]:
        """Get Gong users"""
        if not self.config.get("enabled", False):
            return []
        
        url = f"{self.base_url}/users"
        headers = self._get_headers()
        data = {'cursor': {'limit': 100}}
        
        return await self._make_request(url, headers, data)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get Gong API headers"""
        credentials = base64.b64encode(
            f"{self.config['access_key']}:{self.config['access_key_secret']}".encode()
        ).decode()
        
        return {
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/json'
        }
    
    async def _make_request(self, url: str, headers: Dict[str, str], data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Make Gong API request"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('records', result.get('calls', result.get('users', [])))
                    else:
                        logger.error(f"Gong request failed: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Gong request error: {e}")
            return []

class SlackIntegration:
    """Slack workspace integration"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = "https://slack.com/api"
    
    async def get_channels(self) -> List[Dict[str, Any]]:
        """Get Slack channels"""
        if not self.config.get("enabled", False):
            return []
        
        url = f"{self.base_url}/conversations.list"
        headers = self._get_headers()
        params = {'types': 'public_channel,private_channel'}
        
        return await self._make_request(url, headers, params)
    
    async def get_messages(self, channel_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get messages from a Slack channel"""
        if not self.config.get("enabled", False):
            return []
        
        url = f"{self.base_url}/conversations.history"
        headers = self._get_headers()
        params = {
            'channel': channel_id,
            'limit': limit
        }
        
        return await self._make_request(url, headers, params)
    
    async def get_users(self) -> List[Dict[str, Any]]:
        """Get Slack users"""
        if not self.config.get("enabled", False):
            return []
        
        url = f"{self.base_url}/users.list"
        headers = self._get_headers()
        
        return await self._make_request(url, headers)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get Slack API headers"""
        return {
            'Authorization': f'Bearer {self.config["bot_token"]}',
            'Content-Type': 'application/json'
        }
    
    async def _make_request(self, url: str, headers: Dict[str, str], 
                          params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Make Slack API request"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('ok'):
                            return data.get('channels', data.get('messages', data.get('members', [])))
                        else:
                            logger.error(f"Slack API error: {data.get('error')}")
                            return []
                    else:
                        logger.error(f"Slack request failed: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Slack request error: {e}")
            return []

class LookerIntegration:
    """Looker business intelligence integration"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = f"{config['base_url']}/api/{config['api_version']}"
        self.access_token = None
    
    async def authenticate(self) -> bool:
        """Authenticate with Looker"""
        if not self.config.get("enabled", False):
            return False
        
        url = f"{self.base_url}/login"
        data = {
            'client_id': self.config['client_id'],
            'client_secret': self.config['client_secret']
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        auth_data = await response.json()
                        self.access_token = auth_data['access_token']
                        logger.info("Looker authentication successful")
                        return True
                    else:
                        logger.error(f"Looker authentication failed: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Looker authentication error: {e}")
            return False
    
    async def get_dashboards(self) -> List[Dict[str, Any]]:
        """Get Looker dashboards"""
        if not self.access_token:
            await self.authenticate()
        
        url = f"{self.base_url}/dashboards"
        headers = self._get_headers()
        
        return await self._make_request(url, headers)
    
    async def get_looks(self) -> List[Dict[str, Any]]:
        """Get Looker looks (saved queries)"""
        if not self.access_token:
            await self.authenticate()
        
        url = f"{self.base_url}/looks"
        headers = self._get_headers()
        
        return await self._make_request(url, headers)
    
    async def run_look(self, look_id: int, format: str = 'json') -> Dict[str, Any]:
        """Run a Looker look and get results"""
        if not self.access_token:
            await self.authenticate()
        
        url = f"{self.base_url}/looks/{look_id}/run/{format}"
        headers = self._get_headers()
        
        result = await self._make_request(url, headers)
        return result[0] if isinstance(result, list) and result else result
    
    def _get_headers(self) -> Dict[str, str]:
        """Get Looker API headers"""
        return {
            'Authorization': f'token {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    async def _make_request(self, url: str, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """Make Looker API request"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Looker request failed: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Looker request error: {e}")
            return []

class AutomationManager:
    """Manages automation workflows with n8n and Zapier"""
    
    def __init__(self, config: Dict[str, Any], db_manager: EnterpriseDatabaseManager):
        self.config = config
        self.db_manager = db_manager
    
    async def trigger_n8n_workflow(self, workflow_data: Dict[str, Any]) -> bool:
        """Trigger n8n workflow via webhook"""
        webhook_url = self.config.get('n8n_webhook_url')
        if not webhook_url:
            logger.warning("n8n webhook URL not configured")
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=workflow_data) as response:
                    if response.status == 200:
                        logger.info("n8n workflow triggered successfully")
                        return True
                    else:
                        logger.error(f"n8n workflow trigger failed: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"n8n workflow trigger error: {e}")
            return False
    
    async def trigger_zapier_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """Trigger Zapier webhook"""
        webhook_url = self.config.get('zapier_webhook_url')
        if not webhook_url:
            logger.warning("Zapier webhook URL not configured")
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=webhook_data) as response:
                    if response.status == 200:
                        logger.info("Zapier webhook triggered successfully")
                        return True
                    else:
                        logger.error(f"Zapier webhook trigger failed: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Zapier webhook trigger error: {e}")
            return False
    
    async def sync_data_to_database(self, api_name: str, data: List[Dict[str, Any]], persona: str):
        """Sync API data to database"""
        if not data:
            return
        
        try:
            # Log the sync operation
            await self._log_api_operation(api_name, 'sync', 'started', len(data))
            
            # Process and store data based on API type
            if api_name == 'salesforce':
                await self._process_salesforce_data(data, persona)
            elif api_name == 'hubspot':
                await self._process_hubspot_data(data, persona)
            elif api_name == 'apollo':
                await self._process_apollo_data(data, persona)
            elif api_name == 'gong':
                await self._process_gong_data(data, persona)
            elif api_name == 'slack':
                await self._process_slack_data(data, persona)
            elif api_name == 'looker':
                await self._process_looker_data(data, persona)
            
            # Log successful completion
            await self._log_api_operation(api_name, 'sync', 'completed', len(data))
            
        except Exception as e:
            logger.error(f"Error syncing {api_name} data: {e}")
            await self._log_api_operation(api_name, 'sync', 'error', 0, str(e))
    
    async def _process_salesforce_data(self, data: List[Dict[str, Any]], persona: str):
        """Process Salesforce data for ingestion"""
        # Convert Salesforce records to text for embedding
        for record in data:
            content = self._salesforce_record_to_text(record)
            metadata = {
                'source': 'salesforce',
                'record_type': record.get('attributes', {}).get('type', 'unknown'),
                'record_id': record.get('Id'),
                'persona': persona,
                'timestamp': datetime.now().isoformat()
            }
            
            # Store in database (this would use the ingestion pipeline)
            # For now, we'll just log it
            logger.info(f"Processing Salesforce {metadata['record_type']}: {record.get('Name', record.get('Id'))}")
    
    async def _process_hubspot_data(self, data: List[Dict[str, Any]], persona: str):
        """Process HubSpot data for ingestion"""
        for record in data:
            content = self._hubspot_record_to_text(record)
            metadata = {
                'source': 'hubspot',
                'record_id': record.get('id'),
                'persona': persona,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Processing HubSpot record: {record.get('id')}")
    
    async def _process_apollo_data(self, data: List[Dict[str, Any]], persona: str):
        """Process Apollo data for ingestion"""
        for record in data:
            content = self._apollo_record_to_text(record)
            metadata = {
                'source': 'apollo',
                'record_id': record.get('id'),
                'persona': persona,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Processing Apollo record: {record.get('id')}")
    
    async def _process_gong_data(self, data: List[Dict[str, Any]], persona: str):
        """Process Gong data for ingestion"""
        for record in data:
            content = self._gong_record_to_text(record)
            metadata = {
                'source': 'gong',
                'call_id': record.get('id'),
                'persona': persona,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Processing Gong call: {record.get('id')}")
    
    async def _process_slack_data(self, data: List[Dict[str, Any]], persona: str):
        """Process Slack data for ingestion"""
        for record in data:
            content = self._slack_record_to_text(record)
            metadata = {
                'source': 'slack',
                'message_id': record.get('ts'),
                'channel': record.get('channel'),
                'persona': persona,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Processing Slack message: {record.get('ts')}")
    
    async def _process_looker_data(self, data: List[Dict[str, Any]], persona: str):
        """Process Looker data for ingestion"""
        for record in data:
            content = self._looker_record_to_text(record)
            metadata = {
                'source': 'looker',
                'dashboard_id': record.get('id'),
                'persona': persona,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Processing Looker dashboard: {record.get('id')}")
    
    def _salesforce_record_to_text(self, record: Dict[str, Any]) -> str:
        """Convert Salesforce record to searchable text"""
        text_parts = []
        
        # Add name/title
        if record.get('Name'):
            text_parts.append(f"Name: {record['Name']}")
        
        # Add type-specific fields
        record_type = record.get('attributes', {}).get('type', '')
        if record_type == 'Account':
            if record.get('Industry'):
                text_parts.append(f"Industry: {record['Industry']}")
            if record.get('BillingCity'):
                text_parts.append(f"Location: {record['BillingCity']}, {record.get('BillingState', '')}")
        elif record_type == 'Opportunity':
            if record.get('StageName'):
                text_parts.append(f"Stage: {record['StageName']}")
            if record.get('Amount'):
                text_parts.append(f"Amount: ${record['Amount']}")
        
        return ' | '.join(text_parts)
    
    def _hubspot_record_to_text(self, record: Dict[str, Any]) -> str:
        """Convert HubSpot record to searchable text"""
        properties = record.get('properties', {})
        text_parts = []
        
        # Common fields
        for field in ['firstname', 'lastname', 'email', 'company', 'dealname']:
            if properties.get(field):
                text_parts.append(f"{field.title()}: {properties[field]}")
        
        return ' | '.join(text_parts)
    
    def _apollo_record_to_text(self, record: Dict[str, Any]) -> str:
        """Convert Apollo record to searchable text"""
        text_parts = []
        
        if record.get('name'):
            text_parts.append(f"Name: {record['name']}")
        if record.get('title'):
            text_parts.append(f"Title: {record['title']}")
        if record.get('organization', {}).get('name'):
            text_parts.append(f"Company: {record['organization']['name']}")
        
        return ' | '.join(text_parts)
    
    def _gong_record_to_text(self, record: Dict[str, Any]) -> str:
        """Convert Gong record to searchable text"""
        text_parts = []
        
        if record.get('title'):
            text_parts.append(f"Call: {record['title']}")
        if record.get('primaryUserId'):
            text_parts.append(f"User: {record['primaryUserId']}")
        if record.get('purpose'):
            text_parts.append(f"Purpose: {record['purpose']}")
        
        return ' | '.join(text_parts)
    
    def _slack_record_to_text(self, record: Dict[str, Any]) -> str:
        """Convert Slack record to searchable text"""
        text_parts = []
        
        if record.get('text'):
            text_parts.append(f"Message: {record['text']}")
        if record.get('user'):
            text_parts.append(f"User: {record['user']}")
        
        return ' | '.join(text_parts)
    
    def _looker_record_to_text(self, record: Dict[str, Any]) -> str:
        """Convert Looker record to searchable text"""
        text_parts = []
        
        if record.get('title'):
            text_parts.append(f"Dashboard: {record['title']}")
        if record.get('description'):
            text_parts.append(f"Description: {record['description']}")
        
        return ' | '.join(text_parts)
    
    async def _log_api_operation(self, api_name: str, operation: str, status: str, 
                                records_processed: int = 0, error_message: str = None):
        """Log API operation to database"""
        if not self.db_manager.postgresql_manager:
            return
        
        query = """
        INSERT INTO api_integration_logs (api_name, operation, status, records_processed, error_message, metadata)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        metadata = {'timestamp': datetime.now().isoformat()}
        
        await self.db_manager.postgresql_manager.execute_update(
            query, (api_name, operation, status, records_processed, error_message, json.dumps(metadata))
        )

class EnterpriseAPIManager:
    """Main API integration manager coordinating all business systems"""
    
    def __init__(self, config_path: Optional[str] = None, db_manager: Optional[EnterpriseDatabaseManager] = None):
        self.config = APIConfig(config_path)
        self.db_manager = db_manager or EnterpriseDatabaseManager()
        
        # Initialize integrations
        self.salesforce = SalesforceIntegration(self.config.config['salesforce'])
        self.hubspot = HubSpotIntegration(self.config.config['hubspot'])
        self.apollo = ApolloIntegration(self.config.config['apollo'])
        self.gong = GongIntegration(self.config.config['gong'])
        self.slack = SlackIntegration(self.config.config['slack'])
        self.looker = LookerIntegration(self.config.config['looker'])
        self.automation = AutomationManager(self.config.config['automation'], self.db_manager)
    
    async def sync_all_data(self, persona: str = 'sophia') -> Dict[str, Any]:
        """Sync data from all enabled APIs"""
        results = {}
        
        # Salesforce
        if self.config.config['salesforce'].get('enabled'):
            try:
                accounts = await self.salesforce.get_accounts()
                opportunities = await self.salesforce.get_opportunities()
                contacts = await self.salesforce.get_contacts()
                
                all_sf_data = accounts + opportunities + contacts
                await self.automation.sync_data_to_database('salesforce', all_sf_data, persona)
                results['salesforce'] = len(all_sf_data)
            except Exception as e:
                logger.error(f"Salesforce sync error: {e}")
                results['salesforce'] = 0
        
        # HubSpot
        if self.config.config['hubspot'].get('enabled'):
            try:
                contacts = await self.hubspot.get_contacts()
                deals = await self.hubspot.get_deals()
                companies = await self.hubspot.get_companies()
                
                all_hs_data = contacts + deals + companies
                await self.automation.sync_data_to_database('hubspot', all_hs_data, persona)
                results['hubspot'] = len(all_hs_data)
            except Exception as e:
                logger.error(f"HubSpot sync error: {e}")
                results['hubspot'] = 0
        
        # Apollo
        if self.config.config['apollo'].get('enabled'):
            try:
                # Example search for property management companies
                people = await self.apollo.search_people({
                    'organization_industry_tag_ids': ['property management']
                })
                organizations = await self.apollo.search_organizations({
                    'industry_tag_ids': ['property management']
                })
                
                all_apollo_data = people + organizations
                await self.automation.sync_data_to_database('apollo', all_apollo_data, persona)
                results['apollo'] = len(all_apollo_data)
            except Exception as e:
                logger.error(f"Apollo sync error: {e}")
                results['apollo'] = 0
        
        # Gong
        if self.config.config['gong'].get('enabled'):
            try:
                calls = await self.gong.get_calls()
                await self.automation.sync_data_to_database('gong', calls, persona)
                results['gong'] = len(calls)
            except Exception as e:
                logger.error(f"Gong sync error: {e}")
                results['gong'] = 0
        
        # Slack
        if self.config.config['slack'].get('enabled'):
            try:
                channels = await self.slack.get_channels()
                all_messages = []
                for channel in channels[:5]:  # Limit to first 5 channels
                    messages = await self.slack.get_messages(channel['id'])
                    all_messages.extend(messages)
                
                await self.automation.sync_data_to_database('slack', all_messages, persona)
                results['slack'] = len(all_messages)
            except Exception as e:
                logger.error(f"Slack sync error: {e}")
                results['slack'] = 0
        
        # Looker
        if self.config.config['looker'].get('enabled'):
            try:
                dashboards = await self.looker.get_dashboards()
                await self.automation.sync_data_to_database('looker', dashboards, persona)
                results['looker'] = len(dashboards)
            except Exception as e:
                logger.error(f"Looker sync error: {e}")
                results['looker'] = 0
        
        return results
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all API integrations"""
        health = {}
        
        # Test each integration
        health['salesforce'] = await self.salesforce.authenticate() if self.config.config['salesforce'].get('enabled') else False
        health['hubspot'] = self.config.config['hubspot'].get('enabled', False) and bool(self.config.config['hubspot'].get('api_key'))
        health['apollo'] = self.config.config['apollo'].get('enabled', False) and bool(self.config.config['apollo'].get('api_key'))
        health['gong'] = self.config.config['gong'].get('enabled', False) and bool(self.config.config['gong'].get('access_key'))
        health['slack'] = self.config.config['slack'].get('enabled', False) and bool(self.config.config['slack'].get('bot_token'))
        health['looker'] = await self.looker.authenticate() if self.config.config['looker'].get('enabled') else False
        
        return health

# Example usage and testing
async def main():
    """Test the API integration manager"""
    api_manager = EnterpriseAPIManager()
    
    # Health check
    health = await api_manager.health_check()
    print("API Integration Health Check:")
    for system, status in health.items():
        print(f"  {system}: {'✅' if status else '❌'}")
    
    # Test sync (only if APIs are configured)
    if any(health.values()):
        results = await api_manager.sync_all_data('sophia')
        print(f"\nSync Results: {results}")

if __name__ == "__main__":
    asyncio.run(main())

