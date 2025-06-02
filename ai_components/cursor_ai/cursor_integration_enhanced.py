#!/usr/bin/env python3
"""
Enhanced Cursor AI Integration Module
Provides real API integration with MCP servers, PostgreSQL logging, and Weaviate Cloud updates
"""

import os
import sys
import json
import time
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import logging

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared.database import initialize_database
from ai_components.orchestration.ai_orchestrator import WeaviateManager

logger = logging.getLogger(__name__)

class CursorAIClient:
    """Enhanced Cursor AI API Client with real integration"""
    
    def __init__(self, api_key: str = None, mcp_servers: Dict[str, str] = None):
        self.api_key = api_key or os.environ.get('CURSOR_AI_API_KEY')
        self.base_url = "https://api.cursor.sh/v1"  # Real Cursor AI API endpoint
        self.session = None
        self.db = None
        self.weaviate_manager = WeaviateManager()
        
        # MCP server endpoints
        self.mcp_servers = mcp_servers or {
            'orchestrator': 'http://localhost:8002',
            'memory': 'http://localhost:8003',
            'weaviate': 'http://localhost:8001',
            'deployment': 'http://localhost:8005',
            'tools': 'http://localhost:8006'
        }
        
        self.performance_metrics = {
            'requests_made': 0,
            'total_latency': 0,
            'errors': 0,
            'cache_hits': 0
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'Orchestra-AI/1.0'
            },
            timeout=aiohttp.ClientTimeout(total=300)  # 5 minute timeout
        )
        
        # Initialize database
        postgres_url = os.environ.get(
            'POSTGRES_URL',
            'postgresql://postgres:password@localhost:5432/orchestra'
        )
        weaviate_url = os.environ.get('WEAVIATE_URL', 'http://localhost:8080')
        weaviate_api_key = os.environ.get('WEAVIATE_API_KEY')
        
        self.db = await initialize_database(postgres_url, weaviate_url, weaviate_api_key)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        if self.db:
            await self.db.close()
    
    async def analyze_code(self, file_path: str, context: Dict = None) -> Dict:
        """Analyze code file with Cursor AI"""
        start_time = time.time()
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                code_content = f.read()
            
            # Get context from MCP servers
            mcp_context = await self._get_mcp_context(file_path, context)
            
            # Prepare request
            request_data = {
                "action": "analyze",
                "content": code_content,
                "file_path": file_path,
                "context": mcp_context,
                "options": {
                    "include_suggestions": True,
                    "include_metrics": True,
                    "analysis_depth": "comprehensive"
                }
            }
            
            # Make API call
            async with self.session.post(
                f"{self.base_url}/analyze",
                json=request_data
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    # Log to PostgreSQL
                    await self._log_action(
                        action="analyze_code",
                        file_path=file_path,
                        status="success",
                        latency=time.time() - start_time,
                        result=result
                    )
                    
                    # Update Weaviate
                    await self._update_weaviate_context(
                        "code_analysis",
                        file_path,
                        result
                    )
                    
                    self.performance_metrics['requests_made'] += 1
                    self.performance_metrics['total_latency'] += time.time() - start_time
                    
                    return result
                    
                else:
                    error_msg = f"API error: {response.status} - {await response.text()}"
                    await self._log_error("analyze_code", file_path, error_msg)
                    raise Exception(error_msg)
                    
        except Exception as e:
            self.performance_metrics['errors'] += 1
            await self._log_error("analyze_code", file_path, str(e))
            
            # Fallback to mock analysis for continuity
            return await self._fallback_analysis(file_path, code_content)
    
    async def generate_code(self, prompt: str, context: Dict = None) -> Dict:
        """Generate code with Cursor AI"""
        start_time = time.time()
        
        try:
            # Get context from MCP servers
            mcp_context = await self._get_mcp_context("code_generation", context)
            
            request_data = {
                "action": "generate",
                "prompt": prompt,
                "context": mcp_context,
                "options": {
                    "language": context.get("language", "python"),
                    "style": "production",
                    "include_tests": True,
                    "include_docs": True
                }
            }
            
            async with self.session.post(
                f"{self.base_url}/generate",
                json=request_data
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    await self._log_action(
                        action="generate_code",
                        file_path="generated",
                        status="success",
                        latency=time.time() - start_time,
                        result=result
                    )
                    
                    await self._update_weaviate_context(
                        "code_generation",
                        prompt,
                        result
                    )
                    
                    self.performance_metrics['requests_made'] += 1
                    self.performance_metrics['total_latency'] += time.time() - start_time
                    
                    return result
                else:
                    error_msg = f"API error: {response.status} - {await response.text()}"
                    await self._log_error("generate_code", "generated", error_msg)
                    raise Exception(error_msg)
                    
        except Exception as e:
            self.performance_metrics['errors'] += 1
            await self._log_error("generate_code", "generated", str(e))
            return {"error": str(e), "fallback": True}
    
    async def refactor_code(self, file_path: str, refactor_type: str, context: Dict = None) -> Dict:
        """Refactor code with Cursor AI"""
        start_time = time.time()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code_content = f.read()
            
            mcp_context = await self._get_mcp_context(file_path, context)
            
            request_data = {
                "action": "refactor",
                "content": code_content,
                "file_path": file_path,
                "refactor_type": refactor_type,
                "context": mcp_context,
                "options": {
                    "preserve_behavior": True,
                    "improve_performance": True,
                    "add_type_hints": True
                }
            }
            
            async with self.session.post(
                f"{self.base_url}/refactor",
                json=request_data
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    await self._log_action(
                        action="refactor_code",
                        file_path=file_path,
                        status="success",
                        latency=time.time() - start_time,
                        result=result
                    )
                    
                    await self._update_weaviate_context(
                        "code_refactoring",
                        file_path,
                        result
                    )
                    
                    self.performance_metrics['requests_made'] += 1
                    self.performance_metrics['total_latency'] += time.time() - start_time
                    
                    return result
                else:
                    error_msg = f"API error: {response.status} - {await response.text()}"
                    await self._log_error("refactor_code", file_path, error_msg)
                    raise Exception(error_msg)
                    
        except Exception as e:
            self.performance_metrics['errors'] += 1
            await self._log_error("refactor_code", file_path, str(e))
            return {"error": str(e), "fallback": True}
    
    async def _get_mcp_context(self, identifier: str, context: Dict = None) -> Dict:
        """Get context from MCP servers"""
        mcp_context = {
            "timestamp": datetime.now().isoformat(),
            "identifier": identifier
        }
        
        try:
            # Get memory context
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.mcp_servers['memory']}/context/{identifier}"
                ) as response:
                    if response.status == 200:
                        mcp_context["memory"] = await response.json()
                
                # Get orchestrator context
                async with session.get(
                    f"{self.mcp_servers['orchestrator']}/tasks"
                ) as response:
                    if response.status == 200:
                        mcp_context["active_tasks"] = await response.json()
                
                # Get tools context
                async with session.get(
                    f"{self.mcp_servers['tools']}/available"
                ) as response:
                    if response.status == 200:
                        mcp_context["available_tools"] = await response.json()
        
        except Exception as e:
            logger.warning(f"Failed to get MCP context: {e}")
            mcp_context["mcp_error"] = str(e)
        
        # Add provided context
        if context:
            mcp_context.update(context)
        
        return mcp_context
    
    async def _log_action(self, action: str, file_path: str, status: str, 
                         latency: float, result: Dict = None) -> None:
        """Log action to PostgreSQL"""
        try:
            await self.db.execute_query(
                """
                INSERT INTO cursor_ai_logs 
                (action, file_path, status, latency_seconds, result, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                action, file_path, status, latency, json.dumps(result) if result else None,
                datetime.now()
            )
        except Exception as e:
            logger.error(f"Failed to log action: {e}")
    
    async def _log_error(self, action: str, file_path: str, error: str) -> None:
        """Log error to PostgreSQL"""
        try:
            await self.db.execute_query(
                """
                INSERT INTO cursor_ai_logs 
                (action, file_path, status, error_message, created_at)
                VALUES ($1, $2, $3, $4, $5)
                """,
                action, file_path, "error", error, datetime.now()
            )
        except Exception as e:
            logger.error(f"Failed to log error: {e}")
    
    async def _update_weaviate_context(self, context_type: str, identifier: str, 
                                     data: Dict) -> None:
        """Update Weaviate with context data"""
        try:
            self.weaviate_manager.store_context(
                workflow_id="cursor_ai_operations",
                task_id=f"{context_type}_{int(time.time())}",
                context_type=context_type,
                content=json.dumps(data),
                metadata={
                    "identifier": identifier,
                    "timestamp": datetime.now().isoformat(),
                    "tool": "cursor_ai"
                }
            )
        except Exception as e:
            logger.error(f"Failed to update Weaviate: {e}")
    
    async def _fallback_analysis(self, file_path: str, content: str) -> Dict:
        """Fallback analysis when API is unavailable"""
        return {
            "status": "fallback_analysis",
            "file_path": file_path,
            "analysis": {
                "lines_of_code": len(content.splitlines()),
                "character_count": len(content),
                "estimated_complexity": "medium",
                "suggestions": [
                    "API unavailable - using fallback analysis",
                    "Consider adding type hints",
                    "Review function documentation"
                ]
            },
            "fallback": True,
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_performance_metrics(self) -> Dict:
        """Get performance metrics"""
        avg_latency = (
            self.performance_metrics['total_latency'] / 
            self.performance_metrics['requests_made']
            if self.performance_metrics['requests_made'] > 0 else 0
        )
        
        error_rate = (
            self.performance_metrics['errors'] / 
            self.performance_metrics['requests_made']
            if self.performance_metrics['requests_made'] > 0 else 0
        )
        
        return {
            "requests_made": self.performance_metrics['requests_made'],
            "average_latency": avg_latency,
            "error_rate": error_rate,
            "cache_hits": self.performance_metrics['cache_hits'],
            "status": "operational" if error_rate < 0.1 else "degraded"
        }
    
    async def test_integration(self) -> Dict:
        """Test the integration"""
        test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        
        # Test API connectivity
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                test_results["tests"]["api_connectivity"] = {
                    "status": "passed" if response.status == 200 else "failed",
                    "response_code": response.status
                }
        except Exception as e:
            test_results["tests"]["api_connectivity"] = {
                "status": "failed",
                "error": str(e)
            }
        
        # Test MCP server connectivity
        mcp_tests = {}
        for name, url in self.mcp_servers.items():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{url}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                        mcp_tests[name] = {
                            "status": "passed" if response.status == 200 else "failed",
                            "response_code": response.status
                        }
            except Exception as e:
                mcp_tests[name] = {
                    "status": "failed",
                    "error": str(e)
                }
        
        test_results["tests"]["mcp_servers"] = mcp_tests
        
        # Test database connectivity
        try:
            await self.db.execute_query("SELECT 1")
            test_results["tests"]["database"] = {"status": "passed"}
        except Exception as e:
            test_results["tests"]["database"] = {
                "status": "failed",
                "error": str(e)
            }
        
        return test_results


async def main():
    """Test the enhanced Cursor AI integration"""
    print("🚀 Testing Enhanced Cursor AI Integration...")
    
    async with CursorAIClient() as client:
        # Run integration tests
        test_results = await client.test_integration()
        print("\n📊 Integration Test Results:")
        print(json.dumps(test_results, indent=2))
        
        # Test code analysis on this file
        current_file = __file__
        print(f"\n🔍 Testing code analysis on {current_file}...")
        
        analysis_result = await client.analyze_code(current_file)
        print("Analysis completed:", analysis_result.get("status", "unknown"))
        
        # Test code generation
        print("\n🏗️  Testing code generation...")
        generation_result = await client.generate_code(
            "Create a simple Python function that calculates fibonacci numbers",
            context={"language": "python", "style": "production"}
        )
        print("Generation completed:", generation_result.get("status", "unknown"))
        
        # Get performance metrics
        metrics = await client.get_performance_metrics()
        print(f"\n📈 Performance Metrics:")
        print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    asyncio.run(main()) 