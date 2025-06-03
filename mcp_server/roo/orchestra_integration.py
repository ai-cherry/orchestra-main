# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
Orchestra AI Integration for Roo Coding Agents
Automatically embeds Orchestra AI capabilities into all Roo modes
"""

import os
import sys
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_server.servers.orchestrator_server import get_all_agents, run_agent_task
from mcp_server.storage.async_memory_store import AsyncMemoryStore

logger = logging.getLogger(__name__)


class OrchestraRooIntegration:
    """Integrates Orchestra AI with Roo coding agents across all modes."""
    
    def __init__(self):
        """Initialize Orchestra-Roo integration."""
        # Initialize memory store with default config
        memory_config = {
            "storage_path": "./memory_store",
            "ttl_seconds": 3600,
            "max_items_per_key": 100,
            "enable_compression": False
        }
        self.memory_store = AsyncMemoryStore(memory_config)
        self.active_agents: List[Dict] = []
        self.mode_handlers: Dict[str, Callable] = {}
        self.auto_enabled = True
        self._setup_environment()
    
    def _setup_environment(self):
        """Set up environment for passwordless PostgreSQL access."""
        os.environ["POSTGRES_HOST"] = "127.0.0.1"
        os.environ["POSTGRES_PORT"] = "5432"
        os.environ["POSTGRES_USER"] = "postgres"
        os.environ["POSTGRES_PASSWORD"] = ""
        os.environ["POSTGRES_DB"] = "orchestra"
        
        # Weaviate settings
        os.environ["WEAVIATE_HOST"] = "localhost"
        os.environ["WEAVIATE_PORT"] = "8080"
        os.environ["WEAVIATE_GRPC_PORT"] = "50051"
    
    async def initialize(self):
        """Initialize all Orchestra AI components."""
        logger.info("Initializing Orchestra-Roo integration...")
        
        # Load available agents
        try:
            self.active_agents = await get_all_agents()
            logger.info(f"Loaded {len(self.active_agents)} Orchestra agents")
        except Exception as e:
            logger.error(f"Failed to load agents: {e}")
            self.active_agents = self._get_default_agents()
        
        # Initialize memory store async components
        await self.memory_store.initialize()
        
        # Register mode handlers
        self._register_mode_handlers()
        
        logger.info("Orchestra-Roo integration initialized successfully")
    
    def _get_default_agents(self) -> List[Dict]:
        """Get default agent configurations."""
        return [
            {
                "id": "code-analyzer",
                "name": "Code Analyzer",
                "type": "analyzer",
                "capabilities": ["code_analysis", "pattern_detection", "optimization"]
            },
            {
                "id": "task-planner",
                "name": "Task Planner",
                "type": "planner",
                "capabilities": ["task_decomposition", "priority_management", "scheduling"]
            },
            {
                "id": "quality-checker",
                "name": "Quality Checker",
                "type": "validator",
                "capabilities": ["code_review", "testing", "performance_analysis"]
            },
            {
                "id": "doc-generator",
                "name": "Documentation Generator",
                "type": "documenter",
                "capabilities": ["docstring_generation", "api_docs", "readme_updates"]
            }
        ]
    
    def _register_mode_handlers(self):
        """Register handlers for different Roo modes."""
        self.mode_handlers = {
            "code": self._handle_code_mode,
            "architect": self._handle_architect_mode,
            "debug": self._handle_debug_mode,
            "ask": self._handle_ask_mode,
            "orchestrator": self._handle_orchestrator_mode,
            "strategy": self._handle_strategy_mode,
            "research": self._handle_research_mode,
            "analytics": self._handle_analytics_mode,
            "implementation": self._handle_implementation_mode,
            "quality": self._handle_quality_mode,
            "documentation": self._handle_documentation_mode
        }
    
    async def process_roo_request(self, mode: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request from Roo in any mode with Orchestra AI enhancement."""
        if not self.auto_enabled:
            return {"enhanced": False, "response": request}
        
        logger.info(f"Processing Roo request in {mode} mode")
        
        # Get mode-specific handler
        handler = self.mode_handlers.get(mode, self._handle_default_mode)
        
        # Process with Orchestra AI
        try:
            enhanced_response = await handler(request)
            
            # Store in memory for context
            await self._store_interaction(mode, request, enhanced_response)
            
            return {
                "enhanced": True,
                "mode": mode,
                "original_request": request,
                "orchestra_response": enhanced_response,
                "agents_used": list(enhanced_response.get("agents", {}).keys()),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {
                "enhanced": False,
                "error": str(e),
                "response": request
            }
    
    async def _handle_code_mode(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle code mode requests with code analysis and optimization."""
        response = {"agents": {}}
        
        # Use code analyzer agent
        if "code" in request:
            analyzer_result = await run_agent_task(
                "code-analyzer",
                "analyze_code",
                {"code": request["code"], "language": request.get("language", "python")}
            )
            response["agents"]["code-analyzer"] = analyzer_result
        
        # Use quality checker for code review
        if request.get("review", False):
            review_result = await run_agent_task(
                "quality-checker",
                "code_review",
                {"code": request["code"]}
            )
            response["agents"]["quality-checker"] = review_result
        
        return response
    
    async def _handle_architect_mode(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle architect mode with system design assistance."""
        response = {"agents": {}}
        
        # Use task planner for architecture decomposition
        planner_result = await run_agent_task(
            "task-planner",
            "decompose_architecture",
            {"requirements": request.get("requirements", {})}
        )
        response["agents"]["task-planner"] = planner_result
        
        return response
    
    async def _handle_debug_mode(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle debug mode with error analysis and fix suggestions."""
        response = {"agents": {}}
        
        # Analyze error patterns
        if "error" in request:
            analyzer_result = await run_agent_task(
                "code-analyzer",
                "analyze_error",
                {"error": request["error"], "context": request.get("context", {})}
            )
            response["agents"]["code-analyzer"] = analyzer_result
        
        return response
    
    async def _handle_ask_mode(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ask mode with knowledge retrieval."""
        response = {"agents": {}}
        
        # Search memory for relevant information
        query = request.get("question", "")
        # Use get method to search for memories
        memories = []
        for i in range(5):  # Get up to 5 recent memories
            memory = await self.memory_store.get(f"memory_{i}", scope="ask")
            if memory:
                memories.append(memory)
        response["relevant_memories"] = memories
        
        return response
    
    async def _handle_orchestrator_mode(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle orchestrator mode with multi-agent coordination."""
        response = {"agents": {}}
        
        # Coordinate multiple agents based on task
        task_type = request.get("task_type", "general")
        
        if task_type == "full_stack":
            # Use all agents for comprehensive analysis
            for agent in self.active_agents:
                result = await run_agent_task(
                    agent["id"],
                    "process",
                    request
                )
                response["agents"][agent["id"]] = result
        
        return response
    
    async def _handle_strategy_mode(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle strategy mode with planning and optimization."""
        response = {"agents": {}}
        
        # Strategic planning
        planner_result = await run_agent_task(
            "task-planner",
            "strategic_planning",
            request
        )
        response["agents"]["task-planner"] = planner_result
        
        return response
    
    async def _handle_research_mode(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle research mode with data gathering and analysis."""
        response = {"agents": {}}
        
        # Research and analysis
        topic = request.get("topic", "")
        
        # Search existing knowledge
        memories = []
        for i in range(10):  # Get up to 10 recent memories
            memory = await self.memory_store.get(f"research_{topic}_{i}", scope="research")
            if memory:
                memories.append(memory)
        response["existing_knowledge"] = memories
        
        return response
    
    async def _handle_analytics_mode(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analytics mode with data analysis."""
        response = {"agents": {}}
        
        # Performance analytics
        if "metrics" in request:
            analyzer_result = await run_agent_task(
                "code-analyzer",
                "analyze_metrics",
                request["metrics"]
            )
            response["agents"]["code-analyzer"] = analyzer_result
        
        return response
    
    async def _handle_implementation_mode(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle implementation mode with deployment assistance."""
        response = {"agents": {}}
        
        # Implementation planning
        planner_result = await run_agent_task(
            "task-planner",
            "implementation_plan",
            request
        )
        response["agents"]["task-planner"] = planner_result
        
        return response
    
    async def _handle_quality_mode(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle quality mode with comprehensive testing."""
        response = {"agents": {}}
        
        # Quality assurance
        qa_result = await run_agent_task(
            "quality-checker",
            "comprehensive_check",
            request
        )
        response["agents"]["quality-checker"] = qa_result
        
        return response
    
    async def _handle_documentation_mode(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle documentation mode with auto-generation."""
        response = {"agents": {}}
        
        # Documentation generation
        doc_result = await run_agent_task(
            "doc-generator",
            "generate_docs",
            request
        )
        response["agents"]["doc-generator"] = doc_result
        
        return response
    
    async def _handle_default_mode(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Default handler for unknown modes."""
        return {
            "agents": {},
            "message": "Mode not specifically handled, using general processing"
        }
    
    async def _store_interaction(self, mode: str, request: Dict, response: Dict):
        """Store interaction in memory for context."""
        try:
            # Use set method to store interaction
            interaction_data = {
                "type": "roo_interaction",
                "mode": mode,
                "request": request,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }
            key = f"interaction_{mode}_{datetime.now().timestamp()}"
            await self.memory_store.set(key, interaction_data, scope="session")
        except Exception as e:
            logger.error(f"Failed to store interaction: {e}")
    
    def enable_auto_mode(self):
        """Enable automatic Orchestra AI enhancement."""
        self.auto_enabled = True
        logger.info("Orchestra AI auto-enhancement enabled")
    
    def disable_auto_mode(self):
        """Disable automatic Orchestra AI enhancement."""
        self.auto_enabled = False
        logger.info("Orchestra AI auto-enhancement disabled")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current integration status."""
        return {
            "enabled": self.auto_enabled,
            "active_agents": len(self.active_agents),
            "registered_modes": list(self.mode_handlers.keys()),
            "memory_initialized": self.memory_store is not None,
            "timestamp": datetime.now().isoformat()
        }


# Global instance
orchestra_roo = OrchestraRooIntegration()


async def initialize_orchestra_roo():
    """Initialize the Orchestra-Roo integration."""
    await orchestra_roo.initialize()
    return orchestra_roo


if __name__ == "__main__":
    # Test the integration
    async def test():
        await initialize_orchestra_roo()
        
        # Test code mode
        result = await orchestra_roo.process_roo_request(
            "code",
            {
                "code": "def hello(): print('Hello')",
                "language": "python",
                "review": True
            }
        )
        print(json.dumps(result, indent=2))
        
        # Get status
        status = await orchestra_roo.get_status()
        print(f"\nStatus: {json.dumps(status, indent=2)}")
    
    asyncio.run(test())