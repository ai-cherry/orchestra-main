# Orchestra AI Premium Configuration Implementation
# Quality and performance optimized orchestrator setup

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
try:
    from langchain_anthropic import ChatAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    ChatAnthropic = None
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

class PremiumOrchestratorState(TypedDict):
    """Enhanced state management for premium orchestrator workflows"""
    task_id: str
    original_message: str
    task_type: str
    complexity: str
    quality_requirement: float
    persona: str
    context: Dict[str, Any]
    task_queue: List[Dict]
    active_agents: Dict[str, Any]
    agent_results: List[Dict]
    validation_results: List[Dict]
    refinement_cycles: int
    final_response: str
    workflow_steps: List[str]
    performance_metrics: Dict[str, Any]
    quality_metrics: Dict[str, Any]
    error_log: List[str]

class PremiumBaseAgent:
    """Enhanced base class for premium specialized agents"""
    
    def __init__(self, name: str, description: str, model_config: Dict, tools: List = None):
        self.name = name
        self.description = description
        self.tools = tools or []
        self.model_config = model_config
        
        # Initialize premium LLM based on agent specialization
        self.llm = self._initialize_premium_llm(model_config)
        
        # Quality thresholds
        self.quality_threshold = 0.85
        self.max_refinement_cycles = 2
    
    def _initialize_premium_llm(self, config: Dict):
        """Initialize premium LLM with optimal configuration"""
        try:
            model_type = config.get('model_type', 'openai')
            
            if model_type == 'anthropic' and ANTHROPIC_AVAILABLE:
                try:
                    return ChatAnthropic(
                        model=config.get('model', 'claude-3-5-sonnet-20241022'),
                        temperature=config.get('temperature', 0.7),
                        max_tokens=config.get('max_tokens', 4000),
                        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", "demo_key")
                    )
                except Exception as e:
                    logger.warning(f"Failed to initialize Anthropic model: {str(e)}, falling back to OpenAI")
                    return ChatOpenAI(
                        model="gpt-4o",
                        temperature=config.get('temperature', 0.7),
                        max_tokens=config.get('max_tokens', 4000),
                        openai_api_key=os.getenv("OPENAI_API_KEY", "demo_key")
                    )
            else:
                return ChatOpenAI(
                    model=config.get('model', 'gpt-4o'),
                    temperature=config.get('temperature', 0.7),
                    max_tokens=config.get('max_tokens', 4000),
                    top_p=config.get('top_p', 0.95),
                    frequency_penalty=config.get('frequency_penalty', 0.1),
                    presence_penalty=config.get('presence_penalty', 0.1),
                    openai_api_key=os.getenv("OPENAI_API_KEY", "demo_key")
                )
        except Exception as e:
            logger.warning(f"Failed to initialize premium LLM for {self.name}: {str(e)}. Using fallback.")
            return None
    
    async def execute_with_quality_assurance(self, task: Dict, context: Dict) -> Dict:
        """Execute agent task with quality assurance pipeline"""
        try:
            if self.llm is None:
                return await self._mock_execution(task)
            
            # Phase 1: Primary execution
            primary_result = await self._primary_execution(task, context)
            
            # Phase 2: Quality validation
            quality_score = await self._validate_quality(primary_result, task)
            
            # Phase 3: Refinement if needed
            if quality_score < self.quality_threshold:
                refined_result = await self._refine_result(primary_result, task, context)
                return refined_result
            
            return primary_result
            
        except Exception as e:
            logger.error(f"Premium agent {self.name} execution failed: {str(e)}")
            return await self._error_fallback(task, str(e))
    
    async def _primary_execution(self, task: Dict, context: Dict) -> Dict:
        """Primary execution with enhanced prompting"""
        instruction = task.get("instruction", "")
        
        # Enhanced system prompt for quality
        enhanced_prompt = f"""
        You are {self.name}, a premium AI specialist. {self.description}
        
        Quality Standards:
        - Provide comprehensive, well-structured responses
        - Include specific examples and actionable insights
        - Ensure accuracy and relevance to the request
        - Maintain professional tone while being engaging
        - Consider multiple perspectives and potential challenges
        
        Context: {json.dumps(context, indent=2)}
        
        Task: {instruction}
        
        Deliver your highest quality response:
        """
        
        messages = [
            SystemMessage(content=enhanced_prompt),
            HumanMessage(content=instruction)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        return {
            "agent_name": self.name,
            "task_id": task.get("id"),
            "result": response.content,
            "status": "completed",
            "execution_time": datetime.now().isoformat(),
            "model_used": self.model_config.get('model', 'unknown'),
            "quality_focused": True
        }
    
    async def _validate_quality(self, result: Dict, task: Dict) -> float:
        """Validate response quality using AI assessment"""
        try:
            if self.llm is None:
                return 0.8  # Assume good quality for mock responses
            
            validation_prompt = f"""
            Evaluate the quality of this AI response on a scale of 0.0 to 1.0:
            
            Original Task: {task.get('instruction', '')}
            
            Response to Evaluate:
            {result.get('result', '')}
            
            Quality Criteria:
            - Completeness (addresses all aspects of the request)
            - Accuracy (factually correct and reliable)
            - Relevance (directly related to the request)
            - Clarity (well-structured and easy to understand)
            - Depth (provides sufficient detail and insights)
            - Actionability (includes practical next steps or recommendations)
            
            Respond with only a number between 0.0 and 1.0 representing the overall quality score.
            """
            
            validation_response = await self.llm.ainvoke([
                SystemMessage(content="You are a quality assessment expert. Provide only numerical scores."),
                HumanMessage(content=validation_prompt)
            ])
            
            try:
                quality_score = float(validation_response.content.strip())
                return max(0.0, min(1.0, quality_score))  # Clamp between 0 and 1
            except ValueError:
                logger.warning(f"Could not parse quality score: {validation_response.content}")
                return 0.7  # Default moderate quality
                
        except Exception as e:
            logger.error(f"Quality validation failed: {str(e)}")
            return 0.7  # Default moderate quality
    
    async def _refine_result(self, original_result: Dict, task: Dict, context: Dict) -> Dict:
        """Refine result to improve quality"""
        try:
            refinement_prompt = f"""
            Improve and enhance this response to meet the highest quality standards:
            
            Original Task: {task.get('instruction', '')}
            
            Current Response:
            {original_result.get('result', '')}
            
            Enhancement Guidelines:
            - Add more specific details and examples
            - Improve structure and clarity
            - Include additional insights or perspectives
            - Ensure completeness and actionability
            - Maintain professional yet engaging tone
            
            Provide the enhanced version:
            """
            
            messages = [
                SystemMessage(content=f"You are {self.name}, refining your response for maximum quality."),
                HumanMessage(content=refinement_prompt)
            ]
            
            refined_response = await self.llm.ainvoke(messages)
            
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": refined_response.content,
                "status": "refined",
                "execution_time": datetime.now().isoformat(),
                "model_used": self.model_config.get('model', 'unknown'),
                "refinement_applied": True,
                "original_quality_issue": "Below quality threshold"
            }
            
        except Exception as e:
            logger.error(f"Result refinement failed: {str(e)}")
            # Return original result if refinement fails
            original_result["refinement_attempted"] = True
            original_result["refinement_error"] = str(e)
            return original_result
    
    async def _mock_execution(self, task: Dict) -> Dict:
        """Mock execution for demo mode"""
        return {
            "agent_name": self.name,
            "task_id": task.get("id"),
            "result": f"I'm {self.name} and I would provide premium quality assistance with: {task.get('instruction', 'the requested task')}. (Premium demo mode)",
            "status": "completed",
            "execution_time": datetime.now().isoformat(),
            "model_used": "demo_mode",
            "quality_focused": True
        }
    
    async def _error_fallback(self, task: Dict, error: str) -> Dict:
        """Error fallback with quality focus"""
        return {
            "agent_name": self.name,
            "task_id": task.get("id"),
            "result": f"I apologize, but I encountered an issue while providing premium assistance. I'll ensure this is resolved for future requests. Error: {error}",
            "status": "error_with_fallback",
            "execution_time": datetime.now().isoformat(),
            "error_handled": True
        }

class PremiumPersonaOrchestrator:
    """Premium orchestrator with quality and performance optimization"""
    
    def __init__(self, persona_name: str, model_config: Dict):
        self.persona_name = persona_name
        self.model_config = model_config
        self.agents = {}
        self.workflow_graph = self._build_premium_workflow_graph()
        
        # Premium LLM configuration
        self.primary_llm = self._initialize_premium_primary_llm(model_config)
        
        # Quality settings
        self.quality_threshold = 0.85
        self.orchestration_threshold = 0.4  # Lower threshold for more orchestration
        self.max_refinement_cycles = 2
    
    def _initialize_premium_primary_llm(self, config: Dict):
        """Initialize premium primary LLM"""
        try:
            return ChatOpenAI(
                model=config.get("primary_model", "gpt-4o"),
                temperature=config.get("temperature", 0.7),
                max_tokens=config.get("max_tokens", 4000),
                top_p=0.95,
                frequency_penalty=0.1,
                presence_penalty=0.1,
                openai_api_key=os.getenv("OPENAI_API_KEY", "demo_key")
            )
        except Exception as e:
            logger.warning(f"Failed to initialize premium primary LLM: {str(e)}")
            return None
    
    def _build_premium_workflow_graph(self) -> StateGraph:
        """Build premium LangGraph workflow with quality focus"""
        workflow = StateGraph(PremiumOrchestratorState)
        
        # Enhanced workflow nodes
        workflow.add_node("deep_task_analysis", self._deep_task_analysis)
        workflow.add_node("quality_agent_selection", self._quality_agent_selection)
        workflow.add_node("parallel_task_execution", self._parallel_task_execution)
        workflow.add_node("cross_validation", self._cross_validation)
        workflow.add_node("premium_synthesis", self._premium_synthesis)
        workflow.add_node("quality_assurance", self._quality_assurance)
        workflow.add_node("refinement_cycle", self._refinement_cycle)
        
        # Define premium workflow edges
        workflow.add_edge("deep_task_analysis", "quality_agent_selection")
        workflow.add_edge("quality_agent_selection", "parallel_task_execution")
        workflow.add_edge("parallel_task_execution", "cross_validation")
        workflow.add_edge("cross_validation", "premium_synthesis")
        workflow.add_edge("premium_synthesis", "quality_assurance")
        
        # Conditional edge for refinement
        workflow.add_conditional_edges(
            "quality_assurance",
            self._should_refine,
            {
                "refine": "refinement_cycle",
                "complete": END
            }
        )
        workflow.add_edge("refinement_cycle", "quality_assurance")
        
        # Set entry point
        workflow.set_entry_point("deep_task_analysis")
        
        return workflow.compile()
    
    async def orchestrate_premium_task(self, request: Dict) -> Dict:
        """Main premium orchestration method"""
        try:
            # Initialize premium state
            initial_state = PremiumOrchestratorState(
                task_id=str(uuid.uuid4()),
                original_message=request.get("message", ""),
                task_type="",
                complexity="",
                quality_requirement=0.85,  # High quality requirement
                persona=self.persona_name,
                context=request.get("context", {}),
                task_queue=[],
                active_agents={},
                agent_results=[],
                validation_results=[],
                refinement_cycles=0,
                final_response="",
                workflow_steps=[],
                performance_metrics={},
                quality_metrics={},
                error_log=[]
            )
            
            # Execute premium workflow
            start_time = datetime.now()
            final_state = await self.workflow_graph.ainvoke(initial_state)
            end_time = datetime.now()
            
            # Calculate premium metrics
            execution_time = (end_time - start_time).total_seconds()
            final_state["performance_metrics"] = {
                "execution_time": execution_time,
                "agents_used": len(final_state.get("agent_results", [])),
                "workflow_steps": len(final_state.get("workflow_steps", [])),
                "refinement_cycles": final_state.get("refinement_cycles", 0),
                "quality_score": final_state.get("quality_metrics", {}).get("final_score", 0.8),
                "premium_features_used": True
            }
            
            return {
                "task_id": final_state["task_id"],
                "response": final_state["final_response"],
                "orchestration_used": True,
                "premium_quality": True,
                "agents_involved": [r["agent_name"] for r in final_state.get("agent_results", [])],
                "workflow_steps": final_state["workflow_steps"],
                "performance_metrics": final_state["performance_metrics"],
                "quality_metrics": final_state.get("quality_metrics", {}),
                "persona": self.persona_name
            }
            
        except Exception as e:
            logger.error(f"Premium orchestration failed for {self.persona_name}: {str(e)}")
            return await self._premium_fallback(request, str(e))
    
    async def _deep_task_analysis(self, state: PremiumOrchestratorState) -> PremiumOrchestratorState:
        """Deep task analysis with quality focus"""
        try:
            message = state["original_message"]
            
            if self.primary_llm is None:
                # Mock analysis
                state["complexity"] = "medium"
                state["task_type"] = "general"
                state["quality_requirement"] = 0.85
                state["workflow_steps"].append("mock_analysis_completed")
                return state
            
            # Enhanced analysis prompt
            analysis_prompt = f"""
            Conduct a comprehensive analysis of this task with focus on quality requirements:
            
            Task: "{message}"
            Persona: {self.persona_name}
            
            Analyze and respond in JSON format:
            {{
                "complexity": "simple|medium|complex|expert",
                "task_type": "creative|analytical|operational|strategic|conversational",
                "quality_requirement": 0.0-1.0,
                "domain_expertise_needed": ["domain1", "domain2"],
                "estimated_agents_needed": number,
                "quality_factors": ["factor1", "factor2"],
                "success_criteria": ["criteria1", "criteria2"],
                "reasoning": "detailed explanation"
            }}
            """
            
            analysis_response = await self.primary_llm.ainvoke([
                SystemMessage(content="You are a premium task analysis expert focused on quality outcomes."),
                HumanMessage(content=analysis_prompt)
            ])
            
            try:
                analysis = json.loads(analysis_response.content)
                state["complexity"] = analysis.get("complexity", "medium")
                state["task_type"] = analysis.get("task_type", "general")
                state["quality_requirement"] = analysis.get("quality_requirement", 0.85)
                state["workflow_steps"].append("deep_analysis_completed")
                
                logger.info(f"Premium task analysis: {analysis}")
                
            except json.JSONDecodeError:
                # Fallback analysis
                state["complexity"] = "medium"
                state["task_type"] = "general"
                state["quality_requirement"] = 0.85
                state["error_log"].append("Failed to parse premium task analysis")
            
            return state
            
        except Exception as e:
            state["error_log"].append(f"Deep task analysis failed: {str(e)}")
            state["complexity"] = "medium"
            state["task_type"] = "general"
            state["quality_requirement"] = 0.85
            return state
    
    async def _quality_agent_selection(self, state: PremiumOrchestratorState) -> PremiumOrchestratorState:
        """Quality-focused agent selection"""
        try:
            complexity = state["complexity"]
            task_type = state["task_type"]
            quality_req = state["quality_requirement"]
            
            # Get available agents
            available_agents = self.get_available_agents()
            
            # Quality-first selection (use more agents for better results)
            if quality_req >= 0.8 or complexity in ["complex", "expert"]:
                # Use multiple agents for high quality
                selected_agents = available_agents[:3] if len(available_agents) >= 3 else available_agents
            elif complexity == "medium":
                selected_agents = available_agents[:2] if len(available_agents) >= 2 else available_agents
            else:
                selected_agents = [available_agents[0]] if available_agents else []
            
            # Create premium task queue
            state["task_queue"] = [
                {
                    "id": str(uuid.uuid4()),
                    "agent_name": agent_name,
                    "instruction": self._create_premium_agent_instruction(agent_name, state["original_message"]),
                    "priority": idx,
                    "quality_requirement": quality_req
                }
                for idx, agent_name in enumerate(selected_agents)
            ]
            
            state["workflow_steps"].append(f"premium_agents_selected: {', '.join(selected_agents)}")
            logger.info(f"Selected premium agents: {selected_agents}")
            
            return state
            
        except Exception as e:
            state["error_log"].append(f"Premium agent selection failed: {str(e)}")
            state["task_queue"] = []
            return state
    
    async def _parallel_task_execution(self, state: PremiumOrchestratorState) -> PremiumOrchestratorState:
        """Parallel execution for performance"""
        try:
            if not state["task_queue"]:
                # Direct premium response
                direct_response = await self._get_premium_direct_response(state["original_message"])
                state["agent_results"] = [{
                    "agent_name": "premium_direct_response",
                    "result": direct_response,
                    "status": "completed",
                    "quality_focused": True
                }]
                state["workflow_steps"].append("premium_direct_response_generated")
                return state
            
            # Execute tasks in parallel for performance
            tasks = []
            for task in state["task_queue"]:
                agent_name = task["agent_name"]
                agent = self.agents.get(agent_name)
                
                if agent and hasattr(agent, 'execute_with_quality_assurance'):
                    task_coroutine = agent.execute_with_quality_assurance(task, state["context"])
                else:
                    task_coroutine = self._execute_premium_with_llm(task, agent_name)
                
                tasks.append(task_coroutine)
            
            # Parallel execution
            agent_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and log them
            valid_results = []
            for i, result in enumerate(agent_results):
                if isinstance(result, Exception):
                    state["error_log"].append(f"Agent execution failed: {str(result)}")
                    # Create fallback result
                    fallback_result = {
                        "agent_name": state["task_queue"][i]["agent_name"],
                        "result": f"Premium fallback response for {state['task_queue'][i]['agent_name']}",
                        "status": "fallback",
                        "quality_focused": True
                    }
                    valid_results.append(fallback_result)
                else:
                    valid_results.append(result)
            
            state["agent_results"] = valid_results
            state["workflow_steps"].append(f"parallel_execution_completed_{len(valid_results)}_agents")
            
            return state
            
        except Exception as e:
            state["error_log"].append(f"Parallel task execution failed: {str(e)}")
            # Fallback to direct response
            direct_response = await self._get_premium_direct_response(state["original_message"])
            state["agent_results"] = [{
                "agent_name": "premium_fallback_response",
                "result": direct_response,
                "status": "completed",
                "quality_focused": True
            }]
            return state
    
    async def _cross_validation(self, state: PremiumOrchestratorState) -> PremiumOrchestratorState:
        """Cross-validation for quality assurance"""
        try:
            agent_results = state["agent_results"]
            
            if len(agent_results) <= 1:
                # Skip cross-validation for single results
                state["validation_results"] = []
                state["workflow_steps"].append("cross_validation_skipped_single_result")
                return state
            
            # Perform cross-validation between agents
            validation_results = []
            
            for i, result in enumerate(agent_results):
                for j, other_result in enumerate(agent_results):
                    if i != j:  # Don't validate against self
                        validation = await self._validate_against_peer(result, other_result)
                        validation_results.append(validation)
            
            state["validation_results"] = validation_results
            state["workflow_steps"].append("cross_validation_completed")
            
            return state
            
        except Exception as e:
            state["error_log"].append(f"Cross-validation failed: {str(e)}")
            state["validation_results"] = []
            return state
    
    async def _validate_against_peer(self, result: Dict, peer_result: Dict) -> Dict:
        """Validate one result against another"""
        try:
            if self.primary_llm is None:
                return {
                    "validator": peer_result["agent_name"],
                    "validated": result["agent_name"],
                    "consistency_score": 0.8,
                    "validation_notes": "Mock validation - premium demo mode"
                }
            
            validation_prompt = f"""
            Compare these two AI responses for consistency and quality:
            
            Response A (from {result['agent_name']}):
            {result['result']}
            
            Response B (from {peer_result['agent_name']}):
            {peer_result['result']}
            
            Evaluate:
            1. Consistency (do they align or contradict?)
            2. Complementarity (do they add value to each other?)
            3. Quality comparison
            
            Respond in JSON:
            {{
                "consistency_score": 0.0-1.0,
                "complementarity_score": 0.0-1.0,
                "quality_comparison": "A_better|B_better|equivalent",
                "validation_notes": "brief explanation"
            }}
            """
            
            validation_response = await self.primary_llm.ainvoke([
                SystemMessage(content="You are a quality validation expert comparing AI responses."),
                HumanMessage(content=validation_prompt)
            ])
            
            try:
                validation_data = json.loads(validation_response.content)
                return {
                    "validator": peer_result["agent_name"],
                    "validated": result["agent_name"],
                    "consistency_score": validation_data.get("consistency_score", 0.8),
                    "complementarity_score": validation_data.get("complementarity_score", 0.8),
                    "quality_comparison": validation_data.get("quality_comparison", "equivalent"),
                    "validation_notes": validation_data.get("validation_notes", "")
                }
            except json.JSONDecodeError:
                return {
                    "validator": peer_result["agent_name"],
                    "validated": result["agent_name"],
                    "consistency_score": 0.8,
                    "validation_notes": "Could not parse validation response"
                }
                
        except Exception as e:
            return {
                "validator": peer_result["agent_name"],
                "validated": result["agent_name"],
                "consistency_score": 0.7,
                "validation_notes": f"Validation error: {str(e)}"
            }
    
    async def _premium_synthesis(self, state: PremiumOrchestratorState) -> PremiumOrchestratorState:
        """Premium synthesis with quality focus"""
        try:
            agent_results = state["agent_results"]
            validation_results = state["validation_results"]
            
            if len(agent_results) == 1:
                # Single result, use directly
                state["final_response"] = agent_results[0]["result"]
                state["workflow_steps"].append("single_premium_result_used")
                return state
            
            # Premium synthesis with validation insights
            synthesis_prompt = f"""
            Create a premium, comprehensive response by synthesizing these expert analyses:
            
            Original request: "{state['original_message']}"
            Quality requirement: {state['quality_requirement']}
            
            Expert Results:
            {json.dumps([{"expert": r["agent_name"], "analysis": r["result"]} for r in agent_results], indent=2)}
            
            Cross-Validation Insights:
            {json.dumps(validation_results, indent=2)}
            
            Synthesis Guidelines:
            - Integrate the best insights from all experts
            - Resolve any contradictions using validation data
            - Ensure comprehensive coverage of the topic
            - Maintain {self.persona_name} persona voice and expertise
            - Provide actionable recommendations
            - Include specific examples and implementation details
            - Structure for maximum clarity and impact
            
            Create the highest quality response possible:
            """
            
            if self.primary_llm is None:
                # Mock synthesis
                state["final_response"] = f"Premium synthesis of {len(agent_results)} expert analyses for {self.persona_name}. (Demo mode)"
            else:
                synthesis_response = await self.primary_llm.ainvoke([
                    SystemMessage(content=f"You are {self.persona_name}, creating a premium synthesis of expert analyses."),
                    HumanMessage(content=synthesis_prompt)
                ])
                state["final_response"] = synthesis_response.content
            
            state["workflow_steps"].append("premium_synthesis_completed")
            
            return state
            
        except Exception as e:
            state["error_log"].append(f"Premium synthesis failed: {str(e)}")
            # Use best available result as fallback
            if state["agent_results"]:
                state["final_response"] = state["agent_results"][0]["result"]
            else:
                state["final_response"] = "I apologize, but I encountered an error creating a premium response."
            return state
    
    async def _quality_assurance(self, state: PremiumOrchestratorState) -> PremiumOrchestratorState:
        """Premium quality assurance check"""
        try:
            response = state["final_response"]
            
            # Calculate quality metrics
            quality_metrics = await self._calculate_quality_metrics(response, state["original_message"])
            state["quality_metrics"] = quality_metrics
            
            # Check if refinement is needed
            final_score = quality_metrics.get("overall_score", 0.8)
            
            if final_score < state["quality_requirement"] and state["refinement_cycles"] < self.max_refinement_cycles:
                state["workflow_steps"].append(f"quality_check_failed_score_{final_score}")
                return state
            
            state["workflow_steps"].append(f"quality_assurance_passed_score_{final_score}")
            return state
            
        except Exception as e:
            state["error_log"].append(f"Quality assurance failed: {str(e)}")
            # Assume quality is acceptable if we can't measure it
            state["quality_metrics"] = {"overall_score": 0.8, "error": str(e)}
            state["workflow_steps"].append("quality_assurance_error_assumed_acceptable")
            return state
    
    async def _calculate_quality_metrics(self, response: str, original_request: str) -> Dict:
        """Calculate comprehensive quality metrics"""
        try:
            if self.primary_llm is None:
                return {
                    "overall_score": 0.85,
                    "completeness": 0.85,
                    "accuracy": 0.85,
                    "relevance": 0.85,
                    "clarity": 0.85,
                    "actionability": 0.85,
                    "demo_mode": True
                }
            
            metrics_prompt = f"""
            Evaluate this AI response across multiple quality dimensions:
            
            Original Request: {original_request}
            
            Response to Evaluate:
            {response}
            
            Rate each dimension from 0.0 to 1.0:
            
            Respond in JSON format:
            {{
                "completeness": 0.0-1.0,
                "accuracy": 0.0-1.0,
                "relevance": 0.0-1.0,
                "clarity": 0.0-1.0,
                "depth": 0.0-1.0,
                "actionability": 0.0-1.0,
                "structure": 0.0-1.0,
                "engagement": 0.0-1.0,
                "overall_score": 0.0-1.0,
                "improvement_suggestions": ["suggestion1", "suggestion2"]
            }}
            """
            
            metrics_response = await self.primary_llm.ainvoke([
                SystemMessage(content="You are a quality assessment expert. Provide detailed numerical evaluations."),
                HumanMessage(content=metrics_prompt)
            ])
            
            try:
                metrics = json.loads(metrics_response.content)
                # Ensure all scores are valid
                for key, value in metrics.items():
                    if isinstance(value, (int, float)) and key != "improvement_suggestions":
                        metrics[key] = max(0.0, min(1.0, float(value)))
                return metrics
            except json.JSONDecodeError:
                logger.warning("Could not parse quality metrics response")
                return {"overall_score": 0.8, "parse_error": True}
                
        except Exception as e:
            logger.error(f"Quality metrics calculation failed: {str(e)}")
            return {"overall_score": 0.8, "error": str(e)}
    
    def _should_refine(self, state: PremiumOrchestratorState) -> str:
        """Determine if refinement is needed"""
        quality_score = state.get("quality_metrics", {}).get("overall_score", 0.8)
        refinement_cycles = state.get("refinement_cycles", 0)
        
        if quality_score < state["quality_requirement"] and refinement_cycles < self.max_refinement_cycles:
            return "refine"
        return "complete"
    
    async def _refinement_cycle(self, state: PremiumOrchestratorState) -> PremiumOrchestratorState:
        """Refinement cycle for quality improvement"""
        try:
            state["refinement_cycles"] += 1
            
            current_response = state["final_response"]
            quality_metrics = state.get("quality_metrics", {})
            improvement_suggestions = quality_metrics.get("improvement_suggestions", [])
            
            refinement_prompt = f"""
            Refine and improve this response to meet the highest quality standards:
            
            Original Request: {state['original_message']}
            Quality Requirement: {state['quality_requirement']}
            Current Quality Score: {quality_metrics.get('overall_score', 'unknown')}
            
            Current Response:
            {current_response}
            
            Improvement Areas:
            {json.dumps(improvement_suggestions, indent=2)}
            
            Quality Metrics to Improve:
            {json.dumps({k: v for k, v in quality_metrics.items() if isinstance(v, (int, float)) and v < 0.85}, indent=2)}
            
            Create an enhanced version that addresses these quality gaps:
            """
            
            if self.primary_llm is None:
                state["final_response"] = f"Refined response (cycle {state['refinement_cycles']}): {current_response} [Premium demo mode]"
            else:
                refinement_response = await self.primary_llm.ainvoke([
                    SystemMessage(content=f"You are {self.persona_name}, refining your response for maximum quality."),
                    HumanMessage(content=refinement_prompt)
                ])
                state["final_response"] = refinement_response.content
            
            state["workflow_steps"].append(f"refinement_cycle_{state['refinement_cycles']}_completed")
            
            return state
            
        except Exception as e:
            state["error_log"].append(f"Refinement cycle failed: {str(e)}")
            state["workflow_steps"].append(f"refinement_cycle_{state['refinement_cycles']}_failed")
            return state
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agents for this persona"""
        return list(self.agents.keys())
    
    def _create_premium_agent_instruction(self, agent_name: str, original_message: str) -> str:
        """Create premium instruction for an agent"""
        return f"As {agent_name}, provide your highest quality analysis and recommendations for: {original_message}"
    
    async def _get_premium_direct_response(self, message: str) -> str:
        """Get premium direct response without agent orchestration"""
        try:
            if self.primary_llm is None:
                return f"I'm {self.persona_name}, and I'd provide premium quality assistance with: {message}. (Premium demo mode)"
            
            premium_prompt = f"""
            As {self.persona_name}, provide a comprehensive, high-quality response to this request:
            
            {message}
            
            Quality Standards:
            - Comprehensive coverage of the topic
            - Specific, actionable recommendations
            - Clear structure and professional presentation
            - Relevant examples and insights
            - Forward-thinking perspective
            
            Deliver your premium response:
            """
            
            response = await self.primary_llm.ainvoke([
                SystemMessage(content=f"You are {self.persona_name}, providing premium quality assistance."),
                HumanMessage(content=premium_prompt)
            ])
            return response.content
        except Exception as e:
            return f"I apologize, but I'm having trouble providing a premium response right now. Error: {str(e)}"
    
    async def _execute_premium_with_llm(self, task: Dict, agent_name: str) -> Dict:
        """Execute task using premium LLM when specific agent is not available"""
        try:
            if self.primary_llm is None:
                return {
                    "agent_name": agent_name,
                    "task_id": task["id"],
                    "result": f"Premium {agent_name} analysis would be provided here. (Demo mode)",
                    "status": "completed",
                    "execution_time": datetime.now().isoformat(),
                    "quality_focused": True
                }
            
            instruction = task["instruction"]
            premium_prompt = f"""
            Acting as {agent_name}, provide premium quality analysis for:
            
            {instruction}
            
            Quality Requirements:
            - Comprehensive and detailed analysis
            - Specific recommendations and next steps
            - Professional expertise and insights
            - Clear structure and actionable content
            
            Deliver your premium analysis:
            """
            
            response = await self.primary_llm.ainvoke([
                SystemMessage(content=f"You are acting as premium {agent_name} agent."),
                HumanMessage(content=premium_prompt)
            ])
            
            return {
                "agent_name": agent_name,
                "task_id": task["id"],
                "result": response.content,
                "status": "completed",
                "execution_time": datetime.now().isoformat(),
                "quality_focused": True,
                "premium_execution": True
            }
        except Exception as e:
            return {
                "agent_name": agent_name,
                "task_id": task["id"],
                "result": f"Premium error handling: I encountered an issue but will ensure quality in future responses. Error: {str(e)}",
                "status": "error_handled",
                "execution_time": datetime.now().isoformat(),
                "quality_focused": True
            }
    
    async def _premium_fallback(self, request: Dict, error: str) -> Dict:
        """Premium fallback response"""
        try:
            fallback_response = await self._get_premium_direct_response(request.get("message", ""))
            return {
                "task_id": str(uuid.uuid4()),
                "response": fallback_response,
                "orchestration_used": False,
                "premium_quality": True,
                "fallback_reason": error,
                "persona": self.persona_name
            }
        except Exception as fallback_error:
            return {
                "task_id": str(uuid.uuid4()),
                "response": f"I apologize, but I'm experiencing technical difficulties. I'm committed to providing premium quality assistance and will resolve this issue promptly.",
                "orchestration_used": False,
                "premium_quality": False,
                "error": str(fallback_error),
                "persona": self.persona_name
            }

def enhanced_should_use_orchestration(message: str, persona: str, context: Dict = None) -> bool:
    """Enhanced orchestration decision with quality focus"""
    
    # Quality-focused keywords (lower threshold for orchestration)
    quality_keywords = [
        "comprehensive", "detailed", "thorough", "in-depth", "complete",
        "professional", "expert", "advanced", "sophisticated", "premium",
        "strategy", "analysis", "research", "plan", "develop", "create",
        "design", "implement", "optimize", "improve", "enhance"
    ]
    
    # Complexity indicators
    complexity_keywords = [
        "analyze", "evaluate", "compare", "assess", "review", "examine",
        "multi-step", "workflow", "process", "framework", "methodology",
        "campaign", "project", "initiative", "program", "system"
    ]
    
    # Domain expertise indicators
    expertise_keywords = [
        "technical", "business", "marketing", "financial", "strategic",
        "operational", "creative", "innovative", "scientific", "academic"
    ]
    
    message_lower = message.lower()
    
    # Calculate scores
    quality_score = sum(1 for keyword in quality_keywords if keyword in message_lower)
    complexity_score = sum(1 for keyword in complexity_keywords if keyword in message_lower)
    expertise_score = sum(1 for keyword in expertise_keywords if keyword in message_lower)
    
    # Length-based complexity
    word_count = len(message.split())
    length_score = min(word_count / 15, 2.0)  # Normalize, cap at 2.0
    
    # Context-based scoring
    context_score = 0
    if context:
        if context.get('quality_preference') == 'high':
            context_score += 1
        if context.get('complexity_preference') == 'high':
            context_score += 1
    
    total_score = quality_score + complexity_score + expertise_score + length_score + context_score
    
    # Lower thresholds for quality-focused orchestration
    if persona in ["cherry", "sophia"]:
        threshold = 1.0  # Very low threshold for creative and strategic personas
    else:
        threshold = 1.5  # Low threshold for operational persona
    
    return total_score >= threshold

# Premium model configurations
PREMIUM_MODEL_CONFIGS = {
    "cherry": {
        "primary_model": "gpt-4o",
        "temperature": 0.8,
        "max_tokens": 4000,
        "creativity_boost": True,
        "quality_focus": True
    },
    "sophia": {
        "primary_model": "gpt-4o",
        "temperature": 0.6,
        "max_tokens": 4000,
        "analytical_mode": True,
        "quality_focus": True
    },
    "karen": {
        "primary_model": "gpt-4o",
        "temperature": 0.4,
        "max_tokens": 4000,
        "efficiency_mode": True,
        "quality_focus": True
    }
}

# Premium agent model configurations
PREMIUM_AGENT_CONFIGS = {
    # Creative agents (Cherry)
    "content_writer": {
        "model_type": "anthropic",
        "model": "claude-3-5-sonnet-20241022",
        "temperature": 0.9,
        "max_tokens": 4000
    },
    "visual_designer": {
        "model_type": "openai",
        "model": "gpt-4o",
        "temperature": 0.8,
        "max_tokens": 3000
    },
    "brand_strategist": {
        "model_type": "openai",
        "model": "gpt-4o",
        "temperature": 0.7,
        "max_tokens": 3500
    },
    
    # Strategic agents (Sophia)
    "market_researcher": {
        "model_type": "openai",
        "model": "gpt-4o",
        "temperature": 0.3,
        "max_tokens": 4000
    },
    "data_analyst": {
        "model_type": "openai",
        "model": "gpt-4o",
        "temperature": 0.2,
        "max_tokens": 3500
    },
    "strategic_planner": {
        "model_type": "openai",
        "model": "gpt-4o",
        "temperature": 0.4,
        "max_tokens": 4000
    },
    
    # Operational agents (Karen)
    "task_manager": {
        "model_type": "openai",
        "model": "gpt-4o",
        "temperature": 0.3,
        "max_tokens": 3000
    },
    "process_optimizer": {
        "model_type": "openai",
        "model": "gpt-4o",
        "temperature": 0.2,
        "max_tokens": 3000
    },
    "automation_specialist": {
        "model_type": "openai",
        "model": "gpt-4o",
        "temperature": 0.3,
        "max_tokens": 3500
    }
}

# Export main classes
__all__ = [
    "PremiumPersonaOrchestrator",
    "PremiumBaseAgent", 
    "PremiumOrchestratorState",
    "enhanced_should_use_orchestration",
    "PREMIUM_MODEL_CONFIGS",
    "PREMIUM_AGENT_CONFIGS"
]

