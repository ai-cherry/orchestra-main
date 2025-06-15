# Orchestra AI Persona Orchestrators
# Persona-specific orchestrator implementations

from orchestrator_engine import PersonaOrchestrator
from specialized_agents import agent_registry
from langchain_openai import ChatOpenAI
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class CherryOrchestrator(PersonaOrchestrator):
    """Creative AI Orchestrator for design and content creation"""
    
    def __init__(self):
        model_config = {
            "primary_model": "gpt-4-turbo-preview",
            "temperature": 0.7,  # Higher creativity
            "max_tokens": 2000,
            "creativity_boost": True
        }
        super().__init__("cherry", model_config)
        
        # Initialize creative agents
        self.agents = {
            "content_writer": agent_registry.get_agent("content_writer"),
            "visual_designer": agent_registry.get_agent("visual_designer"),
            "brand_strategist": agent_registry.get_agent("brand_strategist")
        }
        
        # Creative task patterns
        self.creative_patterns = {
            "content_creation": ["content_writer", "brand_strategist"],
            "design_project": ["visual_designer", "brand_strategist"],
            "brand_development": ["brand_strategist", "visual_designer", "content_writer"],
            "marketing_campaign": ["brand_strategist", "content_writer", "visual_designer"]
        }
    
    def _choose_agents_for_task(self, task_type: str, complexity: str, available_agents: List[str]) -> List[str]:
        """Choose appropriate creative agents based on task characteristics"""
        
        # Analyze task for creative patterns
        if "brand" in task_type.lower() or "identity" in task_type.lower():
            return self.creative_patterns.get("brand_development", ["brand_strategist"])
        elif "design" in task_type.lower() or "visual" in task_type.lower():
            return self.creative_patterns.get("design_project", ["visual_designer"])
        elif "content" in task_type.lower() or "write" in task_type.lower():
            return self.creative_patterns.get("content_creation", ["content_writer"])
        elif "campaign" in task_type.lower() or "marketing" in task_type.lower():
            return self.creative_patterns.get("marketing_campaign", available_agents)
        
        # Default selection based on complexity
        if complexity == "complex":
            return available_agents[:2]  # Use multiple agents for complex creative tasks
        else:
            return [available_agents[0]] if available_agents else []
    
    def _create_agent_instruction(self, agent_name: str, original_message: str) -> str:
        """Create creative-specific instruction for an agent"""
        
        creative_context = """
        Context: You are part of Cherry's creative team, focusing on innovative, engaging, and visually appealing solutions.
        Brand Voice: Creative, inspiring, innovative, and user-focused.
        """
        
        agent_instructions = {
            "content_writer": f"{creative_context}\nAs the content writer, create compelling, engaging content that tells a story and connects with the audience.",
            "visual_designer": f"{creative_context}\nAs the visual designer, provide detailed design concepts that are both beautiful and functional.",
            "brand_strategist": f"{creative_context}\nAs the brand strategist, ensure all creative work aligns with brand values and market positioning."
        }
        
        base_instruction = agent_instructions.get(agent_name, creative_context)
        return f"{base_instruction}\n\nTask: {original_message}"

class SophiaOrchestrator(PersonaOrchestrator):
    """Strategic AI Orchestrator for analysis and planning"""
    
    def __init__(self):
        model_config = {
            "primary_model": "gpt-4-turbo-preview",
            "temperature": 0.3,  # Lower temperature for analytical precision
            "max_tokens": 2500,
            "analytical_mode": True
        }
        super().__init__("sophia", model_config)
        
        # Initialize strategic agents
        self.agents = {
            "market_researcher": agent_registry.get_agent("market_researcher"),
            "data_analyst": agent_registry.get_agent("data_analyst"),
            "strategic_planner": agent_registry.get_agent("strategic_planner")
        }
        
        # Strategic task patterns
        self.strategic_patterns = {
            "market_analysis": ["market_researcher", "data_analyst"],
            "strategic_planning": ["strategic_planner", "market_researcher"],
            "business_intelligence": ["data_analyst", "market_researcher", "strategic_planner"],
            "competitive_analysis": ["market_researcher", "strategic_planner"],
            "data_insights": ["data_analyst", "strategic_planner"]
        }
    
    def _choose_agents_for_task(self, task_type: str, complexity: str, available_agents: List[str]) -> List[str]:
        """Choose appropriate strategic agents based on task characteristics"""
        
        # Analyze task for strategic patterns
        if "market" in task_type.lower() or "research" in task_type.lower():
            return self.strategic_patterns.get("market_analysis", ["market_researcher"])
        elif "strategy" in task_type.lower() or "plan" in task_type.lower():
            return self.strategic_patterns.get("strategic_planning", ["strategic_planner"])
        elif "data" in task_type.lower() or "analysis" in task_type.lower():
            return self.strategic_patterns.get("data_insights", ["data_analyst"])
        elif "competitive" in task_type.lower() or "competitor" in task_type.lower():
            return self.strategic_patterns.get("competitive_analysis", ["market_researcher"])
        elif "intelligence" in task_type.lower() or "insight" in task_type.lower():
            return self.strategic_patterns.get("business_intelligence", available_agents)
        
        # Default selection based on complexity
        if complexity == "complex":
            return available_agents  # Use all agents for complex strategic tasks
        elif complexity == "medium":
            return available_agents[:2]  # Use two agents for medium complexity
        else:
            return [available_agents[0]] if available_agents else []
    
    def _create_agent_instruction(self, agent_name: str, original_message: str) -> str:
        """Create strategic-specific instruction for an agent"""
        
        strategic_context = """
        Context: You are part of Sophia's strategic analysis team, focusing on data-driven insights and strategic thinking.
        Approach: Analytical, evidence-based, comprehensive, and forward-thinking.
        """
        
        agent_instructions = {
            "market_researcher": f"{strategic_context}\nAs the market researcher, provide comprehensive market intelligence and competitive insights.",
            "data_analyst": f"{strategic_context}\nAs the data analyst, focus on quantitative analysis, trends, and statistical insights.",
            "strategic_planner": f"{strategic_context}\nAs the strategic planner, develop comprehensive strategies and implementation frameworks."
        }
        
        base_instruction = agent_instructions.get(agent_name, strategic_context)
        return f"{base_instruction}\n\nTask: {original_message}"

class KarenOrchestrator(PersonaOrchestrator):
    """Operational AI Orchestrator for execution and automation"""
    
    def __init__(self):
        model_config = {
            "primary_model": "gpt-4-turbo-preview",
            "temperature": 0.2,  # Low temperature for operational precision
            "max_tokens": 2000,
            "efficiency_mode": True
        }
        super().__init__("karen", model_config)
        
        # Initialize operational agents
        self.agents = {
            "task_manager": agent_registry.get_agent("task_manager"),
            "process_optimizer": agent_registry.get_agent("process_optimizer"),
            "automation_specialist": agent_registry.get_agent("automation_specialist")
        }
        
        # Operational task patterns
        self.operational_patterns = {
            "project_management": ["task_manager", "process_optimizer"],
            "process_improvement": ["process_optimizer", "automation_specialist"],
            "automation_design": ["automation_specialist", "process_optimizer"],
            "workflow_optimization": ["process_optimizer", "task_manager", "automation_specialist"],
            "task_organization": ["task_manager", "process_optimizer"]
        }
    
    def _choose_agents_for_task(self, task_type: str, complexity: str, available_agents: List[str]) -> List[str]:
        """Choose appropriate operational agents based on task characteristics"""
        
        # Analyze task for operational patterns
        if "project" in task_type.lower() or "manage" in task_type.lower():
            return self.operational_patterns.get("project_management", ["task_manager"])
        elif "process" in task_type.lower() or "optimize" in task_type.lower():
            return self.operational_patterns.get("process_improvement", ["process_optimizer"])
        elif "automat" in task_type.lower() or "workflow" in task_type.lower():
            return self.operational_patterns.get("automation_design", ["automation_specialist"])
        elif "task" in task_type.lower() or "organize" in task_type.lower():
            return self.operational_patterns.get("task_organization", ["task_manager"])
        elif "efficiency" in task_type.lower() or "streamline" in task_type.lower():
            return self.operational_patterns.get("workflow_optimization", available_agents)
        
        # Default selection based on complexity
        if complexity == "complex":
            return available_agents  # Use all agents for complex operational tasks
        elif complexity == "medium":
            return available_agents[:2]  # Use two agents for medium complexity
        else:
            return [available_agents[0]] if available_agents else []
    
    def _create_agent_instruction(self, agent_name: str, original_message: str) -> str:
        """Create operational-specific instruction for an agent"""
        
        operational_context = """
        Context: You are part of Karen's operational excellence team, focusing on efficiency, execution, and systematic improvement.
        Approach: Practical, systematic, results-oriented, and process-focused.
        """
        
        agent_instructions = {
            "task_manager": f"{operational_context}\nAs the task manager, break down complex work into manageable, actionable tasks with clear timelines.",
            "process_optimizer": f"{operational_context}\nAs the process optimizer, identify inefficiencies and design streamlined workflows.",
            "automation_specialist": f"{operational_context}\nAs the automation specialist, identify automation opportunities and design technical solutions."
        }
        
        base_instruction = agent_instructions.get(agent_name, operational_context)
        return f"{base_instruction}\n\nTask: {original_message}"

# ============================================================================
# ORCHESTRATOR MANAGER
# ============================================================================

class OrchestratorManager:
    """Manages all persona orchestrators and routing"""
    
    def __init__(self):
        self.orchestrators = {
            "cherry": CherryOrchestrator(),
            "sophia": SophiaOrchestrator(),
            "karen": KarenOrchestrator()
        }
        
        logger.info("Orchestrator Manager initialized with all personas")
    
    async def get_orchestrator(self, persona: str) -> PersonaOrchestrator:
        """Get orchestrator for specific persona"""
        orchestrator = self.orchestrators.get(persona.lower())
        if not orchestrator:
            raise ValueError(f"Unknown persona: {persona}")
        return orchestrator
    
    async def orchestrate_request(self, persona: str, request: Dict) -> Dict:
        """Route request to appropriate persona orchestrator"""
        try:
            orchestrator = await self.get_orchestrator(persona)
            result = await orchestrator.orchestrate_task(request)
            
            logger.info(f"Orchestration completed for {persona}: {result.get('task_id')}")
            return result
            
        except Exception as e:
            logger.error(f"Orchestration failed for {persona}: {str(e)}")
            return {
                "task_id": "error",
                "response": f"I apologize, but I encountered an error while processing your request. Please try again.",
                "orchestration_used": False,
                "error": str(e),
                "persona": persona
            }
    
    def get_orchestrator_status(self) -> Dict:
        """Get status of all orchestrators"""
        return {
            "orchestrators_active": len(self.orchestrators),
            "available_personas": list(self.orchestrators.keys()),
            "agent_counts": {
                persona: len(orch.get_available_agents()) 
                for persona, orch in self.orchestrators.items()
            },
            "system_health": "operational"
        }
    
    def get_available_agents(self, persona: str = None) -> Dict:
        """Get available agents for persona or all personas"""
        if persona:
            orchestrator = self.orchestrators.get(persona.lower())
            if orchestrator:
                return {persona: orchestrator.get_available_agents()}
            return {}
        
        return {
            persona: orch.get_available_agents() 
            for persona, orch in self.orchestrators.items()
        }

# Global orchestrator manager instance
orchestrator_manager = OrchestratorManager()

# Export main classes
__all__ = [
    "CherryOrchestrator",
    "SophiaOrchestrator", 
    "KarenOrchestrator",
    "OrchestratorManager",
    "orchestrator_manager"
]

