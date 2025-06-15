# Orchestra AI Premium Persona Orchestrators
# Quality and performance optimized persona implementations

from premium_orchestrator_engine import PremiumPersonaOrchestrator, PREMIUM_MODEL_CONFIGS
from premium_specialized_agents import premium_agent_registry
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class PremiumCherryOrchestrator(PremiumPersonaOrchestrator):
    """Premium Cherry orchestrator focused on creative excellence"""
    
    def __init__(self):
        model_config = PREMIUM_MODEL_CONFIGS["cherry"]
        super().__init__("cherry", model_config)
        
        # Initialize premium creative agents
        self.agents = {
            "content_writer": premium_agent_registry.get_agent("content_writer"),
            "visual_designer": premium_agent_registry.get_agent("visual_designer"),
            "brand_strategist": premium_agent_registry.get_agent("brand_strategist")
        }
        
        # Premium creative settings
        self.creativity_boost = True
        self.quality_threshold = 0.9  # Higher threshold for creative work
        self.orchestration_threshold = 0.3  # Lower threshold for more orchestration
        
        logger.info("Premium Cherry Orchestrator initialized with creative excellence focus")
    
    def get_available_agents(self) -> List[str]:
        """Get available premium creative agents"""
        return ["content_writer", "visual_designer", "brand_strategist"]

class PremiumSophiaOrchestrator(PremiumPersonaOrchestrator):
    """Premium Sophia orchestrator focused on strategic excellence"""
    
    def __init__(self):
        model_config = PREMIUM_MODEL_CONFIGS["sophia"]
        super().__init__("sophia", model_config)
        
        # Initialize premium strategic agents
        self.agents = {
            "market_researcher": premium_agent_registry.get_agent("market_researcher"),
            "data_analyst": premium_agent_registry.get_agent("data_analyst"),
            "strategic_planner": premium_agent_registry.get_agent("strategic_planner")
        }
        
        # Premium strategic settings
        self.analytical_mode = True
        self.quality_threshold = 0.9  # Higher threshold for strategic work
        self.orchestration_threshold = 0.3  # Lower threshold for more orchestration
        
        logger.info("Premium Sophia Orchestrator initialized with strategic excellence focus")
    
    def get_available_agents(self) -> List[str]:
        """Get available premium strategic agents"""
        return ["market_researcher", "data_analyst", "strategic_planner"]

class PremiumKarenOrchestrator(PremiumPersonaOrchestrator):
    """Premium Karen orchestrator focused on operational excellence"""
    
    def __init__(self):
        model_config = PREMIUM_MODEL_CONFIGS["karen"]
        super().__init__("karen", model_config)
        
        # Initialize premium operational agents
        self.agents = {
            "task_manager": premium_agent_registry.get_agent("task_manager"),
            "process_optimizer": premium_agent_registry.get_agent("process_optimizer"),
            "automation_specialist": premium_agent_registry.get_agent("automation_specialist")
        }
        
        # Premium operational settings
        self.efficiency_mode = True
        self.quality_threshold = 0.85  # High threshold for operational work
        self.orchestration_threshold = 0.4  # Moderate threshold for operational tasks
        
        logger.info("Premium Karen Orchestrator initialized with operational excellence focus")
    
    def get_available_agents(self) -> List[str]:
        """Get available premium operational agents"""
        return ["task_manager", "process_optimizer", "automation_specialist"]

class PremiumOrchestratorManager:
    """Premium orchestrator manager with quality and performance focus"""
    
    def __init__(self):
        self.orchestrators = {
            "cherry": PremiumCherryOrchestrator(),
            "sophia": PremiumSophiaOrchestrator(),
            "karen": PremiumKarenOrchestrator()
        }
        
        logger.info("Premium Orchestrator Manager initialized with all premium personas")
    
    async def orchestrate_premium_request(self, request: Dict) -> Dict:
        """Orchestrate request using premium quality and performance settings"""
        try:
            persona = request.get("persona", "cherry")
            
            if persona not in self.orchestrators:
                logger.warning(f"Premium persona '{persona}' not found, defaulting to cherry")
                persona = "cherry"
            
            orchestrator = self.orchestrators[persona]
            
            # Add premium context
            premium_context = request.get("context", {})
            premium_context.update({
                "quality_preference": "premium",
                "performance_mode": "optimized",
                "cost_consideration": "quality_first"
            })
            request["context"] = premium_context
            
            # Execute premium orchestration
            result = await orchestrator.orchestrate_premium_task(request)
            
            # Add premium metadata
            result["premium_quality"] = True
            result["cost_optimized"] = False
            result["quality_first"] = True
            
            return result
            
        except Exception as e:
            logger.error(f"Premium orchestration failed: {str(e)}")
            return {
                "task_id": "error",
                "response": "I apologize, but I'm experiencing technical difficulties with the premium orchestration system. I'm committed to providing the highest quality assistance and will resolve this issue promptly.",
                "orchestration_used": False,
                "premium_quality": False,
                "error": str(e),
                "persona": request.get("persona", "unknown")
            }
    
    def get_orchestrator_status(self) -> Dict:
        """Get premium orchestrator system status"""
        return {
            "orchestrators_active": len(self.orchestrators),
            "available_personas": list(self.orchestrators.keys()),
            "agent_counts": {
                persona: len(orchestrator.get_available_agents())
                for persona, orchestrator in self.orchestrators.items()
            },
            "system_health": "premium_operational",
            "quality_mode": "premium",
            "performance_mode": "optimized"
        }
    
    def get_available_agents(self, persona: str = None) -> Dict:
        """Get available premium agents by persona"""
        if persona and persona in self.orchestrators:
            return {
                persona: self.orchestrators[persona].get_available_agents()
            }
        
        return {
            persona: orchestrator.get_available_agents()
            for persona, orchestrator in self.orchestrators.items()
        }

# Global premium orchestrator manager
premium_orchestrator_manager = PremiumOrchestratorManager()

# Export main classes
__all__ = [
    "PremiumCherryOrchestrator",
    "PremiumSophiaOrchestrator",
    "PremiumKarenOrchestrator", 
    "PremiumOrchestratorManager",
    "premium_orchestrator_manager"
]

