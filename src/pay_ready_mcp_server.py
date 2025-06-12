#!/usr/bin/env python3
"""
Pay Ready/Sophia MCP Server - Unified Sales Intelligence Platform
Integrates: Hubspot, Gong.io, Slack, Apollo.io, Phantom Buster
Focus: Sales Intelligence + Client Health + Employee Performance
"""

import os
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

import httpx
import redis.asyncio as redis
from pydantic import BaseModel
import pulumi

# Import base MCP server (assuming it's been moved to src)
from legacy.mcp_server.servers.base_mcp_server import BaseMCPServer, MCPServerConfig


class IntegrationType(Enum):
    """Types of integrations supported."""
    HUBSPOT = "hubspot"
    GONG = "gong"
    SLACK = "slack"
    APOLLO = "apollo"
    PHANTOM_BUSTER = "phantom_buster"


@dataclass
class SalesMetric:
    """Sales performance metric."""
    metric_name: str
    value: float
    period: str
    employee_id: Optional[str] = None
    client_id: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class IntegrationConnector:
    """Base connector for third-party integrations."""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


class HubspotConnector(IntegrationConnector):
    """Hubspot CRM integration."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "https://api.hubapi.com")
    
    async def get_deals(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch deals from Hubspot."""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        response = await self.client.get(
            f"{self.base_url}/crm/v3/objects/deals",
            headers=headers,
            params={"limit": limit, "properties": "dealname,amount,dealstage,closedate"}
        )
        response.raise_for_status()
        
        return response.json().get("results", [])
    
    async def get_contacts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch contacts from Hubspot."""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        response = await self.client.get(
            f"{self.base_url}/crm/v3/objects/contacts",
            headers=headers,
            params={"limit": limit, "properties": "firstname,lastname,email,company,lifecyclestage"}
        )
        response.raise_for_status()
        
        return response.json().get("results", [])


class GongConnector(IntegrationConnector):
    """Gong.io call analytics integration."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "https://api.gong.io/v2")
    
    async def get_calls(self, from_date: datetime = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch call data from Gong."""
        if from_date is None:
            from_date = datetime.utcnow() - timedelta(days=7)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "filter": {
                "fromDateTime": from_date.isoformat(),
                "toDateTime": datetime.utcnow().isoformat()
            },
            "cursor": {
                "limit": limit
            }
        }
        
        response = await self.client.post(
            f"{self.base_url}/calls",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        
        return response.json().get("calls", [])
    
    async def get_call_analytics(self, call_id: str) -> Dict[str, Any]:
        """Get detailed analytics for a specific call."""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        response = await self.client.get(
            f"{self.base_url}/calls/{call_id}/extensive",
            headers=headers
        )
        response.raise_for_status()
        
        return response.json()


class SlackConnector(IntegrationConnector):
    """Slack team communication integration."""
    
    def __init__(self, bot_token: str):
        super().__init__(bot_token, "https://slack.com/api")
    
    async def get_team_messages(self, channel_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch recent messages from a Slack channel."""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        response = await self.client.get(
            f"{self.base_url}/conversations.history",
            headers=headers,
            params={"channel": channel_id, "limit": limit}
        )
        response.raise_for_status()
        
        return response.json().get("messages", [])
    
    async def post_notification(self, channel_id: str, message: str) -> bool:
        """Post a notification to Slack channel."""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        payload = {
            "channel": channel_id,
            "text": message
        }
        
        response = await self.client.post(
            f"{self.base_url}/chat.postMessage",
            headers=headers,
            json=payload
        )
        
        return response.status_code == 200


class ApolloConnector(IntegrationConnector):
    """Apollo.io lead generation integration."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "https://api.apollo.io/v1")
    
    async def search_people(self, query: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        """Search for people using Apollo."""
        headers = {"X-Api-Key": self.api_key}
        
        payload = {
            "q_keywords": query.get("keywords", ""),
            "page": 1,
            "per_page": min(limit, 200)  # Apollo max is 200
        }
        
        response = await self.client.post(
            f"{self.base_url}/mixed_people/search",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        
        return response.json().get("people", [])
    
    async def get_account_info(self, domain: str) -> Dict[str, Any]:
        """Get account information for a domain."""
        headers = {"X-Api-Key": self.api_key}
        
        response = await self.client.get(
            f"{self.base_url}/organizations/bulk_enrich",
            headers=headers,
            params={"domains": domain}
        )
        response.raise_for_status()
        
        organizations = response.json().get("organizations", [])
        return organizations[0] if organizations else {}


class PhantomBusterConnector(IntegrationConnector):
    """Phantom Buster data collection integration."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "https://api.phantombuster.com/api/v2")
    
    async def get_agents(self) -> List[Dict[str, Any]]:
        """Get list of Phantom Buster agents."""
        headers = {"X-Phantombuster-Key": self.api_key}
        
        response = await self.client.get(
            f"{self.base_url}/agents/fetch-all",
            headers=headers
        )
        response.raise_for_status()
        
        return response.json().get("data", [])
    
    async def launch_agent(self, agent_id: str, arguments: Dict[str, Any] = None) -> str:
        """Launch a Phantom Buster agent."""
        headers = {"X-Phantombuster-Key": self.api_key}
        
        payload = {
            "id": agent_id,
            "arguments": arguments or {}
        }
        
        response = await self.client.post(
            f"{self.base_url}/agents/launch",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        
        return response.json().get("containerId", "")


class PayReadySophiaMCPServer(BaseMCPServer):
    """Unified MCP Server for Pay Ready/Sophia Sales Intelligence Platform."""
    
    def __init__(self):
        config = MCPServerConfig(
            name="pay-ready-sophia",
            version="1.0.0",
            service_type="sales-intelligence-mcp",
            required_secrets=[
                "HUBSPOT_API_KEY",
                "GONG_API_KEY", 
                "SLACK_BOT_TOKEN",
                "APOLLO_API_KEY",
                "PHANTOMBUSTER_API_KEY",
                "REDIS_URL"
            ],
            optional_secrets=[
                "PINECONE_API_KEY",
                "PINECONE_ENVIRONMENT",
                "SLACK_CHANNEL_ID"
            ],
            project_id=os.getenv("PROJECT_ID", "pay-ready-local"),
            pubsub_topic="sales-intelligence-events",
        )
        
        super().__init__(config)
        
        # Initialize connectors
        self.hubspot: Optional[HubspotConnector] = None
        self.gong: Optional[GongConnector] = None
        self.slack: Optional[SlackConnector] = None
        self.apollo: Optional[ApolloConnector] = None
        self.phantom_buster: Optional[PhantomBusterConnector] = None
        self.redis_client: Optional[redis.Redis] = None
        
        # Cache for performance
        self.cache_ttl = 300  # 5 minutes
        self.metrics_cache: Dict[str, Any] = {}
    
    async def on_start(self):
        """Initialize all integrations."""
        try:
            # Initialize Redis for caching
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            
            # Initialize integration connectors
            config = pulumi.Config()
            self.hubspot = HubspotConnector(config.require_secret("HUBSPOT_API_KEY"))
            self.gong = GongConnector(config.require_secret("GONG_API_KEY"))
            self.slack = SlackConnector(config.require_secret("SLACK_BOT_TOKEN"))
            self.apollo = ApolloConnector(config.require_secret("APOLLO_API_KEY"))
            self.phantom_buster = PhantomBusterConnector(config.require_secret("PHANTOMBUSTER_API_KEY"))
            
            print("✅ Pay Ready/Sophia MCP Server initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize Pay Ready/Sophia MCP Server: {e}")
            raise
    
    async def on_stop(self):
        """Clean up connections."""
        if self.hubspot:
            await self.hubspot.close()
        if self.gong:
            await self.gong.close()
        if self.slack:
            await self.slack.close()
        if self.apollo:
            await self.apollo.close()
        if self.phantom_buster:
            await self.phantom_buster.close()
        if self.redis_client:
            await self.redis_client.close()
    
    async def check_health(self) -> Dict[str, Any]:
        """Check health of all integrations."""
        health_details = {}
        
        # Check Redis
        try:
            await self.redis_client.ping()
            health_details["redis"] = {"healthy": True}
        except Exception as e:
            health_details["redis"] = {"healthy": False, "error": str(e)}
        
        # Check integrations (simplified ping)
        integrations = {
            "hubspot": self.hubspot,
            "gong": self.gong,
            "slack": self.slack,
            "apollo": self.apollo,
            "phantom_buster": self.phantom_buster
        }
        
        for name, connector in integrations.items():
            health_details[name] = {
                "healthy": connector is not None,
                "initialized": connector is not None
            }
        
        return health_details
    
    async def self_heal(self):
        """Attempt to restore failed connections."""
        try:
            await self.on_start()
            print("✅ Self-healing completed")
        except Exception as e:
            print(f"❌ Self-healing failed: {e}")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available sales intelligence tools."""
        return [
            {
                "name": "get_sales_pipeline",
                "description": "Get current sales pipeline from Hubspot with deal analysis",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "stage_filter": {"type": "string", "description": "Filter by deal stage"},
                        "limit": {"type": "integer", "default": 50, "description": "Max deals to return"}
                    }
                }
            },
            {
                "name": "analyze_call_performance",
                "description": "Analyze call performance and employee metrics from Gong",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "employee_id": {"type": "string", "description": "Specific employee to analyze"},
                        "days_back": {"type": "integer", "default": 7, "description": "Days to look back"}
                    }
                }
            },
            {
                "name": "get_client_health_score",
                "description": "Calculate client health scores based on engagement data",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "client_id": {"type": "string", "description": "Specific client to analyze"},
                        "include_predictions": {"type": "boolean", "default": True}
                    }
                }
            },
            {
                "name": "generate_lead_intelligence",
                "description": "Generate leads using Apollo and enrich with additional data",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "search_criteria": {
                            "type": "object",
                            "properties": {
                                "keywords": {"type": "string"},
                                "industry": {"type": "string"},
                                "company_size": {"type": "string"}
                            }
                        },
                        "limit": {"type": "integer", "default": 25}
                    },
                    "required": ["search_criteria"]
                }
            },
            {
                "name": "send_performance_alert",
                "description": "Send performance alerts to Slack channel",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "alert_type": {
                            "type": "string",
                            "enum": ["low_performance", "high_performance", "deal_risk", "client_churn"]
                        },
                        "message": {"type": "string"},
                        "priority": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"}
                    },
                    "required": ["alert_type", "message"]
                }
            },
            {
                "name": "launch_data_collection",
                "description": "Launch Phantom Buster agent for data collection",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "collection_type": {
                            "type": "string",
                            "enum": ["linkedin_contacts", "company_data", "social_media", "email_finder"]
                        },
                        "target_criteria": {"type": "object"},
                        "agent_config": {"type": "object"}
                    },
                    "required": ["collection_type"]
                }
            }
        ]
    
    async def call_tool(self, name: str, arguments: dict) -> str:
        """Execute sales intelligence tools."""
        try:
            if name == "get_sales_pipeline":
                return await self._get_sales_pipeline(**arguments)
            elif name == "analyze_call_performance":
                return await self._analyze_call_performance(**arguments)
            elif name == "get_client_health_score":
                return await self._get_client_health_score(**arguments)
            elif name == "generate_lead_intelligence":
                return await self._generate_lead_intelligence(**arguments)
            elif name == "send_performance_alert":
                return await self._send_performance_alert(**arguments)
            elif name == "launch_data_collection":
                return await self._launch_data_collection(**arguments)
            else:
                return f"Unknown tool: {name}"
                
        except Exception as e:
            return f"Error executing {name}: {str(e)}"
    
    async def _get_sales_pipeline(self, stage_filter: str = None, limit: int = 50) -> str:
        """Get and analyze sales pipeline data."""
        cache_key = f"pipeline:{stage_filter}:{limit}"
        
        # Check cache first
        cached = await self.redis_client.get(cache_key)
        if cached:
            return f"🔄 [CACHED] {cached}"
        
        deals = await self.hubspot.get_deals(limit)
        
        # Filter by stage if specified
        if stage_filter:
            deals = [d for d in deals if stage_filter.lower() in 
                    d.get("properties", {}).get("dealstage", "").lower()]
        
        # Calculate pipeline metrics
        total_value = sum(float(d.get("properties", {}).get("amount", 0) or 0) for d in deals)
        deal_count = len(deals)
        avg_deal_size = total_value / deal_count if deal_count > 0 else 0
        
        # Stage distribution
        stages = {}
        for deal in deals:
            stage = deal.get("properties", {}).get("dealstage", "Unknown")
            stages[stage] = stages.get(stage, 0) + 1
        
        result = f"""
📊 **Sales Pipeline Analysis**
━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 **Summary:**
• Total Deals: {deal_count}
• Pipeline Value: ${total_value:,.2f}
• Average Deal Size: ${avg_deal_size:,.2f}

📈 **Stage Distribution:**
{chr(10).join(f"• {stage}: {count} deals" for stage, count in stages.items())}

🕐 Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
        """
        
        # Cache for 5 minutes
        await self.redis_client.setex(cache_key, self.cache_ttl, result)
        
        return result
    
    async def _analyze_call_performance(self, employee_id: str = None, days_back: int = 7) -> str:
        """Analyze call performance metrics."""
        cache_key = f"call_performance:{employee_id}:{days_back}"
        
        cached = await self.redis_client.get(cache_key)
        if cached:
            return f"🔄 [CACHED] {cached}"
        
        from_date = datetime.utcnow() - timedelta(days=days_back)
        calls = await self.gong.get_calls(from_date, limit=100)
        
        if employee_id:
            # Filter calls for specific employee
            calls = [c for c in calls if c.get("primaryUserId") == employee_id]
        
        # Calculate metrics
        total_calls = len(calls)
        total_duration = sum(c.get("duration", 0) for c in calls)
        avg_duration = total_duration / total_calls if total_calls > 0 else 0
        
        # Employee performance breakdown
        employee_stats = {}
        for call in calls:
            emp_id = call.get("primaryUserId", "Unknown")
            if emp_id not in employee_stats:
                employee_stats[emp_id] = {"calls": 0, "duration": 0}
            employee_stats[emp_id]["calls"] += 1
            employee_stats[emp_id]["duration"] += call.get("duration", 0)
        
        result = f"""
📞 **Call Performance Analysis** ({days_back} days)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 **Overall Metrics:**
• Total Calls: {total_calls}
• Total Talk Time: {total_duration/60:.1f} minutes
• Average Call Duration: {avg_duration/60:.1f} minutes

👥 **Employee Performance:**
{chr(10).join(f"• {emp_id}: {stats['calls']} calls, {stats['duration']/60:.1f} min" for emp_id, stats in employee_stats.items())}

🕐 Analysis Period: {from_date.strftime('%Y-%m-%d')} to {datetime.utcnow().strftime('%Y-%m-%d')}
        """
        
        await self.redis_client.setex(cache_key, self.cache_ttl, result)
        return result
    
    async def _get_client_health_score(self, client_id: str = None, include_predictions: bool = True) -> str:
        """Calculate client health scores."""
        # This is a simplified version - in production you'd have more sophisticated scoring
        contacts = await self.hubspot.get_contacts(limit=100)
        
        if client_id:
            contacts = [c for c in contacts if c.get("id") == client_id]
        
        health_scores = []
        for contact in contacts:
            props = contact.get("properties", {})
            
            # Simple health scoring algorithm
            score = 100  # Start with perfect score
            
            # Deduct points based on lifecycle stage
            lifecycle = props.get("lifecyclestage", "").lower()
            if "customer" in lifecycle:
                score += 20  # Existing customers are valuable
            elif "lead" in lifecycle:
                score -= 10  # Leads need nurturing
            elif "subscriber" in lifecycle:
                score -= 30  # Low engagement
            
            # Add some randomness for demonstration (replace with real metrics)
            import random
            score += random.randint(-20, 20)
            score = max(0, min(100, score))  # Keep in 0-100 range
            
            health_scores.append({
                "client_id": contact.get("id"),
                "name": f"{props.get('firstname', '')} {props.get('lastname', '')}".strip(),
                "company": props.get("company", "Unknown"),
                "health_score": score,
                "risk_level": "Low" if score > 70 else "Medium" if score > 40 else "High"
            })
        
        # Sort by health score (lowest first - most at risk)
        health_scores.sort(key=lambda x: x["health_score"])
        
        result = f"""
🏥 **Client Health Analysis**
━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 **Health Score Distribution:**
• High Risk (0-40): {len([s for s in health_scores if s['health_score'] <= 40])} clients
• Medium Risk (41-70): {len([s for s in health_scores if 41 <= s['health_score'] <= 70])} clients  
• Low Risk (71-100): {len([s for s in health_scores if s['health_score'] > 70])} clients

🚨 **Top 5 At-Risk Clients:**
{chr(10).join(f"• {s['name']} ({s['company']}): {s['health_score']}/100 - {s['risk_level']} Risk" for s in health_scores[:5])}

🕐 Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
        """
        
        return result
    
    async def _generate_lead_intelligence(self, search_criteria: dict, limit: int = 25) -> str:
        """Generate and enrich leads using Apollo."""
        leads = await self.apollo.search_people(search_criteria, limit)
        
        # Enrich leads with additional intelligence
        enriched_leads = []
        for lead in leads[:10]:  # Limit to first 10 for demo
            company_domain = lead.get("organization", {}).get("website_url", "")
            company_info = {}
            
            if company_domain:
                try:
                    company_info = await self.apollo.get_account_info(company_domain)
                except:
                    pass  # Continue if enrichment fails
            
            enriched_leads.append({
                "name": f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip(),
                "title": lead.get("title", "Unknown"),
                "company": lead.get("organization", {}).get("name", "Unknown"),
                "email": lead.get("email", "Not available"),
                "linkedin": lead.get("linkedin_url", ""),
                "company_size": company_info.get("estimated_num_employees", "Unknown"),
                "industry": company_info.get("industry", "Unknown")
            })
        
        result = f"""
🎯 **Lead Intelligence Report**
━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 **Search Criteria:** {json.dumps(search_criteria, indent=2)}
📊 **Results:** {len(leads)} total leads found, showing top {len(enriched_leads)}

🚀 **Qualified Leads:**
{chr(10).join(f'''• {lead['name']} - {lead['title']}
  Company: {lead['company']} ({lead['company_size']} employees)
  Industry: {lead['industry']}
  Email: {lead['email']}''' for lead in enriched_leads)}

🕐 Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
        """
        
        return result
    
    async def _send_performance_alert(self, alert_type: str, message: str, priority: str = "medium") -> str:
        """Send performance alerts to Slack."""
        channel_id = os.getenv("SLACK_CHANNEL_ID", "general")
        
        # Format alert with emojis based on type and priority
        emoji_map = {
            "low_performance": "🔴",
            "high_performance": "🟢", 
            "deal_risk": "⚠️",
            "client_churn": "🚨"
        }
        
        priority_emoji = {"low": "🔵", "medium": "🟡", "high": "🔴"}
        
        formatted_message = f"{emoji_map.get(alert_type, '📢')} {priority_emoji.get(priority, '🟡')} **{alert_type.replace('_', ' ').title()}**\n\n{message}\n\n_Sent: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC_"
        
        success = await self.slack.post_notification(channel_id, formatted_message)
        
        if success:
            return f"✅ Alert sent successfully to Slack channel: {channel_id}"
        else:
            return f"❌ Failed to send alert to Slack channel: {channel_id}"
    
    async def _launch_data_collection(self, collection_type: str, target_criteria: dict = None, agent_config: dict = None) -> str:
        """Launch Phantom Buster data collection."""
        agents = await self.phantom_buster.get_agents()
        
        # Find appropriate agent based on collection type
        agent_mapping = {
            "linkedin_contacts": "LinkedIn Network Booster",
            "company_data": "LinkedIn Company Employees",
            "social_media": "Social Media Profile Scraper",
            "email_finder": "Email Finder"
        }
        
        target_agent_name = agent_mapping.get(collection_type, "")
        suitable_agent = None
        
        for agent in agents:
            if target_agent_name.lower() in agent.get("name", "").lower():
                suitable_agent = agent
                break
        
        if not suitable_agent:
            return f"❌ No suitable agent found for collection type: {collection_type}"
        
        # Launch the agent
        container_id = await self.phantom_buster.launch_agent(
            suitable_agent["id"], 
            agent_config or {}
        )
        
        result = f"""
🤖 **Data Collection Launched**
━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 **Collection Type:** {collection_type}
🔧 **Agent Used:** {suitable_agent.get('name', 'Unknown')}
🆔 **Container ID:** {container_id}
📋 **Target Criteria:** {json.dumps(target_criteria or {}, indent=2)}

⏳ **Status:** Collection started - check Phantom Buster dashboard for progress
🕐 **Launched:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
        """
        
        return result


# Startup function for production deployment
async def create_server() -> PayReadySophiaMCPServer:
    """Create and initialize the Pay Ready/Sophia MCP server."""
    server = PayReadySophiaMCPServer()
    await server.start()
    return server


if __name__ == "__main__":
    # Development/testing entry point
    async def main():
        server = await create_server()
        
        print("🚀 Pay Ready/Sophia MCP Server running...")
        print("📊 Available tools:")
        tools = await server.list_tools()
        for tool in tools:
            print(f"  • {tool['name']}: {tool['description']}")
        
        # Keep server running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️ Shutting down...")
            await server.stop()
    
    asyncio.run(main()) 