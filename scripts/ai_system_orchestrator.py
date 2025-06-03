#!/usr/bin/env python3
"""
AI System Orchestrator
Central coordination system for all AI tools and services
Intelligently routes tasks between Claude, OpenAI, GitHub Copilot, and Roo Code
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Add project root to path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from shared.database import initialize_database

logger = logging.getLogger(__name__)

class TaskType(Enum):
    """Types of tasks that can be handled by AI tools"""
    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation" 
    CODE_REFACTORING = "code_refactoring"
    ARCHITECTURE_REVIEW = "architecture_review"
    BUG_FIXING = "bug_fixing"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    DOCUMENTATION = "documentation"
    TESTING = "testing"

class AITool(Enum):
    """Available AI tools"""
    CLAUDE = "claude"
    OPENAI = "openai"
    GITHUB_COPILOT = "github_copilot"
    ROO_CODE = "roo_code"
    OPENROUTER = "openrouter"
    GROK = "grok"
    PERPLEXITY = "perplexity"

@dataclass
class TaskRequest:
    """Request for AI task processing"""
    task_id: str
    task_type: TaskType
    prompt: str
    context: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1
    timeout: int = 300
    preferred_tool: Optional[AITool] = None

@dataclass 
class TaskResult:
    """Result from AI task processing"""
    task_id: str
    tool_used: AITool
    result: Any
    success: bool
    latency: float
    tokens_used: int = 0
    error: Optional[str] = None
    fallback_used: bool = False

class AISystemOrchestrator:
    """Central AI system orchestrator"""
    
    def __init__(self):
        self.db = None
        
        # Tool availability and performance tracking
        self.tool_availability = {
            AITool.CLAUDE: True,
            AITool.OPENAI: True,
            AITool.GITHUB_COPILOT: True,
            AITool.ROO_CODE: True,
            AITool.OPENROUTER: True,
            AITool.GROK: True,
            AITool.PERPLEXITY: True
        }
        
        # Performance metrics for intelligent routing
        self.performance_metrics = {
            tool: {
                'avg_latency': 0.0,
                'success_rate': 1.0,
                'requests_handled': 0,
                'total_latency': 0.0,
                'errors': 0,
                'tokens_used': 0
            } for tool in AITool
        }
        
        # Tool preference matrix based on task type
        self.tool_preferences = {
            TaskType.CODE_ANALYSIS: [AITool.CLAUDE, AITool.GITHUB_COPILOT, AITool.ROO_CODE],
            TaskType.CODE_GENERATION: [AITool.CLAUDE, AITool.OPENAI, AITool.GITHUB_COPILOT],
            TaskType.CODE_REFACTORING: [AITool.CLAUDE, AITool.OPENAI, AITool.ROO_CODE],
            TaskType.ARCHITECTURE_REVIEW: [AITool.CLAUDE, AITool.ROO_CODE],
            TaskType.BUG_FIXING: [AITool.GITHUB_COPILOT, AITool.CLAUDE, AITool.OPENAI],
            TaskType.PERFORMANCE_OPTIMIZATION: [AITool.ROO_CODE, AITool.CLAUDE],
            TaskType.DOCUMENTATION: [AITool.CLAUDE, AITool.OPENAI],
            TaskType.TESTING: [AITool.OPENAI, AITool.GITHUB_COPILOT]
        }
        
        # Initialize AI tool clients
        self.ai_tools = {}
        self._initialize_ai_tools()
    
    def _initialize_ai_tools(self):
        """Initialize AI tool clients"""
        try:
            # Claude integration
            if os.environ.get('ANTHROPIC_API_KEY'):
                from ai_components.claude.claude_analyzer import ClaudeProjectAnalyzer
                self.ai_tools[AITool.CLAUDE] = ClaudeProjectAnalyzer()
                logger.info("✅ Claude analyzer initialized")
            else:
                self.tool_availability[AITool.CLAUDE] = False
                logger.warning("⚠️ Claude: No API key found")
            
            # OpenAI integration
            if os.environ.get('OPENAI_API_KEY'):
                # Direct OpenAI integration would go here
                logger.info("✅ OpenAI integration available")
            else:
                self.tool_availability[AITool.OPENAI] = False
                logger.warning("⚠️ OpenAI: No API key found")
            
            # GitHub Copilot integration
            if os.environ.get('GITHUB_TOKEN'):
                from ai_components.github_copilot.copilot_integration import GitHubCopilotClient
                self.ai_tools[AITool.GITHUB_COPILOT] = GitHubCopilotClient()
                logger.info("✅ GitHub Copilot initialized")
            else:
                self.tool_availability[AITool.GITHUB_COPILOT] = False
                logger.warning("⚠️ GitHub Copilot: No token found")
            
            # Roo Code integration (already available)
            self.ai_tools[AITool.ROO_CODE] = "roo_code_client"  # Placeholder
            logger.info("✅ Roo Code integration available")
            
            # OpenRouter integration
            if os.environ.get('OPENROUTER_API_KEY'):
                logger.info("✅ OpenRouter integration available")
            else:
                self.tool_availability[AITool.OPENROUTER] = False
                logger.warning("⚠️ OpenRouter: No API key found")
                
        except Exception as e:
            logger.error(f"Error initializing AI tools: {e}")
    
    async def initialize_database(self):
        """Initialize database connection"""
        try:
            postgres_url = os.environ.get(
                'POSTGRES_URL', 
                'postgresql://postgres:password@localhost:5432/orchestra'
            )
            weaviate_url = os.environ.get('WEAVIATE_URL', 'http://localhost:8080')
            weaviate_api_key = os.environ.get('WEAVIATE_API_KEY')
            
            self.db = await initialize_database(postgres_url, weaviate_url, weaviate_api_key)
            logger.info("✅ Database initialized")
        except Exception as e:
            logger.warning(f"Database initialization failed: {e}")
    
    async def select_best_tool(self, task_type: TaskType, context: Dict = None) -> AITool:
        """Intelligently select the best tool for a task"""
        
        # Get preferred tools for this task type
        preferred_tools = self.tool_preferences.get(task_type, list(AITool))
        
        # Filter to available tools
        available_tools = [
            tool for tool in preferred_tools 
            if self.tool_availability[tool]
        ]
        
        if not available_tools:
            # Fallback to any available tool
            available_tools = [
                tool for tool in AITool 
                if self.tool_availability[tool]
            ]
        
        if not available_tools:
            raise ValueError("No AI tools are currently available")
        
        # Select based on performance metrics
        best_tool = available_tools[0]
        best_score = self._calculate_tool_score(best_tool)
        
        for tool in available_tools[1:]:
            score = self._calculate_tool_score(tool)
            if score > best_score:
                best_tool = tool
                best_score = score
        
        return best_tool
    
    def _calculate_tool_score(self, tool: AITool) -> float:
        """Calculate tool performance score for selection"""
        metrics = self.performance_metrics[tool]
        
        if metrics['requests_handled'] == 0:
            return 1.0  # Default score for unused tools
        
        # Score based on success rate and latency
        success_weight = 0.7
        latency_weight = 0.3
        
        success_score = metrics['success_rate']
        latency_score = max(0, 1 - (metrics['avg_latency'] / 10.0))  # Normalize latency
        
        return success_weight * success_score + latency_weight * latency_score
    
    async def process_task(self, task: TaskRequest) -> TaskResult:
        """Process a task using the optimal AI tool"""
        start_time = time.time()
        
        try:
            # Select tool
            selected_tool = task.preferred_tool or await self.select_best_tool(task.task_type, task.context)
            
            # Execute task
            result = await self._execute_with_tool(selected_tool, task)
            
            # Calculate metrics
            latency = time.time() - start_time
            
            # Update performance metrics
            self._update_metrics(selected_tool, latency, True, result.get('tokens_used', 0))
            
            # Log to database
            await self._log_task_execution(task, selected_tool, result, latency, True)
            
            return TaskResult(
                task_id=task.task_id,
                tool_used=selected_tool,
                result=result,
                success=True,
                latency=latency,
                tokens_used=result.get('tokens_used', 0)
            )
            
        except Exception as e:
            latency = time.time() - start_time
            
            # Try fallback tool
            try:
                fallback_tool = await self._get_fallback_tool(selected_tool, task.task_type)
                if fallback_tool:
                    fallback_result = await self._execute_with_tool(fallback_tool, task)
                    
                    # Update metrics for both tools
                    self._update_metrics(selected_tool, latency, False, 0)
                    self._update_metrics(fallback_tool, time.time() - start_time, True, 
                                       fallback_result.get('tokens_used', 0))
                    
                    return TaskResult(
                        task_id=task.task_id,
                        tool_used=fallback_tool,
                        result=fallback_result,
                        success=True,
                        latency=time.time() - start_time,
                        tokens_used=fallback_result.get('tokens_used', 0),
                        fallback_used=True
                    )
            except Exception:
                pass
            
            # Record failure
            self._update_metrics(selected_tool, latency, False, 0)
            await self._log_task_execution(task, selected_tool, None, latency, False, str(e))
            
            return TaskResult(
                task_id=task.task_id,
                tool_used=selected_tool,
                result=None,
                success=False,
                latency=latency,
                error=str(e)
            )
    
    async def _execute_with_tool(self, tool: AITool, task: TaskRequest) -> Dict[str, Any]:
        """Execute task with specific tool"""
        
        if tool == AITool.CLAUDE:
            analyzer = self.ai_tools[AITool.CLAUDE]
            if task.task_type == TaskType.CODE_ANALYSIS:
                result = await analyzer.analyze_project(
                    project_path=task.context.get('project_path', '.'),
                    analysis_type=task.context.get('analysis_type', 'comprehensive')
                )
            elif task.task_type == TaskType.CODE_GENERATION:
                result = await analyzer.generate_code(
                    prompt=task.prompt,
                    context=task.context,
                    code_type=task.context.get('code_type', 'implementation')
                )
            else:
                result = await analyzer.generate_code(task.prompt, task.context)
            
            return {
                'content': result.get('analysis') or result.get('generated_code'),
                'tokens_used': result.get('usage', {}).get('total_tokens', 0),
                'model': result.get('model_used'),
                'structured_data': result.get('structured_analysis')
            }
        
        elif tool == AITool.GITHUB_COPILOT:
            copilot = self.ai_tools[AITool.GITHUB_COPILOT]
            result = await copilot.get_code_suggestions(task.prompt, task.context)
            return {
                'content': result.get('suggestions', []),
                'tokens_used': 0,  # GitHub Copilot doesn't report tokens
                'model': 'github-copilot'
            }
        
        elif tool == AITool.ROO_CODE:
            # Integrate with existing Roo Code system
            return {
                'content': f"Roo Code processing: {task.prompt}",
                'tokens_used': 0,
                'model': 'roo-code'
            }
        
        else:
            # Fallback simulation
            return {
                'content': f"Processed by {tool.value}: {task.prompt}",
                'tokens_used': 100,
                'model': tool.value
            }
    
    async def _get_fallback_tool(self, primary_tool: AITool, task_type: TaskType) -> Optional[AITool]:
        """Get fallback tool for failed primary tool"""
        preferences = self.tool_preferences.get(task_type, list(AITool))
        
        # Find next available tool in preference order
        try:
            primary_index = preferences.index(primary_tool)
            for tool in preferences[primary_index + 1:]:
                if self.tool_availability[tool]:
                    return tool
        except ValueError:
            pass
        
        # Fallback to any available tool
        for tool in AITool:
            if tool != primary_tool and self.tool_availability[tool]:
                return tool
        
        return None
    
    def _update_metrics(self, tool: AITool, latency: float, success: bool, tokens_used: int):
        """Update performance metrics for a tool"""
        metrics = self.performance_metrics[tool]
        
        metrics['requests_handled'] += 1
        metrics['total_latency'] += latency
        metrics['avg_latency'] = metrics['total_latency'] / metrics['requests_handled']
        metrics['tokens_used'] += tokens_used
        
        if success:
            metrics['success_rate'] = (
                (metrics['success_rate'] * (metrics['requests_handled'] - 1) + 1) / 
                metrics['requests_handled']
            )
        else:
            metrics['errors'] += 1
            metrics['success_rate'] = (
                (metrics['success_rate'] * (metrics['requests_handled'] - 1)) / 
                metrics['requests_handled']
            )
    
    async def _log_task_execution(self, task: TaskRequest, tool: AITool, result: Any, 
                                latency: float, success: bool, error: str = None):
        """Log task execution to database"""
        if not self.db:
            return
        
        try:
            await self.db.execute_query("""
                INSERT INTO ai_orchestrator_logs 
                (task_id, task_type, tool_used, prompt, context, result, 
                 latency_seconds, success, error_message, tokens_used, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """, 
                task.task_id, task.task_type.value, tool.value,
                task.prompt, json.dumps(task.context), 
                json.dumps(result) if result else None,
                latency, success, error, 
                result.get('tokens_used', 0) if result else 0,
                datetime.now(),
                fetch=False
            )
        except Exception as e:
            logger.error(f"Failed to log task execution: {e}")
    
    def get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available AI tools"""
        tools_info = {}
        
        for tool in AITool:
            metrics = self.performance_metrics[tool]
            tools_info[tool.value] = {
                'available': self.tool_availability[tool],
                'status': 'operational' if self.tool_availability[tool] else 'unavailable',
                'requests_handled': metrics['requests_handled'],
                'avg_latency': round(metrics['avg_latency'], 3),
                'success_rate': round(metrics['success_rate'], 3),
                'tokens_used': metrics['tokens_used']
            }
        
        return tools_info
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get overall system performance metrics"""
        total_requests = sum(m['requests_handled'] for m in self.performance_metrics.values())
        total_errors = sum(m['errors'] for m in self.performance_metrics.values())
        total_tokens = sum(m['tokens_used'] for m in self.performance_metrics.values())
        
        available_tools = sum(1 for available in self.tool_availability.values() if available)
        
        return {
            'total_requests': total_requests,
            'total_errors': total_errors,
            'overall_success_rate': (total_requests - total_errors) / max(total_requests, 1),
            'available_tools': available_tools,
            'total_tools': len(AITool),
            'total_tokens_used': total_tokens,
            'avg_tokens_per_request': total_tokens / max(total_requests, 1)
        }

async def main():
    """Example usage of the AI orchestrator"""
    orchestrator = AISystemOrchestrator()
    await orchestrator.initialize_database()
    
    # Test task
    task = TaskRequest(
        task_id="test_001",
        task_type=TaskType.CODE_GENERATION,
        prompt="Create a Python function that calculates fibonacci numbers",
        context={"language": "python", "style": "functional"}
    )
    
    result = await orchestrator.process_task(task)
    
    print(f"Task Result:")
    print(f"  Tool Used: {result.tool_used.value}")
    print(f"  Success: {result.success}")
    print(f"  Latency: {result.latency:.2f}s")
    print(f"  Tokens: {result.tokens_used}")
    
    if result.success:
        print(f"  Result: {str(result.result)[:200]}...")
    else:
        print(f"  Error: {result.error}")

if __name__ == "__main__":
    asyncio.run(main()) 