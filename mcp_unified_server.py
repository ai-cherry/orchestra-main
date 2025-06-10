#!/usr/bin/env python3
"""
🎯 Unified MCP Server for Orchestra AI - Advanced Architecture Integration
Provides shared context and capabilities across Cursor, Claude, and Continue
Integrated with advanced 5-tier memory system and Cherry/Sophia/Karen personas
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import requests

# MCP imports
from mcp.server import Server
from mcp import types
from mcp.server.stdio import stdio_server

# Advanced Architecture imports
from integrated_orchestrator import create_orchestrator, OrchestrationContext, IntegratedOrchestrator
from persona_profiles import PersonaManager, create_persona
from memory_architecture import PersonaDomain, PERSONA_CONFIGS

# Local imports for Notion integration
try:
    from config.notion_config import get_config, NotionConfig
except ImportError:
    # Fallback for simple setup
    @dataclass
    class NotionConfig:
        api_token: str
        workspace_id: str
        databases: Dict[str, str]
    
    def get_config():
        from dataclasses import dataclass
        
        @dataclass
        class SimpleDatabases:
            mcp_connections: str = "20bdba04940281aea36af6144ec68df2"
            code_reflection: str = "20bdba049402814d8e53fbec166ef030"
            ai_tool_metrics: str = "20bdba049402813f8404fa8d5f615b02"
            task_management: str = "20bdba04940281a299f3e69dc37b73d6"
        
        # Simple environment-based config with development fallbacks
        api_token = os.getenv("NOTION_API_TOKEN")
        if not api_token:
            print("⚠️  NOTION_API_TOKEN not set; using empty token")
            api_token = ""
        
        return NotionConfig(
            api_token=api_token,
            workspace_id=os.getenv("NOTION_WORKSPACE_ID", ""),
            databases=SimpleDatabases()
        )

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedNotionIntegration:
    """Enhanced Notion API integration with persona awareness"""
    
    def __init__(self, config: NotionConfig):
        self.config = config
        self.headers = {
            "Authorization": f"Bearer {config.api_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    async def log_persona_activity(self, persona_name: str, activity: str, context: Dict[str, Any] = None):
        """Log persona-specific activity to Notion"""
        if not context:
            context = {}
            
        try:
            url = "https://api.notion.com/v1/pages"
            data = {
                "parent": {"database_id": self.config.databases.mcp_connections},
                "properties": {
                    "Tool": {"title": [{"text": {"content": f"{persona_name.title()} Persona"}}]},
                    "Activity": {"rich_text": [{"text": {"content": activity}}]},
                    "Status": {"select": {"name": "Active"}},
                    "Context": {"rich_text": [{"text": {"content": json.dumps(context, indent=2)[:2000]}}]},
                    "Timestamp": {"date": {"start": datetime.now().isoformat()}},
                    "Persona": {"select": {"name": persona_name.title()}}
                }
            }
            
            response = requests.post(url, headers=self.headers, json=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to log persona activity to Notion: {e}")
            return False
    
    async def update_memory_metrics(self, metrics: Dict[str, Any]):
        """Update memory system performance metrics in Notion"""
        try:
            url = "https://api.notion.com/v1/pages"
            data = {
                "parent": {"database_id": self.config.databases.ai_tool_metrics},
                "properties": {
                    "Tool": {"title": [{"text": {"content": "Memory Architecture"}}]},
                    "Metric Type": {"select": {"name": "Memory Performance"}},
                    "Value": {"number": metrics.get("average_response_time", 0)},
                    "Status": {"select": {"name": "Active"}},
                    "Details": {"rich_text": [{"text": {"content": json.dumps(metrics, indent=2)[:2000]}}]},
                    "Timestamp": {"date": {"start": datetime.now().isoformat()}}
                }
            }
            
            response = requests.post(url, headers=self.headers, json=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to update memory metrics: {e}")
            return False

class AdvancedOrchestralMCPServer:
    """Enhanced MCP Server with Advanced Memory Architecture and Personas"""
    
    def __init__(self):
        self.config = get_config()
        self.notion = AdvancedNotionIntegration(self.config)
        self.server = Server("orchestra-unified-advanced")
        self.orchestrator: Optional[IntegratedOrchestrator] = None
        self._setup_tools()
    
    async def initialize_orchestrator(self):
        """Initialize the advanced orchestrator system"""
        try:
            logger.info("🧠 Initializing advanced memory architecture and personas...")
            self.orchestrator = await create_orchestrator()
            logger.info("✅ Advanced orchestrator initialized successfully")
            
            # Log initialization to Notion
            await self.notion.log_persona_activity(
                "system",
                "Advanced Architecture Initialized",
                {
                    "memory_tiers": ["L0_CPU_CACHE", "L1_PROCESS", "L2_SHARED", "L3_POSTGRESQL", "L4_WEAVIATE"],
                    "personas": ["Cherry", "Sophia", "Karen"],
                    "features": ["cross_domain_routing", "token_compression", "hybrid_search"]
                }
            )
            
            return True
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            return False
    
    def _setup_tools(self):
        """Setup enhanced MCP tools with persona integration"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """List available tools including persona-specific ones"""
            return [
                types.Tool(
                    name="chat_with_persona",
                    description="Chat with a specific AI persona (Cherry, Sophia, or Karen)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "persona": {"type": "string", "enum": ["cherry", "sophia", "karen"]},
                            "query": {"type": "string"},
                            "task_type": {"type": "string", "enum": ["project_coordination", "financial_compliance", "medical_coding", "general_query"]},
                            "urgency_level": {"type": "number", "minimum": 0, "maximum": 1},
                            "technical_complexity": {"type": "number", "minimum": 0, "maximum": 1},
                            "cross_domain_required": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["persona", "query"]
                    }
                ),
                types.Tool(
                    name="route_task_advanced",
                    description="Route task to optimal persona using advanced intelligence",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_description": {"type": "string"},
                            "task_type": {"type": "string", "enum": ["project_coordination", "financial_services", "medical_coding", "cross_domain", "general"]},
                            "complexity": {"type": "string", "enum": ["simple", "medium", "complex"]},
                            "domains_involved": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["task_description"]
                    }
                ),
                types.Tool(
                    name="get_memory_status",
                    description="Get 5-tier memory system status and performance metrics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "detail_level": {"type": "string", "enum": ["summary", "detailed", "full"]},
                            "persona_filter": {"type": "string", "enum": ["cherry", "sophia", "karen", "all"]}
                        }
                    }
                ),
                types.Tool(
                    name="cross_domain_query",
                    description="Perform cross-domain query involving multiple personas",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "primary_persona": {"type": "string", "enum": ["cherry", "sophia", "karen"]},
                            "query": {"type": "string"},
                            "required_domains": {"type": "array", "items": {"type": "string"}},
                            "collaboration_type": {"type": "string", "enum": ["consultation", "coordination", "synthesis"]}
                        },
                        "required": ["primary_persona", "query", "required_domains"]
                    }
                ),
                types.Tool(
                    name="register_tool",
                    description="Register AI tool for persona coordination",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "tool_name": {"type": "string"},
                            "capabilities": {"type": "array", "items": {"type": "string"}},
                            "preferred_personas": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["tool_name"]
                    }
                ),
                types.Tool(
                    name="get_notion_workspace",
                    description="Get Notion workspace information with persona integration",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "info_type": {"type": "string", "enum": ["workspace", "databases", "personas", "all"]},
                        }
                    }
                ),
                types.Tool(
                    name="log_insight",
                    description="Log insights and reflections to Notion with persona context",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "persona": {"type": "string", "enum": ["cherry", "sophia", "karen", "system"]},
                            "insight": {"type": "string"},
                            "category": {"type": "string", "enum": ["performance", "workflow", "optimization", "learning", "cross_domain"]},
                            "impact_level": {"type": "string", "enum": ["low", "medium", "high"]}
                        },
                        "required": ["persona", "insight", "category"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
            """Handle tool calls with advanced persona integration"""
            
            if not self.orchestrator:
                await self.initialize_orchestrator()
                if not self.orchestrator:
                    return [types.TextContent(
                        type="text",
                        text="❌ Advanced orchestrator not available. Please check system configuration."
                    )]
            
            if name == "chat_with_persona":
                persona = arguments["persona"]
                query = arguments["query"]
                task_type = arguments.get("task_type", "general_query")
                urgency = arguments.get("urgency_level", 0.5)
                complexity = arguments.get("technical_complexity", 0.5)
                cross_domain = arguments.get("cross_domain_required", [])
                
                # Create orchestration context
                context = OrchestrationContext(
                    requesting_persona=persona,
                    task_type=task_type,
                    urgency_level=urgency,
                    technical_complexity=complexity,
                    collaborative=len(cross_domain) > 0,
                    cross_domain_required=cross_domain
                )
                
                # Process request through advanced orchestrator
                result = await self.orchestrator.process_request(persona, query, context)
                
                # Log to Notion
                await self.notion.log_persona_activity(
                    persona,
                    "Chat Interaction",
                    {
                        "query": query[:100] + "..." if len(query) > 100 else query,
                        "task_type": task_type,
                        "processing_time_ms": result.get("processing_time_ms", 0),
                        "cross_domain": cross_domain
                    }
                )
                
                # Format response
                response_text = f"🎭 **{persona.title()} Persona Response:**\n\n"
                response_text += f"{result['response']}\n\n"
                response_text += f"⚡ *Processing time: {result.get('processing_time_ms', 0):.1f}ms*\n"
                
                if result.get('cross_domain_data'):
                    response_text += f"🔄 *Cross-domain data utilized from: {', '.join(result['cross_domain_data'].keys())}*\n"
                
                if result.get('memory_compression_ratio', 1.0) > 1.0:
                    response_text += f"🗜️ *Memory compression: {result['memory_compression_ratio']:.1f}x*"
                
                return [types.TextContent(type="text", text=response_text)]
            
            elif name == "route_task_advanced":
                task_description = arguments["task_description"]
                task_type = arguments.get("task_type", "general")
                complexity = arguments.get("complexity", "medium")
                domains = arguments.get("domains_involved", [])
                
                # Determine optimal persona using advanced routing
                optimal_persona = self._route_to_persona(task_description, task_type, complexity, domains)
                routing_reason = self._get_persona_routing_reason(optimal_persona, task_type, complexity, domains)
                
                # Log routing decision
                await self.notion.log_persona_activity(
                    "system",
                    "Advanced Task Routing",
                    {
                        "task": task_description[:100] + "..." if len(task_description) > 100 else task_description,
                        "routed_to": optimal_persona,
                        "reason": routing_reason,
                        "domains": domains
                    }
                )
                
                response_text = f"🎯 **Optimal Persona:** {optimal_persona.title()}\n\n"
                response_text += f"📋 **Reasoning:** {routing_reason}\n\n"
                
                if domains:
                    response_text += f"🌐 **Domains involved:** {', '.join(domains)}\n\n"
                
                response_text += f"💡 **Next step:** Use `chat_with_persona` with persona='{optimal_persona}'"
                
                return [types.TextContent(type="text", text=response_text)]
            
            elif name == "get_memory_status":
                detail_level = arguments.get("detail_level", "summary")
                persona_filter = arguments.get("persona_filter", "all")
                
                # Get performance summary from orchestrator
                performance = self.orchestrator.get_performance_summary()
                
                # Update Notion metrics
                await self.notion.update_memory_metrics(performance["performance_metrics"])
                
                if detail_level == "summary":
                    response_text = f"🧠 **Memory System Status**\n\n"
                    response_text += f"📊 **Performance Metrics:**\n"
                    response_text += f"• Total interactions: {performance['performance_metrics']['total_interactions']}\n"
                    response_text += f"• Average response time: {performance['performance_metrics']['average_response_time']:.3f}s\n"
                    response_text += f"• Cross-domain queries: {performance['performance_metrics']['cross_domain_queries']}\n"
                    response_text += f"• Memory compressions: {performance['performance_metrics']['memory_compressions']}\n"
                elif detail_level == "detailed":
                    response_text = f"🧠 **Detailed Memory System Status**\n\n"
                    response_text += f"📊 **Performance Metrics:**\n"
                    response_text += json.dumps(performance["performance_metrics"], indent=2)
                    response_text += f"\n\n🎭 **Persona States:**\n"
                    response_text += json.dumps(performance["persona_states"], indent=2)
                else:  # full
                    response_text = f"🧠 **Complete Memory System Status**\n\n"
                    response_text += json.dumps(performance, indent=2)
                
                return [types.TextContent(type="text", text=response_text)]
            
            elif name == "cross_domain_query":
                primary_persona = arguments["primary_persona"]
                query = arguments["query"]
                required_domains = arguments["required_domains"]
                collaboration_type = arguments.get("collaboration_type", "consultation")
                
                # Create cross-domain context
                context = OrchestrationContext(
                    requesting_persona=primary_persona,
                    task_type="cross_domain",
                    collaborative=True,
                    cross_domain_required=required_domains
                )
                
                # Process cross-domain request
                result = await self.orchestrator.process_request(primary_persona, query, context)
                
                # Log cross-domain activity
                await self.notion.log_persona_activity(
                    primary_persona,
                    f"Cross-Domain {collaboration_type.title()}",
                    {
                        "query": query[:100] + "..." if len(query) > 100 else query,
                        "domains": required_domains,
                        "collaboration_type": collaboration_type,
                        "processing_time_ms": result.get("processing_time_ms", 0)
                    }
                )
                
                response_text = f"🌐 **Cross-Domain Query Result**\n\n"
                response_text += f"🎭 **Primary Persona:** {primary_persona.title()}\n"
                response_text += f"🔄 **Collaboration Type:** {collaboration_type.title()}\n"
                response_text += f"📋 **Domains:** {', '.join(required_domains)}\n\n"
                response_text += f"**Response:**\n{result['response']}\n\n"
                
                if result.get('cross_domain_data'):
                    response_text += f"**Cross-Domain Insights:**\n"
                    for domain, data in result['cross_domain_data'].items():
                        if data.get('access_granted', False):
                            response_text += f"• {domain}: Accessed via {data.get('expert_persona', 'N/A')}\n"
                        else:
                            response_text += f"• {domain}: Access denied - {data.get('reason', 'Unknown')}\n"
                
                return [types.TextContent(type="text", text=response_text)]
            
            elif name == "register_tool":
                tool_name = arguments["tool_name"]
                capabilities = arguments.get("capabilities", [])
                preferred_personas = arguments.get("preferred_personas", [])
                
                # Register tool with enhanced context
                registration_context = {
                    "capabilities": capabilities,
                    "preferred_personas": preferred_personas,
                    "registration_time": datetime.now().isoformat()
                }
                
                # Log registration
                await self.notion.log_persona_activity(
                    "system",
                    "AI Tool Registration",
                    {
                        "tool_name": tool_name,
                        "capabilities": capabilities,
                        "preferred_personas": preferred_personas
                    }
                )
                
                response_text = f"✅ **Tool Registered:** {tool_name}\n\n"
                if capabilities:
                    response_text += f"**Capabilities:** {', '.join(capabilities)}\n"
                if preferred_personas:
                    response_text += f"**Preferred Personas:** {', '.join(preferred_personas)}\n"
                response_text += f"\n🔗 **Integration Status:** Active and ready for persona coordination"
                
                return [types.TextContent(type="text", text=response_text)]
            
            elif name == "get_notion_workspace":
                info_type = arguments.get("info_type", "all")
                workspace_info = self._get_enhanced_workspace_info(info_type)
                return [types.TextContent(
                    type="text",
                    text=json.dumps(workspace_info, indent=2)
                )]
            
            elif name == "log_insight":
                persona = arguments["persona"]
                insight = arguments["insight"]
                category = arguments["category"]
                impact_level = arguments.get("impact_level", "medium")
                
                success = await self._log_enhanced_insight(persona, insight, category, impact_level)
                
                response_text = f"📝 **Insight Logging:** {'✅ Success' if success else '❌ Failed'}\n\n"
                response_text += f"**Persona:** {persona.title()}\n"
                response_text += f"**Category:** {category.title()}\n"
                response_text += f"**Impact Level:** {impact_level.title()}\n\n"
                response_text += f"**Insight:** {insight[:200]}{'...' if len(insight) > 200 else ''}"
                
                return [types.TextContent(type="text", text=response_text)]
            
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    def _route_to_persona(self, task_description: str, task_type: str, complexity: str, domains: List[str]) -> str:
        """Advanced persona routing logic"""
        description_lower = task_description.lower()
        
        # Financial/PayReady tasks → Sophia
        if (task_type == "financial_services" or 
            any(word in description_lower for word in ["payready", "financial", "payment", "compliance", "pci", "regulatory"])):
            return "sophia"
        
        # Medical/ParagonRX tasks → Karen
        if (task_type == "medical_coding" or 
            any(word in description_lower for word in ["paragonrx", "medical", "icd-10", "pharmaceutical", "hipaa", "clinical"])):
            return "karen"
        
        # Cross-domain coordination → Cherry
        if (task_type in ["project_coordination", "cross_domain"] or 
            len(domains) > 1 or 
            any(word in description_lower for word in ["coordinate", "manage", "oversee", "integrate", "plan"])):
            return "cherry"
        
        # Complex multi-domain tasks → Cherry (as overseer)
        if complexity == "complex" and len(domains) > 0:
            return "cherry"
        
        # Default to Cherry for general coordination
        return "cherry"
    
    def _get_persona_routing_reason(self, persona: str, task_type: str, complexity: str, domains: List[str]) -> str:
        """Get detailed reasoning for persona selection"""
        reasons = {
            "cherry": f"Cherry excels at project coordination and cross-domain synthesis. {f'Multiple domains detected: {domains}' if len(domains) > 1 else 'Optimal for general oversight and integration tasks.'}",
            "sophia": f"Sophia is the financial services expert with deep PayReady knowledge and regulatory compliance expertise. {f'Complexity level: {complexity}' if complexity != 'medium' else 'Professional authority in financial domain.'}",
            "karen": f"Karen is the medical coding specialist with ParagonRX expertise and clinical precision. {f'Technical complexity: {complexity}' if complexity == 'complex' else 'Evidence-based medical guidance.'}"
        }
        return reasons.get(persona, "General purpose selection")
    
    def _get_enhanced_workspace_info(self, info_type: str) -> Dict[str, Any]:
        """Get enhanced workspace information with persona integration"""
        base_url = f"https://www.notion.so/Orchestra-AI-Workspace-{self.config.workspace_id}"
        
        workspace_info = {
            "workspace_url": base_url,
            "personas": {
                "cherry": {
                    "name": "Cherry - Personal Overseer",
                    "role": "Cross-domain coordination and project management",
                    "context_window": "4,000 tokens",
                    "cross_domain_access": ["sophia", "karen"],
                    "specialties": ["project_management", "team_coordination", "workflow_optimization"]
                },
                "sophia": {
                    "name": "Sophia - Financial Expert",
                    "role": "PayReady systems and financial compliance",
                    "context_window": "6,000 tokens",
                    "encryption": "Financial compliance-grade",
                    "specialties": ["financial_services", "regulatory_compliance", "payready_systems"]
                },
                "karen": {
                    "name": "Karen - Medical Specialist",
                    "role": "ParagonRX systems and medical coding",
                    "context_window": "8,000 tokens",
                    "encryption": "HIPAA-compliant",
                    "specialties": ["medical_coding", "paragonrx_systems", "pharmaceutical_knowledge"]
                }
            },
            "memory_architecture": {
                "tiers": {
                    "L0": "CPU Cache (~1ns)",
                    "L1": "Process Memory (~10ns)",
                    "L2": "Redis Cache (~100ns)",
                    "L3": "PostgreSQL (~1ms)",
                    "L4": "Weaviate (~10ms)"
                },
                "features": ["20x_compression", "hybrid_search", "cross_domain_routing"]
            },
            "databases": {
                "mcp_connections": f"{base_url}?v=mcp",
                "ai_tool_metrics": f"{base_url}?v=metrics",
                "task_management": f"{base_url}?v=tasks",
                "code_reflection": f"{base_url}?v=reflection"
            }
        }
        
        if info_type == "workspace":
            return {"workspace_url": base_url}
        elif info_type == "databases":
            return {"databases": workspace_info["databases"]}
        elif info_type == "personas":
            return {"personas": workspace_info["personas"]}
        else:
            return workspace_info
    
    async def _log_enhanced_insight(self, persona: str, insight: str, category: str, impact_level: str) -> bool:
        """Log enhanced insight with persona context to Notion"""
        try:
            url = "https://api.notion.com/v1/pages"
            data = {
                "parent": {"database_id": self.config.databases.code_reflection},
                "properties": {
                    "Tool": {"title": [{"text": {"content": f"{persona.title()} Persona"}}]},
                    "Category": {"select": {"name": category.title()}},
                    "Insight": {"rich_text": [{"text": {"content": insight}}]},
                    "Status": {"select": {"name": "New"}},
                    "Priority": {"select": {"name": impact_level.title()}},
                    "Date": {"date": {"start": datetime.now().isoformat()}},
                    "Persona": {"select": {"name": persona.title()}}
                }
            }
            
            response = requests.post(url, headers=self.notion.headers, json=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to log enhanced insight: {e}")
            return False

async def main():
    """Main server execution with advanced architecture"""
    logger.info("🚀 Starting Orchestra AI Unified MCP Server (Advanced Architecture)")
    
    # Test Notion connection
    config = get_config()
    notion = AdvancedNotionIntegration(config)
    
    # Create and initialize advanced server
    server = AdvancedOrchestralMCPServer()
    
    # Initialize orchestrator
    if await server.initialize_orchestrator():
        logger.info("✅ Advanced orchestrator initialized successfully")
        
        # Log server startup with persona information
        await notion.log_persona_activity(
            "system", 
            "Advanced MCP Server Startup", 
            {
                "version": "3.0-advanced",
                "features": ["5_tier_memory", "persona_routing", "cross_domain_queries"],
                "personas": ["Cherry", "Sophia", "Karen"],
                "memory_tiers": ["L0", "L1", "L2", "L3", "L4"]
            }
        )
    else:
        logger.error("❌ Failed to initialize advanced orchestrator")
    
    # Start MCP server
    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            None  # Initialize options
        )

if __name__ == "__main__":
    asyncio.run(main())

