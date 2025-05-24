#!/usr/bin/env python3
"""
Web Scraping MCP Server for Orchestra AI
Integrates the Web Scraping AI Agent Team with the Orchestra AI ecosystem.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import List, Optional, Dict, Any

# Import our web scraping agent system
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_scraping_ai_agents import (
    WebScrapingOrchestrator,
    ScrapingTask,
    ScrapingResult,
    ScrapingStrategy,
    TaskPriority
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrchestraWebScrapingMCPServer:
    """MCP Server for Web Scraping AI Agent Team integration with Orchestra AI."""
    
    def __init__(self):
        self.orchestrator: Optional[WebScrapingOrchestrator] = None
        self.is_initialized = False
    
    async def initialize_agents(self):
        """Initialize the web scraping agent system."""
        if self.is_initialized:
            return
        
        logger.info("Initializing Web Scraping AI Agent Team...")
        
        # Load configuration from environment
        config = {
            'redis_host': os.getenv('REDIS_HOST', 'localhost'),
            'redis_port': int(os.getenv('REDIS_PORT', 6379)),
            'redis_db': int(os.getenv('REDIS_DB', 0)),
            'search_agents': int(os.getenv('SEARCH_AGENTS', 2)),
            'scraper_agents': int(os.getenv('SCRAPER_AGENTS', 3)),
            'analyzer_agents': int(os.getenv('ANALYZER_AGENTS', 2)),
            'zenrows_api_key': os.getenv('ZENROWS_API_KEY'),
            'apify_api_key': os.getenv('APIFY_API_KEY'),
            'phantombuster_api_key': os.getenv('PHANTOMBUSTER_API_KEY'),
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
        }
        
        # Initialize orchestrator
        self.orchestrator = WebScrapingOrchestrator(config)
        
        # Start orchestrator in background
        asyncio.create_task(self.orchestrator.start())
        
        self.is_initialized = True
        logger.info("Web Scraping AI Agent Team initialized successfully")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available web scraping tools."""
        return [
            {
                "name": "web_search",
                "description": "Search the web using various search engines",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "engine": {
                            "type": "string",
                            "enum": ["google", "bing", "duckduckgo"],
                            "default": "google",
                            "description": "Search engine to use"
                        },
                        "max_results": {
                            "type": "integer",
                            "default": 10,
                            "description": "Maximum number of results"
                        },
                        "strategy": {
                            "type": "string",
                            "enum": ["fast_static", "dynamic_content", "stealth_mode"],
                            "default": "fast_static",
                            "description": "Scraping strategy"
                        }
                    },
                    "required": ["query"]
                },
            },
            {
                "name": "scrape_website",
                "description": "Scrape content from a website using various strategies",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to scrape"
                        },
                        "strategy": {
                            "type": "string",
                            "enum": ["fast_static", "dynamic_content", "stealth_mode", "bulk_extraction"],
                            "default": "fast_static",
                            "description": "Scraping strategy"
                        },
                        "wait_for_selector": {
                            "type": "string",
                            "description": "CSS selector to wait for (dynamic content only)"
                        },
                        "custom_js": {
                            "type": "string",
                            "description": "Custom JavaScript to execute (dynamic content only)"
                        },
                        "user_agent": {
                            "type": "string",
                            "description": "Custom user agent string"
                        }
                    },
                    "required": ["url"]
                },
            },
            {
                "name": "analyze_content",
                "description": "Analyze scraped content using AI",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Content to analyze"
                        },
                        "analysis_type": {
                            "type": "string",
                            "enum": ["summary", "sentiment", "entities", "keywords", "general"],
                            "default": "summary",
                            "description": "Type of analysis to perform"
                        }
                    },
                    "required": ["content"]
                },
            },
            {
                "name": "bulk_scrape",
                "description": "Scrape multiple URLs in parallel",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "urls": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of URLs to scrape"
                        },
                        "strategy": {
                            "type": "string",
                            "enum": ["fast_static", "dynamic_content", "stealth_mode"],
                            "default": "fast_static",
                            "description": "Scraping strategy"
                        },
                        "max_concurrent": {
                            "type": "integer",
                            "default": 5,
                            "description": "Maximum concurrent scraping tasks"
                        }
                    },
                    "required": ["urls"]
                },
            },
            {
                "name": "get_task_status",
                "description": "Get the status of a scraping task",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "Task ID to check"
                        }
                    },
                    "required": ["task_id"]
                },
            },
        ]
    
    async def call_tool(self, name: str, arguments: dict) -> str:
        """Handle tool calls for web scraping operations."""
        if not self.is_initialized:
            await self.initialize_agents()
        
        try:
            if name == "web_search":
                result = await self.handle_web_search(**arguments)
            elif name == "scrape_website":
                result = await self.handle_scrape_website(**arguments)
            elif name == "analyze_content":
                result = await self.handle_analyze_content(**arguments)
            elif name == "bulk_scrape":
                result = await self.handle_bulk_scrape(**arguments)
            elif name == "get_task_status":
                result = await self.handle_get_task_status(**arguments)
            else:
                result = f"Unknown tool: {name}"
            
            return result
                
        except Exception as e:
            logger.error(f"Error in tool {name}: {str(e)}")
            return f"Error: {str(e)}"
    
    async def handle_web_search(self, query: str, engine: str = 'google', 
                               max_results: int = 10, strategy: str = 'fast_static') -> str:
        """Handle web search requests."""
        task = ScrapingTask(
            task_id=f"search_{int(time.time())}_{hash(query) % 10000}",
            url="",
            task_type="search",
            priority=TaskPriority.HIGH,
            strategy=ScrapingStrategy(strategy),
            parameters={
                'query': query,
                'engine': engine,
                'max_results': max_results
            }
        )
        
        task_id = await self.orchestrator.submit_task(task)
        
        # Wait for result with timeout
        for _ in range(60):  # Wait up to 60 seconds
            result = await self.orchestrator.get_result(task_id)
            if result:
                return self._format_search_result(result)
            await asyncio.sleep(1)
        
        return f"Search task {task_id} is still processing. Use get_task_status to check progress."
    
    async def handle_scrape_website(self, url: str, strategy: str = 'fast_static', **kwargs) -> str:
        """Handle website scraping requests."""
        task = ScrapingTask(
            task_id=f"scrape_{int(time.time())}_{hash(url) % 10000}",
            url=url,
            task_type="scrape",
            priority=TaskPriority.HIGH,
            strategy=ScrapingStrategy(strategy),
            parameters=kwargs
        )
        
        task_id = await self.orchestrator.submit_task(task)
        
        # Wait for result with timeout
        for _ in range(90):  # Wait up to 90 seconds
            result = await self.orchestrator.get_result(task_id)
            if result:
                return self._format_scrape_result(result)
            await asyncio.sleep(1)
        
        return f"Scraping task {task_id} is still processing. Use get_task_status to check progress."
    
    async def handle_analyze_content(self, content: str, analysis_type: str = 'summary') -> str:
        """Handle content analysis requests."""
        task = ScrapingTask(
            task_id=f"analyze_{int(time.time())}_{hash(content[:100]) % 10000}",
            url="",
            task_type="analyze",
            priority=TaskPriority.MEDIUM,
            strategy=ScrapingStrategy.FAST_STATIC,
            parameters={
                'content': content,
                'analysis_type': analysis_type
            }
        )
        
        task_id = await self.orchestrator.submit_task(task)
        
        # Wait for result with timeout
        for _ in range(45):  # Wait up to 45 seconds
            result = await self.orchestrator.get_result(task_id)
            if result:
                return self._format_analysis_result(result)
            await asyncio.sleep(1)
        
        return f"Analysis task {task_id} is still processing. Use get_task_status to check progress."
    
    async def handle_bulk_scrape(self, urls: List[str], strategy: str = 'fast_static', 
                                max_concurrent: int = 5) -> str:
        """Handle bulk scraping requests."""
        task_ids = []
        
        # Submit tasks in batches to respect concurrency limit
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i:i + max_concurrent]
            
            for url in batch:
                task = ScrapingTask(
                    task_id=f"bulk_scrape_{int(time.time())}_{hash(url) % 10000}",
                    url=url,
                    task_type="scrape",
                    priority=TaskPriority.MEDIUM,
                    strategy=ScrapingStrategy(strategy),
                    parameters={}
                )
                
                task_id = await self.orchestrator.submit_task(task)
                task_ids.append(task_id)
            
            # Wait for batch to complete before proceeding
            await asyncio.sleep(2)
        
        return f"Bulk scraping initiated for {len(urls)} URLs. Task IDs: {', '.join(task_ids[:5])}{'...' if len(task_ids) > 5 else ''}"
    
    async def handle_get_task_status(self, task_id: str) -> str:
        """Handle task status requests."""
        result = await self.orchestrator.get_result(task_id)
        
        if result:
            return f"Task {task_id} completed with status: {result.status}\nQuality score: {result.quality_score}\nProcessing time: {result.processing_time:.2f}s"
        else:
            return f"Task {task_id} is still processing or not found."
    
    async def get_agent_status(self) -> str:
        """Get current status of all agents."""
        if not self.orchestrator:
            return json.dumps({"error": "Agent system not initialized"})
        
        agents_status = {}
        for agent_id, agent in self.orchestrator.agents.items():
            agents_status[agent_id] = {
                "type": agent.agent_type.value,
                "is_busy": agent.is_busy,
                "completed_tasks": agent.completed_tasks,
                "success_rate": agent.success_rate,
                "last_activity": agent.last_activity.isoformat()
            }
        
        return json.dumps(agents_status, indent=2)
    
    async def get_active_tasks(self) -> str:
        """Get currently active tasks."""
        # This would integrate with Redis to get actual task data
        active_tasks = {
            "queue_size": self.orchestrator.task_queue.qsize() if self.orchestrator else 0,
            "timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(active_tasks, indent=2)
    
    async def get_recent_results(self) -> str:
        """Get recent scraping results."""
        if not self.orchestrator:
            return json.dumps({"error": "Agent system not initialized"})
        
        recent_results = []
        for result in self.orchestrator.results_storage[-10:]:  # Last 10 results
            recent_results.append({
                "task_id": result.task_id,
                "status": result.status,
                "quality_score": result.quality_score,
                "processing_time": result.processing_time,
                "timestamp": result.timestamp.isoformat(),
                "content_preview": result.extracted_content[:200] + "..." if len(result.extracted_content) > 200 else result.extracted_content
            })
        
        return json.dumps(recent_results, indent=2)
    
    def _format_search_result(self, result: ScrapingResult) -> str:
        """Format search result for display."""
        if result.status == "success":
            search_data = result.data.get('search_results', [])
            formatted = "Search completed successfully!\n"
            formatted += f"Quality Score: {result.quality_score:.2f}\n"
            formatted += f"Processing Time: {result.processing_time:.2f}s\n"
            formatted += f"Results Found: {len(search_data)}\n\n"
            
            for i, item in enumerate(search_data[:5], 1):
                formatted += f"{i}. {item.get('title', 'No title')}\n"
                formatted += f"   URL: {item.get('url', 'No URL')}\n"
                formatted += f"   Description: {item.get('description', 'No description')}\n\n"
            
            if len(search_data) > 5:
                formatted += f"... and {len(search_data) - 5} more results\n"
            
            return formatted
        else:
            return f"Search failed: {result.data.get('error', 'Unknown error')}"
    
    def _format_scrape_result(self, result: ScrapingResult) -> str:
        """Format scrape result for display."""
        if result.status == "success":
            formatted = "Website scraped successfully!\n"
            formatted += f"URL: {result.url}\n"
            formatted += f"Quality Score: {result.quality_score:.2f}\n"
            formatted += f"Processing Time: {result.processing_time:.2f}s\n"
            formatted += f"Content Length: {len(result.extracted_content)} characters\n"
            formatted += f"Links Found: {len(result.extracted_links)}\n"
            formatted += f"Images Found: {len(result.images)}\n\n"
            
            # Include content preview
            preview_length = 500
            if len(result.extracted_content) > preview_length:
                formatted += f"Content Preview:\n{result.extracted_content[:preview_length]}...\n\n"
            else:
                formatted += f"Content:\n{result.extracted_content}\n\n"
            
            # Include structured data if available
            if result.structured_data:
                title = result.structured_data.get('title', 'No title')
                description = result.structured_data.get('description', 'No description')
                formatted += f"Title: {title}\n"
                formatted += f"Description: {description}\n"
            
            return formatted
        else:
            return f"Scraping failed: {result.data.get('error', 'Unknown error')}"
    
    def _format_analysis_result(self, result: ScrapingResult) -> str:
        """Format analysis result for display."""
        if result.status == "success":
            formatted = "Content analysis completed!\n"
            formatted += f"Quality Score: {result.quality_score:.2f}\n"
            formatted += f"Processing Time: {result.processing_time:.2f}s\n\n"
            
            analysis_data = result.data
            analysis_type = result.metadata.get('analysis_type', 'unknown')
            
            formatted += f"Analysis Type: {analysis_type}\n"
            formatted += f"Results:\n{json.dumps(analysis_data, indent=2)}\n"
            
            return formatted
        else:
            return f"Analysis failed: {result.data.get('error', 'Unknown error')}"


# For backward compatibility
WebScrapingMCPServer = OrchestraWebScrapingMCPServer


async def main():
    """Main entry point for the Web Scraping MCP Server."""
    from mcp.server.stdio import stdio_server
    
    server = OrchestraWebScrapingMCPServer()
    
    async with stdio_server() as streams:
        await server.start(streams[0])


if __name__ == "__main__":
    asyncio.run(main()) 