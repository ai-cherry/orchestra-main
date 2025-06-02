#!/usr/bin/env python3
"""
Unified AI System Orchestrator
Manages and coordinates all AI tools: Cursor AI, Claude, GitHub Copilot, Roo Code, Factory AI
"""

import os
import sys
import json
import time
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import logging
from enum import Enum

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from shared.database import initialize_database
from ai_components.orchestration.ai_orchestrator import WeaviateManager

logger = logging.getLogger(__name__)

class TaskType(Enum):
    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation"
    CODE_REFACTORING = "code_refactoring"
    PROJECT_ANALYSIS = "project_analysis"
    DOCUMENTATION = "documentation"
    CODE_COMPLETION = "code_completion"
    IMPROVEMENT_SUGGESTIONS = "improvement_suggestions"

class AITool(Enum):
    CURSOR_AI = "cursor_ai"
    CLAUDE = "claude"
    GITHUB_COPILOT = "github_copilot"
    ROO_CODE = "roo_code"
    FACTORY_AI = "factory_ai"

class AISystemOrchestrator:
    """Unified orchestrator for all AI tools"""
    
    def __init__(self):
        self.db = None
        self.weaviate_manager = WeaviateManager()
        
        # Tool availability cache
        self.tool_status = {
            AITool.CURSOR_AI: {"available": False, "last_check": None},
            AITool.CLAUDE: {"available": False, "last_check": None},
            AITool.GITHUB_COPILOT: {"available": False, "last_check": None},
            AITool.ROO_CODE: {"available": False, "last_check": None},
            AITool.FACTORY_AI: {"available": False, "last_check": None}
        }
        
        # Tool preference matrix
        self.tool_preferences = {
            TaskType.CODE_ANALYSIS: [AITool.CLAUDE, AITool.CURSOR_AI, AITool.FACTORY_AI],
            TaskType.CODE_GENERATION: [AITool.CLAUDE, AITool.CURSOR_AI, AITool.GITHUB_COPILOT],
            TaskType.CODE_REFACTORING: [AITool.CURSOR_AI, AITool.CLAUDE, AITool.FACTORY_AI],
            TaskType.PROJECT_ANALYSIS: [AITool.CLAUDE, AITool.FACTORY_AI, AITool.CURSOR_AI],
            TaskType.DOCUMENTATION: [AITool.GITHUB_COPILOT, AITool.CLAUDE, AITool.FACTORY_AI],
            TaskType.CODE_COMPLETION: [AITool.GITHUB_COPILOT, AITool.CURSOR_AI, AITool.CLAUDE],
            TaskType.IMPROVEMENT_SUGGESTIONS: [AITool.GITHUB_COPILOT, AITool.CLAUDE, AITool.CURSOR_AI]
        }
        
        # Performance tracking
        self.performance_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "tool_usage": {tool.value: 0 for tool in AITool},
            "task_distribution": {task.value: 0 for task in TaskType},
            "average_latency": 0.0,
            "total_latency": 0.0
        }
        
        # Load balancing
        self.load_balancer = {
            "round_robin_index": 0,
            "tool_loads": {tool.value: 0 for tool in AITool},
            "max_concurrent_per_tool": 5
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        # Initialize database
        postgres_url = os.environ.get(
            'POSTGRES_URL',
            'postgresql://postgres:password@localhost:5432/orchestra'
        )
        weaviate_url = os.environ.get('WEAVIATE_URL', 'http://localhost:8080')
        weaviate_api_key = os.environ.get('WEAVIATE_API_KEY')
        
        self.db = await initialize_database(postgres_url, weaviate_url, weaviate_api_key)
        await self._initialize_tools()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.db:
            await self.db.close()
    
    async def execute_task(self, task_type: TaskType, request_data: Dict, 
                          preferred_tool: AITool = None) -> Dict:
        """Execute a task using the best available AI tool"""
        start_time = time.time()
        task_id = f"{task_type.value}_{int(time.time())}"
        
        try:
            # Update tool availability
            await self._update_tool_availability()
            
            # Select best tool
            selected_tool = await self._select_tool(task_type, preferred_tool)
            
            if not selected_tool:
                raise Exception("No AI tools available for this task")
            
            # Execute task
            result = await self._execute_with_tool(selected_tool, task_type, request_data)
            
            # Update metrics
            latency = time.time() - start_time
            await self._update_metrics(task_type, selected_tool, latency, True)
            
            # Log execution
            await self._log_execution(
                task_id=task_id,
                task_type=task_type,
                selected_tool=selected_tool,
                status="success",
                latency=latency,
                result=result
            )
            
            return {
                "task_id": task_id,
                "task_type": task_type.value,
                "selected_tool": selected_tool.value,
                "status": "success",
                "result": result,
                "latency": latency,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            # Update error metrics
            latency = time.time() - start_time
            await self._update_metrics(task_type, None, latency, False)
            
            # Log error
            await self._log_execution(
                task_id=task_id,
                task_type=task_type,
                selected_tool=None,
                status="error",
                latency=latency,
                error=str(e)
            )
            
            return {
                "task_id": task_id,
                "task_type": task_type.value,
                "status": "error",
                "error": str(e),
                "latency": latency,
                "timestamp": datetime.now().isoformat()
            }
    
    async def analyze_code(self, file_path: str, analysis_depth: str = "standard") -> Dict:
        """Analyze code using the best available tool"""
        request_data = {
            "file_path": file_path,
            "analysis_depth": analysis_depth
        }
        return await self.execute_task(TaskType.CODE_ANALYSIS, request_data)
    
    async def generate_code(self, prompt: str, language: str = "python", 
                          context: Dict = None) -> Dict:
        """Generate code using the best available tool"""
        request_data = {
            "prompt": prompt,
            "language": language,
            "context": context or {}
        }
        return await self.execute_task(TaskType.CODE_GENERATION, request_data)
    
    async def refactor_code(self, code_content: str, refactor_goals: List[str],
                          file_path: str = None) -> Dict:
        """Refactor code using the best available tool"""
        request_data = {
            "code_content": code_content,
            "refactor_goals": refactor_goals,
            "file_path": file_path
        }
        return await self.execute_task(TaskType.CODE_REFACTORING, request_data)
    
    async def analyze_project(self, project_path: str, analysis_type: str = "comprehensive") -> Dict:
        """Analyze entire project using the best available tool"""
        request_data = {
            "project_path": project_path,
            "analysis_type": analysis_type
        }
        return await self.execute_task(TaskType.PROJECT_ANALYSIS, request_data)
    
    async def get_code_completions(self, code_context: str, cursor_position: int,
                                 file_path: str = None, language: str = "python") -> Dict:
        """Get code completions using the best available tool"""
        request_data = {
            "code_context": code_context,
            "cursor_position": cursor_position,
            "file_path": file_path,
            "language": language
        }
        return await self.execute_task(TaskType.CODE_COMPLETION, request_data)
    
    async def suggest_improvements(self, code_content: str, file_path: str = None) -> Dict:
        """Get improvement suggestions using the best available tool"""
        request_data = {
            "code_content": code_content,
            "file_path": file_path
        }
        return await self.execute_task(TaskType.IMPROVEMENT_SUGGESTIONS, request_data)
    
    async def generate_documentation(self, code_content: str, doc_type: str = "docstring") -> Dict:
        """Generate documentation using the best available tool"""
        request_data = {
            "code_content": code_content,
            "doc_type": doc_type
        }
        return await self.execute_task(TaskType.DOCUMENTATION, request_data)
    
    async def compare_tools(self, test_prompt: str) -> Dict:
        """Compare performance of all available AI tools"""
        comparison_results = {
            "test_prompt": test_prompt,
            "timestamp": datetime.now().isoformat(),
            "tool_results": {},
            "analysis": {}
        }
        
        available_tools = [tool for tool, status in self.tool_status.items() if status["available"]]
        
        for tool in available_tools:
            try:
                start_time = time.time()
                result = await self._execute_with_tool(
                    tool, 
                    TaskType.CODE_GENERATION, 
                    {"prompt": test_prompt, "language": "python"}
                )
                latency = time.time() - start_time
                
                comparison_results["tool_results"][tool.value] = {
                    "latency": latency,
                    "success": True,
                    "result_length": len(str(result))
                }
                
            except Exception as e:
                comparison_results["tool_results"][tool.value] = {
                    "latency": 0,
                    "success": False,
                    "error": str(e)
                }
        
        # Analyze results
        comparison_results["analysis"] = await self._analyze_tool_comparison(
            comparison_results["tool_results"]
        )
        
        return comparison_results
    
    async def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        await self._update_tool_availability()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "tool_status": {
                tool.value: status for tool, status in self.tool_status.items()
            },
            "performance_metrics": self.performance_metrics.copy(),
            "load_balancer_state": {
                "tool_loads": self.load_balancer["tool_loads"].copy(),
                "round_robin_index": self.load_balancer["round_robin_index"]
            },
            "system_health": self._calculate_system_health()
        }
    
    async def _initialize_tools(self) -> None:
        """Initialize all AI tools"""
        print("🔧 Initializing AI tools...")
        
        # Initialize database tables
        await self._setup_orchestrator_database()
        
        # Check tool availability
        await self._update_tool_availability()
        
        available_count = sum(1 for status in self.tool_status.values() if status["available"])
        print(f"✅ Initialized {available_count}/{len(self.tool_status)} AI tools")
    
    async def _update_tool_availability(self) -> None:
        """Update availability status for all tools"""
        current_time = datetime.now()
        
        for tool in AITool:
            # Check if we need to update (cache for 60 seconds)
            last_check = self.tool_status[tool]["last_check"]
            if last_check and (current_time - last_check).seconds < 60:
                continue
            
            try:
                available = await self._check_tool_availability(tool)
                self.tool_status[tool] = {
                    "available": available,
                    "last_check": current_time
                }
            except Exception as e:
                logger.warning(f"Failed to check {tool.value} availability: {e}")
                self.tool_status[tool]["available"] = False
    
    async def _check_tool_availability(self, tool: AITool) -> bool:
        """Check if a specific tool is available"""
        try:
            if tool == AITool.CURSOR_AI:
                from ai_components.cursor_ai.cursor_integration_enhanced import CursorAIClient
                async with CursorAIClient() as client:
                    test_result = await client.test_integration()
                    return test_result.get("tests", {}).get("api_connectivity", {}).get("status") == "passed"
            
            elif tool == AITool.CLAUDE:
                from ai_components.claude.claude_analyzer import ClaudeAnalyzer
                # Check if API key is configured
                return bool(os.environ.get('ANTHROPIC_API_KEY'))
            
            elif tool == AITool.GITHUB_COPILOT:
                from ai_components.github_copilot.copilot_integration import GitHubCopilotClient
                # Check if integration is possible (always true for simulation)
                return True
            
            elif tool == AITool.ROO_CODE:
                # Check if Roo configuration exists
                return Path(".roo").exists()
            
            elif tool == AITool.FACTORY_AI:
                # Check if Factory AI configuration exists
                return Path(".factory").exists()
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking {tool.value} availability: {e}")
            return False
    
    async def _select_tool(self, task_type: TaskType, preferred_tool: AITool = None) -> Optional[AITool]:
        """Select the best tool for a given task type"""
        # If preferred tool is specified and available, use it
        if preferred_tool and self.tool_status[preferred_tool]["available"]:
            return preferred_tool
        
        # Get available tools for this task type
        preferred_tools = self.tool_preferences[task_type]
        available_tools = [
            tool for tool in preferred_tools 
            if self.tool_status[tool]["available"]
        ]
        
        if not available_tools:
            return None
        
        # Load balancing: select tool with lowest current load
        selected_tool = min(
            available_tools,
            key=lambda tool: self.load_balancer["tool_loads"][tool.value]
        )
        
        # Update load
        self.load_balancer["tool_loads"][selected_tool.value] += 1
        
        return selected_tool
    
    async def _execute_with_tool(self, tool: AITool, task_type: TaskType, request_data: Dict) -> Dict:
        """Execute task with specific tool"""
        try:
            if tool == AITool.CURSOR_AI:
                return await self._execute_cursor_ai(task_type, request_data)
            elif tool == AITool.CLAUDE:
                return await self._execute_claude(task_type, request_data)
            elif tool == AITool.GITHUB_COPILOT:
                return await self._execute_github_copilot(task_type, request_data)
            elif tool == AITool.ROO_CODE:
                return await self._execute_roo_code(task_type, request_data)
            elif tool == AITool.FACTORY_AI:
                return await self._execute_factory_ai(task_type, request_data)
            else:
                raise Exception(f"Unknown tool: {tool}")
                
        finally:
            # Decrease load after execution
            self.load_balancer["tool_loads"][tool.value] = max(
                0, self.load_balancer["tool_loads"][tool.value] - 1
            )
    
    async def _execute_cursor_ai(self, task_type: TaskType, request_data: Dict) -> Dict:
        """Execute task with Cursor AI"""
        from ai_components.cursor_ai.cursor_integration_enhanced import CursorAIClient
        
        async with CursorAIClient() as client:
            if task_type == TaskType.CODE_ANALYSIS:
                return await client.analyze_code(request_data["file_path"])
            elif task_type == TaskType.CODE_GENERATION:
                return await client.generate_code(
                    request_data["prompt"], 
                    request_data.get("context", {})
                )
            elif task_type == TaskType.CODE_REFACTORING:
                return await client.refactor_code(
                    request_data["file_path"],
                    "optimization",
                    request_data.get("context", {})
                )
            else:
                raise Exception(f"Task type {task_type} not supported by Cursor AI")
    
    async def _execute_claude(self, task_type: TaskType, request_data: Dict) -> Dict:
        """Execute task with Claude"""
        from ai_components.claude.claude_analyzer import ClaudeAnalyzer
        
        async with ClaudeAnalyzer() as analyzer:
            if task_type == TaskType.CODE_ANALYSIS:
                # For file analysis, read file and analyze content
                file_path = request_data["file_path"]
                with open(file_path, 'r') as f:
                    code_content = f.read()
                return await analyzer.refactor_code(
                    code_content, 
                    ["analyze code quality", "identify issues"],
                    file_path
                )
            elif task_type == TaskType.CODE_GENERATION:
                return await analyzer.generate_code(
                    request_data["prompt"],
                    request_data.get("context", {}),
                    "implementation"
                )
            elif task_type == TaskType.CODE_REFACTORING:
                return await analyzer.refactor_code(
                    request_data["code_content"],
                    request_data["refactor_goals"],
                    request_data.get("file_path")
                )
            elif task_type == TaskType.PROJECT_ANALYSIS:
                return await analyzer.analyze_project(
                    request_data["project_path"],
                    request_data.get("analysis_type", "comprehensive")
                )
            else:
                raise Exception(f"Task type {task_type} not supported by Claude")
    
    async def _execute_github_copilot(self, task_type: TaskType, request_data: Dict) -> Dict:
        """Execute task with GitHub Copilot"""
        from ai_components.github_copilot.copilot_integration import GitHubCopilotClient
        
        async with GitHubCopilotClient() as client:
            if task_type == TaskType.CODE_COMPLETION:
                return await client.get_code_completions(
                    request_data["code_context"],
                    request_data["cursor_position"],
                    request_data.get("file_path"),
                    request_data.get("language", "python")
                )
            elif task_type == TaskType.IMPROVEMENT_SUGGESTIONS:
                return await client.suggest_improvements(
                    request_data["code_content"],
                    request_data.get("file_path")
                )
            elif task_type == TaskType.DOCUMENTATION:
                return await client.generate_documentation(
                    request_data["code_content"],
                    request_data.get("doc_type", "docstring")
                )
            elif task_type == TaskType.CODE_GENERATION:
                # Simulate code generation using completion
                return await client.get_code_completions(
                    request_data["prompt"],
                    len(request_data["prompt"])
                )
            else:
                raise Exception(f"Task type {task_type} not supported by GitHub Copilot")
    
    async def _execute_roo_code(self, task_type: TaskType, request_data: Dict) -> Dict:
        """Execute task with Roo Code (via MCP)"""
        # Roo Code works through MCP servers - simulate integration
        return {
            "tool": "roo_code",
            "task_type": task_type.value,
            "result": "Roo Code execution simulated",
            "note": "Integrate with actual Roo mode switching for real implementation"
        }
    
    async def _execute_factory_ai(self, task_type: TaskType, request_data: Dict) -> Dict:
        """Execute task with Factory AI"""
        # Factory AI is architecturally ready but not implemented - simulate
        return {
            "tool": "factory_ai",
            "task_type": task_type.value,
            "result": "Factory AI execution simulated",
            "note": "Factory AI droids are configured but need real API integration"
        }
    
    async def _update_metrics(self, task_type: TaskType, selected_tool: Optional[AITool],
                            latency: float, success: bool) -> None:
        """Update performance metrics"""
        self.performance_metrics["total_requests"] += 1
        
        if success:
            self.performance_metrics["successful_requests"] += 1
            if selected_tool:
                self.performance_metrics["tool_usage"][selected_tool.value] += 1
        else:
            self.performance_metrics["failed_requests"] += 1
        
        self.performance_metrics["task_distribution"][task_type.value] += 1
        self.performance_metrics["total_latency"] += latency
        self.performance_metrics["average_latency"] = (
            self.performance_metrics["total_latency"] / 
            self.performance_metrics["total_requests"]
        )
    
    async def _log_execution(self, task_id: str, task_type: TaskType, 
                           selected_tool: Optional[AITool], status: str,
                           latency: float, result: Dict = None, error: str = None) -> None:
        """Log task execution to database"""
        try:
            await self.db.execute_query(
                """
                INSERT INTO ai_orchestrator_logs 
                (task_id, task_type, selected_tool, status, latency_seconds, 
                 result, error_message, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                task_id, task_type.value, 
                selected_tool.value if selected_tool else None,
                status, latency, 
                json.dumps(result) if result else None,
                error, datetime.now()
            )
        except Exception as e:
            logger.error(f"Failed to log execution: {e}")
    
    async def _analyze_tool_comparison(self, tool_results: Dict) -> Dict:
        """Analyze comparison results between tools"""
        analysis = {
            "fastest_tool": None,
            "most_reliable": None,
            "success_rate": 0,
            "average_latency": 0,
            "recommendations": []
        }
        
        successful_tools = {
            tool: result for tool, result in tool_results.items() 
            if result.get("success", False)
        }
        
        if successful_tools:
            # Find fastest tool
            fastest = min(successful_tools.items(), key=lambda x: x[1]["latency"])
            analysis["fastest_tool"] = fastest[0]
            
            # Calculate success rate
            analysis["success_rate"] = len(successful_tools) / len(tool_results)
            
            # Calculate average latency
            total_latency = sum(result["latency"] for result in successful_tools.values())
            analysis["average_latency"] = total_latency / len(successful_tools)
            
            # Generate recommendations
            if analysis["success_rate"] >= 0.8:
                analysis["recommendations"].append("Multiple tools available - good redundancy")
            
            if analysis["fastest_tool"]:
                analysis["recommendations"].append(
                    f"Use {analysis['fastest_tool']} for fastest response times"
                )
        
        return analysis
    
    def _calculate_system_health(self) -> Dict:
        """Calculate overall system health"""
        available_tools = sum(1 for status in self.tool_status.values() if status["available"])
        total_tools = len(self.tool_status)
        
        success_rate = (
            self.performance_metrics["successful_requests"] / 
            max(1, self.performance_metrics["total_requests"])
        )
        
        health_score = (
            (available_tools / total_tools) * 0.5 +  # Tool availability: 50%
            success_rate * 0.3 +  # Success rate: 30%
            (1.0 if self.performance_metrics["average_latency"] < 5.0 else 0.5) * 0.2  # Latency: 20%
        ) * 100
        
        return {
            "health_score": health_score,
            "available_tools": available_tools,
            "total_tools": total_tools,
            "success_rate": success_rate,
            "average_latency": self.performance_metrics["average_latency"],
            "status": "healthy" if health_score >= 80 else "degraded" if health_score >= 60 else "critical"
        }
    
    async def _setup_orchestrator_database(self) -> None:
        """Setup database tables for orchestrator"""
        await self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS ai_orchestrator_logs (
                id SERIAL PRIMARY KEY,
                task_id VARCHAR(200) NOT NULL,
                task_type VARCHAR(100) NOT NULL,
                selected_tool VARCHAR(100),
                status VARCHAR(50) NOT NULL,
                latency_seconds FLOAT DEFAULT 0.0,
                result JSONB,
                error_message TEXT,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL
            );
        """)
        
        await self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_orchestrator_logs_task_type 
            ON ai_orchestrator_logs(task_type);
        """)
        
        await self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_orchestrator_logs_created_at 
            ON ai_orchestrator_logs(created_at DESC);
        """)


async def main():
    """Test the unified AI system orchestrator"""
    print("🚀 Testing Unified AI System Orchestrator...")
    
    async with AISystemOrchestrator() as orchestrator:
        # Get system status
        print("\n📊 System Status:")
        status = await orchestrator.get_system_status()
        print(json.dumps(status, indent=2, default=str))
        
        # Test code generation
        print("\n🏗️  Testing code generation...")
        try:
            result = await orchestrator.generate_code(
                "Create a Python function that calculates the area of a circle",
                "python"
            )
            print(f"✅ Code generation: {result['status']} using {result.get('selected_tool', 'unknown')}")
        except Exception as e:
            print(f"❌ Code generation failed: {e}")
        
        # Test code analysis
        print("\n🔍 Testing code analysis...")
        try:
            # Analyze this file
            result = await orchestrator.analyze_code(__file__)
            print(f"✅ Code analysis: {result['status']} using {result.get('selected_tool', 'unknown')}")
        except Exception as e:
            print(f"❌ Code analysis failed: {e}")
        
        # Test code completion
        print("\n💡 Testing code completion...")
        try:
            result = await orchestrator.get_code_completions(
                "def fibonacci(n", 15, "test.py", "python"
            )
            print(f"✅ Code completion: {result['status']} using {result.get('selected_tool', 'unknown')}")
        except Exception as e:
            print(f"❌ Code completion failed: {e}")
        
        # Compare tools
        print("\n⚖️  Comparing AI tools...")
        try:
            comparison = await orchestrator.compare_tools("def hello_world():")
            print("✅ Tool comparison completed")
            analysis = comparison.get("analysis", {})
            if analysis.get("fastest_tool"):
                print(f"   Fastest tool: {analysis['fastest_tool']}")
            print(f"   Success rate: {analysis.get('success_rate', 0):.1%}")
        except Exception as e:
            print(f"❌ Tool comparison failed: {e}")
        
        # Final system status
        print("\n📈 Final System Status:")
        final_status = await orchestrator.get_system_status()
        health = final_status["system_health"]
        print(f"   Health Score: {health['health_score']:.1f}/100")
        print(f"   Status: {health['status']}")
        print(f"   Available Tools: {health['available_tools']}/{health['total_tools']}")
        print(f"   Success Rate: {health['success_rate']:.1%}")


if __name__ == "__main__":
    asyncio.run(main()) 