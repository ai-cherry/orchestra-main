# Orchestra AI Premium Orchestration Endpoints
# Quality and performance optimized API endpoints

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import asyncio
import logging
from datetime import datetime
import json

from premium_persona_orchestrators import premium_orchestrator_manager
from premium_orchestrator_engine import enhanced_should_use_orchestration

logger = logging.getLogger(__name__)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class PremiumChatRequest(BaseModel):
    """Premium chat request with quality and performance options"""
    persona: str = Field(..., description="Persona to use (cherry, sophia, karen)")
    message: str = Field(..., description="User message")
    context: Optional[Dict[str, Any]] = Field(default={}, description="Additional context")
    quality_preference: Optional[str] = Field(default="premium", description="Quality preference (premium, high, standard)")
    performance_mode: Optional[str] = Field(default="optimized", description="Performance mode (optimized, balanced, cost_efficient)")
    orchestration_preference: Optional[str] = Field(default="auto", description="Orchestration preference (auto, force, disable)")

class PremiumChatResponse(BaseModel):
    """Premium chat response with comprehensive metadata"""
    task_id: str
    response: str
    orchestration_used: bool
    premium_quality: bool
    agents_involved: List[str]
    workflow_steps: List[str]
    performance_metrics: Dict[str, Any]
    quality_metrics: Optional[Dict[str, Any]] = None
    persona: str
    timestamp: str
    cost_estimate: Optional[float] = None
    model_usage: Optional[Dict[str, Any]] = None

class PremiumComplexityAnalysis(BaseModel):
    """Premium complexity analysis request"""
    message: str = Field(..., description="Message to analyze")
    persona: str = Field(..., description="Persona context")
    context: Optional[Dict[str, Any]] = Field(default={}, description="Additional context")

class PremiumComplexityResponse(BaseModel):
    """Premium complexity analysis response"""
    complexity_score: float
    task_type: str
    recommended_orchestration: bool
    quality_requirement: float
    estimated_agents: int
    reasoning: str
    premium_features_recommended: List[str]

class PremiumSystemStatus(BaseModel):
    """Premium system status response"""
    orchestrators_active: int
    available_personas: List[str]
    agent_counts: Dict[str, int]
    system_health: str
    quality_mode: str
    performance_mode: str
    premium_features_enabled: bool

# ============================================================================
# PREMIUM ORCHESTRATION ENDPOINTS
# ============================================================================

def add_premium_orchestration_endpoints(app):
    """Add premium orchestration endpoints to FastAPI app"""
    
    router = APIRouter(prefix="/api/premium", tags=["premium_orchestration"])
    
    @router.post("/chat", response_model=PremiumChatResponse)
    async def premium_orchestrated_chat(request: PremiumChatRequest):
        """Premium orchestrated chat with quality and performance optimization"""
        try:
            start_time = datetime.now()
            
            # Validate persona
            if request.persona not in ["cherry", "sophia", "karen"]:
                raise HTTPException(status_code=400, detail=f"Invalid persona: {request.persona}")
            
            # Prepare premium request
            premium_request = {
                "persona": request.persona,
                "message": request.message,
                "context": {
                    **request.context,
                    "quality_preference": request.quality_preference,
                    "performance_mode": request.performance_mode,
                    "orchestration_preference": request.orchestration_preference,
                    "premium_mode": True
                }
            }
            
            # Determine orchestration strategy
            should_orchestrate = True
            if request.orchestration_preference == "disable":
                should_orchestrate = False
            elif request.orchestration_preference == "auto":
                should_orchestrate = enhanced_should_use_orchestration(
                    request.message, 
                    request.persona, 
                    premium_request["context"]
                )
            
            # Execute premium orchestration
            if should_orchestrate:
                result = await premium_orchestrator_manager.orchestrate_premium_request(premium_request)
            else:
                # Direct premium response
                orchestrator = premium_orchestrator_manager.orchestrators[request.persona]
                direct_response = await orchestrator._get_premium_direct_response(request.message)
                
                result = {
                    "task_id": f"direct_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "response": direct_response,
                    "orchestration_used": False,
                    "premium_quality": True,
                    "agents_involved": ["direct_premium_response"],
                    "workflow_steps": ["premium_direct_response"],
                    "performance_metrics": {
                        "execution_time": (datetime.now() - start_time).total_seconds(),
                        "agents_used": 0,
                        "workflow_steps": 1,
                        "premium_features_used": True
                    },
                    "persona": request.persona
                }
            
            # Add cost estimation
            cost_estimate = calculate_premium_cost_estimate(result)
            result["cost_estimate"] = cost_estimate
            
            # Add model usage information
            result["model_usage"] = extract_model_usage(result)
            
            # Add timestamp
            result["timestamp"] = datetime.now().isoformat()
            
            logger.info(f"Premium chat completed for {request.persona}: {result['task_id']}")
            
            return PremiumChatResponse(**result)
            
        except Exception as e:
            logger.error(f"Premium orchestrated chat failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Premium orchestration error: {str(e)}")
    
    @router.get("/status", response_model=PremiumSystemStatus)
    async def premium_orchestration_status():
        """Get premium orchestration system status"""
        try:
            status = premium_orchestrator_manager.get_orchestrator_status()
            status["premium_features_enabled"] = True
            
            return PremiumSystemStatus(**status)
            
        except Exception as e:
            logger.error(f"Premium status check failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Status check error: {str(e)}")
    
    @router.get("/agents")
    async def premium_available_agents(persona: Optional[str] = None):
        """Get available premium agents by persona"""
        try:
            agents = premium_orchestrator_manager.get_available_agents(persona)
            
            # Add agent capabilities information
            agent_details = {}
            for p, agent_list in agents.items():
                agent_details[p] = []
                for agent_name in agent_list:
                    agent_info = get_premium_agent_info(agent_name)
                    agent_details[p].append(agent_info)
            
            return {
                "available_agents": agent_details,
                "total_agents": sum(len(agent_list) for agent_list in agents.values()),
                "premium_features": True
            }
            
        except Exception as e:
            logger.error(f"Premium agents list failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Agents list error: {str(e)}")
    
    @router.post("/complexity-analysis", response_model=PremiumComplexityResponse)
    async def premium_complexity_analysis(request: PremiumComplexityAnalysis):
        """Analyze message complexity for premium orchestration decisions"""
        try:
            # Enhanced complexity analysis
            complexity_score = calculate_enhanced_complexity(request.message, request.persona)
            task_type = determine_premium_task_type(request.message)
            quality_requirement = calculate_quality_requirement(request.message, request.context)
            
            # Orchestration recommendation
            should_orchestrate = enhanced_should_use_orchestration(
                request.message, 
                request.persona, 
                request.context
            )
            
            # Estimate required agents
            estimated_agents = estimate_required_agents(complexity_score, task_type, quality_requirement)
            
            # Premium features recommendation
            premium_features = recommend_premium_features(request.message, task_type, quality_requirement)
            
            # Generate reasoning
            reasoning = generate_complexity_reasoning(
                complexity_score, task_type, quality_requirement, should_orchestrate
            )
            
            return PremiumComplexityResponse(
                complexity_score=complexity_score,
                task_type=task_type,
                recommended_orchestration=should_orchestrate,
                quality_requirement=quality_requirement,
                estimated_agents=estimated_agents,
                reasoning=reasoning,
                premium_features_recommended=premium_features
            )
            
        except Exception as e:
            logger.error(f"Premium complexity analysis failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Complexity analysis error: {str(e)}")
    
    @router.post("/test-orchestration")
    async def premium_test_orchestration(
        persona: str = "cherry",
        complexity: str = "medium",
        quality_mode: str = "premium"
    ):
        """Test premium orchestration functionality"""
        try:
            test_messages = {
                "simple": "Hello, how are you?",
                "medium": "Create a comprehensive marketing strategy for a new AI startup",
                "complex": "Develop a complete business transformation plan including market analysis, competitive positioning, operational optimization, and implementation roadmap with risk mitigation strategies"
            }
            
            test_message = test_messages.get(complexity, test_messages["medium"])
            
            test_request = PremiumChatRequest(
                persona=persona,
                message=test_message,
                context={"test_mode": True, "quality_preference": quality_mode},
                quality_preference=quality_mode,
                performance_mode="optimized",
                orchestration_preference="auto"
            )
            
            result = await premium_orchestrated_chat(test_request)
            
            return {
                "test_completed": True,
                "test_parameters": {
                    "persona": persona,
                    "complexity": complexity,
                    "quality_mode": quality_mode
                },
                "result_summary": {
                    "task_id": result.task_id,
                    "orchestration_used": result.orchestration_used,
                    "agents_involved": len(result.agents_involved),
                    "execution_time": result.performance_metrics.get("execution_time", 0),
                    "quality_score": result.quality_metrics.get("overall_score", 0) if result.quality_metrics else None
                },
                "premium_features_tested": True
            }
            
        except Exception as e:
            logger.error(f"Premium orchestration test failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")
    
    # Add router to app
    app.include_router(router)
    logger.info("Premium orchestration endpoints added successfully")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_premium_cost_estimate(result: Dict) -> float:
    """Calculate estimated cost for premium orchestration"""
    try:
        base_cost = 0.02  # Base cost for premium orchestration
        
        # Model usage costs
        agents_used = len(result.get("agents_involved", []))
        agent_cost = agents_used * 0.015  # Premium agent cost
        
        # Quality features cost
        quality_features_cost = 0.01 if result.get("premium_quality", False) else 0
        
        # Refinement cycles cost
        refinement_cycles = result.get("performance_metrics", {}).get("refinement_cycles", 0)
        refinement_cost = refinement_cycles * 0.005
        
        total_cost = base_cost + agent_cost + quality_features_cost + refinement_cost
        
        return round(total_cost, 4)
        
    except Exception as e:
        logger.warning(f"Cost estimation failed: {str(e)}")
        return 0.05  # Default premium cost estimate

def extract_model_usage(result: Dict) -> Dict[str, Any]:
    """Extract model usage information from result"""
    try:
        model_usage = {
            "primary_model": "gpt-4o",
            "agents_models": {},
            "total_tokens_estimated": 0,
            "premium_features_used": result.get("premium_quality", False)
        }
        
        # Extract agent model information
        for agent_result in result.get("agent_results", []):
            agent_name = agent_result.get("agent_name", "unknown")
            model_used = agent_result.get("model_used", "gpt-4o")
            model_usage["agents_models"][agent_name] = model_used
        
        # Estimate token usage
        response_length = len(result.get("response", ""))
        estimated_tokens = response_length * 1.3  # Rough estimation
        model_usage["total_tokens_estimated"] = int(estimated_tokens)
        
        return model_usage
        
    except Exception as e:
        logger.warning(f"Model usage extraction failed: {str(e)}")
        return {"error": str(e)}

def get_premium_agent_info(agent_name: str) -> Dict[str, Any]:
    """Get detailed information about a premium agent"""
    agent_info_map = {
        "content_writer": {
            "name": "Premium Content Writer",
            "model": "claude-3-5-sonnet",
            "specialties": ["creative_writing", "copywriting", "seo_optimization"],
            "quality_focus": "creativity_and_engagement"
        },
        "visual_designer": {
            "name": "Premium Visual Designer",
            "model": "gpt-4o",
            "specialties": ["design_strategy", "brand_aesthetics", "ux_optimization"],
            "quality_focus": "visual_excellence"
        },
        "brand_strategist": {
            "name": "Premium Brand Strategist",
            "model": "gpt-4o",
            "specialties": ["brand_positioning", "market_strategy", "brand_architecture"],
            "quality_focus": "strategic_impact"
        },
        "market_researcher": {
            "name": "Premium Market Researcher",
            "model": "gpt-4o",
            "specialties": ["market_analysis", "competitive_intelligence", "consumer_insights"],
            "quality_focus": "analytical_rigor"
        },
        "data_analyst": {
            "name": "Premium Data Analyst",
            "model": "gpt-4o",
            "specialties": ["statistical_analysis", "predictive_modeling", "data_visualization"],
            "quality_focus": "analytical_precision"
        },
        "strategic_planner": {
            "name": "Premium Strategic Planner",
            "model": "gpt-4o",
            "specialties": ["strategic_planning", "scenario_analysis", "implementation_roadmaps"],
            "quality_focus": "strategic_depth"
        },
        "task_manager": {
            "name": "Premium Task Manager",
            "model": "gpt-4o",
            "specialties": ["project_management", "resource_optimization", "workflow_design"],
            "quality_focus": "operational_excellence"
        },
        "process_optimizer": {
            "name": "Premium Process Optimizer",
            "model": "gpt-4o",
            "specialties": ["process_improvement", "efficiency_optimization", "lean_methodologies"],
            "quality_focus": "efficiency_maximization"
        },
        "automation_specialist": {
            "name": "Premium Automation Specialist",
            "model": "gpt-4o",
            "specialties": ["automation_design", "workflow_automation", "intelligent_processes"],
            "quality_focus": "automation_sophistication"
        }
    }
    
    return agent_info_map.get(agent_name, {
        "name": f"Premium {agent_name.replace('_', ' ').title()}",
        "model": "gpt-4o",
        "specialties": ["premium_capabilities"],
        "quality_focus": "excellence"
    })

def calculate_enhanced_complexity(message: str, persona: str) -> float:
    """Calculate enhanced complexity score for premium orchestration"""
    try:
        # Base complexity factors
        word_count = len(message.split())
        length_factor = min(word_count / 20, 1.0)
        
        # Premium complexity keywords
        premium_keywords = [
            "comprehensive", "detailed", "thorough", "in-depth", "complete",
            "professional", "expert", "advanced", "sophisticated", "premium",
            "strategy", "analysis", "research", "plan", "develop", "create",
            "design", "implement", "optimize", "improve", "enhance",
            "framework", "methodology", "systematic", "strategic", "innovative"
        ]
        
        keyword_matches = sum(1 for keyword in premium_keywords if keyword.lower() in message.lower())
        keyword_factor = min(keyword_matches / 5, 1.0)
        
        # Domain complexity
        domain_keywords = {
            "business": ["business", "market", "revenue", "profit", "strategy", "competitive"],
            "technical": ["technical", "system", "architecture", "implementation", "integration"],
            "creative": ["creative", "design", "brand", "visual", "content", "storytelling"],
            "analytical": ["analysis", "data", "metrics", "performance", "optimization", "insights"]
        }
        
        domain_factor = 0
        for domain, keywords in domain_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in message.lower())
            domain_factor = max(domain_factor, min(matches / 3, 1.0))
        
        # Persona-specific adjustments
        persona_multipliers = {
            "cherry": 1.2,  # Creative tasks often more complex
            "sophia": 1.3,  # Strategic tasks typically complex
            "karen": 1.0    # Operational tasks baseline
        }
        
        persona_multiplier = persona_multipliers.get(persona, 1.0)
        
        # Calculate final complexity score
        complexity_score = (length_factor + keyword_factor + domain_factor) * persona_multiplier / 3
        
        return min(complexity_score, 1.0)
        
    except Exception as e:
        logger.warning(f"Enhanced complexity calculation failed: {str(e)}")
        return 0.5  # Default medium complexity

def determine_premium_task_type(message: str) -> str:
    """Determine premium task type for orchestration optimization"""
    message_lower = message.lower()
    
    task_type_keywords = {
        "creative": ["create", "design", "write", "develop", "generate", "craft", "compose"],
        "analytical": ["analyze", "evaluate", "assess", "examine", "research", "investigate"],
        "strategic": ["strategy", "plan", "roadmap", "framework", "approach", "methodology"],
        "operational": ["manage", "organize", "optimize", "implement", "execute", "coordinate"],
        "conversational": ["hello", "hi", "how", "what", "why", "explain", "tell"]
    }
    
    type_scores = {}
    for task_type, keywords in task_type_keywords.items():
        score = sum(1 for keyword in keywords if keyword in message_lower)
        type_scores[task_type] = score
    
    # Return the task type with highest score
    if max(type_scores.values()) == 0:
        return "general"
    
    return max(type_scores, key=type_scores.get)

def calculate_quality_requirement(message: str, context: Dict) -> float:
    """Calculate quality requirement for premium orchestration"""
    try:
        base_quality = 0.8  # Premium baseline
        
        # Quality indicators in message
        quality_keywords = [
            "premium", "high-quality", "professional", "excellent", "superior",
            "best", "top-tier", "world-class", "exceptional", "outstanding"
        ]
        
        quality_mentions = sum(1 for keyword in quality_keywords if keyword in message.lower())
        quality_boost = min(quality_mentions * 0.05, 0.15)
        
        # Context-based quality requirements
        context_quality = context.get("quality_preference", "premium")
        context_boost = {
            "premium": 0.1,
            "high": 0.05,
            "standard": 0.0
        }.get(context_quality, 0.1)
        
        final_quality = min(base_quality + quality_boost + context_boost, 1.0)
        
        return final_quality
        
    except Exception as e:
        logger.warning(f"Quality requirement calculation failed: {str(e)}")
        return 0.85  # Default premium quality requirement

def estimate_required_agents(complexity_score: float, task_type: str, quality_requirement: float) -> int:
    """Estimate number of agents required for premium orchestration"""
    try:
        base_agents = 1
        
        # Complexity-based agents
        if complexity_score > 0.8:
            base_agents = 3
        elif complexity_score > 0.6:
            base_agents = 2
        
        # Task type adjustments
        task_type_agents = {
            "creative": 2,      # Often benefits from multiple creative perspectives
            "analytical": 2,    # Data analysis + strategic interpretation
            "strategic": 3,     # Research + analysis + planning
            "operational": 2,   # Planning + optimization
            "conversational": 1 # Usually single agent sufficient
        }
        
        task_agents = task_type_agents.get(task_type, 1)
        
        # Quality requirement adjustments
        if quality_requirement > 0.9:
            quality_agents = 3  # Maximum agents for highest quality
        elif quality_requirement > 0.8:
            quality_agents = 2
        else:
            quality_agents = 1
        
        # Take the maximum to ensure quality
        estimated_agents = max(base_agents, task_agents, quality_agents)
        
        return min(estimated_agents, 3)  # Cap at 3 agents
        
    except Exception as e:
        logger.warning(f"Agent estimation failed: {str(e)}")
        return 2  # Default premium agent count

def recommend_premium_features(message: str, task_type: str, quality_requirement: float) -> List[str]:
    """Recommend premium features for the request"""
    features = []
    
    # Always include base premium features
    features.extend(["premium_models", "quality_assurance", "performance_optimization"])
    
    # Task-specific features
    if task_type == "creative":
        features.extend(["advanced_creativity", "multi_perspective_synthesis", "brand_alignment"])
    elif task_type == "analytical":
        features.extend(["advanced_analytics", "statistical_rigor", "data_visualization"])
    elif task_type == "strategic":
        features.extend(["scenario_planning", "strategic_frameworks", "implementation_roadmaps"])
    elif task_type == "operational":
        features.extend(["process_optimization", "efficiency_analysis", "automation_recommendations"])
    
    # Quality-based features
    if quality_requirement > 0.9:
        features.extend(["iterative_refinement", "cross_validation", "expert_review"])
    
    # Message-specific features
    message_lower = message.lower()
    if "comprehensive" in message_lower:
        features.append("comprehensive_analysis")
    if "detailed" in message_lower:
        features.append("detailed_specifications")
    if "professional" in message_lower:
        features.append("professional_presentation")
    
    return list(set(features))  # Remove duplicates

def generate_complexity_reasoning(
    complexity_score: float, 
    task_type: str, 
    quality_requirement: float, 
    should_orchestrate: bool
) -> str:
    """Generate reasoning for complexity analysis"""
    try:
        reasoning_parts = []
        
        # Complexity assessment
        if complexity_score > 0.8:
            reasoning_parts.append("High complexity task requiring sophisticated analysis and multi-faceted approach.")
        elif complexity_score > 0.6:
            reasoning_parts.append("Medium-high complexity task benefiting from specialized expertise.")
        elif complexity_score > 0.4:
            reasoning_parts.append("Medium complexity task with moderate orchestration benefits.")
        else:
            reasoning_parts.append("Lower complexity task suitable for direct response.")
        
        # Task type reasoning
        task_reasoning = {
            "creative": "Creative tasks benefit from multiple perspectives and iterative refinement.",
            "analytical": "Analytical tasks require rigorous methodology and data-driven insights.",
            "strategic": "Strategic tasks need comprehensive analysis and long-term thinking.",
            "operational": "Operational tasks benefit from systematic optimization and efficiency focus.",
            "conversational": "Conversational tasks typically suitable for direct engagement."
        }
        
        if task_type in task_reasoning:
            reasoning_parts.append(task_reasoning[task_type])
        
        # Quality reasoning
        if quality_requirement > 0.9:
            reasoning_parts.append("Premium quality requirements justify comprehensive orchestration approach.")
        elif quality_requirement > 0.8:
            reasoning_parts.append("High quality standards support enhanced orchestration benefits.")
        
        # Orchestration recommendation reasoning
        if should_orchestrate:
            reasoning_parts.append("Orchestration recommended for optimal quality and comprehensive results.")
        else:
            reasoning_parts.append("Direct response sufficient for this request type and complexity level.")
        
        return " ".join(reasoning_parts)
        
    except Exception as e:
        logger.warning(f"Reasoning generation failed: {str(e)}")
        return "Premium orchestration analysis completed with standard reasoning."

# Export main function
__all__ = ["add_premium_orchestration_endpoints"]

