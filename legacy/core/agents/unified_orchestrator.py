"""
Unified AI Agent Orchestrator
Extends existing MultiAgentSwarmSystem with enhanced capabilities for all domains
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import yaml

from core.agents.multi_agent_swarm import (
    MultiAgentSwarmSystem, SupervisorAgent, SpecializedAgent,
    AgentRole, AgentTask, TaskPriority, TaskStatus
)
from core.memory.advanced_memory_system import MemoryRouter, MemoryLayer
from core.personas.enhanced_personality_engine import PersonalityEngine
from core.coordination.cross_domain_coordinator import CrossDomainCoordinator
from services.weaviate_service import WeaviateService
from shared.database import UnifiedDatabase
from core.cache_manager import CacheManager
from core.monitoring import MetricsCollector
from shared.circuit_breaker import CircuitBreaker


class EnhancedAgentRole(Enum):
    """Extended agent roles for all domains"""
    # Existing roles from base system
    TRAVEL_PLANNER = "travel_planner"
    MARKET_ANALYST = "market_analyst"
    CLINICAL_RESEARCHER = "clinical_researcher"
    
    # New specialized roles
    WEB_SCRAPER_SPECIALIST = "web_scraper_specialist"
    INTEGRATION_SPECIALIST = "integration_specialist"
    DATABASE_SPECIALIST = "database_specialist"
    ANALYTICS_SPECIALIST = "analytics_specialist"
    CRM_SPECIALIST = "crm_specialist"
    COMMUNICATION_SPECIALIST = "communication_specialist"
    DEVOPS_SPECIALIST = "devops_specialist"
    
    # Domain supervisors
    FINANCE_SUPERVISOR = "finance_supervisor"
    RANCH_SUPERVISOR = "ranch_supervisor"
    ANALYTICS_SUPERVISOR = "analytics_supervisor"
    RESEARCH_SUPERVISOR = "research_supervisor"
    
    # AI Operators (distinct from agents)
    AI_OPERATOR = "ai_operator"


@dataclass
class WebScrapingConfig:
    """Configuration for web scraping agents"""
    focus_areas: List[str]
    search_domains: List[str]
    time_frames: List[str]
    tools: List[str]
    continuous_monitoring: bool = False


@dataclass
class IntegrationConfig:
    """Configuration for platform integrations"""
    platform: str
    api_endpoint: str
    auth_method: str
    rate_limit: int
    circuit_breaker_config: Dict[str, Any]


class UnifiedOrchestrator(MultiAgentSwarmSystem):
    """
    Unified orchestrator extending the base MultiAgentSwarmSystem
    Integrates all domain-specific capabilities and enhancements
    """
    
    def __init__(
        self,
        memory_router: MemoryRouter,
        personality_engine: PersonalityEngine,
        coordinator: CrossDomainCoordinator,
        db: UnifiedDatabase,
        weaviate: WeaviateService,
        cache_manager: CacheManager,
        metrics: MetricsCollector
    ):
        # Initialize base system
        super().__init__(memory_router, personality_engine, coordinator)
        
        # Add enhanced components
        self.db = db
        self.weaviate = weaviate
        self.cache_manager = cache_manager
        self.metrics = metrics
        
        # Load enhanced configuration
        self.config = self._load_enhanced_config()
        
        # Initialize circuit breakers for all integrations
        self.circuit_breakers = self._initialize_all_circuit_breakers()
        
        # Web scraping teams
        self.web_scraping_teams: Dict[str, List[SpecializedAgent]] = {}
        
        # Integration specialists
        self.integration_specialists: Dict[str, SpecializedAgent] = {}
        
        # AI Operators (separate from agents)
        self.ai_operators: Dict[str, Any] = {}
        
        # Natural language query handlers
        self.query_handlers: Dict[str, Any] = {}
        
        # Initialize all enhanced components
        asyncio.create_task(self._initialize_enhanced_system())
    
    def _load_enhanced_config(self) -> Dict[str, Any]:
        """Load the enhanced configuration"""
        try:
            with open("config/ai_agent_teams.yaml", "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Failed to load enhanced config: {e}")
            return {}
    
    def _initialize_all_circuit_breakers(self) -> Dict[str, CircuitBreaker]:
        """Initialize circuit breakers for all integrations"""
        breakers = {}
        
        # Integration-specific configurations
        configs = {
            # Sophia integrations
            "gong_io": {"failure_threshold": 5, "recovery_timeout": 60},
            "sql_databases": {"failure_threshold": 3, "recovery_timeout": 30},
            "sharepoint": {"failure_threshold": 5, "recovery_timeout": 45},
            "looker": {"failure_threshold": 5, "recovery_timeout": 45},
            "lattice": {"failure_threshold": 5, "recovery_timeout": 60},
            "hubspot": {"failure_threshold": 3, "recovery_timeout": 30},
            "apollo_io": {"failure_threshold": 5, "recovery_timeout": 45},
            "linkedin": {"failure_threshold": 3, "recovery_timeout": 60},
            "netsuite": {"failure_threshold": 5, "recovery_timeout": 90},
            "slack": {"failure_threshold": 10, "recovery_timeout": 30},
            "github": {"failure_threshold": 5, "recovery_timeout": 30},
            "linear": {"failure_threshold": 5, "recovery_timeout": 30},
            "asana": {"failure_threshold": 5, "recovery_timeout": 30},
            
            # ParagonRX integrations
            "paragon_crm": {"failure_threshold": 3, "recovery_timeout": 60},
            "clinical_databases": {"failure_threshold": 5, "recovery_timeout": 60},
            
            # Web scraping
            "web_scraper": {"failure_threshold": 10, "recovery_timeout": 30},
            "specialized_browser": {"failure_threshold": 5, "recovery_timeout": 45}
        }
        
        for name, config in configs.items():
            breakers[name] = CircuitBreaker(
                failure_threshold=config["failure_threshold"],
                recovery_timeout=config["recovery_timeout"],
                expected_exception=Exception
            )
        
        return breakers
    
    async def _initialize_enhanced_system(self):
        """Initialize all enhanced components"""
        try:
            # Initialize web scraping teams
            await self._initialize_web_scraping_teams()
            
            # Initialize integration specialists
            await self._initialize_integration_specialists()
            
            # Initialize natural language query handlers
            await self._initialize_query_handlers()
            
            # Initialize AI operators interface
            await self._initialize_ai_operators()
            
            self.logger.info("Enhanced orchestration system initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize enhanced system: {e}")
    
    async def _initialize_web_scraping_teams(self):
        """Initialize web scraping teams for each domain"""
        domains = self.config.get("domains", {})
        
        for domain_key, domain_config in domains.items():
            for team_key, team_config in domain_config.get("teams", {}).items():
                web_team = team_config.get("web_scraping_team")
                if web_team:
                    team_id = f"{domain_key}_{team_key}_web_team"
                    self.web_scraping_teams[team_id] = []
                    
                    for agent_config in web_team.get("agents", []):
                        # Create specialized web scraping agent
                        agent = await self._create_web_scraping_agent(
                            agent_config,
                            domain_key,
                            team_key
                        )
                        self.web_scraping_teams[team_id].append(agent)
                        
                        # Register with supervisor
                        await self.supervisor.register_agent(agent)
    
    async def _create_web_scraping_agent(
        self,
        config: Dict[str, Any],
        domain: str,
        team: str
    ) -> SpecializedAgent:
        """Create a specialized web scraping agent"""
        from core.agents.web_scraping_agents import EnhancedWebScrapingAgent
        
        agent = EnhancedWebScrapingAgent(
            agent_id=config.get("id"),
            domain=domain,
            memory_router=self.memory_router,
            weaviate=self.weaviate,
            circuit_breaker=self.circuit_breakers.get("web_scraper"),
            config=WebScrapingConfig(
                focus_areas=config.get("focus_areas", []),
                search_domains=config.get("search_domains", []),
                time_frames=config.get("time_frames", ["daily"]),
                tools=config.get("tools", ["web_scraper"]),
                continuous_monitoring=config.get("continuous_monitoring", False)
            )
        )
        
        return agent
    
    async def _initialize_integration_specialists(self):
        """Initialize platform integration specialists"""
        sophia_config = self.config.get("domains", {}).get("sophia", {})
        analytics_team = sophia_config.get("teams", {}).get("analytics", {})
        
        for specialist_config in analytics_team.get("integration_specialists", []):
            specialist = await self._create_integration_specialist(specialist_config)
            platform = specialist_config.get("platform")
            self.integration_specialists[platform] = specialist
            
            # Register with supervisor
            await self.supervisor.register_agent(specialist)
    
    async def _create_integration_specialist(
        self,
        config: Dict[str, Any]
    ) -> SpecializedAgent:
        """Create a platform integration specialist"""
        from core.agents.integration_specialists import PlatformIntegrationAgent
        
        agent = PlatformIntegrationAgent(
            agent_id=config.get("id"),
            platform=config.get("platform"),
            role=EnhancedAgentRole[config.get("role")],
            memory_router=self.memory_router,
            db=self.db,
            circuit_breaker=self.circuit_breakers.get(config.get("platform")),
            capabilities=config.get("capabilities", [])
        )
        
        return agent
    
    async def _initialize_query_handlers(self):
        """Initialize natural language query handlers"""
        # Create query handlers for each domain
        self.query_handlers = {
            "cherry": CherryQueryHandler(self),
            "sophia": SophiaQueryHandler(self),
            "paragon_rx": ParagonQueryHandler(self)
        }
    
    async def _initialize_ai_operators(self):
        """Initialize AI operators management system"""
        from core.agents.ai_operators import AIOperatorManager
        
        self.operator_manager = AIOperatorManager(
            db=self.db,
            memory_router=self.memory_router,
            metrics=self.metrics
        )
    
    async def process_natural_language_query(
        self,
        query: str,
        domain: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process natural language queries with enhanced context understanding
        Examples:
        - "Sophia, give me an overall health analysis of Client X"
        - "Cherry, what are the best swing trade opportunities today?"
        - "Karen, find new clinical trials for diabetes"
        """
        start_time = datetime.now()
        
        try:
            # Get appropriate query handler
            handler = self.query_handlers.get(domain)
            if not handler:
                raise ValueError(f"No query handler for domain: {domain}")
            
            # Check cache for similar queries
            cache_key = f"nlq:{domain}:{query}:{user_id}"
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                self.metrics.record_counter("nlq_cache_hits", 1)
                return cached_result
            
            # Process query through handler
            result = await handler.process_query(query, user_id, context)
            
            # Cache successful results
            if result.get("success"):
                await self.cache_manager.set(cache_key, result, ttl=300)
            
            # Record metrics
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics.record_histogram("nlq_processing_time", processing_time)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Natural language query failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "domain": domain
            }
    
    async def create_data_ingestion_pipeline(
        self,
        source: str,
        destination: str,
        transformation_rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a data ingestion pipeline for large file processing"""
        pipeline_config = {
            "source": source,
            "destination": destination,
            "transformations": transformation_rules,
            "chunking": {
                "enabled": True,
                "chunk_size": 1000000,  # 1MB chunks
                "parallel_processing": True
            },
            "vector_indexing": {
                "enabled": True,
                "embedding_model": "text-embedding-ada-002",
                "metadata_extraction": True
            }
        }
        
        # Create pipeline in database
        pipeline_id = await self._store_pipeline_config(pipeline_config)
        
        # Start ingestion process
        asyncio.create_task(self._run_ingestion_pipeline(pipeline_id))
        
        return {
            "pipeline_id": pipeline_id,
            "status": "started",
            "config": pipeline_config
        }
    
    async def _store_pipeline_config(self, config: Dict[str, Any]) -> str:
        """Store pipeline configuration in database"""
        query = """
        INSERT INTO data_ingestion_pipelines (
            config, status, created_at
        ) VALUES ($1, $2, $3)
        RETURNING pipeline_id
        """
        
        result = await self.db.fetchone(
            query,
            json.dumps(config),
            "initialized",
            datetime.now()
        )
        
        return result["pipeline_id"]
    
    async def _run_ingestion_pipeline(self, pipeline_id: str):
        """Run data ingestion pipeline asynchronously"""
        try:
            # Get pipeline config
            config = await self._get_pipeline_config(pipeline_id)
            
            # Process data through pipeline
            # This would integrate with existing data ingestion services
            
            # Update pipeline status
            await self._update_pipeline_status(pipeline_id, "completed")
            
        except Exception as e:
            self.logger.error(f"Pipeline {pipeline_id} failed: {e}")
            await self._update_pipeline_status(pipeline_id, "failed", str(e))
    
    async def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get comprehensive orchestrator status"""
        base_status = await self.get_swarm_status()
        
        enhanced_status = {
            **base_status,
            "web_scraping_teams": {
                team_id: len(agents)
                for team_id, agents in self.web_scraping_teams.items()
            },
            "integration_specialists": list(self.integration_specialists.keys()),
            "circuit_breakers": {
                name: {
                    "state": breaker.state,
                    "failure_count": breaker.failure_count
                }
                for name, breaker in self.circuit_breakers.items()
            },
            "ai_operators": await self.operator_manager.get_operator_count(),
            "cache_stats": await self.cache_manager.get_stats(),
            "database_health": await self._check_database_health()
        }
        
        return enhanced_status
    
    async def _check_database_health(self) -> str:
        """Check database health status"""
        try:
            await self.db.execute("SELECT 1")
            return "healthy"
        except Exception:
            return "unhealthy"


class CherryQueryHandler:
    """Natural language query handler for Cherry domain"""
    
    def __init__(self, orchestrator: UnifiedOrchestrator):
        self.orchestrator = orchestrator
        self.logger = logging.getLogger(__name__)
    
    async def process_query(
        self,
        query: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process Cherry-specific queries"""
        query_lower = query.lower()
        
        # Determine query intent
        if "swing trade" in query_lower or "trading" in query_lower:
            return await self._handle_trading_query(query, user_id, context)
        elif "ranch" in query_lower or "property" in query_lower:
            return await self._handle_ranch_query(query, user_id, context)
        else:
            return await self._handle_general_query(query, user_id, context)
    
    async def _handle_trading_query(
        self,
        query: str,
        user_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle trading-related queries"""
        # Create task for swing trade analyst
        task = AgentTask(
            task_id=f"cherry_trading_{datetime.now().timestamp()}",
            agent_role=AgentRole.MARKET_ANALYST,
            persona="cherry",
            task_type="market_analysis",
            description=query,
            priority=TaskPriority.HIGH,
            context=context or {}
        )
        
        # Submit to supervisor
        task_id = await self.orchestrator.supervisor.submit_task(task)
        
        # Wait for results (with timeout)
        result = await self._wait_for_task_completion(task_id, timeout=30)
        
        return {
            "success": True,
            "query": query,
            "response": result,
            "domain": "cherry_finance"
        }
    
    async def _wait_for_task_completion(
        self,
        task_id: str,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Wait for task completion with timeout"""
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < timeout:
            # Check if task is completed
            if task_id in [t.task_id for t in self.orchestrator.supervisor.completed_tasks]:
                task = next(t for t in self.orchestrator.supervisor.completed_tasks if t.task_id == task_id)
                return task.results
            
            await asyncio.sleep(0.5)
        
        return {"error": "Task timeout"}


class SophiaQueryHandler:
    """Natural language query handler for Sophia domain"""
    
    def __init__(self, orchestrator: UnifiedOrchestrator):
        self.orchestrator = orchestrator
        self.logger = logging.getLogger(__name__)
    
    async def process_query(
        self,
        query: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process Sophia-specific queries
        Examples:
        - "Give me an overall health analysis of Client X"
        - "How is Sales Rep Y doing this month"
        """
        query_lower = query.lower()
        
        # Extract entities from query
        client_name = self._extract_client_name(query)
        employee_name = self._extract_employee_name(query)
        
        if client_name:
            return await self._handle_client_query(query, client_name, user_id, context)
        elif employee_name:
            return await self._handle_employee_query(query, employee_name, user_id, context)
        else:
            return await self._handle_business_query(query, user_id, context)
    
    async def _handle_client_query(
        self,
        query: str,
        client_name: str,
        user_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle client-related queries"""
        # Gather data from all integration specialists
        data_sources = {}
        
        for platform, specialist in self.orchestrator.integration_specialists.items():
            try:
                # Create task for each specialist
                task = AgentTask(
                    task_id=f"sophia_client_{platform}_{datetime.now().timestamp()}",
                    agent_role=specialist.role,
                    persona="sophia",
                    task_type="client_data_extraction",
                    description=f"Extract data for client {client_name}",
                    priority=TaskPriority.HIGH,
                    context={
                        "client_name": client_name,
                        "platform": platform,
                        "query": query
                    }
                )
                
                # Submit task
                task_id = await self.orchestrator.supervisor.submit_task(task)
                data_sources[platform] = task_id
                
            except Exception as e:
                self.logger.error(f"Failed to query {platform}: {e}")
        
        # Collect results from all sources
        aggregated_data = {}
        for platform, task_id in data_sources.items():
            result = await self._wait_for_task_completion(task_id)
            if result and not result.get("error"):
                aggregated_data[platform] = result
        
        # Analyze aggregated data
        analysis = await self._analyze_client_health(client_name, aggregated_data)
        
        return {
            "success": True,
            "query": query,
            "client": client_name,
            "analysis": analysis,
            "data_sources": list(aggregated_data.keys()),
            "domain": "sophia_analytics"
        }
    
    def _extract_client_name(self, query: str) -> Optional[str]:
        """Extract client name from query"""
        # Simple pattern matching - would use NLP in production
        import re
        patterns = [
            r"client\s+(\w+)",
            r"Client\s+(\w+)",
            r"customer\s+(\w+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_employee_name(self, query: str) -> Optional[str]:
        """Extract employee name from query"""
        import re
        patterns = [
            r"(?:sales rep|rep|employee)\s+(\w+)",
            r"(?:Sales Rep|Rep|Employee)\s+(\w+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    async def _analyze_client_health(
        self,
        client_name: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze client health from aggregated data"""
        health_score = 85  # Base score
        insights = []
        risks = []
        opportunities = []
        
        # Analyze Gong.io data
        if "gong_io" in data:
            gong_data = data["gong_io"]
            # Analyze call sentiment, engagement, etc.
            insights.append("Recent calls show positive sentiment")
        
        # Analyze HubSpot data
        if "hubspot" in data:
            hubspot_data = data["hubspot"]
            # Analyze pipeline, deals, etc.
            opportunities.append("3 deals in negotiation stage")
        
        # Analyze Slack mentions
        if "slack" in data:
            slack_data = data["slack"]
            # Analyze team discussions
            insights.append("Team actively discussing expansion opportunities")
        
        return {
            "health_score": health_score,
            "status": "healthy" if health_score > 70 else "at_risk",
            "insights": insights,
            "risks": risks,
            "opportunities": opportunities,
            "recommendations": [
                "Schedule quarterly business review",
                "Explore upsell opportunities"
            ],
            "last_updated": datetime.now().isoformat()
        }
    
    async def _wait_for_task_completion(
        self,
        task_id: str,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Wait for task completion with timeout"""
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < timeout:
            if task_id in [t.task_id for t in self.orchestrator.supervisor.completed_tasks]:
                task = next(t for t in self.orchestrator.supervisor.completed_tasks if t.task_id == task_id)
                return task.results
            
            await asyncio.sleep(0.5)
        
        return {"error": "Task timeout"}


class ParagonQueryHandler:
    """Natural language query handler for ParagonRX domain"""
    
    def __init__(self, orchestrator: UnifiedOrchestrator):
        self.orchestrator = orchestrator
        self.logger = logging.getLogger(__name__)
    
    async def process_query(
        self,
        query: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process ParagonRX-specific queries"""
        query_lower = query.lower()
        
        if "clinical trial" in query_lower or "study" in query_lower:
            return await self._handle_clinical_trial_query(query, user_id, context)
        elif "cro" in query_lower or "research organization" in query_lower:
            return await self._handle_cro_query(query, user_id, context)
        else:
            return await self._handle_pharma_query(query, user_id, context)
    
    async def _handle_clinical_trial_query(
        self,
        query: str,
        user_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle clinical trial queries"""
        # Use web scraping team for clinical trials
        web_team_id = "paragon_rx_research_web_team"
        web_team = self.orchestrator.web_scraping_teams.get(web_team_id, [])
        
        if not web_team:
            return {
                "success": False,
                "error": "Web scraping team not available"
            }
        
        # Create task for web scraping
        task = AgentTask(
            task_id=f"paragon_trial_search_{datetime.now().timestamp()}",
            agent_role=EnhancedAgentRole.WEB_SCRAPER_SPECIALIST,
            persona="karen",
            task_type="clinical_trial_search",
            description=query,
            priority=TaskPriority.HIGH,
            context={
                "search_domains": ["clinicaltrials.gov", "pubmed.ncbi.nlm.nih.gov"],
                "continuous_monitoring": True,
                **context
            }
        )
        
        # Submit to first available web scraper
        task_id = await self.orchestrator.supervisor.submit_task(task)
        
        # Wait for results
        result = await self._wait_for_task_completion(task_id)
        
        # Sync with Paragon CRM if results found
        if result.get("trials_found"):
            await self._sync_with_paragon_crm(result)
        
        return {
            "success": True,
            "query": query,
            "results": result,
            "domain": "paragon_rx"
        }
    
    async def _sync_with_paragon_crm(self, trial_data: Dict[str, Any]):
        """Sync clinical trial data with Paragon CRM"""
        try:
            # Use Paragon CRM integration
            crm_task = AgentTask(
                task_id=f"paragon_crm_sync_{datetime.now().timestamp()}",
                agent_role=AgentRole.CLINICAL_RESEARCHER,
                persona="karen",
                task_type="crm_synchronization",
                description="Sync clinical trial data with CRM",
                priority=TaskPriority.MEDIUM,
                context={"trial_data": trial_data}
            )
            
            await self.orchestrator.supervisor.submit_task(crm_task)
            
        except Exception as e:
            self.logger.error(f"CRM sync failed: {e}")
    
    async def _wait_for_task_completion(
        self,
        task_id: str,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Wait for task completion with timeout"""
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < timeout:
            if task_id in [t.task_id for t in self.orchestrator.supervisor.completed_tasks]:
                task = next(t for t in self.orchestrator.supervisor.completed_tasks if t.task_id == task_id)
                return task.results
            
            await asyncio.sleep(0.5)
        
        return {"error": "Task timeout"}


# Database schema for enhanced orchestration
ENHANCED_ORCHESTRATION_SCHEMA = """
-- Data ingestion pipelines
CREATE TABLE IF NOT EXISTS data_ingestion_pipelines (
    pipeline_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config JSONB NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    error_message TEXT,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_pipelines_status ON data_ingestion_pipelines(status);
CREATE INDEX idx_pipelines_created ON data_ingestion_pipelines(created_at);

-- Natural language query logs
CREATE TABLE IF NOT EXISTS nlq_logs (
    query_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(50) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    query TEXT NOT NULL,
    response JSONB,
    processing_time_ms INTEGER,
    success BOOLEAN NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_nlq_domain_user ON nlq_logs(domain, user_id);
CREATE INDEX idx_nlq_created ON nlq_logs(created_at);

-- Web scraping results cache
CREATE TABLE IF NOT EXISTS web_scraping_cache (
    cache_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(50) NOT NULL,
    search_query TEXT NOT NULL,
    search_domains TEXT[],
    results JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_scraping_domain_query ON web_scraping_cache(domain, search_query);
CREATE INDEX idx_scraping_expires ON web_scraping_cache(expires_at);

-- Integration health metrics
CREATE TABLE IF NOT EXISTS integration_health (
    integration_name VARCHAR(100) PRIMARY KEY,
    status VARCHAR(50) NOT NULL,
    last_success TIMESTAMP,
    failure_count INTEGER DEFAULT 0,
    avg_response_time_ms FLOAT,
    circuit_breaker_state VARCHAR(50),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Performance optimization example
EXPLAIN ANALYZE
SELECT
    p.pipeline_id,
    p.status,
    p.created_at,
    COUNT(l.query_id) as query_count
FROM data_ingestion_pipelines p
LEFT JOIN nlq_logs l ON l.created_at >= p.created_at
WHERE p.status = 'active'
GROUP BY p.pipeline_id, p.status, p.created_at
ORDER BY p.created_at DESC
LIMIT 100;
"""