# Orchestra AI Orchestrator Engine
# Core orchestration system using LangGraph for multi-agent coordination

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from typing import Dict, List, Any, Optional, TypedDict
import asyncio
import json
import logging
from datetime import datetime
import uuid
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrchestratorState(TypedDict):
    """State management for orchestrator workflows"""
    task_id: str
    original_message: str
    task_type: str
    complexity: str
    persona: str
    context: Dict[str, Any]
    task_queue: List[Dict]
    active_agents: Dict[str, Any]
    agent_results: List[Dict]
    final_response: str
    workflow_steps: List[str]
    performance_metrics: Dict[str, Any]
    error_log: List[str]

class BaseAgent:
    """Base class for specialized agents"""
    
    def __init__(self, name: str, description: str, tools: List = None):
        self.name = name
        self.description = description
        self.tools = tools or []
        
        # Initialize LLM with fallback
        try:
            self.llm = ChatOpenAI(
                model="gpt-4-turbo-preview",
                temperature=0.3,
                max_tokens=1500,
                openai_api_key=os.getenv("OPENAI_API_KEY", "demo_key")
            )
        except Exception as e:
            logger.warning(f"Failed to initialize LLM for {name}: {str(e)}. Using mock mode.")
            self.llm = None
    
    async def execute(self, task: Dict, context: Dict) -> Dict:
        """Execute agent task"""
        try:
            if self.llm is None:
                # Mock response when LLM is not available
                return {
                    "agent_name": self.name,
                    "task_id": task.get("id"),
                    "result": f"I'm {self.name} and I would help with: {task.get('instruction', 'the requested task')}. (Demo mode)",
                    "status": "completed",
                    "execution_time": datetime.now().isoformat()
                }
            
            # Prepare messages for the agent
            messages = [
                SystemMessage(content=f"You are {self.name}. {self.description}"),
                HumanMessage(content=task.get("instruction", ""))
            ]
            
            # Get response from LLM
            response = await self.llm.ainvoke(messages)
            
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": response.content,
                "status": "completed",
                "execution_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Agent {self.name} execution failed: {str(e)}")
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": f"Error: {str(e)}",
                "status": "failed",
                "execution_time": datetime.now().isoformat()
            }

class PersonaOrchestrator:
    """Base orchestrator for persona-specific agent management"""
    
    def __init__(self, persona_name: str, model_config: Dict):
        self.persona_name = persona_name
        self.model_config = model_config
        self.agents = {}
        self.workflow_graph = self._build_workflow_graph()
        
        # Initialize primary LLM with fallback
        try:
            self.primary_llm = ChatOpenAI(
                model=model_config.get("primary_model", "gpt-4-turbo-preview"),
                temperature=model_config.get("temperature", 0.5),
                max_tokens=model_config.get("max_tokens", 2000),
                openai_api_key=os.getenv("OPENAI_API_KEY", "demo_key")
            )
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI LLM: {str(e)}. Using mock LLM.")
            self.primary_llm = None
    
    def _build_workflow_graph(self) -> StateGraph:
        """Build LangGraph workflow for persona orchestration"""
        workflow = StateGraph(OrchestratorState)
        
        # Add workflow nodes
        workflow.add_node("task_analyzer", self._analyze_task)
        workflow.add_node("agent_selector", self._select_agents)
        workflow.add_node("task_executor", self._execute_tasks)
        workflow.add_node("result_synthesizer", self._synthesize_results)
        workflow.add_node("quality_checker", self._check_quality)
        
        # Define workflow edges
        workflow.add_edge("task_analyzer", "agent_selector")
        workflow.add_edge("agent_selector", "task_executor")
        workflow.add_edge("task_executor", "result_synthesizer")
        workflow.add_edge("result_synthesizer", "quality_checker")
        workflow.add_edge("quality_checker", END)
        
        # Set entry point
        workflow.set_entry_point("task_analyzer")
        
        return workflow.compile()
    
    async def orchestrate_task(self, request: Dict) -> Dict:
        """Main orchestration method"""
        try:
            # Initialize state
            initial_state = OrchestratorState(
                task_id=str(uuid.uuid4()),
                original_message=request.get("message", ""),
                task_type="",
                complexity="",
                persona=self.persona_name,
                context=request.get("context", {}),
                task_queue=[],
                active_agents={},
                agent_results=[],
                final_response="",
                workflow_steps=[],
                performance_metrics={},
                error_log=[]
            )
            
            # Execute workflow
            start_time = datetime.now()
            final_state = await self.workflow_graph.ainvoke(initial_state)
            end_time = datetime.now()
            
            # Calculate performance metrics
            execution_time = (end_time - start_time).total_seconds()
            final_state["performance_metrics"] = {
                "execution_time": execution_time,
                "agents_used": len(final_state.get("agent_results", [])),
                "workflow_steps": len(final_state.get("workflow_steps", [])),
                "success_rate": 1.0 if not final_state.get("error_log") else 0.8
            }
            
            return {
                "task_id": final_state["task_id"],
                "response": final_state["final_response"],
                "orchestration_used": True,
                "agents_involved": [r["agent_name"] for r in final_state.get("agent_results", [])],
                "workflow_steps": final_state["workflow_steps"],
                "performance_metrics": final_state["performance_metrics"],
                "persona": self.persona_name
            }
            
        except Exception as e:
            logger.error(f"Orchestration failed for {self.persona_name}: {str(e)}")
            return {
                "task_id": str(uuid.uuid4()),
                "response": f"I apologize, but I encountered an error while processing your request. Let me provide a direct response instead.",
                "orchestration_used": False,
                "error": str(e),
                "persona": self.persona_name
            }
    
    async def _analyze_task(self, state: OrchestratorState) -> OrchestratorState:
        """Analyze incoming task complexity and requirements"""
        try:
            message = state["original_message"]
            
            # Analyze task complexity
            complexity_prompt = f"""
            Analyze this task and determine its complexity level and type:
            Task: "{message}"
            
            Respond with JSON format:
            {{
                "complexity": "simple|medium|complex",
                "task_type": "creative|analytical|operational|conversational",
                "requires_orchestration": true|false,
                "estimated_agents_needed": number,
                "reasoning": "brief explanation"
            }}
            """
            
            analysis_response = await self.primary_llm.ainvoke([
                SystemMessage(content="You are a task analysis expert."),
                HumanMessage(content=complexity_prompt)
            ])
            
            # Parse analysis
            try:
                analysis = json.loads(analysis_response.content)
                state["complexity"] = analysis.get("complexity", "medium")
                state["task_type"] = analysis.get("task_type", "conversational")
                state["workflow_steps"].append("task_analyzed")
                
                logger.info(f"Task analyzed: {analysis}")
                
            except json.JSONDecodeError:
                # Fallback analysis
                state["complexity"] = "medium"
                state["task_type"] = "conversational"
                state["error_log"].append("Failed to parse task analysis")
            
            return state
            
        except Exception as e:
            state["error_log"].append(f"Task analysis failed: {str(e)}")
            state["complexity"] = "simple"
            state["task_type"] = "conversational"
            return state
    
    async def _select_agents(self, state: OrchestratorState) -> OrchestratorState:
        """Select appropriate agents for task execution"""
        try:
            complexity = state["complexity"]
            task_type = state["task_type"]
            
            # Get available agents for this persona
            available_agents = self.get_available_agents()
            
            if complexity == "simple" or not available_agents:
                # Use direct response for simple tasks
                state["task_queue"] = []
                state["workflow_steps"].append("direct_response_selected")
                return state
            
            # Select agents based on task type and complexity
            selected_agents = self._choose_agents_for_task(task_type, complexity, available_agents)
            
            # Create task queue
            state["task_queue"] = [
                {
                    "id": str(uuid.uuid4()),
                    "agent_name": agent_name,
                    "instruction": self._create_agent_instruction(agent_name, state["original_message"]),
                    "priority": idx
                }
                for idx, agent_name in enumerate(selected_agents)
            ]
            
            state["workflow_steps"].append(f"agents_selected: {', '.join(selected_agents)}")
            logger.info(f"Selected agents: {selected_agents}")
            
            return state
            
        except Exception as e:
            state["error_log"].append(f"Agent selection failed: {str(e)}")
            state["task_queue"] = []
            return state
    
    async def _execute_tasks(self, state: OrchestratorState) -> OrchestratorState:
        """Execute tasks with selected agents"""
        try:
            if not state["task_queue"]:
                # Direct response without agents
                direct_response = await self._get_direct_response(state["original_message"])
                state["agent_results"] = [{
                    "agent_name": "direct_response",
                    "result": direct_response,
                    "status": "completed"
                }]
                state["workflow_steps"].append("direct_response_generated")
                return state
            
            # Execute agent tasks
            agent_results = []
            for task in state["task_queue"]:
                agent_name = task["agent_name"]
                agent = self.agents.get(agent_name)
                
                if agent:
                    result = await agent.execute(task, state["context"])
                    agent_results.append(result)
                else:
                    # Fallback to LLM-based execution
                    result = await self._execute_with_llm(task, agent_name)
                    agent_results.append(result)
            
            state["agent_results"] = agent_results
            state["workflow_steps"].append(f"executed_{len(agent_results)}_agents")
            
            return state
            
        except Exception as e:
            state["error_log"].append(f"Task execution failed: {str(e)}")
            # Fallback to direct response
            direct_response = await self._get_direct_response(state["original_message"])
            state["agent_results"] = [{
                "agent_name": "fallback_response",
                "result": direct_response,
                "status": "completed"
            }]
            return state
    
    async def _synthesize_results(self, state: OrchestratorState) -> OrchestratorState:
        """Combine and synthesize results from multiple agents"""
        try:
            agent_results = state["agent_results"]
            
            if len(agent_results) == 1:
                # Single result, use directly
                state["final_response"] = agent_results[0]["result"]
                state["workflow_steps"].append("single_result_used")
                return state
            
            # Synthesize multiple results
            synthesis_prompt = f"""
            Original request: "{state['original_message']}"
            
            Agent results to synthesize:
            {json.dumps([{"agent": r["agent_name"], "result": r["result"]} for r in agent_results], indent=2)}
            
            Create a comprehensive, coherent response that integrates the best insights from all agents.
            Maintain the {self.persona_name} persona voice and style.
            """
            
            synthesis_response = await self.primary_llm.ainvoke([
                SystemMessage(content=f"You are {self.persona_name}, synthesizing multiple agent results into a coherent response."),
                HumanMessage(content=synthesis_prompt)
            ])
            
            state["final_response"] = synthesis_response.content
            state["workflow_steps"].append("results_synthesized")
            
            return state
            
        except Exception as e:
            state["error_log"].append(f"Result synthesis failed: {str(e)}")
            # Use first available result as fallback
            if state["agent_results"]:
                state["final_response"] = state["agent_results"][0]["result"]
            else:
                state["final_response"] = "I apologize, but I encountered an error processing your request."
            return state
    
    async def _check_quality(self, state: OrchestratorState) -> OrchestratorState:
        """Quality check and final validation"""
        try:
            response = state["final_response"]
            
            # Basic quality checks
            if len(response) < 10:
                state["error_log"].append("Response too short")
                # Generate fallback response
                fallback = await self._get_direct_response(state["original_message"])
                state["final_response"] = fallback
            
            state["workflow_steps"].append("quality_checked")
            return state
            
        except Exception as e:
            state["error_log"].append(f"Quality check failed: {str(e)}")
            return state
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agents for this persona"""
        return list(self.agents.keys())
    
    def _choose_agents_for_task(self, task_type: str, complexity: str, available_agents: List[str]) -> List[str]:
        """Choose appropriate agents based on task characteristics"""
        # Default implementation - override in persona-specific orchestrators
        if complexity == "complex" and len(available_agents) > 1:
            return available_agents[:2]  # Use first 2 agents for complex tasks
        elif available_agents:
            return [available_agents[0]]  # Use first agent for simpler tasks
        return []
    
    def _create_agent_instruction(self, agent_name: str, original_message: str) -> str:
        """Create specific instruction for an agent"""
        return f"As {agent_name}, help with this request: {original_message}"
    
    async def _get_direct_response(self, message: str) -> str:
        """Get direct response without agent orchestration"""
        try:
            if self.primary_llm is None:
                return f"I'm {self.persona_name}, and I'd be happy to help with: {message}. (Note: Full AI capabilities are currently in demo mode.)"
            
            response = await self.primary_llm.ainvoke([
                SystemMessage(content=f"You are {self.persona_name}. Respond directly to the user's request."),
                HumanMessage(content=message)
            ])
            return response.content
        except Exception as e:
            return f"I apologize, but I'm having trouble processing your request right now. Error: {str(e)}"
    
    async def _execute_with_llm(self, task: Dict, agent_name: str) -> Dict:
        """Execute task using LLM when specific agent is not available"""
        try:
            instruction = task["instruction"]
            response = await self.primary_llm.ainvoke([
                SystemMessage(content=f"You are acting as {agent_name} agent."),
                HumanMessage(content=instruction)
            ])
            
            return {
                "agent_name": agent_name,
                "task_id": task["id"],
                "result": response.content,
                "status": "completed",
                "execution_time": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "agent_name": agent_name,
                "task_id": task["id"],
                "result": f"Error executing task: {str(e)}",
                "status": "failed",
                "execution_time": datetime.now().isoformat()
            }

def should_use_orchestration(message: str, persona: str) -> bool:
    """Determine if message requires orchestration"""
    
    # Keywords that suggest complex tasks
    orchestration_keywords = [
        "analyze", "research", "create", "develop", "plan", "strategy",
        "comprehensive", "detailed", "multi-step", "workflow", "process",
        "campaign", "project", "report", "presentation", "automation",
        "compare", "evaluate", "design", "build", "implement"
    ]
    
    # Check for multiple requirements
    requirement_indicators = [
        "and", "also", "additionally", "furthermore", "then", "after",
        "step", "phase", "stage", "first", "second", "next", "both"
    ]
    
    message_lower = message.lower()
    
    # Count orchestration indicators
    orchestration_score = sum(1 for keyword in orchestration_keywords if keyword in message_lower)
    requirement_score = sum(1 for indicator in requirement_indicators if indicator in message_lower)
    
    # Length-based complexity
    length_score = len(message.split()) / 20  # Normalize by word count
    
    total_score = orchestration_score + requirement_score + length_score
    
    # Lower threshold for creative and strategic personas
    threshold = 1.5 if persona in ["cherry", "sophia"] else 2.0
    
    return total_score >= threshold

# Export main classes
__all__ = [
    "PersonaOrchestrator",
    "BaseAgent", 
    "OrchestratorState",
    "should_use_orchestration"
]

