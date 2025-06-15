# Orchestra AI Specialized Agents
# Individual agent implementations for different capabilities

from orchestrator_engine import BaseAgent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Dict, List, Any
import asyncio
import json
import logging
import os

logger = logging.getLogger(__name__)

# ============================================================================
# CREATIVE AGENTS (for Cherry)
# ============================================================================

class ContentWriterAgent(BaseAgent):
    """Specialized agent for content creation and writing tasks"""
    
    def __init__(self):
        super().__init__(
            name="ContentWriter",
            description="Expert in creating engaging, well-structured content across various formats and styles. Specializes in storytelling, copywriting, and creative writing."
        )
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.8,  # Higher creativity for content
            max_tokens=2000,
            openai_api_key=os.getenv("OPENAI_API_KEY", "demo_key")
        )
    
    async def execute(self, task: Dict, context: Dict) -> Dict:
        """Execute content writing task"""
        try:
            instruction = task.get("instruction", "")
            
            # Enhanced prompt for content writing
            content_prompt = f"""
            As an expert content writer, create compelling content for this request:
            {instruction}
            
            Guidelines:
            - Use engaging, conversational tone
            - Include relevant examples and analogies
            - Structure content with clear headings and flow
            - Optimize for readability and engagement
            - Maintain brand voice consistency
            """
            
            messages = [
                SystemMessage(content="You are a professional content writer with expertise in creating engaging, high-quality content."),
                HumanMessage(content=content_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": response.content,
                "status": "completed",
                "specialization": "content_creation"
            }
            
        except Exception as e:
            logger.error(f"ContentWriter execution failed: {str(e)}")
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": f"Content creation error: {str(e)}",
                "status": "failed"
            }

class VisualDesignerAgent(BaseAgent):
    """Specialized agent for visual design concepts and creative direction"""
    
    def __init__(self):
        super().__init__(
            name="VisualDesigner",
            description="Expert in visual design, branding, and creative direction. Provides detailed design concepts, color schemes, and visual strategies."
        )
        self.llm = ChatOpenAI(openai_api_key=os.getenv("OPENAI_API_KEY", "demo_key"), 
            model="gpt-4-turbo-preview",
            temperature=0.7,
            max_tokens=1500
        )
    
    async def execute(self, task: Dict, context: Dict) -> Dict:
        """Execute visual design task"""
        try:
            instruction = task.get("instruction", "")
            
            design_prompt = f"""
            As a visual design expert, provide comprehensive design guidance for:
            {instruction}
            
            Include:
            - Visual concept and theme
            - Color palette recommendations
            - Typography suggestions
            - Layout and composition ideas
            - Brand alignment considerations
            - Technical implementation notes
            """
            
            messages = [
                SystemMessage(content="You are a professional visual designer with expertise in branding, UI/UX, and creative direction."),
                HumanMessage(content=design_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": response.content,
                "status": "completed",
                "specialization": "visual_design"
            }
            
        except Exception as e:
            logger.error(f"VisualDesigner execution failed: {str(e)}")
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": f"Design concept error: {str(e)}",
                "status": "failed"
            }

class BrandStrategistAgent(BaseAgent):
    """Specialized agent for brand strategy and marketing positioning"""
    
    def __init__(self):
        super().__init__(
            name="BrandStrategist",
            description="Expert in brand strategy, positioning, and marketing communications. Develops comprehensive brand guidelines and messaging strategies."
        )
        self.llm = ChatOpenAI(openai_api_key=os.getenv("OPENAI_API_KEY", "demo_key"), 
            model="gpt-4-turbo-preview",
            temperature=0.6,
            max_tokens=1800
        )
    
    async def execute(self, task: Dict, context: Dict) -> Dict:
        """Execute brand strategy task"""
        try:
            instruction = task.get("instruction", "")
            
            brand_prompt = f"""
            As a brand strategist, develop comprehensive brand guidance for:
            {instruction}
            
            Provide:
            - Brand positioning and value proposition
            - Target audience analysis
            - Key messaging and tone of voice
            - Competitive differentiation
            - Brand personality and attributes
            - Implementation recommendations
            """
            
            messages = [
                SystemMessage(content="You are a senior brand strategist with expertise in brand development, positioning, and marketing strategy."),
                HumanMessage(content=brand_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": response.content,
                "status": "completed",
                "specialization": "brand_strategy"
            }
            
        except Exception as e:
            logger.error(f"BrandStrategist execution failed: {str(e)}")
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": f"Brand strategy error: {str(e)}",
                "status": "failed"
            }

# ============================================================================
# STRATEGIC AGENTS (for Sophia)
# ============================================================================

class MarketResearchAgent(BaseAgent):
    """Specialized agent for market research and competitive analysis"""
    
    def __init__(self):
        super().__init__(
            name="MarketResearcher",
            description="Expert in market research, competitive analysis, and industry insights. Provides data-driven market intelligence and strategic recommendations."
        )
        self.llm = ChatOpenAI(openai_api_key=os.getenv("OPENAI_API_KEY", "demo_key"), 
            model="gpt-4-turbo-preview",
            temperature=0.3,  # Lower temperature for analytical work
            max_tokens=2000
        )
    
    async def execute(self, task: Dict, context: Dict) -> Dict:
        """Execute market research task"""
        try:
            instruction = task.get("instruction", "")
            
            research_prompt = f"""
            As a market research expert, conduct comprehensive analysis for:
            {instruction}
            
            Provide:
            - Market size and growth trends
            - Competitive landscape analysis
            - Key market drivers and challenges
            - Customer segments and behavior
            - Emerging opportunities and threats
            - Strategic recommendations
            - Data sources and methodology notes
            """
            
            messages = [
                SystemMessage(content="You are a senior market research analyst with expertise in competitive intelligence and market analysis."),
                HumanMessage(content=research_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": response.content,
                "status": "completed",
                "specialization": "market_research"
            }
            
        except Exception as e:
            logger.error(f"MarketResearcher execution failed: {str(e)}")
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": f"Market research error: {str(e)}",
                "status": "failed"
            }

class DataAnalystAgent(BaseAgent):
    """Specialized agent for data analysis and insights generation"""
    
    def __init__(self):
        super().__init__(
            name="DataAnalyst",
            description="Expert in data analysis, statistical modeling, and insights generation. Transforms raw data into actionable business intelligence."
        )
        self.llm = ChatOpenAI(openai_api_key=os.getenv("OPENAI_API_KEY", "demo_key"), 
            model="gpt-4-turbo-preview",
            temperature=0.2,  # Very low temperature for analytical precision
            max_tokens=1800
        )
    
    async def execute(self, task: Dict, context: Dict) -> Dict:
        """Execute data analysis task"""
        try:
            instruction = task.get("instruction", "")
            
            analysis_prompt = f"""
            As a data analyst, provide comprehensive analysis for:
            {instruction}
            
            Include:
            - Data interpretation and key findings
            - Statistical significance and confidence levels
            - Trend analysis and patterns
            - Correlation and causation insights
            - Predictive indicators
            - Visualization recommendations
            - Actionable recommendations
            """
            
            messages = [
                SystemMessage(content="You are a senior data analyst with expertise in statistical analysis, data visualization, and business intelligence."),
                HumanMessage(content=analysis_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": response.content,
                "status": "completed",
                "specialization": "data_analysis"
            }
            
        except Exception as e:
            logger.error(f"DataAnalyst execution failed: {str(e)}")
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": f"Data analysis error: {str(e)}",
                "status": "failed"
            }

class StrategicPlannerAgent(BaseAgent):
    """Specialized agent for strategic planning and business strategy"""
    
    def __init__(self):
        super().__init__(
            name="StrategicPlanner",
            description="Expert in strategic planning, business strategy, and organizational development. Creates comprehensive strategic frameworks and implementation plans."
        )
        self.llm = ChatOpenAI(openai_api_key=os.getenv("OPENAI_API_KEY", "demo_key"), 
            model="gpt-4-turbo-preview",
            temperature=0.4,
            max_tokens=2200
        )
    
    async def execute(self, task: Dict, context: Dict) -> Dict:
        """Execute strategic planning task"""
        try:
            instruction = task.get("instruction", "")
            
            strategy_prompt = f"""
            As a strategic planning expert, develop comprehensive strategy for:
            {instruction}
            
            Provide:
            - Strategic objectives and goals
            - SWOT analysis framework
            - Strategic options and alternatives
            - Implementation roadmap and timeline
            - Resource requirements and allocation
            - Risk assessment and mitigation
            - Success metrics and KPIs
            - Governance and review processes
            """
            
            messages = [
                SystemMessage(content="You are a senior strategic planning consultant with expertise in business strategy, organizational development, and strategic implementation."),
                HumanMessage(content=strategy_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": response.content,
                "status": "completed",
                "specialization": "strategic_planning"
            }
            
        except Exception as e:
            logger.error(f"StrategicPlanner execution failed: {str(e)}")
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": f"Strategic planning error: {str(e)}",
                "status": "failed"
            }

# ============================================================================
# OPERATIONAL AGENTS (for Karen)
# ============================================================================

class TaskManagerAgent(BaseAgent):
    """Specialized agent for task management and project coordination"""
    
    def __init__(self):
        super().__init__(
            name="TaskManager",
            description="Expert in task management, project coordination, and workflow optimization. Breaks down complex projects into manageable tasks and timelines."
        )
        self.llm = ChatOpenAI(openai_api_key=os.getenv("OPENAI_API_KEY", "demo_key"), 
            model="gpt-4-turbo-preview",
            temperature=0.3,
            max_tokens=1800
        )
    
    async def execute(self, task: Dict, context: Dict) -> Dict:
        """Execute task management task"""
        try:
            instruction = task.get("instruction", "")
            
            task_prompt = f"""
            As a task management expert, organize and structure:
            {instruction}
            
            Provide:
            - Task breakdown structure (WBS)
            - Priority matrix and dependencies
            - Timeline and milestone planning
            - Resource allocation recommendations
            - Risk identification and mitigation
            - Progress tracking mechanisms
            - Communication and reporting structure
            - Quality assurance checkpoints
            """
            
            messages = [
                SystemMessage(content="You are a project management expert with expertise in task organization, workflow optimization, and project coordination."),
                HumanMessage(content=task_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": response.content,
                "status": "completed",
                "specialization": "task_management"
            }
            
        except Exception as e:
            logger.error(f"TaskManager execution failed: {str(e)}")
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": f"Task management error: {str(e)}",
                "status": "failed"
            }

class ProcessOptimizerAgent(BaseAgent):
    """Specialized agent for process optimization and efficiency improvement"""
    
    def __init__(self):
        super().__init__(
            name="ProcessOptimizer",
            description="Expert in process optimization, efficiency improvement, and operational excellence. Identifies bottlenecks and implements streamlined workflows."
        )
        self.llm = ChatOpenAI(openai_api_key=os.getenv("OPENAI_API_KEY", "demo_key"), 
            model="gpt-4-turbo-preview",
            temperature=0.2,
            max_tokens=1600
        )
    
    async def execute(self, task: Dict, context: Dict) -> Dict:
        """Execute process optimization task"""
        try:
            instruction = task.get("instruction", "")
            
            optimization_prompt = f"""
            As a process optimization expert, analyze and improve:
            {instruction}
            
            Provide:
            - Current state process mapping
            - Bottleneck and inefficiency identification
            - Root cause analysis
            - Optimization recommendations
            - Future state process design
            - Implementation plan and timeline
            - Performance metrics and KPIs
            - Change management considerations
            """
            
            messages = [
                SystemMessage(content="You are a process optimization specialist with expertise in lean methodologies, workflow analysis, and operational efficiency."),
                HumanMessage(content=optimization_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": response.content,
                "status": "completed",
                "specialization": "process_optimization"
            }
            
        except Exception as e:
            logger.error(f"ProcessOptimizer execution failed: {str(e)}")
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": f"Process optimization error: {str(e)}",
                "status": "failed"
            }

class AutomationSpecialistAgent(BaseAgent):
    """Specialized agent for automation and workflow digitization"""
    
    def __init__(self):
        super().__init__(
            name="AutomationSpecialist",
            description="Expert in automation, workflow digitization, and technology integration. Identifies automation opportunities and designs automated solutions."
        )
        self.llm = ChatOpenAI(openai_api_key=os.getenv("OPENAI_API_KEY", "demo_key"), 
            model="gpt-4-turbo-preview",
            temperature=0.3,
            max_tokens=1700
        )
    
    async def execute(self, task: Dict, context: Dict) -> Dict:
        """Execute automation task"""
        try:
            instruction = task.get("instruction", "")
            
            automation_prompt = f"""
            As an automation specialist, design automation solutions for:
            {instruction}
            
            Provide:
            - Automation opportunity assessment
            - Technology stack recommendations
            - Workflow automation design
            - Integration requirements
            - Implementation roadmap
            - ROI analysis and cost-benefit
            - Risk assessment and mitigation
            - Maintenance and support considerations
            """
            
            messages = [
                SystemMessage(content="You are an automation specialist with expertise in workflow automation, RPA, and technology integration."),
                HumanMessage(content=automation_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": response.content,
                "status": "completed",
                "specialization": "automation"
            }
            
        except Exception as e:
            logger.error(f"AutomationSpecialist execution failed: {str(e)}")
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": f"Automation design error: {str(e)}",
                "status": "failed"
            }

# ============================================================================
# AGENT REGISTRY
# ============================================================================

class AgentRegistry:
    """Central registry for all available agents"""
    
    def __init__(self):
        self.agents = {
            # Creative agents (Cherry)
            "content_writer": ContentWriterAgent,
            "visual_designer": VisualDesignerAgent,
            "brand_strategist": BrandStrategistAgent,
            
            # Strategic agents (Sophia)
            "market_researcher": MarketResearchAgent,
            "data_analyst": DataAnalystAgent,
            "strategic_planner": StrategicPlannerAgent,
            
            # Operational agents (Karen)
            "task_manager": TaskManagerAgent,
            "process_optimizer": ProcessOptimizerAgent,
            "automation_specialist": AutomationSpecialistAgent
        }
        
        self.persona_agents = {
            "cherry": ["content_writer", "visual_designer", "brand_strategist"],
            "sophia": ["market_researcher", "data_analyst", "strategic_planner"],
            "karen": ["task_manager", "process_optimizer", "automation_specialist"]
        }
    
    def get_agent(self, agent_type: str) -> BaseAgent:
        """Get agent instance by type"""
        if agent_type in self.agents:
            return self.agents[agent_type]()
        raise ValueError(f"Unknown agent type: {agent_type}")
    
    def list_agents_for_persona(self, persona: str) -> List[str]:
        """List available agents for specific persona"""
        return self.persona_agents.get(persona, [])
    
    def get_all_agents(self) -> Dict[str, BaseAgent]:
        """Get all agent instances"""
        return {name: agent_class() for name, agent_class in self.agents.items()}

# Global agent registry instance
agent_registry = AgentRegistry()

# Export main classes and registry
__all__ = [
    "ContentWriterAgent",
    "VisualDesignerAgent", 
    "BrandStrategistAgent",
    "MarketResearchAgent",
    "DataAnalystAgent",
    "StrategicPlannerAgent",
    "TaskManagerAgent",
    "ProcessOptimizerAgent",
    "AutomationSpecialistAgent",
    "AgentRegistry",
    "agent_registry"
]

