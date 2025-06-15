# Orchestra AI Premium Specialized Agents
# Quality and performance optimized agent implementations

from premium_orchestrator_engine import PremiumBaseAgent, PREMIUM_AGENT_CONFIGS
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Dict, List, Any
import asyncio
import json
import logging
import os

logger = logging.getLogger(__name__)

# ============================================================================
# PREMIUM CREATIVE AGENTS (Cherry Persona)
# ============================================================================

class PremiumContentWriter(PremiumBaseAgent):
    """Premium content writer with Claude-3.5-Sonnet for superior creativity"""
    
    def __init__(self):
        config = PREMIUM_AGENT_CONFIGS["content_writer"]
        super().__init__(
            name="PremiumContentWriter",
            description="Elite content creation specialist using Claude-3.5-Sonnet for superior creativity, storytelling, and engaging copy across all formats and industries.",
            model_config=config
        )
    
    async def execute_with_quality_assurance(self, task: Dict, context: Dict) -> Dict:
        """Premium content creation with quality assurance"""
        try:
            if self.llm is None:
                return await self._mock_execution(task)
            
            instruction = task.get("instruction", "")
            
            # Premium content creation prompt
            premium_prompt = f"""
            As an elite content creation specialist, deliver exceptional content that exceeds industry standards:
            
            Request: {instruction}
            
            Premium Quality Standards:
            - Compelling headlines and hooks that capture attention immediately
            - Rich, engaging narrative with perfect tone and voice
            - Strategic use of storytelling techniques and emotional triggers
            - SEO optimization without compromising readability
            - Clear call-to-actions and conversion-focused elements
            - Industry-specific expertise and credible insights
            - Flawless grammar, style, and professional presentation
            
            Content Strategy Considerations:
            - Target audience psychology and motivations
            - Brand voice consistency and personality
            - Content distribution and platform optimization
            - Measurable objectives and success metrics
            
            Deliver your premium content creation:
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an elite content creation specialist known for exceptional quality and creativity."),
                HumanMessage(content=premium_prompt)
            ])
            
            # Quality validation specific to content
            quality_score = await self._validate_content_quality(response.content, instruction)
            
            result = {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": response.content,
                "status": "completed",
                "execution_time": datetime.now().isoformat(),
                "model_used": self.model_config.get('model', 'claude-3-5-sonnet'),
                "quality_score": quality_score,
                "premium_features": ["advanced_storytelling", "seo_optimization", "conversion_focus"]
            }
            
            # Refine if quality is below threshold
            if quality_score < self.quality_threshold:
                result = await self._refine_content(result, task, context)
            
            return result
            
        except Exception as e:
            logger.error(f"Premium content writer execution failed: {str(e)}")
            return await self._error_fallback(task, str(e))
    
    async def _validate_content_quality(self, content: str, original_request: str) -> float:
        """Validate content-specific quality metrics"""
        try:
            if self.llm is None:
                return 0.85
            
            validation_prompt = f"""
            Evaluate this content for premium quality across content-specific criteria:
            
            Original Request: {original_request}
            
            Content to Evaluate:
            {content}
            
            Content Quality Criteria (rate 0.0-1.0):
            - Engagement: Does it capture and hold attention?
            - Clarity: Is the message clear and easy to understand?
            - Creativity: Does it show original thinking and fresh perspectives?
            - Persuasiveness: Does it effectively influence the reader?
            - Professional Polish: Is it error-free and well-structured?
            - Brand Alignment: Does it maintain consistent voice and tone?
            - Actionability: Does it provide clear next steps or value?
            
            Respond with only a number between 0.0 and 1.0 representing overall content quality.
            """
            
            validation_response = await self.llm.ainvoke([
                SystemMessage(content="You are a content quality expert. Provide only numerical scores."),
                HumanMessage(content=validation_prompt)
            ])
            
            try:
                return max(0.0, min(1.0, float(validation_response.content.strip())))
            except ValueError:
                return 0.8
                
        except Exception as e:
            logger.error(f"Content quality validation failed: {str(e)}")
            return 0.8
    
    async def _refine_content(self, original_result: Dict, task: Dict, context: Dict) -> Dict:
        """Refine content for premium quality"""
        try:
            refinement_prompt = f"""
            Enhance this content to achieve premium quality standards:
            
            Original Request: {task.get('instruction', '')}
            
            Current Content:
            {original_result.get('result', '')}
            
            Premium Enhancement Guidelines:
            - Strengthen the opening hook and headline
            - Add more compelling storytelling elements
            - Improve flow and readability
            - Enhance persuasive elements and emotional appeal
            - Add specific examples and credible details
            - Optimize for engagement and conversion
            - Ensure flawless professional presentation
            
            Deliver the enhanced premium version:
            """
            
            refined_response = await self.llm.ainvoke([
                SystemMessage(content="You are refining content to achieve premium quality standards."),
                HumanMessage(content=refinement_prompt)
            ])
            
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": refined_response.content,
                "status": "premium_refined",
                "execution_time": datetime.now().isoformat(),
                "model_used": self.model_config.get('model', 'claude-3-5-sonnet'),
                "refinement_applied": True,
                "premium_features": ["advanced_storytelling", "seo_optimization", "conversion_focus", "quality_refinement"]
            }
            
        except Exception as e:
            logger.error(f"Content refinement failed: {str(e)}")
            original_result["refinement_attempted"] = True
            original_result["refinement_error"] = str(e)
            return original_result

class PremiumVisualDesigner(PremiumBaseAgent):
    """Premium visual designer with GPT-4o for advanced design thinking"""
    
    def __init__(self):
        config = PREMIUM_AGENT_CONFIGS["visual_designer"]
        super().__init__(
            name="PremiumVisualDesigner",
            description="Elite visual design specialist using GPT-4o for sophisticated design concepts, brand aesthetics, and comprehensive visual strategies.",
            model_config=config
        )
    
    async def execute_with_quality_assurance(self, task: Dict, context: Dict) -> Dict:
        """Premium visual design with quality assurance"""
        try:
            if self.llm is None:
                return await self._mock_execution(task)
            
            instruction = task.get("instruction", "")
            
            premium_prompt = f"""
            As an elite visual design specialist, create comprehensive design solutions that set industry standards:
            
            Design Brief: {instruction}
            
            Premium Design Standards:
            - Sophisticated visual hierarchy and composition principles
            - Strategic color psychology and brand-aligned palettes
            - Typography excellence with perfect readability and impact
            - User experience optimization and accessibility considerations
            - Cross-platform consistency and responsive design thinking
            - Current design trends balanced with timeless principles
            - Brand differentiation and competitive positioning
            
            Design Strategy Framework:
            - Target audience visual preferences and behaviors
            - Brand personality expression through visual elements
            - Technical implementation considerations and constraints
            - Scalability across multiple touchpoints and formats
            - Measurable design objectives and success metrics
            
            Deliver your premium design solution with detailed specifications:
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an elite visual design specialist known for sophisticated and effective design solutions."),
                HumanMessage(content=premium_prompt)
            ])
            
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": response.content,
                "status": "completed",
                "execution_time": datetime.now().isoformat(),
                "model_used": self.model_config.get('model', 'gpt-4o'),
                "premium_features": ["advanced_composition", "color_psychology", "ux_optimization", "brand_strategy"]
            }
            
        except Exception as e:
            logger.error(f"Premium visual designer execution failed: {str(e)}")
            return await self._error_fallback(task, str(e))

class PremiumBrandStrategist(PremiumBaseAgent):
    """Premium brand strategist with GPT-4o for comprehensive brand development"""
    
    def __init__(self):
        config = PREMIUM_AGENT_CONFIGS["brand_strategist"]
        super().__init__(
            name="PremiumBrandStrategist",
            description="Elite brand strategy specialist using GPT-4o for comprehensive brand development, positioning, and strategic brand management.",
            model_config=config
        )
    
    async def execute_with_quality_assurance(self, task: Dict, context: Dict) -> Dict:
        """Premium brand strategy with quality assurance"""
        try:
            if self.llm is None:
                return await self._mock_execution(task)
            
            instruction = task.get("instruction", "")
            
            premium_prompt = f"""
            As an elite brand strategy specialist, develop comprehensive brand solutions that drive market leadership:
            
            Brand Challenge: {instruction}
            
            Premium Brand Strategy Framework:
            - Deep market analysis and competitive landscape assessment
            - Target audience psychographics and behavioral insights
            - Unique value proposition and brand differentiation strategy
            - Brand personality, voice, and messaging architecture
            - Visual identity system and brand expression guidelines
            - Brand experience design across all customer touchpoints
            - Brand governance and consistency management protocols
            
            Strategic Considerations:
            - Market positioning and competitive advantages
            - Brand equity building and long-term value creation
            - Cultural relevance and social impact alignment
            - Digital transformation and omnichannel presence
            - Crisis management and brand reputation protection
            - Performance metrics and brand health monitoring
            
            Deliver your comprehensive brand strategy with implementation roadmap:
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an elite brand strategy specialist known for building market-leading brands."),
                HumanMessage(content=premium_prompt)
            ])
            
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": response.content,
                "status": "completed",
                "execution_time": datetime.now().isoformat(),
                "model_used": self.model_config.get('model', 'gpt-4o'),
                "premium_features": ["market_analysis", "positioning_strategy", "brand_architecture", "implementation_roadmap"]
            }
            
        except Exception as e:
            logger.error(f"Premium brand strategist execution failed: {str(e)}")
            return await self._error_fallback(task, str(e))

# ============================================================================
# PREMIUM STRATEGIC AGENTS (Sophia Persona)
# ============================================================================

class PremiumMarketResearcher(PremiumBaseAgent):
    """Premium market researcher with GPT-4o for comprehensive market intelligence"""
    
    def __init__(self):
        config = PREMIUM_AGENT_CONFIGS["market_researcher"]
        super().__init__(
            name="PremiumMarketResearcher",
            description="Elite market research specialist using GPT-4o for comprehensive market intelligence, consumer insights, and strategic market analysis.",
            model_config=config
        )
    
    async def execute_with_quality_assurance(self, task: Dict, context: Dict) -> Dict:
        """Premium market research with quality assurance"""
        try:
            if self.llm is None:
                return await self._mock_execution(task)
            
            instruction = task.get("instruction", "")
            
            premium_prompt = f"""
            As an elite market research specialist, conduct comprehensive market intelligence that drives strategic decisions:
            
            Research Objective: {instruction}
            
            Premium Research Framework:
            - Market size, growth trends, and future projections
            - Competitive landscape analysis and market share dynamics
            - Consumer behavior patterns and decision-making factors
            - Market segmentation and target audience profiling
            - Industry trends, disruptions, and emerging opportunities
            - Regulatory environment and compliance considerations
            - Technology adoption and digital transformation impacts
            
            Research Methodology:
            - Primary and secondary data source integration
            - Quantitative and qualitative research approaches
            - Statistical analysis and predictive modeling
            - Cross-industry benchmarking and best practices
            - Expert interviews and thought leadership insights
            - Real-time market monitoring and trend analysis
            
            Deliver comprehensive market intelligence with actionable insights and strategic recommendations:
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an elite market research specialist known for comprehensive and actionable market intelligence."),
                HumanMessage(content=premium_prompt)
            ])
            
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": response.content,
                "status": "completed",
                "execution_time": datetime.now().isoformat(),
                "model_used": self.model_config.get('model', 'gpt-4o'),
                "premium_features": ["comprehensive_analysis", "predictive_modeling", "competitive_intelligence", "strategic_insights"]
            }
            
        except Exception as e:
            logger.error(f"Premium market researcher execution failed: {str(e)}")
            return await self._error_fallback(task, str(e))

class PremiumDataAnalyst(PremiumBaseAgent):
    """Premium data analyst with GPT-4o for advanced analytics and insights"""
    
    def __init__(self):
        config = PREMIUM_AGENT_CONFIGS["data_analyst"]
        super().__init__(
            name="PremiumDataAnalyst",
            description="Elite data analysis specialist using GPT-4o for advanced analytics, statistical modeling, and data-driven insights.",
            model_config=config
        )
    
    async def execute_with_quality_assurance(self, task: Dict, context: Dict) -> Dict:
        """Premium data analysis with quality assurance"""
        try:
            if self.llm is None:
                return await self._mock_execution(task)
            
            instruction = task.get("instruction", "")
            
            premium_prompt = f"""
            As an elite data analysis specialist, deliver advanced analytics that drive strategic decision-making:
            
            Analysis Request: {instruction}
            
            Premium Analytics Framework:
            - Comprehensive data exploration and quality assessment
            - Advanced statistical analysis and hypothesis testing
            - Predictive modeling and machine learning applications
            - Data visualization and storytelling techniques
            - Pattern recognition and anomaly detection
            - Correlation analysis and causal inference
            - Performance metrics and KPI optimization
            
            Analytical Rigor:
            - Statistical significance testing and confidence intervals
            - Bias detection and mitigation strategies
            - Data validation and quality assurance protocols
            - Sensitivity analysis and scenario modeling
            - Cross-validation and model performance evaluation
            - Actionable insights and strategic recommendations
            
            Deliver comprehensive data analysis with clear methodology, findings, and strategic implications:
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an elite data analysis specialist known for rigorous methodology and actionable insights."),
                HumanMessage(content=premium_prompt)
            ])
            
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": response.content,
                "status": "completed",
                "execution_time": datetime.now().isoformat(),
                "model_used": self.model_config.get('model', 'gpt-4o'),
                "premium_features": ["advanced_statistics", "predictive_modeling", "data_visualization", "strategic_insights"]
            }
            
        except Exception as e:
            logger.error(f"Premium data analyst execution failed: {str(e)}")
            return await self._error_fallback(task, str(e))

class PremiumStrategicPlanner(PremiumBaseAgent):
    """Premium strategic planner with GPT-4o for comprehensive strategic planning"""
    
    def __init__(self):
        config = PREMIUM_AGENT_CONFIGS["strategic_planner"]
        super().__init__(
            name="PremiumStrategicPlanner",
            description="Elite strategic planning specialist using GPT-4o for comprehensive strategic planning, scenario analysis, and long-term strategic development.",
            model_config=config
        )
    
    async def execute_with_quality_assurance(self, task: Dict, context: Dict) -> Dict:
        """Premium strategic planning with quality assurance"""
        try:
            if self.llm is None:
                return await self._mock_execution(task)
            
            instruction = task.get("instruction", "")
            
            premium_prompt = f"""
            As an elite strategic planning specialist, develop comprehensive strategic solutions that drive long-term success:
            
            Strategic Challenge: {instruction}
            
            Premium Strategic Planning Framework:
            - Environmental scanning and SWOT analysis
            - Scenario planning and future state visioning
            - Strategic objective setting and prioritization
            - Resource allocation and capability assessment
            - Risk analysis and mitigation strategies
            - Implementation roadmap and milestone planning
            - Performance measurement and strategic control systems
            
            Strategic Thinking Approach:
            - Systems thinking and interconnected analysis
            - Long-term perspective with short-term tactical alignment
            - Stakeholder analysis and engagement strategies
            - Innovation and competitive advantage development
            - Change management and organizational readiness
            - Continuous monitoring and adaptive planning
            
            Deliver comprehensive strategic plan with clear implementation pathway and success metrics:
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an elite strategic planning specialist known for comprehensive and executable strategic plans."),
                HumanMessage(content=premium_prompt)
            ])
            
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": response.content,
                "status": "completed",
                "execution_time": datetime.now().isoformat(),
                "model_used": self.model_config.get('model', 'gpt-4o'),
                "premium_features": ["scenario_planning", "strategic_frameworks", "implementation_roadmap", "performance_metrics"]
            }
            
        except Exception as e:
            logger.error(f"Premium strategic planner execution failed: {str(e)}")
            return await self._error_fallback(task, str(e))

# ============================================================================
# PREMIUM OPERATIONAL AGENTS (Karen Persona)
# ============================================================================

class PremiumTaskManager(PremiumBaseAgent):
    """Premium task manager with GPT-4o for advanced project and task management"""
    
    def __init__(self):
        config = PREMIUM_AGENT_CONFIGS["task_manager"]
        super().__init__(
            name="PremiumTaskManager",
            description="Elite task management specialist using GPT-4o for advanced project management, workflow optimization, and operational excellence.",
            model_config=config
        )
    
    async def execute_with_quality_assurance(self, task: Dict, context: Dict) -> Dict:
        """Premium task management with quality assurance"""
        try:
            if self.llm is None:
                return await self._mock_execution(task)
            
            instruction = task.get("instruction", "")
            
            premium_prompt = f"""
            As an elite task management specialist, create comprehensive project management solutions that ensure operational excellence:
            
            Management Challenge: {instruction}
            
            Premium Task Management Framework:
            - Project scope definition and requirements analysis
            - Work breakdown structure and task decomposition
            - Resource planning and capacity management
            - Timeline development and critical path analysis
            - Risk identification and contingency planning
            - Quality assurance and deliverable standards
            - Communication protocols and stakeholder management
            
            Operational Excellence Standards:
            - Agile and lean methodology integration
            - Performance metrics and KPI tracking
            - Continuous improvement and optimization
            - Team coordination and collaboration tools
            - Documentation and knowledge management
            - Change management and scope control
            
            Deliver comprehensive task management plan with clear execution framework and success metrics:
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an elite task management specialist known for operational excellence and project success."),
                HumanMessage(content=premium_prompt)
            ])
            
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": response.content,
                "status": "completed",
                "execution_time": datetime.now().isoformat(),
                "model_used": self.model_config.get('model', 'gpt-4o'),
                "premium_features": ["project_planning", "resource_optimization", "risk_management", "performance_tracking"]
            }
            
        except Exception as e:
            logger.error(f"Premium task manager execution failed: {str(e)}")
            return await self._error_fallback(task, str(e))

class PremiumProcessOptimizer(PremiumBaseAgent):
    """Premium process optimizer with GPT-4o for advanced process improvement"""
    
    def __init__(self):
        config = PREMIUM_AGENT_CONFIGS["process_optimizer"]
        super().__init__(
            name="PremiumProcessOptimizer",
            description="Elite process optimization specialist using GPT-4o for advanced process improvement, efficiency enhancement, and operational transformation.",
            model_config=config
        )
    
    async def execute_with_quality_assurance(self, task: Dict, context: Dict) -> Dict:
        """Premium process optimization with quality assurance"""
        try:
            if self.llm is None:
                return await self._mock_execution(task)
            
            instruction = task.get("instruction", "")
            
            premium_prompt = f"""
            As an elite process optimization specialist, design comprehensive process improvements that drive operational excellence:
            
            Optimization Challenge: {instruction}
            
            Premium Process Optimization Framework:
            - Current state analysis and process mapping
            - Bottleneck identification and root cause analysis
            - Future state design and process reengineering
            - Efficiency metrics and performance benchmarking
            - Technology integration and automation opportunities
            - Change management and implementation planning
            - Continuous improvement and monitoring systems
            
            Optimization Methodologies:
            - Lean Six Sigma and process excellence principles
            - Value stream mapping and waste elimination
            - Statistical process control and quality management
            - Digital transformation and automation strategies
            - Human factors and ergonomic considerations
            - Cost-benefit analysis and ROI optimization
            
            Deliver comprehensive process optimization plan with clear implementation roadmap and measurable outcomes:
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an elite process optimization specialist known for transformational efficiency improvements."),
                HumanMessage(content=premium_prompt)
            ])
            
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": response.content,
                "status": "completed",
                "execution_time": datetime.now().isoformat(),
                "model_used": self.model_config.get('model', 'gpt-4o'),
                "premium_features": ["process_mapping", "efficiency_analysis", "automation_design", "continuous_improvement"]
            }
            
        except Exception as e:
            logger.error(f"Premium process optimizer execution failed: {str(e)}")
            return await self._error_fallback(task, str(e))

class PremiumAutomationSpecialist(PremiumBaseAgent):
    """Premium automation specialist with GPT-4o for advanced automation solutions"""
    
    def __init__(self):
        config = PREMIUM_AGENT_CONFIGS["automation_specialist"]
        super().__init__(
            name="PremiumAutomationSpecialist",
            description="Elite automation specialist using GPT-4o for advanced automation design, workflow automation, and intelligent process automation.",
            model_config=config
        )
    
    async def execute_with_quality_assurance(self, task: Dict, context: Dict) -> Dict:
        """Premium automation with quality assurance"""
        try:
            if self.llm is None:
                return await self._mock_execution(task)
            
            instruction = task.get("instruction", "")
            
            premium_prompt = f"""
            As an elite automation specialist, design comprehensive automation solutions that transform operational efficiency:
            
            Automation Challenge: {instruction}
            
            Premium Automation Framework:
            - Process analysis and automation opportunity assessment
            - Technology stack evaluation and tool selection
            - Workflow design and automation architecture
            - Integration planning and system connectivity
            - Error handling and exception management
            - Security and compliance considerations
            - Performance monitoring and optimization
            
            Automation Technologies:
            - Robotic Process Automation (RPA) and intelligent automation
            - API integration and system orchestration
            - Machine learning and AI-powered automation
            - Low-code/no-code platform utilization
            - Cloud automation and infrastructure as code
            - Business process management and workflow engines
            
            Deliver comprehensive automation solution with technical specifications and implementation plan:
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an elite automation specialist known for innovative and reliable automation solutions."),
                HumanMessage(content=premium_prompt)
            ])
            
            return {
                "agent_name": self.name,
                "task_id": task.get("id"),
                "result": response.content,
                "status": "completed",
                "execution_time": datetime.now().isoformat(),
                "model_used": self.model_config.get('model', 'gpt-4o'),
                "premium_features": ["automation_design", "technology_integration", "workflow_orchestration", "intelligent_automation"]
            }
            
        except Exception as e:
            logger.error(f"Premium automation specialist execution failed: {str(e)}")
            return await self._error_fallback(task, str(e))

# ============================================================================
# PREMIUM AGENT REGISTRY
# ============================================================================

class PremiumAgentRegistry:
    """Registry for premium specialized agents with quality focus"""
    
    def __init__(self):
        self.agents = {
            # Creative agents (Cherry)
            "content_writer": PremiumContentWriter,
            "visual_designer": PremiumVisualDesigner,
            "brand_strategist": PremiumBrandStrategist,
            
            # Strategic agents (Sophia)
            "market_researcher": PremiumMarketResearcher,
            "data_analyst": PremiumDataAnalyst,
            "strategic_planner": PremiumStrategicPlanner,
            
            # Operational agents (Karen)
            "task_manager": PremiumTaskManager,
            "process_optimizer": PremiumProcessOptimizer,
            "automation_specialist": PremiumAutomationSpecialist
        }
        
        logger.info(f"Premium Agent Registry initialized with {len(self.agents)} premium agents")
    
    def get_agent(self, agent_type: str):
        """Get premium agent instance by type"""
        if agent_type in self.agents:
            return self.agents[agent_type]()
        else:
            logger.warning(f"Premium agent type '{agent_type}' not found")
            return None
    
    def list_agents(self) -> List[str]:
        """List all available premium agent types"""
        return list(self.agents.keys())
    
    def get_agents_by_persona(self, persona: str) -> List[str]:
        """Get premium agents for specific persona"""
        persona_agents = {
            "cherry": ["content_writer", "visual_designer", "brand_strategist"],
            "sophia": ["market_researcher", "data_analyst", "strategic_planner"],
            "karen": ["task_manager", "process_optimizer", "automation_specialist"]
        }
        return persona_agents.get(persona, [])

# Global premium agent registry
premium_agent_registry = PremiumAgentRegistry()

# Export main classes
__all__ = [
    "PremiumContentWriter",
    "PremiumVisualDesigner", 
    "PremiumBrandStrategist",
    "PremiumMarketResearcher",
    "PremiumDataAnalyst",
    "PremiumStrategicPlanner",
    "PremiumTaskManager",
    "PremiumProcessOptimizer",
    "PremiumAutomationSpecialist",
    "PremiumAgentRegistry",
    "premium_agent_registry"
]

