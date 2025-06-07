"""
AI Agent Orchestrator Service
Manages specialized AI agent teams across Cherry, Sophia, and ParagonRX domains
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Set
from dataclasses import dataclass, field
from enum import Enum
import yaml
import uuid
from abc import ABC, abstractmethod

from shared.database import UnifiedDatabase
from services.weaviate_service import WeaviateService
from core.agents.multi_agent_swarm import (
    AgentRole, TaskPriority, TaskStatus, AgentTask,
    SpecializedAgent, SupervisorAgent, MultiAgentSwarmSystem
)
from core.memory.advanced_memory_system import MemoryRouter, MemoryLayer
from core.monitoring import MetricsCollector
from shared.circuit_breaker import CircuitBreaker
from core.cache_manager import CacheManager


class DomainType(Enum):
    """Domain types for agent teams"""
    CHERRY = "cherry"
    SOPHIA = "sophia"
    PARAGON_RX = "paragon_rx"


class AgentTeamType(Enum):
    """Types of agent teams"""
    FINANCE = "finance"
    RANCH_MANAGEMENT = "ranch_management"
    ANALYTICS = "analytics"
    RESEARCH = "research"


@dataclass
class AgentTeamConfig:
    """Configuration for an agent team"""
    domain: DomainType
    team_type: AgentTeamType
    supervisor_id: str
    agents: List[Dict[str, Any]]
    performance_targets: Dict[str, Any]
    integrations: List[str] = field(default_factory=list)


@dataclass
class AgentOperator:
    """Operator entity for managing agent teams"""
    operator_id: str
    name: str
    domain: DomainType
    permissions: List[str]
    managed_teams: List[str]
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)


class AIAgentOrchestrator:
    """
    Main orchestrator for AI agent teams across all domains
    Implements performance-first architecture with hot-swappable modules
    """
    
    def __init__(
        self,
        db: UnifiedDatabase,
        weaviate: WeaviateService,
        memory_router: MemoryRouter,
        cache_manager: CacheManager,
        metrics_collector: MetricsCollector
    ):
        self.db = db
        self.weaviate = weaviate
        self.memory_router = memory_router
        self.cache_manager = cache_manager
        self.metrics = metrics_collector
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config = self._load_configuration()
        
        # Initialize circuit breakers for external APIs
        self.circuit_breakers = self._initialize_circuit_breakers()
        
        # Agent team registry
        self.agent_teams: Dict[str, AgentTeamConfig] = {}
        self.agent_operators: Dict[str, AgentOperator] = {}
        self.swarm_systems: Dict[DomainType, MultiAgentSwarmSystem] = {}
        
        # Performance tracking
        self.performance_metrics = {
            "total_requests": 0,
            "average_response_time": 0.0,
            "p99_response_time": 0.0,
            "success_rate": 1.0
        }
        
        # Initialize agent teams
        asyncio.create_task(self._initialize_agent_teams())
    
    def _load_configuration(self) -> Dict[str, Any]:
        """Load AI agent teams configuration"""
        try:
            with open("config/ai_agent_teams.yaml", "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            return {}
    
    def _initialize_circuit_breakers(self) -> Dict[str, CircuitBreaker]:
        """Initialize circuit breakers for external integrations"""
        breakers = {}
        
        # Define circuit breaker configurations for each integration
        integration_configs = {
            "gong_io": {"failure_threshold": 5, "recovery_timeout": 60},
            "hubspot": {"failure_threshold": 3, "recovery_timeout": 30},
            "apollo_io": {"failure_threshold": 5, "recovery_timeout": 45},
            "linkedin": {"failure_threshold": 3, "recovery_timeout": 60},
            "netsuite": {"failure_threshold": 5, "recovery_timeout": 90},
            "slack": {"failure_threshold": 10, "recovery_timeout": 30},
            "github": {"failure_threshold": 5, "recovery_timeout": 30},
            "linear": {"failure_threshold": 5, "recovery_timeout": 30},
            "asana": {"failure_threshold": 5, "recovery_timeout": 30},
            "paragon_crm": {"failure_threshold": 3, "recovery_timeout": 60}
        }
        
        for integration, config in integration_configs.items():
            breakers[integration] = CircuitBreaker(
                failure_threshold=config["failure_threshold"],
                recovery_timeout=config["recovery_timeout"],
                expected_exception=Exception
            )
        
        return breakers
    
    async def _initialize_agent_teams(self):
        """Initialize all agent teams from configuration"""
        try:
            domains = self.config.get("domains", {})
            
            for domain_key, domain_config in domains.items():
                domain_type = DomainType(domain_key)
                
                # Initialize swarm system for domain
                from core.personas.enhanced_personality_engine import PersonalityEngine
                from core.coordination.cross_domain_coordinator import CrossDomainCoordinator
                
                personality_engine = PersonalityEngine(self.memory_router)
                coordinator = CrossDomainCoordinator(self.memory_router, personality_engine)
                
                swarm_system = MultiAgentSwarmSystem(
                    self.memory_router,
                    personality_engine,
                    coordinator
                )
                
                self.swarm_systems[domain_type] = swarm_system
                
                # Initialize teams for domain
                for team_key, team_config in domain_config.get("teams", {}).items():
                    team_type = AgentTeamType(team_key)
                    
                    agent_team = AgentTeamConfig(
                        domain=domain_type,
                        team_type=team_type,
                        supervisor_id=team_config.get("supervisor"),
                        agents=team_config.get("agents", []),
                        performance_targets=self.config.get("performance", {}),
                        integrations=[
                            integration 
                            for agent in team_config.get("agents", [])
                            for integration in agent.get("integrations", [])
                        ]
                    )
                    
                    team_id = f"{domain_key}_{team_key}"
                    self.agent_teams[team_id] = agent_team
                    
                    # Create specialized agents for the team
                    await self._create_team_agents(team_id, agent_team)
            
            self.logger.info(f"Initialized {len(self.agent_teams)} agent teams")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agent teams: {e}")
    
    async def _create_team_agents(self, team_id: str, team_config: AgentTeamConfig):
        """Create specialized agents for a team"""
        swarm_system = self.swarm_systems.get(team_config.domain)
        if not swarm_system:
            return
        
        for agent_config in team_config.agents:
            # Create specialized agent based on role
            agent_id = agent_config.get("id")
            agent_role = agent_config.get("role")
            
            # This would create specific agent implementations
            # For now, we'll register them with the supervisor
            self.logger.info(f"Created agent {agent_id} for team {team_id}")
    
    async def process_request(
        self,
        domain: DomainType,
        request: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a request using the appropriate agent team
        Implements performance-first processing with caching
        """
        start_time = datetime.now()
        request_id = str(uuid.uuid4())
        
        try:
            # Check cache first
            cache_key = f"{domain.value}:{request}:{user_id}"
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                self.metrics.record_counter("cache_hits", 1)
                return cached_result
            
            # Get appropriate swarm system
            swarm_system = self.swarm_systems.get(domain)
            if not swarm_system:
                raise ValueError(f"No swarm system for domain {domain}")
            
            # Process request through swarm
            result = await swarm_system.process_complex_request(
                user_id=user_id,
                request=request,
                persona=domain.value,
                context=context or {}
            )
            
            # Cache successful results
            if result.get("processing_complete"):
                await self.cache_manager.set(
                    cache_key,
                    result,
                    ttl=300  # 5 minutes
                )
            
            # Record metrics
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics.record_histogram("request_processing_time", processing_time)
            self.metrics.record_counter("requests_processed", 1)
            
            # Update performance metrics
            await self._update_performance_metrics(processing_time, True)
            
            return {
                "request_id": request_id,
                "domain": domain.value,
                "result": result,
                "processing_time_ms": processing_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            await self._update_performance_metrics(processing_time, False)
            
            self.logger.error(f"Request processing failed: {e}")
            self.metrics.record_counter("request_failures", 1)
            
            return {
                "request_id": request_id,
                "domain": domain.value,
                "error": str(e),
                "processing_time_ms": processing_time,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _update_performance_metrics(self, processing_time: float, success: bool):
        """Update orchestrator performance metrics"""
        self.performance_metrics["total_requests"] += 1
        
        # Update average response time
        current_avg = self.performance_metrics["average_response_time"]
        total = self.performance_metrics["total_requests"]
        self.performance_metrics["average_response_time"] = (
            (current_avg * (total - 1) + processing_time) / total
        )
        
        # Update success rate
        if success:
            current_rate = self.performance_metrics["success_rate"]
            self.performance_metrics["success_rate"] = (
                (current_rate * (total - 1) + 1.0) / total
            )
        else:
            current_rate = self.performance_metrics["success_rate"]
            self.performance_metrics["success_rate"] = (
                (current_rate * (total - 1) + 0.0) / total
            )
    
    async def create_agent_operator(
        self,
        name: str,
        domain: DomainType,
        permissions: List[str],
        managed_teams: List[str]
    ) -> AgentOperator:
        """Create a new agent operator"""
        operator = AgentOperator(
            operator_id=str(uuid.uuid4()),
            name=name,
            domain=domain,
            permissions=permissions,
            managed_teams=managed_teams
        )
        
        self.agent_operators[operator.operator_id] = operator
        
        # Store in database
        await self._store_operator_in_db(operator)
        
        return operator
    
    async def _store_operator_in_db(self, operator: AgentOperator):
        """Store agent operator in database with optimized query"""
        query = """
        INSERT INTO agent_operators (
            operator_id, name, domain, permissions, 
            managed_teams, created_at, last_active
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (operator_id) DO UPDATE SET
            last_active = EXCLUDED.last_active
        """
        
        await self.db.execute(
            query,
            operator.operator_id,
            operator.name,
            operator.domain.value,
            json.dumps(operator.permissions),
            json.dumps(operator.managed_teams),
            operator.created_at,
            operator.last_active
        )
    
    async def get_team_status(self, team_id: str) -> Dict[str, Any]:
        """Get status of a specific agent team"""
        team_config = self.agent_teams.get(team_id)
        if not team_config:
            return {"error": f"Team {team_id} not found"}
        
        swarm_system = self.swarm_systems.get(team_config.domain)
        if not swarm_system:
            return {"error": f"No swarm system for domain {team_config.domain}"}
        
        # Get swarm status
        swarm_status = await swarm_system.get_swarm_status()
        
        return {
            "team_id": team_id,
            "domain": team_config.domain.value,
            "team_type": team_config.team_type.value,
            "supervisor_id": team_config.supervisor_id,
            "agent_count": len(team_config.agents),
            "integrations": team_config.integrations,
            "swarm_status": swarm_status,
            "performance_metrics": self.performance_metrics,
            "last_updated": datetime.now().isoformat()
        }
    
    async def get_orchestrator_health(self) -> Dict[str, Any]:
        """Get overall orchestrator health status"""
        health_status = {
            "status": "healthy",
            "domains": {},
            "circuit_breakers": {},
            "performance": self.performance_metrics,
            "database": "connected",
            "weaviate": "connected",
            "timestamp": datetime.now().isoformat()
        }
        
        # Check domain health
        for domain, swarm in self.swarm_systems.items():
            try:
                status = await swarm.get_swarm_status()
                health_status["domains"][domain.value] = {
                    "status": "operational",
                    "agent_count": status.get("total_agents", 0)
                }
            except Exception as e:
                health_status["domains"][domain.value] = {
                    "status": "error",
                    "error": str(e)
                }
                health_status["status"] = "degraded"
        
        # Check circuit breaker status
        for name, breaker in self.circuit_breakers.items():
            health_status["circuit_breakers"][name] = {
                "state": breaker.state,
                "failure_count": breaker.failure_count
            }
        
        return health_status
    
    async def execute_with_circuit_breaker(
        self,
        integration: str,
        operation: callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute an operation with circuit breaker protection"""
        breaker = self.circuit_breakers.get(integration)
        if not breaker:
            # No circuit breaker for this integration, execute directly
            return await operation(*args, **kwargs)
        
        try:
            return await breaker.call(operation, *args, **kwargs)
        except Exception as e:
            self.logger.error(f"Circuit breaker triggered for {integration}: {e}")
            raise


# Database schema for agent operators
AGENT_OPERATOR_SCHEMA = """
CREATE TABLE IF NOT EXISTS agent_operators (
    operator_id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(50) NOT NULL,
    permissions JSONB NOT NULL DEFAULT '[]',
    managed_teams JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_active TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_agent_operators_domain ON agent_operators(domain);
CREATE INDEX idx_agent_operators_last_active ON agent_operators(last_active);

-- Performance analysis
EXPLAIN ANALYZE
SELECT operator_id, name, domain, managed_teams
FROM agent_operators
WHERE domain = 'cherry'
AND last_active > NOW() - INTERVAL '7 days';
"""