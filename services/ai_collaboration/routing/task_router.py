#!/usr/bin/env python3
"""
AI Task Router Implementation
Routes tasks to appropriate AI agents based on capabilities, load, and performance
"""

import asyncio
import random
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, field
import logging
from enum import Enum

from ..interfaces import ITaskRouter, IDatabase, ICache, IMetricsCollector
from ..models.entities import AIAgent, AITask
from ..models.enums import AIAgentType, TaskStatus, MetricType
from ..models.value_objects import AgentCapabilities, TaskPayload
from ..exceptions import RoutingError


logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """Task routing strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    CAPABILITY_MATCH = "capability_match"
    PERFORMANCE_BASED = "performance_based"
    HYBRID = "hybrid"


@dataclass
class AgentLoad:
    """Track agent load and performance"""
    agent_id: str
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    avg_completion_time: float = 0.0
    success_rate: float = 1.0
    last_assigned: Optional[datetime] = None
    
    @property
    def load_score(self) -> float:
        """Calculate load score (lower is better)"""
        # Consider active tasks and recent performance
        base_load = self.active_tasks
        performance_penalty = (1 - self.success_rate) * 10
        return base_load + performance_penalty
    
    @property
    def performance_score(self) -> float:
        """Calculate performance score (higher is better)"""
        # Combine success rate and speed
        if self.completed_tasks == 0:
            return 0.5  # Neutral score for new agents
        
        speed_score = 1.0 / (1.0 + self.avg_completion_time / 60)  # Normalize to minutes
        return (self.success_rate * 0.7) + (speed_score * 0.3)


@dataclass
class RoutingDecision:
    """Routing decision with reasoning"""
    agent_id: str
    score: float
    strategy: RoutingStrategy
    reasons: List[str] = field(default_factory=list)
    alternatives: List[Tuple[str, float]] = field(default_factory=list)


class AITaskRouter(ITaskRouter):
    """
    Intelligent task router with multiple strategies
    
    Features:
    - Multiple routing strategies (round-robin, least-loaded, capability-based, etc.)
    - Real-time load tracking
    - Performance-based routing
    - Automatic failover
    - Task affinity support
    - Circuit breaker for failing agents
    """
    
    def __init__(
        self,
        database: IDatabase,
        cache: ICache,
        metrics_collector: IMetricsCollector,
        default_strategy: RoutingStrategy = RoutingStrategy.HYBRID,
        max_retries: int = 3,
        circuit_breaker_threshold: float = 0.5,
        circuit_breaker_timeout: int = 300
    ):
        self.database = database
        self.cache = cache
        self.metrics = metrics_collector
        self.default_strategy = default_strategy
        self.max_retries = max_retries
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout
        
        # Agent tracking
        self.agent_loads: Dict[str, AgentLoad] = {}
        self.available_agents: Dict[AIAgentType, List[AIAgent]] = defaultdict(list)
        self.circuit_breakers: Dict[str, datetime] = {}
        
        # Round-robin tracking
        self.round_robin_indices: Dict[AIAgentType, int] = defaultdict(int)
        
        # Task affinity (for related tasks)
        self.task_affinity: Dict[str, str] = {}  # parent_task_id -> agent_id
        
        # Background task
        self._monitor_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start the router and load agent data"""
        await self._load_agents()
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Task router started")
    
    async def stop(self) -> None:
        """Stop the router"""
        if self._monitor_task:
            self._monitor_task.cancel()
            await asyncio.gather(self._monitor_task, return_exceptions=True)
        logger.info("Task router stopped")
    
    async def route_task(
        self,
        task: AITask,
        strategy: Optional[RoutingStrategy] = None
    ) -> RoutingDecision:
        """
        Route a task to the most appropriate agent
        
        Args:
            task: Task to route
            strategy: Optional routing strategy override
            
        Returns:
            Routing decision with selected agent
        """
        try:
            strategy = strategy or self.default_strategy
            
            # Get available agents for this task type
            suitable_agents = await self._get_suitable_agents(task)
            
            if not suitable_agents:
                raise RoutingError(f"No suitable agents found for task type: {task.agent_type}")
            
            # Check for task affinity
            if task.metadata.get("parent_task_id"):
                parent_id = task.metadata["parent_task_id"]
                if parent_id in self.task_affinity:
                    affinity_agent_id = self.task_affinity[parent_id]
                    if any(a.id == affinity_agent_id for a in suitable_agents):
                        return RoutingDecision(
                            agent_id=affinity_agent_id,
                            score=1.0,
                            strategy=strategy,
                            reasons=["Task affinity with parent task"]
                        )
            
            # Apply routing strategy
            if strategy == RoutingStrategy.ROUND_ROBIN:
                decision = await self._route_round_robin(task, suitable_agents)
            elif strategy == RoutingStrategy.LEAST_LOADED:
                decision = await self._route_least_loaded(task, suitable_agents)
            elif strategy == RoutingStrategy.CAPABILITY_MATCH:
                decision = await self._route_capability_match(task, suitable_agents)
            elif strategy == RoutingStrategy.PERFORMANCE_BASED:
                decision = await self._route_performance_based(task, suitable_agents)
            else:  # HYBRID
                decision = await self._route_hybrid(task, suitable_agents)
            
            # Update tracking
            await self._update_assignment(decision.agent_id, task.id)
            
            # Store affinity if this task might have children
            if task.metadata.get("has_subtasks"):
                self.task_affinity[task.id] = decision.agent_id
            
            return decision
            
        except Exception as e:
            logger.error(f"Error routing task {task.id}: {e}")
            raise RoutingError(f"Failed to route task: {e}")
    
    async def update_task_status(
        self,
        task_id: str,
        agent_id: str,
        status: TaskStatus,
        completion_time: Optional[float] = None
    ) -> None:
        """
        Update task status and agent performance metrics
        
        Args:
            task_id: Task ID
            agent_id: Agent ID that processed the task
            status: New task status
            completion_time: Time taken to complete (in seconds)
        """
        try:
            if agent_id not in self.agent_loads:
                self.agent_loads[agent_id] = AgentLoad(agent_id=agent_id)
            
            load = self.agent_loads[agent_id]
            
            if status == TaskStatus.IN_PROGRESS:
                load.active_tasks += 1
            elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                load.active_tasks = max(0, load.active_tasks - 1)
                
                if status == TaskStatus.COMPLETED:
                    load.completed_tasks += 1
                    if completion_time:
                        # Update average completion time
                        total_time = load.avg_completion_time * (load.completed_tasks - 1)
                        load.avg_completion_time = (total_time + completion_time) / load.completed_tasks
                else:
                    load.failed_tasks += 1
                
                # Update success rate
                total_tasks = load.completed_tasks + load.failed_tasks
                load.success_rate = load.completed_tasks / total_tasks if total_tasks > 0 else 1.0
                
                # Check circuit breaker
                if load.success_rate < self.circuit_breaker_threshold:
                    self.circuit_breakers[agent_id] = datetime.utcnow()
                    logger.warning(f"Circuit breaker activated for agent {agent_id}")
            
            # Update cache
            await self._update_load_cache(agent_id, load)
            
        except Exception as e:
            logger.error(f"Error updating task status: {e}")
    
    async def get_agent_loads(self) -> Dict[str, Dict[str, Any]]:
        """
        Get current load information for all agents
        
        Returns:
            Dictionary of agent loads
        """
        result = {}
        
        for agent_id, load in self.agent_loads.items():
            result[agent_id] = {
                "active_tasks": load.active_tasks,
                "completed_tasks": load.completed_tasks,
                "failed_tasks": load.failed_tasks,
                "avg_completion_time": load.avg_completion_time,
                "success_rate": load.success_rate,
                "load_score": load.load_score,
                "performance_score": load.performance_score,
                "circuit_breaker_active": agent_id in self.circuit_breakers
            }
        
        return result
    
    async def _load_agents(self) -> None:
        """Load available agents from database"""
        try:
            query = """
                SELECT * FROM ai_agents 
                WHERE status = 'active' 
                ORDER BY created_at
            """
            
            rows = await self.database.fetch_many(query)
            
            self.available_agents.clear()
            
            for row in rows:
                agent = AIAgent(
                    id=row["id"],
                    name=row["name"],
                    type=AIAgentType(row["type"]),
                    status=row["status"],
                    capabilities=AgentCapabilities(
                        skills=row["skills"] or [],
                        max_concurrent_tasks=row["max_concurrent_tasks"] or 5,
                        supported_languages=row["supported_languages"] or [],
                        performance_metrics={}
                    ),
                    metadata=row["metadata"] or {}
                )
                
                self.available_agents[agent.type].append(agent)
                
                # Initialize load tracking
                if agent.id not in self.agent_loads:
                    # Try to load from cache
                    cached_load = await self._get_load_from_cache(agent.id)
                    if cached_load:
                        self.agent_loads[agent.id] = cached_load
                    else:
                        self.agent_loads[agent.id] = AgentLoad(agent_id=agent.id)
            
            logger.info(f"Loaded {sum(len(agents) for agents in self.available_agents.values())} agents")
            
        except Exception as e:
            logger.error(f"Error loading agents: {e}")
            raise
    
    async def _get_suitable_agents(self, task: AITask) -> List[AIAgent]:
        """Get agents suitable for a task"""
        agents = self.available_agents.get(task.agent_type, [])
        
        # Filter out circuit-broken agents
        now = datetime.utcnow()
        suitable = []
        
        for agent in agents:
            if agent.id in self.circuit_breakers:
                breaker_time = self.circuit_breakers[agent.id]
                if (now - breaker_time).total_seconds() < self.circuit_breaker_timeout:
                    continue
                else:
                    # Reset circuit breaker
                    del self.circuit_breakers[agent.id]
            
            # Check if agent has capacity
            load = self.agent_loads.get(agent.id)
            if load and load.active_tasks >= agent.capabilities.max_concurrent_tasks:
                continue
            
            # Check capabilities match
            if task.metadata.get("required_skills"):
                required_skills = set(task.metadata["required_skills"])
                agent_skills = set(agent.capabilities.skills)
                if not required_skills.issubset(agent_skills):
                    continue
            
            suitable.append(agent)
        
        return suitable
    
    async def _route_round_robin(
        self,
        task: AITask,
        agents: List[AIAgent]
    ) -> RoutingDecision:
        """Round-robin routing strategy"""
        if not agents:
            raise RoutingError("No agents available")
        
        index = self.round_robin_indices[task.agent_type] % len(agents)
        self.round_robin_indices[task.agent_type] += 1
        
        selected = agents[index]
        
        return RoutingDecision(
            agent_id=selected.id,
            score=1.0,
            strategy=RoutingStrategy.ROUND_ROBIN,
            reasons=["Round-robin selection"],
            alternatives=[(a.id, 1.0) for a in agents if a.id != selected.id]
        )
    
    async def _route_least_loaded(
        self,
        task: AITask,
        agents: List[AIAgent]
    ) -> RoutingDecision:
        """Least-loaded routing strategy"""
        agent_scores = []
        
        for agent in agents:
            load = self.agent_loads.get(agent.id, AgentLoad(agent_id=agent.id))
            score = 1.0 / (1.0 + load.load_score)
            agent_scores.append((agent, score, load))
        
        # Sort by score (highest first)
        agent_scores.sort(key=lambda x: x[1], reverse=True)
        
        selected = agent_scores[0]
        
        return RoutingDecision(
            agent_id=selected[0].id,
            score=selected[1],
            strategy=RoutingStrategy.LEAST_LOADED,
            reasons=[
                f"Lowest load score: {selected[2].load_score:.2f}",
                f"Active tasks: {selected[2].active_tasks}"
            ],
            alternatives=[(a[0].id, a[1]) for a in agent_scores[1:5]]
        )
    
    async def _route_capability_match(
        self,
        task: AITask,
        agents: List[AIAgent]
    ) -> RoutingDecision:
        """Capability-based routing strategy"""
        agent_scores = []
        
        required_skills = set(task.metadata.get("required_skills", []))
        preferred_skills = set(task.metadata.get("preferred_skills", []))
        
        for agent in agents:
            agent_skills = set(agent.capabilities.skills)
            
            # Calculate match score
            required_match = len(required_skills & agent_skills) / len(required_skills) if required_skills else 1.0
            preferred_match = len(preferred_skills & agent_skills) / len(preferred_skills) if preferred_skills else 0.0
            
            # Bonus for exact matches
            exact_match_bonus = 0.2 if required_skills == agent_skills else 0.0
            
            score = (required_match * 0.7) + (preferred_match * 0.3) + exact_match_bonus
            agent_scores.append((agent, score, agent_skills))
        
        # Sort by score
        agent_scores.sort(key=lambda x: x[1], reverse=True)
        
        selected = agent_scores[0]
        
        return RoutingDecision(
            agent_id=selected[0].id,
            score=selected[1],
            strategy=RoutingStrategy.CAPABILITY_MATCH,
            reasons=[
                f"Capability match score: {selected[1]:.2f}",
                f"Skills: {', '.join(selected[2])}"
            ],
            alternatives=[(a[0].id, a[1]) for a in agent_scores[1:5]]
        )
    
    async def _route_performance_based(
        self,
        task: AITask,
        agents: List[AIAgent]
    ) -> RoutingDecision:
        """Performance-based routing strategy"""
        agent_scores = []
        
        for agent in agents:
            load = self.agent_loads.get(agent.id, AgentLoad(agent_id=agent.id))
            
            # Get recent performance metrics
            recent_metrics = await self.metrics.get_aggregated_metrics(
                agent_id=agent.id,
                metric_type=MetricType.TASK_COMPLETION_TIME
            )
            
            # Calculate performance score
            base_score = load.performance_score
            
            # Adjust for recent performance
            if recent_metrics and recent_metrics.get("mean", 0) > 0:
                speed_factor = 60.0 / recent_metrics["mean"]  # Normalize to minutes
                base_score = (base_score * 0.7) + (min(speed_factor, 2.0) * 0.3)
            
            # Penalize if recently assigned (to distribute load)
            if load.last_assigned:
                time_since_assignment = (datetime.utcnow() - load.last_assigned).total_seconds()
                if time_since_assignment < 10:
                    base_score *= 0.8
            
            agent_scores.append((agent, base_score, load))
        
        # Sort by score
        agent_scores.sort(key=lambda x: x[1], reverse=True)
        
        selected = agent_scores[0]
        
        return RoutingDecision(
            agent_id=selected[0].id,
            score=selected[1],
            strategy=RoutingStrategy.PERFORMANCE_BASED,
            reasons=[
                f"Performance score: {selected[1]:.2f}",
                f"Success rate: {selected[2].success_rate:.2%}",
                f"Avg completion time: {selected[2].avg_completion_time:.1f}s"
            ],
            alternatives=[(a[0].id, a[1]) for a in agent_scores[1:5]]
        )
    
    async def _route_hybrid(
        self,
        task: AITask,
        agents: List[AIAgent]
    ) -> RoutingDecision:
        """Hybrid routing strategy combining multiple factors"""
        # Get scores from different strategies
        strategies = [
            (self._route_least_loaded, 0.3),
            (self._route_capability_match, 0.3),
            (self._route_performance_based, 0.4)
        ]
        
        agent_scores: Dict[str, float] = defaultdict(float)
        all_reasons = []
        
        for strategy_func, weight in strategies:
            decision = await strategy_func(task, agents)
            
            # Add weighted score
            agent_scores[decision.agent_id] += decision.score * weight
            
            # Add weighted scores for alternatives
            for alt_id, alt_score in decision.alternatives:
                agent_scores[alt_id] += alt_score * weight * 0.8  # Slightly lower weight for alternatives
            
            all_reasons.extend(decision.reasons)
        
        # Find best agent
        best_agent_id = max(agent_scores.items(), key=lambda x: x[1])[0]
        best_score = agent_scores[best_agent_id]
        
        # Get alternatives
        alternatives = [
            (aid, score) 
            for aid, score in agent_scores.items() 
            if aid != best_agent_id
        ]
        alternatives.sort(key=lambda x: x[1], reverse=True)
        
        return RoutingDecision(
            agent_id=best_agent_id,
            score=best_score,
            strategy=RoutingStrategy.HYBRID,
            reasons=["Hybrid strategy combining:"] + all_reasons[:3],
            alternatives=alternatives[:5]
        )
    
    async def _update_assignment(self, agent_id: str, task_id: str) -> None:
        """Update agent assignment tracking"""
        if agent_id not in self.agent_loads:
            self.agent_loads[agent_id] = AgentLoad(agent_id=agent_id)
        
        self.agent_loads[agent_id].last_assigned = datetime.utcnow()
        
        # Store in cache for persistence
        await self._update_load_cache(agent_id, self.agent_loads[agent_id])
    
    async def _update_load_cache(self, agent_id: str, load: AgentLoad) -> None:
        """Update agent load in cache"""
        cache_key = f"router:load:{agent_id}"
        cache_data = {
            "active_tasks": load.active_tasks,
            "completed_tasks": load.completed_tasks,
            "failed_tasks": load.failed_tasks,
            "avg_completion_time": load.avg_completion_time,
            "success_rate": load.success_rate,
            "last_assigned": load.last_assigned.isoformat() if load.last_assigned else None
        }
        
        await self.cache.set(cache_key, cache_data, ttl=3600)
    
    async def _get_load_from_cache(self, agent_id: str) -> Optional[AgentLoad]:
        """Get agent load from cache"""
        cache_key = f"router:load:{agent_id}"
        cache_data = await self.cache.get(cache_key)
        
        if cache_data:
            return AgentLoad(
                agent_id=agent_id,
                active_tasks=cache_data.get("active_tasks", 0),
                completed_tasks=cache_data.get("completed_tasks", 0),
                failed_tasks=cache_data.get("failed_tasks", 0),
                avg_completion_time=cache_data.get("avg_completion_time", 0.0),
                success_rate=cache_data.get("success_rate", 1.0),
                last_assigned=datetime.fromisoformat(cache_data["last_assigned"]) 
                    if cache_data.get("last_assigned") else None
            )
        
        return None
    
    async def _monitor_loop(self) -> None:
        """Background monitoring loop"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Reload agents periodically
                await self._load_agents()
                
                # Clean up old task affinity
                now = datetime.utcnow()
                old_affinities = []
                
                for task_id in list(self.task_affinity.keys()):
                    # Check if task is old (> 1 hour)
                    # In production, would check actual task status
                    if random.random() < 0.1:  # Simulate cleanup
                        old_affinities.append(task_id)
                
                for task_id in old_affinities:
                    del self.task_affinity[task_id]
                
                if old_affinities:
                    logger.debug(f"Cleaned up {len(old_affinities)} old task affinities")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")