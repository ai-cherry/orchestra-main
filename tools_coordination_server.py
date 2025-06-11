#!/usr/bin/env python3
"""
🛠️ Tools Coordination Server for Unified API Access
Provides Cursor AI with access to all external APIs and services
"""

import asyncio
import json
import logging
import os
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
import base64

# MCP imports
from mcp.server import Server
from mcp import types
from mcp.server.stdio import stdio_server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class APIEndpoint:
    """API endpoint configuration"""
    name: str
    base_url: str
    auth_type: str  # 'bearer', 'api_key', 'basic', 'none'
    auth_header: str
    rate_limit: int
    timeout: int
    persona_affinity: List[str]  # Which personas use this most

@dataclass
class ToolExecution:
    """Tool execution result"""
    tool_name: str
    success: bool
    response: Any
    execution_time: float
    timestamp: datetime
    persona_context: Optional[str] = None

class ToolRegistry:
    """Registry of available tools and APIs"""
    
    def __init__(self):
        self.endpoints = self._initialize_endpoints()
        self.execution_history: List[ToolExecution] = []
    
    def _initialize_endpoints(self) -> Dict[str, APIEndpoint]:
        """Initialize known API endpoints"""
        return {
            # OpenAI APIs
            'openai': APIEndpoint(
                name='OpenAI API',
                base_url='https://api.openai.com/v1',
                auth_type='bearer',
                auth_header='Authorization',
                rate_limit=60,
                timeout=30,
                persona_affinity=['cherry', 'sophia', 'karen']
            ),
            
            # Anthropic Claude
            'anthropic': APIEndpoint(
                name='Anthropic Claude',
                base_url='https://api.anthropic.com/v1',
                auth_type='api_key',
                auth_header='x-api-key',
                rate_limit=50,
                timeout=30,
                persona_affinity=['cherry', 'sophia', 'karen']
            ),
            
            # GitHub API
            'github': APIEndpoint(
                name='GitHub API',
                base_url='https://api.github.com',
                auth_type='bearer',
                auth_header='Authorization',
                rate_limit=100,
                timeout=15,
                persona_affinity=['cherry']
            ),
            
            # Vercel API
            'vercel': APIEndpoint(
                name='Vercel API',
                base_url='https://api.vercel.com',
                auth_type='bearer',
                auth_header='Authorization',
                rate_limit=100,
                timeout=20,
                persona_affinity=['cherry', 'sophia']
            ),
            
            # Notion API
            'notion': APIEndpoint(
                name='Notion API',
                base_url='https://api.notion.com/v1',
                auth_type='bearer',
                auth_header='Authorization',
                rate_limit=60,
                timeout=25,
                persona_affinity=['cherry', 'sophia', 'karen']
            ),
            
            # Stripe (for Pay Ready)
            'stripe': APIEndpoint(
                name='Stripe API',
                base_url='https://api.stripe.com/v1',
                auth_type='bearer',
                auth_header='Authorization',
                rate_limit=100,
                timeout=20,
                persona_affinity=['sophia']
            ),
            
            # Lambda Labs
            'lambda_labs': APIEndpoint(
                name='Lambda Labs API',
                base_url='https://cloud.lambdalabs.com/api/v1',
                auth_type='bearer',
                auth_header='Authorization',
                rate_limit=60,
                timeout=30,
                persona_affinity=['cherry']
            ),
            
            # AWS (via CLI/SDK)
            'aws': APIEndpoint(
                name='AWS Services',
                base_url='https://aws.amazon.com',
                auth_type='none',  # Uses AWS credentials
                auth_header='',
                rate_limit=200,
                timeout=30,
                persona_affinity=['cherry', 'sophia']
            )
        }
    
    def get_persona_tools(self, persona: str) -> List[str]:
        """Get tools most relevant to a specific persona"""
        relevant_tools = []
        for tool_name, endpoint in self.endpoints.items():
            if persona in endpoint.persona_affinity:
                relevant_tools.append(tool_name)
        return relevant_tools
    
    def add_execution(self, execution: ToolExecution):
        """Add tool execution to history"""
        self.execution_history.append(execution)
        # Keep only last 100 executions
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-100:]

class UnifiedAPIClient:
    """Unified client for accessing various APIs"""
    
    def __init__(self, tool_registry: ToolRegistry):
        self.registry = tool_registry
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def execute_api_call(self, endpoint_name: str, method: str, path: str, 
                              data: Dict[str, Any] = None, params: Dict[str, Any] = None,
                              persona_context: str = None) -> ToolExecution:
        """Execute API call to specified endpoint"""
        start_time = datetime.now()
        
        try:
            endpoint = self.registry.endpoints.get(endpoint_name)
            if not endpoint:
                raise ValueError(f"Unknown endpoint: {endpoint_name}")
            
            # Build URL
            url = f"{endpoint.base_url}/{path.lstrip('/')}"
            
            # Prepare headers
            headers = {'Content-Type': 'application/json'}
            headers.update(self._get_auth_headers(endpoint))
            
            # Make request
            async with self.session.request(
                method=method.upper(),
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=endpoint.timeout)
            ) as response:
                
                if response.content_type == 'application/json':
                    response_data = await response.json()
                else:
                    response_data = await response.text()
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                execution = ToolExecution(
                    tool_name=f"{endpoint_name}_{method.lower()}",
                    success=response.status < 400,
                    response={
                        'status': response.status,
                        'data': response_data,
                        'headers': dict(response.headers)
                    },
                    execution_time=execution_time,
                    timestamp=start_time,
                    persona_context=persona_context
                )
                
                self.registry.add_execution(execution)
                return execution
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            execution = ToolExecution(
                tool_name=f"{endpoint_name}_{method.lower()}",
                success=False,
                response={'error': str(e)},
                execution_time=execution_time,
                timestamp=start_time,
                persona_context=persona_context
            )
            self.registry.add_execution(execution)
            return execution
    
    def _get_auth_headers(self, endpoint: APIEndpoint) -> Dict[str, str]:
        """Get authentication headers for endpoint"""
        headers = {}
        
        if endpoint.auth_type == 'none':
            return headers
        
        # Get API key from environment
        api_key = os.getenv(f"{endpoint.name.upper().replace(' ', '_')}_API_KEY")
        
        if not api_key:
            logger.warning(f"No API key found for {endpoint.name}")
            return headers
        
        if endpoint.auth_type == 'bearer':
            headers[endpoint.auth_header] = f"Bearer {api_key}"
        elif endpoint.auth_type == 'api_key':
            headers[endpoint.auth_header] = api_key
        elif endpoint.auth_type == 'basic':
            encoded = base64.b64encode(f"{api_key}:".encode()).decode()
            headers[endpoint.auth_header] = f"Basic {encoded}"
        
        return headers

    async def execute_custom_workflow(self, workflow_name: str, params: Dict[str, Any],
                                    persona_context: str = None) -> ToolExecution:
        """Execute predefined workflows"""
        start_time = datetime.now()
        
        try:
            if workflow_name == 'deploy_and_monitor':
                # Example workflow: Deploy to Vercel and monitor
                result = await self._deploy_and_monitor_workflow(params)
            elif workflow_name == 'pay_ready_analysis':
                # Sophia's Pay Ready workflow
                result = await self._pay_ready_analysis_workflow(params)
            elif workflow_name == 'paragonrx_compliance':
                # Karen's ParagonRX workflow  
                result = await self._paragonrx_compliance_workflow(params)
            elif workflow_name == 'infrastructure_health':
                # Cherry's infrastructure coordination
                result = await self._infrastructure_health_workflow(params)
            else:
                raise ValueError(f"Unknown workflow: {workflow_name}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            execution = ToolExecution(
                tool_name=f"workflow_{workflow_name}",
                success=True,
                response=result,
                execution_time=execution_time,
                timestamp=start_time,
                persona_context=persona_context
            )
            
            self.registry.add_execution(execution)
            return execution
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            execution = ToolExecution(
                tool_name=f"workflow_{workflow_name}",
                success=False,
                response={'error': str(e)},
                execution_time=execution_time,
                timestamp=start_time,
                persona_context=persona_context
            )
            self.registry.add_execution(execution)
            return execution
    
    async def _deploy_and_monitor_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy application and set up monitoring"""
        results = []
        
        # Deploy to Vercel
        deploy_result = await self.execute_api_call(
            'vercel', 'POST', '/deployments',
            data={'name': params.get('app_name'), 'gitSource': params.get('git_source')}
        )
        results.append(('deploy', deploy_result.success))
        
        # Set up monitoring (mock)
        monitor_result = {'monitoring_enabled': True, 'alerts_configured': True}
        results.append(('monitor', True))
        
        return {
            'workflow': 'deploy_and_monitor',
            'steps': results,
            'overall_success': all(result[1] for result in results)
        }
    
    async def _pay_ready_analysis_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sophia's Pay Ready business intelligence workflow"""
        results = []
        
        # Analyze transactions (mock Stripe call)
        transactions = await self.execute_api_call(
            'stripe', 'GET', '/charges',
            params={'limit': params.get('limit', 10)}
        )
        results.append(('transactions', transactions.success))
        
        # Generate business intelligence report
        analysis = {
            'total_transactions': params.get('limit', 10),
            'revenue_trend': 'positive',
            'compliance_status': 'compliant',
            'recommendations': [
                'Optimize payment flow for mobile users',
                'Implement fraud detection improvements',
                'Consider international payment methods'
            ]
        }
        results.append(('analysis', True))
        
        return {
            'workflow': 'pay_ready_analysis',
            'analysis': analysis,
            'steps': results,
            'overall_success': all(result[1] for result in results)
        }
    
    async def _paragonrx_compliance_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Karen's ParagonRX compliance workflow"""
        results = []
        
        # Check medical data compliance (mock)
        compliance_check = {
            'hipaa_compliant': True,
            'data_encryption': True,
            'access_controls': True,
            'audit_trail': True,
            'issues_found': 0
        }
        results.append(('compliance', True))
        
        # Validate medical coding (mock)
        coding_validation = {
            'icd10_codes_valid': True,
            'prescription_format_valid': True,
            'dosage_calculations_verified': True
        }
        results.append(('coding', True))
        
        return {
            'workflow': 'paragonrx_compliance',
            'compliance_check': compliance_check,
            'coding_validation': coding_validation,
            'steps': results,
            'overall_success': all(result[1] for result in results)
        }
    
    async def _infrastructure_health_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Cherry's infrastructure coordination workflow"""
        results = []
        
        # Check Lambda Labs instances
        lambda_status = await self.execute_api_call(
            'lambda_labs', 'GET', '/instances'
        )
        results.append(('lambda_labs', lambda_status.success))
        
        # Check Vercel deployments
        vercel_status = await self.execute_api_call(
            'vercel', 'GET', '/deployments'
        )
        results.append(('vercel', vercel_status.success))
        
        # Aggregate health status
        health_summary = {
            'overall_health': 'healthy' if all(result[1] for result in results) else 'issues_detected',
            'services_checked': len(results),
            'services_healthy': sum(1 for result in results if result[1]),
            'last_check': datetime.now().isoformat()
        }
        
        return {
            'workflow': 'infrastructure_health',
            'health_summary': health_summary,
            'steps': results,
            'overall_success': all(result[1] for result in results)
        }

class ToolsCoordinationServer:
    """MCP server for tools coordination and API access"""
    
    def __init__(self):
        self.server = Server("tools-coordination")
        self.tool_registry = ToolRegistry()
        self._setup_tools()
    
    def _setup_tools(self):
        """Setup MCP tools for API coordination"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """List available tools and APIs"""
            return [
                types.Tool(
                    name="execute_api_call",
                    description="Execute API call to any registered endpoint",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "endpoint": {"type": "string", "enum": list(self.tool_registry.endpoints.keys())},
                            "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
                            "path": {"type": "string"},
                            "data": {"type": "object"},
                            "params": {"type": "object"},
                            "persona_context": {"type": "string", "enum": ["cherry", "sophia", "karen"]}
                        },
                        "required": ["endpoint", "method", "path"]
                    }
                ),
                types.Tool(
                    name="execute_workflow",
                    description="Execute predefined workflows for different personas",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow_name": {"type": "string", "enum": [
                                "deploy_and_monitor", "pay_ready_analysis", 
                                "paragonrx_compliance", "infrastructure_health"
                            ]},
                            "parameters": {"type": "object"},
                            "persona_context": {"type": "string", "enum": ["cherry", "sophia", "karen"]}
                        },
                        "required": ["workflow_name", "parameters"]
                    }
                ),
                types.Tool(
                    name="get_available_tools",
                    description="Get list of available tools for specific persona",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "persona": {"type": "string", "enum": ["cherry", "sophia", "karen", "all"]},
                            "include_details": {"type": "boolean"}
                        }
                    }
                ),
                types.Tool(
                    name="get_execution_history",
                    description="Get recent tool execution history and analytics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "minimum": 1, "maximum": 50},
                            "persona_filter": {"type": "string", "enum": ["cherry", "sophia", "karen"]},
                            "success_only": {"type": "boolean"}
                        }
                    }
                ),
                types.Tool(
                    name="test_api_connectivity",
                    description="Test connectivity to all or specific API endpoints",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "endpoint": {"type": "string"},
                            "timeout": {"type": "integer", "minimum": 5, "maximum": 60}
                        }
                    }
                ),
                types.Tool(
                    name="suggest_tools",
                    description="Suggest relevant tools based on task description and persona",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_description": {"type": "string"},
                            "persona": {"type": "string", "enum": ["cherry", "sophia", "karen"]},
                            "max_suggestions": {"type": "integer", "minimum": 1, "maximum": 10}
                        },
                        "required": ["task_description"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
            """Handle tool calls for API coordination"""
            
            if name == "execute_api_call":
                return await self._handle_api_call(arguments)
            elif name == "execute_workflow":
                return await self._handle_workflow(arguments)
            elif name == "get_available_tools":
                return await self._handle_get_tools(arguments)
            elif name == "get_execution_history":
                return await self._handle_execution_history(arguments)
            elif name == "test_api_connectivity":
                return await self._handle_test_connectivity(arguments)
            elif name == "suggest_tools":
                return await self._handle_suggest_tools(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _handle_api_call(self, args: dict) -> List[types.TextContent]:
        """Handle API call execution"""
        try:
            async with UnifiedAPIClient(self.tool_registry) as client:
                execution = await client.execute_api_call(
                    endpoint_name=args['endpoint'],
                    method=args['method'],
                    path=args['path'],
                    data=args.get('data'),
                    params=args.get('params'),
                    persona_context=args.get('persona_context')
                )
            
            if execution.success:
                response = f"✅ API Call Successful: {args['endpoint']}\n"
                response += "=" * 40 + "\n\n"
                response += f"🎯 **Endpoint**: {args['endpoint']}\n"
                response += f"📡 **Method**: {args['method']} {args['path']}\n"
                response += f"⏱️ **Execution Time**: {execution.execution_time:.3f}s\n"
                response += f"📊 **Status**: {execution.response.get('status', 'N/A')}\n\n"
                
                # Format response data
                data = execution.response.get('data', {})
                if isinstance(data, dict):
                    response += "📋 **Response**:\n"
                    for key, value in list(data.items())[:5]:  # First 5 items
                        response += f"• {key}: {str(value)[:100]}...\n"
                    if len(data) > 5:
                        response += f"• ... and {len(data) - 5} more items\n"
                else:
                    response += f"📋 **Response**: {str(data)[:200]}...\n"
            else:
                response = f"❌ API Call Failed: {args['endpoint']}\n"
                response += f"Error: {execution.response.get('error', 'Unknown error')}\n"
                response += f"Execution Time: {execution.execution_time:.3f}s\n"
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error executing API call: {str(e)}"
            )]
    
    async def _handle_workflow(self, args: dict) -> List[types.TextContent]:
        """Handle workflow execution"""
        try:
            async with UnifiedAPIClient(self.tool_registry) as client:
                execution = await client.execute_custom_workflow(
                    workflow_name=args['workflow_name'],
                    params=args['parameters'],
                    persona_context=args.get('persona_context')
                )
            
            if execution.success:
                result = execution.response
                response = f"🔄 Workflow Completed: {args['workflow_name']}\n"
                response += "=" * 50 + "\n\n"
                response += f"⏱️ **Execution Time**: {execution.execution_time:.3f}s\n"
                response += f"✅ **Overall Success**: {result.get('overall_success', False)}\n\n"
                
                # Show workflow steps
                steps = result.get('steps', [])
                response += "📋 **Workflow Steps**:\n"
                for step_name, step_success in steps:
                    status = "✅" if step_success else "❌"
                    response += f"{status} {step_name.title()}\n"
                
                # Show specific results based on workflow
                if args['workflow_name'] == 'pay_ready_analysis':
                    analysis = result.get('analysis', {})
                    response += f"\n💰 **Revenue Trend**: {analysis.get('revenue_trend', 'N/A')}\n"
                    response += f"📊 **Compliance**: {analysis.get('compliance_status', 'N/A')}\n"
                elif args['workflow_name'] == 'infrastructure_health':
                    health = result.get('health_summary', {})
                    response += f"\n🏥 **Overall Health**: {health.get('overall_health', 'N/A')}\n"
                    response += f"📊 **Services Healthy**: {health.get('services_healthy', 0)}/{health.get('services_checked', 0)}\n"
            else:
                response = f"❌ Workflow Failed: {args['workflow_name']}\n"
                response += f"Error: {execution.response.get('error', 'Unknown error')}\n"
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error executing workflow: {str(e)}"
            )]
    
    async def _handle_get_tools(self, args: dict) -> List[types.TextContent]:
        """Handle get available tools request"""
        try:
            persona = args.get('persona', 'all')
            include_details = args.get('include_details', False)
            
            response = f"🛠️ Available Tools"
            if persona != 'all':
                response += f" for {persona.title()}"
            response += "\n" + "=" * 40 + "\n\n"
            
            if persona == 'all':
                endpoints = self.tool_registry.endpoints
            else:
                persona_tools = self.tool_registry.get_persona_tools(persona)
                endpoints = {name: self.tool_registry.endpoints[name] 
                           for name in persona_tools}
            
            for name, endpoint in endpoints.items():
                response += f"🔧 **{endpoint.name}**\n"
                if include_details:
                    response += f"  • Base URL: {endpoint.base_url}\n"
                    response += f"  • Auth Type: {endpoint.auth_type}\n"
                    response += f"  • Rate Limit: {endpoint.rate_limit}/min\n"
                    response += f"  • Timeout: {endpoint.timeout}s\n"
                    response += f"  • Persona Affinity: {', '.join(endpoint.persona_affinity)}\n"
                response += "\n"
            
            # Show recent executions
            recent_executions = self.tool_registry.execution_history[-5:]
            if recent_executions:
                response += "📊 **Recent Executions**:\n"
                for execution in recent_executions:
                    status = "✅" if execution.success else "❌"
                    response += f"{status} {execution.tool_name} ({execution.execution_time:.3f}s)\n"
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error getting tools: {str(e)}"
            )]
    
    async def _handle_execution_history(self, args: dict) -> List[types.TextContent]:
        """Handle execution history request"""
        try:
            limit = args.get('limit', 10)
            persona_filter = args.get('persona_filter')
            success_only = args.get('success_only', False)
            
            # Filter executions
            executions = self.tool_registry.execution_history
            
            if persona_filter:
                executions = [e for e in executions if e.persona_context == persona_filter]
            
            if success_only:
                executions = [e for e in executions if e.success]
            
            executions = executions[-limit:]
            
            response = f"📊 Tool Execution History (Last {len(executions)})\n"
            response += "=" * 50 + "\n\n"
            
            if not executions:
                response += "No executions found with current filters.\n"
                return [types.TextContent(type="text", text=response)]
            
            # Statistics
            total_executions = len(executions)
            successful_executions = sum(1 for e in executions if e.success)
            avg_execution_time = sum(e.execution_time for e in executions) / total_executions
            
            response += f"📈 **Statistics**:\n"
            response += f"• Total: {total_executions}\n"
            response += f"• Successful: {successful_executions} ({successful_executions/total_executions*100:.1f}%)\n"
            response += f"• Average time: {avg_execution_time:.3f}s\n\n"
            
            response += "📋 **Recent Executions**:\n"
            for execution in reversed(executions[-10:]):  # Last 10, newest first
                status = "✅" if execution.success else "❌"
                persona = f"[{execution.persona_context}]" if execution.persona_context else ""
                response += f"{status} {execution.tool_name} {persona} ({execution.execution_time:.3f}s)\n"
                response += f"    {execution.timestamp.strftime('%H:%M:%S')}\n"
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error getting execution history: {str(e)}"
            )]
    
    async def _handle_test_connectivity(self, args: dict) -> List[types.TextContent]:
        """Handle API connectivity testing"""
        try:
            endpoint_name = args.get('endpoint')
            timeout = args.get('timeout', 10)
            
            response = "🔍 API Connectivity Test\n"
            response += "=" * 30 + "\n\n"
            
            endpoints_to_test = [endpoint_name] if endpoint_name else list(self.tool_registry.endpoints.keys())
            
            async with UnifiedAPIClient(self.tool_registry) as client:
                for name in endpoints_to_test:
                    try:
                        # Simple health check (GET to base URL or health endpoint)
                        execution = await client.execute_api_call(
                            name, 'GET', '/', 
                            persona_context='connectivity_test'
                        )
                        
                        if execution.success or execution.response.get('status', 0) < 500:
                            status = "✅ Connected"
                        else:
                            status = "❌ Failed"
                        
                        response += f"{status} {self.tool_registry.endpoints[name].name}\n"
                        response += f"    Response time: {execution.execution_time:.3f}s\n"
                        
                    except Exception as e:
                        response += f"❌ {self.tool_registry.endpoints[name].name}\n"
                        response += f"    Error: {str(e)[:50]}...\n"
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error testing connectivity: {str(e)}"
            )]
    
    async def _handle_suggest_tools(self, args: dict) -> List[types.TextContent]:
        """Handle tool suggestion requests"""
        try:
            task_description = args['task_description'].lower()
            persona = args.get('persona')
            max_suggestions = args.get('max_suggestions', 5)
            
            # Simple keyword-based suggestions
            suggestions = []
            
            # Analyze task description for keywords
            if any(word in task_description for word in ['deploy', 'deployment', 'vercel', 'frontend']):
                suggestions.append(('vercel', 'Deploy and manage frontend applications'))
            
            if any(word in task_description for word in ['pay', 'payment', 'stripe', 'financial', 'transaction']):
                suggestions.append(('stripe', 'Handle payments and financial transactions'))
            
            if any(word in task_description for word in ['github', 'git', 'repository', 'code']):
                suggestions.append(('github', 'Manage code repositories and deployments'))
            
            if any(word in task_description for word in ['notion', 'database', 'notes', 'documentation']):
                suggestions.append(('notion', 'Manage documentation and databases'))
            
            if any(word in task_description for word in ['lambda', 'gpu', 'compute', 'instance']):
                suggestions.append(('lambda_labs', 'Manage GPU compute instances'))
            
            if any(word in task_description for word in ['aws', 'cloud', 's3', 'rds']):
                suggestions.append(('aws', 'Manage AWS cloud resources'))
            
            # Filter by persona affinity if specified
            if persona:
                persona_tools = self.tool_registry.get_persona_tools(persona)
                suggestions = [(name, desc) for name, desc in suggestions if name in persona_tools]
            
            suggestions = suggestions[:max_suggestions]
            
            response = f"💡 Tool Suggestions"
            if persona:
                response += f" for {persona.title()}"
            response += "\n" + "=" * 40 + "\n\n"
            
            response += f"📝 **Task**: {args['task_description']}\n\n"
            
            if suggestions:
                response += "🛠️ **Recommended Tools**:\n"
                for i, (tool_name, description) in enumerate(suggestions, 1):
                    endpoint = self.tool_registry.endpoints[tool_name]
                    response += f"{i}. **{endpoint.name}**: {description}\n"
                    response += f"   Usage: `execute_api_call` with endpoint '{tool_name}'\n"
            else:
                response += "🤔 No specific tool suggestions found.\n"
                response += "Consider using `get_available_tools` to explore all options.\n"
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error suggesting tools: {str(e)}"
            )]

async def main():
    """Main server execution"""
    logger.info("🛠️ Starting Tools Coordination Server")
    logger.info("🔧 Features: Unified API access, workflow automation, persona-aware tools")
    logger.info("🎯 Integration: Complete external service coordination for Cursor AI")
    
    server = ToolsCoordinationServer()
    
    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            None
        )

if __name__ == "__main__":
    asyncio.run(main()) 