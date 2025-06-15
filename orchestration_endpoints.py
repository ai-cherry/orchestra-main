# Orchestra AI Orchestration Endpoints
# Enhanced chat endpoints with LangGraph orchestration capabilities

from fastapi import HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import logging
import asyncio
from datetime import datetime

from orchestrator_engine import should_use_orchestration
from persona_orchestrators import orchestrator_manager

logger = logging.getLogger(__name__)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class OrchestrationRequest(BaseModel):
    """Request model for orchestrated chat"""
    persona: str
    message: str
    context: Optional[Dict[str, Any]] = {}
    complexity: Optional[str] = "auto"  # auto, simple, medium, complex
    force_orchestration: Optional[bool] = False
    user_preferences: Optional[Dict[str, Any]] = {}

class OrchestrationResponse(BaseModel):
    """Response model for orchestrated chat"""
    task_id: str
    response: str
    orchestration_used: bool
    agents_involved: List[str] = []
    workflow_steps: List[str] = []
    performance_metrics: Dict[str, Any] = {}
    persona: str
    timestamp: str

class AgentStatusResponse(BaseModel):
    """Response model for agent status"""
    orchestrators_active: int
    available_personas: List[str]
    agent_counts: Dict[str, int]
    system_health: str

# ============================================================================
# ORCHESTRATION ENDPOINTS
# ============================================================================

def add_orchestration_endpoints(app):
    """Add orchestration-enhanced chat endpoints to FastAPI app"""
    
    @app.post("/api/chat/orchestrated", response_model=OrchestrationResponse)
    async def orchestrated_chat(request: OrchestrationRequest):
        """Enhanced chat with orchestrator capabilities"""
        try:
            persona = request.persona.lower()
            message = request.message
            complexity = request.complexity
            
            # Validate persona
            if persona not in ["cherry", "sophia", "karen"]:
                raise HTTPException(status_code=400, detail="Invalid persona. Must be cherry, sophia, or karen.")
            
            # Determine if orchestration is needed
            use_orchestration = (
                request.force_orchestration or 
                (complexity != "simple" and should_use_orchestration(message, persona))
            )
            
            if not use_orchestration:
                # Use simple chat response for basic queries
                simple_response = await _get_simple_chat_response(persona, message)
                return OrchestrationResponse(
                    task_id=f"simple_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    response=simple_response,
                    orchestration_used=False,
                    persona=persona,
                    timestamp=datetime.now().isoformat()
                )
            
            # Use orchestrator for complex tasks
            orchestration_request = {
                "message": message,
                "context": request.context,
                "user_preferences": request.user_preferences,
                "complexity": complexity
            }
            
            result = await orchestrator_manager.orchestrate_request(persona, orchestration_request)
            
            return OrchestrationResponse(
                task_id=result.get("task_id", "unknown"),
                response=result.get("response", "No response generated"),
                orchestration_used=result.get("orchestration_used", True),
                agents_involved=result.get("agents_involved", []),
                workflow_steps=result.get("workflow_steps", []),
                performance_metrics=result.get("performance_metrics", {}),
                persona=persona,
                timestamp=datetime.now().isoformat()
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Orchestration error: {str(e)}")
            # Fallback to simple chat
            try:
                fallback_response = await _get_simple_chat_response(request.persona, request.message)
                return OrchestrationResponse(
                    task_id=f"fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    response=fallback_response,
                    orchestration_used=False,
                    persona=request.persona,
                    timestamp=datetime.now().isoformat()
                )
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {str(fallback_error)}")
                raise HTTPException(status_code=500, detail="Chat service temporarily unavailable")
    
    @app.get("/api/orchestration/status", response_model=AgentStatusResponse)
    async def orchestration_status():
        """Get orchestration system status"""
        try:
            status = orchestrator_manager.get_orchestrator_status()
            return AgentStatusResponse(**status)
        except Exception as e:
            logger.error(f"Status check failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Unable to retrieve orchestration status")
    
    @app.get("/api/orchestration/agents")
    async def get_available_agents(persona: Optional[str] = None):
        """Get available agents for persona or all personas"""
        try:
            agents = orchestrator_manager.get_available_agents(persona)
            return {
                "available_agents": agents,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Agent listing failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Unable to retrieve agent information")
    
    @app.post("/api/orchestration/test")
    async def test_orchestration(persona: str, test_message: str = "Create a comprehensive marketing strategy"):
        """Test orchestration functionality"""
        try:
            test_request = {
                "message": test_message,
                "context": {"test_mode": True},
                "user_preferences": {}
            }
            
            result = await orchestrator_manager.orchestrate_request(persona, test_request)
            
            return {
                "test_result": "success",
                "orchestration_response": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Orchestration test failed: {str(e)}")
            return {
                "test_result": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    @app.get("/api/orchestration/complexity-check")
    async def check_message_complexity(message: str, persona: str):
        """Check if a message would trigger orchestration"""
        try:
            requires_orchestration = should_use_orchestration(message, persona)
            
            return {
                "message": message,
                "persona": persona,
                "requires_orchestration": requires_orchestration,
                "recommendation": "orchestrated" if requires_orchestration else "simple",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Complexity check failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Unable to analyze message complexity")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def _get_simple_chat_response(persona: str, message: str) -> str:
    """Get simple chat response without orchestration"""
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage, SystemMessage
        
        # Persona-specific system prompts
        persona_prompts = {
            "cherry": "You are Cherry, a creative AI assistant specializing in content creation, design, and innovation. You're enthusiastic, inspiring, and always thinking outside the box.",
            "sophia": "You are Sophia, a strategic AI assistant focused on analysis, planning, and complex problem-solving. You're analytical, thorough, and data-driven in your approach.",
            "karen": "You are Karen, an operational AI assistant focused on execution, automation, and workflow management. You're practical, efficient, and results-oriented."
        }
        
        llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.7 if persona == "cherry" else 0.5 if persona == "sophia" else 0.3,
            max_tokens=1000
        )
        
        system_prompt = persona_prompts.get(persona, "You are a helpful AI assistant.")
        
        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=message)
        ])
        
        return response.content
        
    except Exception as e:
        logger.error(f"Simple chat response failed: {str(e)}")
        return f"I apologize, but I'm having trouble processing your request right now. Please try again in a moment."

def _classify_task_complexity(message: str) -> str:
    """Classify task complexity level"""
    
    complexity_indicators = {
        "simple": ["what", "how", "when", "where", "who", "define", "explain", "tell me"],
        "medium": ["analyze", "compare", "evaluate", "summarize", "create", "design", "plan"],
        "complex": ["develop", "strategy", "comprehensive", "multi-step", "workflow", "campaign", "implement", "optimize"]
    }
    
    message_lower = message.lower()
    scores = {}
    
    for level, keywords in complexity_indicators.items():
        scores[level] = sum(1 for keyword in keywords if keyword in message_lower)
    
    # Return highest scoring complexity level
    max_score = max(scores.values())
    if max_score == 0:
        return "simple"
    
    return max(scores, key=scores.get)

# Export main function
__all__ = ["add_orchestration_endpoints"]

