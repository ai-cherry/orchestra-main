import logging
import time
import uuid
from typing import Dict, List, Optional, Tuple, Any
import json
import random
import datetime
import hashlib

logger = logging.getLogger(__name__)


class AgentRouter:
    """
    Routes requests to the appropriate agent based on capability, cost, and load.

    This router implements several routing strategies:
    - Capability-based: Routes to agents with specific capabilities
    - Cost-aware: Routes to minimize cost based on agent pricing
    - Load-balanced: Distributes load across multiple capable agents
    - Shadow-testing: Routes to production agent but tests shadow agents
    """

    def __init__(
        self,
        project_id: str,
        spanner_instance_id: Optional[str] = None,
        spanner_database_id: Optional[str] = None,
        use_async_db: bool = False,
        enable_shadow_testing: bool = False,
    ):
        """
        Initialize the AgentRouter.

        Args:
            project_id: Google Cloud project ID
            spanner_instance_id: Cloud Spanner instance ID (optional)
            spanner_database_id: Cloud Spanner database ID (optional)
            use_async_db: Whether to use async database clients
            enable_shadow_testing: Whether to enable shadow testing mode
        """
        self.project_id = project_id
        self.enable_shadow_testing = enable_shadow_testing
        self.agent_registry = {}
        self.capability_index = {}
        self.pricing_index = {}
        self.health_status = {}
        self.shadow_test_results = {}

        # Initialize logger
        self.logger = logger

    def register_agent(
        self,
        agent_id: str,
        capabilities: List[str],
        pricing_tier: str = "standard",
        max_tokens_per_min: int = 100000,
        max_requests_per_min: int = 1000,
        is_shadow: bool = False,
    ) -> None:
        """
        Register an agent with the router.

        Args:
            agent_id: Unique identifier for the agent
            capabilities: List of capabilities the agent supports
            pricing_tier: Pricing tier (economy, standard, premium)
            max_tokens_per_min: Maximum tokens per minute
            max_requests_per_min: Maximum requests per minute
            is_shadow: Whether this is a shadow test agent
        """
        self.agent_registry[agent_id] = {
            "capabilities": capabilities,
            "pricing_tier": pricing_tier,
            "max_tokens_per_min": max_tokens_per_min,
            "max_requests_per_min": max_requests_per_min,
            "current_tokens_per_min": 0,
            "current_requests_per_min": 0,
            "last_reset": time.time(),
            "is_shadow": is_shadow,
        }

        # Update capability index
        for capability in capabilities:
            if capability not in self.capability_index:
                self.capability_index[capability] = []
            self.capability_index[capability].append(agent_id)

        # Update pricing index
        if pricing_tier not in self.pricing_index:
            self.pricing_index[pricing_tier] = []
        self.pricing_index[pricing_tier].append(agent_id)

        # Initialize health status
        self.health_status[agent_id] = {
            "status": "healthy",
            "last_check": time.time(),
            "error_count": 0,
            "latency_ms": 0,
        }

        self.logger.info(f"Agent {agent_id} registered with capabilities: {capabilities}")

    def route_request(
        self,
        required_capability: str,
        request_data: Dict,
        pricing_preference: Optional[str] = None,
        strategy: str = "balanced",
    ) -> Tuple[str, Dict]:
        """
        Route a request to the appropriate agent.

        Args:
            required_capability: The capability required for this request
            request_data: The request data to be processed
            pricing_preference: Preferred pricing tier (economy, standard, premium)
            strategy: Routing strategy (balanced, cost, performance)

        Returns:
            Tuple of (agent_id, modified_request_data)
        """
        # Reset rate limits if needed
        self._reset_rate_limits_if_needed()

        # Get candidate agents
        candidates = self._get_candidate_agents(required_capability, pricing_preference)

        if not candidates:
            raise ValueError(f"No agents available with capability: {required_capability}")

        # Apply routing strategy
        if strategy == "balanced":
            agent_id = self._apply_balanced_strategy(candidates)
        elif strategy == "cost":
            agent_id = self._apply_cost_strategy(candidates)
        elif strategy == "performance":
            agent_id = self._apply_performance_strategy(candidates)
        else:
            raise ValueError(f"Unknown routing strategy: {strategy}")

        # Update rate limiting counters
        self._update_rate_limits(agent_id, request_data)

        # Check if shadow testing is enabled
        shadow_agent_id = None
        if self.enable_shadow_testing:
            shadow_agent_id = self._select_shadow_agent(required_capability, agent_id)

            if shadow_agent_id:
                # Clone request for shadow testing
                shadow_request = request_data.copy()
                shadow_request["_shadow_test"] = True
                shadow_request["_production_agent_id"] = agent_id

                # Execute shadow test asynchronously
                self._execute_shadow_test(shadow_agent_id, shadow_request)

        # Log routing decision
        self.logger.info(
            f"Routing request to agent {agent_id} for capability {required_capability} " f"using {strategy} strategy"
        )
        if shadow_agent_id:
            self.logger.info(f"Shadow testing with agent {shadow_agent_id}")

        return agent_id, request_data

    def _get_candidate_agents(self, required_capability: str, pricing_preference: Optional[str]) -> List[str]:
        """Get candidate agents based on capability and pricing preference."""
        # Filter by capability
        if required_capability not in self.capability_index:
            return []

        candidates = self.capability_index[required_capability].copy()

        # Filter by health status
        candidates = [agent_id for agent_id in candidates if self.health_status[agent_id]["status"] == "healthy"]

        # Filter by pricing preference if specified
        if pricing_preference and pricing_preference in self.pricing_index:
            pricing_candidates = self.pricing_index[pricing_preference]
            candidates = [agent_id for agent_id in candidates if agent_id in pricing_candidates]

        # Filter by rate limits
        candidates = [agent_id for agent_id in candidates if self._check_rate_limits(agent_id)]

        # Filter out shadow agents for production traffic
        candidates = [agent_id for agent_id in candidates if not self.agent_registry[agent_id].get("is_shadow", False)]

        return candidates

    def _check_rate_limits(self, agent_id: str) -> bool:
        """Check if an agent is within its rate limits."""
        agent = self.agent_registry[agent_id]

        # Check token rate limit
        if agent["current_tokens_per_min"] >= agent["max_tokens_per_min"]:
            return False

        # Check request rate limit
        if agent["current_requests_per_min"] >= agent["max_requests_per_min"]:
            return False

        return True

    def _update_rate_limits(self, agent_id: str, request_data: Dict) -> None:
        """Update rate limiting counters for an agent."""
        agent = self.agent_registry[agent_id]

        # Estimate token count from request data
        estimated_tokens = self._estimate_token_count(request_data)

        # Update counters
        agent["current_tokens_per_min"] += estimated_tokens
        agent["current_requests_per_min"] += 1

    def _reset_rate_limits_if_needed(self) -> None:
        """Reset rate limits if the minute window has passed."""
        current_time = time.time()

        for agent_id, agent in self.agent_registry.items():
            # Reset if more than 60 seconds have passed
            if current_time - agent["last_reset"] > 60:
                agent["current_tokens_per_min"] = 0
                agent["current_requests_per_min"] = 0
                agent["last_reset"] = current_time

    def _estimate_token_count(self, request_data: Dict) -> int:
        """Estimate token count from request data."""
        # Simple estimation based on JSON string length
        # In a real implementation, this would use a proper tokenizer
        json_str = json.dumps(request_data)
        return len(json_str) // 4  # Rough estimate of tokens

    def _apply_balanced_strategy(self, candidates: List[str]) -> str:
        """Apply balanced routing strategy."""
        # Find agents with lowest current load
        min_load = float("inf")
        least_loaded_agents = []

        for agent_id in candidates:
            agent = self.agent_registry[agent_id]
            load = (
                agent["current_requests_per_min"] / agent["max_requests_per_min"]
                if agent["max_requests_per_min"] > 0
                else 0
            )

            if load < min_load:
                min_load = load
                least_loaded_agents = [agent_id]
            elif load == min_load:
                least_loaded_agents.append(agent_id)

        # Randomly select from least loaded agents
        return random.choice(least_loaded_agents)

    def _apply_cost_strategy(self, candidates: List[str]) -> str:
        """Apply cost-optimized routing strategy."""
        # Group candidates by pricing tier
        economy = []
        standard = []
        premium = []

        for agent_id in candidates:
            tier = self.agent_registry[agent_id]["pricing_tier"]
            if tier == "economy":
                economy.append(agent_id)
            elif tier == "standard":
                standard.append(agent_id)
            elif tier == "premium":
                premium.append(agent_id)

        # Select from lowest cost tier available
        if economy:
            return random.choice(economy)
        elif standard:
            return random.choice(standard)
        else:
            return random.choice(premium)

    def _apply_performance_strategy(self, candidates: List[str]) -> str:
        """Apply performance-optimized routing strategy."""
        # Find agents with lowest latency
        min_latency = float("inf")
        fastest_agents = []

        for agent_id in candidates:
            latency = self.health_status[agent_id]["latency_ms"]

            if latency < min_latency:
                min_latency = latency
                fastest_agents = [agent_id]
            elif latency == min_latency:
                fastest_agents.append(agent_id)

        # Randomly select from fastest agents
        return random.choice(fastest_agents)

    def update_health_status(self, agent_id: str, status: str, latency_ms: int, error: Optional[str] = None) -> None:
        """
        Update the health status of an agent.

        Args:
            agent_id: Agent ID
            status: Status (healthy, degraded, unhealthy)
            latency_ms: Latency in milliseconds
            error: Error message if any
        """
        if agent_id not in self.health_status:
            self.logger.warning(f"Attempted to update health for unknown agent: {agent_id}")
            return

        self.health_status[agent_id].update(
            {
                "status": status,
                "last_check": time.time(),
                "latency_ms": latency_ms,
            }
        )

        if error:
            self.health_status[agent_id]["last_error"] = error
            self.health_status[agent_id]["error_count"] += 1
        else:
            self.health_status[agent_id]["error_count"] = 0

        self.logger.info(f"Updated health status for agent {agent_id}: {status}")

    def _select_shadow_agent(self, capability: str, production_agent_id: str) -> Optional[str]:
        """Select an agent for shadow testing."""
        if not self.enable_shadow_testing:
            return None

        # Get all shadow agents with the required capability
        shadow_candidates = [
            agent_id
            for agent_id in self.capability_index.get(capability, [])
            if agent_id != production_agent_id
            and self.agent_registry[agent_id].get("is_shadow", False)
            and self.health_status[agent_id]["status"] == "healthy"
        ]

        if not shadow_candidates:
            return None

        # Select a shadow agent (randomly for now)
        return random.choice(shadow_candidates)

    def _execute_shadow_test(self, shadow_agent_id: str, shadow_request: Dict) -> None:
        """Execute a shadow test (in a real implementation, this would be async)."""
        # In a real implementation, this would execute asynchronously
        # For now, just log that we would execute it
        test_id = str(uuid.uuid4())
        self.logger.info(f"Would execute shadow test {test_id} with agent {shadow_agent_id}")

        # Record shadow test in results
        self.shadow_test_results[test_id] = {
            "shadow_agent_id": shadow_agent_id,
            "production_agent_id": shadow_request["_production_agent_id"],
            "request": shadow_request,
            "status": "pending",
            "timestamp": datetime.datetime.now().isoformat(),
        }

    def record_shadow_test_result(self, test_id: str, shadow_result: Dict, production_result: Dict) -> None:
        """
        Record the result of a shadow test.

        Args:
            test_id: Shadow test ID
            shadow_result: Result from shadow agent
            production_result: Result from production agent
        """
        if test_id not in self.shadow_test_results:
            self.logger.warning(f"Unknown shadow test ID: {test_id}")
            return

        # Calculate result hash for comparison
        shadow_hash = self._hash_result(shadow_result)
        production_hash = self._hash_result(production_result)
        match = shadow_hash == production_hash

        # Update shadow test record
        self.shadow_test_results[test_id].update(
            {
                "shadow_result": shadow_result,
                "production_result": production_result,
                "shadow_hash": shadow_hash,
                "production_hash": production_hash,
                "match": match,
                "status": "completed",
                "completed_at": datetime.datetime.now().isoformat(),
            }
        )

        # Log result
        self._log_shadow_test_result(test_id, match)

    def _hash_result(self, result: Dict) -> str:
        """Create a deterministic hash of a result for comparison."""
        # Sort keys to ensure deterministic serialization
        result_json = json.dumps(result, sort_keys=True)
        return hashlib.sha256(result_json.encode()).hexdigest()

    def _log_shadow_test_result(self, test_id: str, match: bool) -> None:
        """Log shadow test result to database and logs."""
        test_data = self.shadow_test_results[test_id]
        shadow_agent_id = test_data["shadow_agent_id"]
        production_agent_id = test_data["production_agent_id"]

        if match:
            self.logger.info(
                f"Shadow test {test_id} MATCH: Shadow agent {shadow_agent_id} "
                f"matches production agent {production_agent_id}"
            )
        else:
            self.logger.warning(
                f"Shadow test {test_id} MISMATCH: Shadow agent {shadow_agent_id} "
                f"differs from production agent {production_agent_id}"
            )

        # In a real implementation, this would store the result in a database
        pass

    def get_agent_stats(self, agent_id: str) -> Dict:
        """Get statistics for an agent."""
        if agent_id not in self.agent_registry:
            raise ValueError(f"Unknown agent ID: {agent_id}")

        agent = self.agent_registry[agent_id]
        health = self.health_status[agent_id]

        return {
            "agent_id": agent_id,
            "capabilities": agent["capabilities"],
            "pricing_tier": agent["pricing_tier"],
            "health_status": health["status"],
            "latency_ms": health["latency_ms"],
            "error_count": health["error_count"],
            "current_load": {
                "tokens_per_min": agent["current_tokens_per_min"],
                "requests_per_min": agent["current_requests_per_min"],
            },
            "capacity": {
                "tokens_per_min": agent["max_tokens_per_min"],
                "requests_per_min": agent["max_requests_per_min"],
            },
        }
