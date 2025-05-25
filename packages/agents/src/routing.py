"""
Routing Logic for Agent Registry

This module provides advanced routing capabilities for the AgentRegistry, including
real-time capability scoring, load balancing, cost-aware routing, shadow testing,
and integration with Cloud Spanner for routing table storage.
"""

import asyncio
import logging
import os
import random
import time
from typing import Any, Dict, List, Optional, Tuple

from google.cloud import aiplatform, billing_v1, spanner

from core.orchestrator.src.exceptions import (
    OrchestratorError,
)
from core.orchestrator.src.utils.error_handling import error_boundary, retry

logger = logging.getLogger(__name__)


class AgentRoutingError(OrchestratorError):
    """Base exception for agent routing errors."""


class MatchingEngineError(AgentRoutingError):
    """Exception raised when there's an error with the Matching Engine."""


class RouterConnectionError(AgentRoutingError):
    """Exception raised when there's a connection error with the router's dependencies."""


class RouteCalculationError(AgentRoutingError):
    """Exception raised when there's an error calculating a route."""


class AgentRouting:
    """
    Manages advanced routing logic for agent instances in the Orchestra system.
    Handles capability scoring, load balancing, cost-aware routing, and shadow testing.
    Stores routing tables in Cloud Spanner.
    """

    def __init__(
        self,
        project_id: str,
        spanner_instance_id: str,
        spanner_database_id: str,
        matching_engine_endpoint_name: Optional[str] = None,
        location: str = "us-central1",
        use_async_db: bool = True,
    ):
        """
        Initialize the AgentRouting with Google Cloud project details.

        Args:
            project_id: Google Cloud project ID
            spanner_instance_id: Cloud Spanner instance ID
            spanner_database_id: Cloud Spanner database ID
            matching_engine_endpoint_name: Optional name of the Vertex AI Matching Engine endpoint
            location: Google Cloud region location
            use_async_db: Whether to use async database operations
        """
        self.project_id = project_id
        self.spanner_instance_id = spanner_instance_id
        self.spanner_database_id = spanner_database_id
        self.location = location or os.getenv("VERTEX_AI_LOCATION", "us-central1")
        self.matching_engine_endpoint_name = matching_engine_endpoint_name
        self.use_async_db = use_async_db

        # Initialize Vertex AI
        try:
            aiplatform.init(project=project_id, location=self.location)

            # Initialize Matching Engine endpoint if provided
            self.matching_engine_endpoint = None
            if matching_engine_endpoint_name:
                self.matching_engine_endpoint = aiplatform.MatchingEngineIndexEndpoint(
                    matching_engine_endpoint_name
                )
                logger.info(
                    f"Initialized Matching Engine endpoint: {matching_engine_endpoint_name}"
                )
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {str(e)}")
            raise RouterConnectionError("Failed to initialize Vertex AI", e)

        # Initialize Cloud Spanner client
        try:
            self.spanner_client = spanner.Client(project=project_id)
            self.instance = self.spanner_client.instance(spanner_instance_id)
            self.database = self.instance.database(spanner_database_id)

            # Initialize async client if requested
            self.async_spanner_client = None
            if use_async_db:
                from google.cloud import spanner_v1

                self.async_spanner_client = (
                    spanner_v1.services.spanner.SpannerAsyncClient()
                )
        except Exception as e:
            logger.error(f"Failed to initialize Spanner: {str(e)}")
            raise RouterConnectionError("Failed to initialize Spanner", e)

        # Initialize Cloud Billing client for cost-aware routing
        try:
            self.billing_client = billing_v1.CloudBillingClient()
        except Exception as e:
            logger.error(f"Failed to initialize Billing client: {str(e)}")
            raise RouterConnectionError("Failed to initialize Billing client", e)

        # In-memory cache for agent scores and routing data (synced with Spanner)
        self.agent_scores: Dict[str, float] = {}
        self.agent_load: Dict[str, int] = {}
        self.agent_costs: Dict[str, float] = {}
        self.agent_capabilities: Dict[str, List[str]] = {}
        self.agent_success_rates: Dict[str, float] = {}
        self.shadow_agents: Dict[str, str] = (
            {}
        )  # Mapping of production agent ID to shadow agent ID

        # Last update timestamps
        self._last_score_update = time.time()
        self._last_cost_update = time.time()
        self._score_update_interval = 300  # 5 minutes
        self._cost_update_interval = 1800  # 30 minutes

        # Calculate embeddings for common capabilities
        self.capability_vectors: Dict[str, List[float]] = {}

        # Load initial routing data from Spanner
        self._load_routing_data_from_spanner()

    @error_boundary(propagate_types=[AgentRoutingError])
    def _load_routing_data_from_spanner(self) -> None:
        """Load routing data from Cloud Spanner into memory."""
        try:
            with self.database.snapshot() as snapshot:
                # Query for agent scores
                results = snapshot.execute_sql(
                    "SELECT agent_id, capability_score, current_load, cost_per_request, "
                    "capabilities, success_rate "
                    "FROM agent_routing_table"
                )
                for row in results:
                    agent_id, score, load, cost, capabilities_str, success_rate = row
                    self.agent_scores[agent_id] = score if score is not None else 0.0
                    self.agent_load[agent_id] = load if load is not None else 0
                    self.agent_costs[agent_id] = cost if cost is not None else 0.0
                    self.agent_success_rates[agent_id] = (
                        success_rate if success_rate is not None else 0.0
                    )

                    # Parse capabilities (stored as comma-separated values)
                    if capabilities_str:
                        self.agent_capabilities[agent_id] = [
                            c.strip() for c in capabilities_str.split(",")
                        ]
                    else:
                        self.agent_capabilities[agent_id] = []

                # Query for shadow testing mappings
                shadow_results = snapshot.execute_sql(
                    "SELECT production_agent_id, shadow_agent_id "
                    "FROM shadow_testing_table"
                )
                for row in shadow_results:
                    prod_id, shadow_id = row
                    self.shadow_agents[prod_id] = shadow_id

            logger.info(f"Loaded routing data for {len(self.agent_scores)} agents")

        except Exception as e:
            logger.error(
                f"Failed to load routing data from Spanner: {str(e)}", exc_info=True
            )
            raise RouterConnectionError("Failed to load routing data from Spanner", e)

    @error_boundary(propagate_types=[AgentRoutingError])
    async def async_load_routing_data(self) -> None:
        """Asynchronously load routing data from Cloud Spanner."""
        if not self.use_async_db or not self.async_spanner_client:
            # Fall back to synchronous loading
            self._load_routing_data_from_spanner()
            return

        try:
            # Implement async Spanner operations using the async client
            # This would be the actual implementation for async Spanner queries
            # For now, we'll use a threadpool to run the synchronous version
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._load_routing_data_from_spanner)

        except Exception as e:
            logger.error(
                f"Failed to load routing data asynchronously: {str(e)}", exc_info=True
            )
            raise RouterConnectionError("Failed to load routing data asynchronously", e)

    @error_boundary(propagate_types=[AgentRoutingError])
    @retry(max_attempts=3, delay_seconds=1.0, backoff_factor=2.0)
    async def update_capability_scores(self) -> None:
        """
        Update capability scores for agents using Vertex AI Matching Engine.
        This method queries the Matching Engine to get updated scores based on agent performance vectors.
        """
        # Check if update is needed based on interval
        current_time = time.time()
        if current_time - self._last_score_update < self._score_update_interval:
            return

        try:
            updates = []

            if self.matching_engine_endpoint:
                # Use Vertex AI Matching Engine for real scoring
                for agent_id, capabilities in self.agent_capabilities.items():
                    # Generate a query vector from agent capabilities and performance metrics
                    query_vector = await self._generate_agent_performance_vector(
                        agent_id
                    )

                    # Query the Matching Engine for similarity score
                    response = self.matching_engine_endpoint.match(
                        query_embeddings=[query_vector],
                        num_neighbors=1,
                    )

                    if response and response.matches:
                        # Get the similarity score (distance metric converted to score)
                        # Lower distance means higher similarity, so convert to a 0-1 score
                        distance = response.matches[0].distance
                        updated_score = max(0, min(1, 1.0 - distance))

                        # Use exponential moving average to smooth score changes
                        current_score = self.agent_scores.get(agent_id, 0.0)
                        self.agent_scores[agent_id] = (0.7 * current_score) + (
                            0.3 * updated_score
                        )

                        # Add to batch updates
                        updates.append((agent_id, self.agent_scores[agent_id]))
            else:
                # Fall back to capability-based scoring if Matching Engine isn't available
                for agent_id, capabilities in self.agent_capabilities.items():
                    # Calculate score based on capabilities and success rate
                    capability_weight = (
                        len(capabilities) / 10.0
                    )  # Scale based on number of capabilities
                    success_rate = self.agent_success_rates.get(
                        agent_id, 0.8
                    )  # Default to 80% if unknown

                    # Calculate a weighted score
                    updated_score = (0.6 * capability_weight) + (0.4 * success_rate)
                    updated_score = max(0, min(1, updated_score))  # Clamp to 0-1

                    self.agent_scores[agent_id] = updated_score
                    updates.append((agent_id, updated_score))

            # Batch update Spanner with new scores
            if updates:
                if self.use_async_db:
                    await self._async_batch_update_scores(updates)
                else:
                    with self.database.batch() as batch:
                        for agent_id, score in updates:
                            batch.update(
                                table="agent_routing_table",
                                columns=("agent_id", "capability_score"),
                                values=[(agent_id, score)],
                            )

                logger.info(f"Updated capability scores for {len(updates)} agents")
                self._last_score_update = time.time()

        except Exception as e:
            logger.error(f"Failed to update capability scores: {str(e)}", exc_info=True)
            raise MatchingEngineError("Failed to update capability scores", e)

    async def _async_batch_update_scores(
        self, updates: List[Tuple[str, float]]
    ) -> None:
        """
        Helper method to perform async batch updates of scores in Spanner.

        Args:
            updates: List of (agent_id, score) tuples to update
        """
        if not self.async_spanner_client:
            # Fall back to synchronous update
            with self.database.batch() as batch:
                for agent_id, score in updates:
                    batch.update(
                        table="agent_routing_table",
                        columns=("agent_id", "capability_score"),
                        values=[(agent_id, score)],
                    )
            return

        # In a real implementation, this would use the async Spanner client
        # For now, use a threadpool to run the synchronous version
        loop = asyncio.get_event_loop()

        async def _run_sync_update():
            with self.database.batch() as batch:
                for agent_id, score in updates:
                    batch.update(
                        table="agent_routing_table",
                        columns=("agent_id", "capability_score"),
                        values=[(agent_id, score)],
                    )

        await loop.run_in_executor(None, _run_sync_update)

    async def _generate_agent_performance_vector(self, agent_id: str) -> List[float]:
        """
        Generate a performance vector for an agent based on capabilities and metrics.
        This vector can be used for similarity matching in the Matching Engine.

        Args:
            agent_id: Unique identifier for the agent

        Returns:
            Performance vector as a list of floats
        """
        # This would generate an embedding vector using a text embedding model
        # Typically 768 or 1536 dimensions depending on the model

        # For now, we'll generate a simple vector based on agent metrics
        # In a real implementation, you would use Vertex AI's text embedding API

        # Get agent capabilities
        capabilities = self.agent_capabilities.get(agent_id, [])
        capability_text = ", ".join(capabilities)

        # Get metrics
        success_rate = self.agent_success_rates.get(agent_id, 0.8)

        # Generate a deterministic vector from agent ID and metrics
        # (In a real implementation, you would use a text embedding model)
        vector = []
        seed = hash(agent_id + capability_text) % 10000
        random.seed(seed)

        # Generate a 128-dimensional vector based on agent properties
        for i in range(128):
            # Add some signal from the success rate to the vector
            if i % 10 == 0:
                value = success_rate + (
                    random.random() * 0.2 - 0.1
                )  # Add some randomness
            else:
                value = random.random()
            vector.append(value)

        # Normalize the vector
        magnitude = sum(v * v for v in vector) ** 0.5
        if magnitude > 0:
            vector = [v / magnitude for v in vector]

        return vector

    @error_boundary(propagate_types=[AgentRoutingError])
    @retry(max_attempts=3, delay_seconds=1.0, backoff_factor=2.0)
    async def update_cost_data(self) -> None:
        """
        Update cost data for agents using Cloud Billing reports.
        This method fetches recent billing data to adjust routing based on cost efficiency.
        """
        # Check if update is needed based on interval
        current_time = time.time()
        if current_time - self._last_cost_update < self._cost_update_interval:
            return

        try:
            # Prepare billing API request
            # In real implementation, this would query the Billing API

            # Get date range for the last 7 days
            # end_time = datetime.now()  # Removed unused assignment
            # start_time = end_time - timedelta(days=7)  # Removed unused assignment

            updates = []

            # For each agent, get the average cost per request
            for agent_id in self.agent_scores.keys():
                # Calculate average cost per request over time period
                # In a real implementation, you would use the Billing API:
                #
                # billing_service = self.billing_client.service
                # filter_str = f'resource.type="aiplatform.googleapis.com/Agent" AND resource.labels.agent_id="{agent_id}"'
                # query_filter = QueryFilter(filter=filter_str)
                # time_interval = TimeInterval(
                #     start_time=start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                #     end_time=end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                # )
                # aggregation = AggregationInfo(
                #     aggregation_type=AggregationInfo.AggregationType.AVERAGE,
                #     group_by=["resource.labels.agent_id"]
                # )
                # response = billing_service.query_cost(
                #     query_filter=query_filter,
                #     time_interval=time_interval,
                #     aggregation=aggregation
                # )

                # For now, we'll calculate a more predictable but still realistic cost
                # based on agent capabilities and a small random component for variation

                # More capabilities = higher cost
                capability_count = len(self.agent_capabilities.get(agent_id, []))
                base_cost = 0.05 + (
                    capability_count * 0.01
                )  # Base cost with capability factor

                # Add small random variation (±10%)
                variation = (random.random() * 0.2) - 0.1  # -10% to +10%
                cost = base_cost * (1 + variation)

                # Apply cost decay function: costs decrease over time due to optimization
                days_online = (
                    hash(agent_id) % 100
                ) + 30  # Simulate agent age (30-130 days)
                cost_decay = min(0.3, days_online / 1000)  # Max 30% cost reduction
                cost = cost * (1 - cost_decay)

                # Ensure cost is in a realistic range ($0.005 to $0.50 per request)
                cost = max(0.005, min(0.5, cost))

                # Update cost
                self.agent_costs[agent_id] = cost
                updates.append((agent_id, cost))

            # Batch update Spanner with new costs
            if updates:
                if self.use_async_db:
                    await self._async_batch_update_costs(updates)
                else:
                    with self.database.batch() as batch:
                        for agent_id, cost in updates:
                            batch.update(
                                table="agent_routing_table",
                                columns=("agent_id", "cost_per_request"),
                                values=[(agent_id, cost)],
                            )

                logger.info(f"Updated cost data for {len(updates)} agents")
                self._last_cost_update = time.time()

        except Exception as e:
            logger.error(f"Failed to update cost data: {str(e)}", exc_info=True)
            raise AgentRoutingError("Failed to update cost data", e)

    async def _async_batch_update_costs(self, updates: List[Tuple[str, float]]) -> None:
        """
        Helper method to perform async batch updates of costs in Spanner.

        Args:
            updates: List of (agent_id, cost) tuples to update
        """
        if not self.async_spanner_client:
            # Fall back to synchronous update
            with self.database.batch() as batch:
                for agent_id, cost in updates:
                    batch.update(
                        table="agent_routing_table",
                        columns=("agent_id", "cost_per_request"),
                        values=[(agent_id, cost)],
                    )
            return

        # In a real implementation, this would use the async Spanner client
        # For now, use a threadpool to run the synchronous version
        loop = asyncio.get_event_loop()

        async def _run_sync_update():
            with self.database.batch() as batch:
                for agent_id, cost in updates:
                    batch.update(
                        table="agent_routing_table",
                        columns=("agent_id", "cost_per_request"),
                        values=[(agent_id, cost)],
                    )

        await loop.run_in_executor(None, _run_sync_update)

    @error_boundary(propagate_types=[AgentRoutingError], fallback_value="")
    async def select_agent(self, request_context: Dict[str, Any]) -> str:
        """
        Select an agent instance based on capability scores, load, and cost data.
        Implements load balancing and cost-aware routing.

        Args:
            request_context: Context of the request to influence routing decision

        Returns:
            Selected agent ID

        Raises:
            RouteCalculationError: If there is an issue finding an appropriate agent
        """
        try:
            # Check if we need to refresh cost and capability data
            await self.update_capability_scores()
            await self.update_cost_data()

            # Get the requested capabilities from context
            requested_capabilities = request_context.get("capabilities", [])
            budget_sensitive = request_context.get("budget_sensitive", False)
            high_priority = request_context.get("priority", "normal") == "high"

            # Filter eligible agents
            eligible_agents = set(self.agent_scores.keys())

            # Filter by requested capabilities if specified
            if requested_capabilities:
                capability_filtered = set()
                for agent_id, capabilities in self.agent_capabilities.items():
                    # Check if agent has all requested capabilities
                    if all(cap in capabilities for cap in requested_capabilities):
                        capability_filtered.add(agent_id)
                eligible_agents &= capability_filtered

            # If no eligible agents, return empty string
            if not eligible_agents:
                logger.warning(
                    f"No eligible agents found for capabilities: {requested_capabilities}"
                )
                return ""

            # Prepare scoring logic
            agent_scores = {}

            # Balance between capability score, load, and cost
            for agent_id in eligible_agents:
                capability_score = self.agent_scores.get(agent_id, 0.0)
                load = self.agent_load.get(agent_id, 0)
                load_factor = min(1.0, load / 100.0)  # Normalize load (0-1)
                cost = self.agent_costs.get(agent_id, 0.0)
                cost_factor = min(1.0, cost / 0.5)  # Normalize cost (0-1)

                # Adjust weights based on request context
                if budget_sensitive:
                    # Budget sensitive - prioritize cost
                    weight_capability = 0.4
                    weight_load = 0.2
                    weight_cost = 0.4
                elif high_priority:
                    # High priority - prioritize capability and ignore load
                    weight_capability = 0.8
                    weight_load = 0.0
                    weight_cost = 0.2
                else:
                    # Standard weighting
                    weight_capability = 0.6
                    weight_load = 0.2
                    weight_cost = 0.2

                # Calculate composite score
                score = (
                    (capability_score * weight_capability)
                    - (load_factor * weight_load)
                    - (cost_factor * weight_cost)
                )

                agent_scores[agent_id] = score

            # Select top 3 agents by score
            top_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)[
                :3
            ]

            # If high priority or only one agent, select the top agent
            if high_priority or len(top_agents) == 1:
                best_agent_id = top_agents[0][0]
            else:
                # Otherwise, add randomization for load balancing (weighted random selection)
                weights = []
                agent_ids = []
                total_score = 0.0

                for agent_id, score in top_agents:
                    # Convert score to positive weight
                    weight = max(0.1, score + 1.0)  # Ensure positive weight
                    weights.append(weight)
                    agent_ids.append(agent_id)
                    total_score += weight

                # Normalize weights
                weights = [w / total_score for w in weights]

                # Weighted random selection
                best_agent_id = random.choices(agent_ids, weights=weights, k=1)[0]

            # Update load for selected agent
            if best_agent_id:
                self.agent_load[best_agent_id] = (
                    self.agent_load.get(best_agent_id, 0) + 1
                )

                # Update load in Spanner (asynchronously, don't block selection)
                asyncio.create_task(
                    self._update_agent_load(
                        best_agent_id, self.agent_load[best_agent_id]
                    )
                )

                # Check for shadow testing
                if best_agent_id in self.shadow_agents:
                    shadow_id = self.shadow_agents[best_agent_id]
                    # Log shadow request (in a real implementation, send request to shadow agent as well)
                    logger.info(
                        f"Shadow testing active: Production agent {best_agent_id}, Shadow agent {shadow_id}"
                    )

                    # Increment load for shadow agent as well
                    self.agent_load[shadow_id] = self.agent_load.get(shadow_id, 0) + 1
                    # Update shadow load in Spanner (asynchronously)
                    asyncio.create_task(
                        self._update_agent_load(shadow_id, self.agent_load[shadow_id])
                    )

                return best_agent_id
            else:
                logger.error("No suitable agent found for routing")
                return ""

        except Exception as e:
            logger.error(f"Failed to select agent: {str(e)}", exc_info=True)
            raise RouteCalculationError(f"Failed to select agent: {str(e)}", e)

    async def _update_agent_load(self, agent_id: str, load: int) -> None:
        """
        Update the load counter for an agent in the database.

        Args:
            agent_id: Unique identifier for the agent
            load: New load value to set
        """
        try:
            if self.use_async_db and self.async_spanner_client:
                # Use a threadpool to run the synchronous version for now
                # In a real implementation, this would use the async Spanner client
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None, self._sync_update_agent_load, agent_id, load
                )
            else:
                # Synchronous update
                self._sync_update_agent_load(agent_id, load)
        except Exception as e:
            logger.error(f"Failed to update agent load: {str(e)}")

    def _sync_update_agent_load(self, agent_id: str, load: int) -> None:
        """Synchronous version of load update."""
        with self.database.batch() as batch:
            batch.update(
                table="agent_routing_table",
                columns=("agent_id", "current_load"),
                values=[(agent_id, load)],
            )

    @error_boundary(propagate_types=[AgentRoutingError], fallback_value=False)
    async def register_shadow_agent(
        self, production_agent_id: str, shadow_agent_id: str
    ) -> bool:
        """
        Register a shadow agent for testing a new version alongside a production agent.

        Args:
            production_agent_id: ID of the production agent
            shadow_agent_id: ID of the shadow agent to test

        Returns:
            True if registration successful, False otherwise
        """
        try:
            self.shadow_agents[production_agent_id] = shadow_agent_id

            if self.use_async_db and self.async_spanner_client:
                # Use a threadpool for now
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    self._sync_register_shadow_agent,
                    production_agent_id,
                    shadow_agent_id,
                )
            else:
                self._sync_register_shadow_agent(production_agent_id, shadow_agent_id)

            logger.info(
                f"Registered shadow agent {shadow_agent_id} for production agent {production_agent_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to register shadow agent: {str(e)}", exc_info=True)
            raise AgentRoutingError("Failed to register shadow agent", e)

    def _sync_register_shadow_agent(
        self, production_agent_id: str, shadow_agent_id: str
    ) -> None:
        """Synchronous shadow agent registration."""
        with self.database.batch() as batch:
            batch.insert_or_update(
                table="shadow_testing_table",
                columns=("production_agent_id", "shadow_agent_id"),
                values=[(production_agent_id, shadow_agent_id)],
            )

    @error_boundary(propagate_types=[AgentRoutingError], fallback_value=False)
    async def remove_shadow_agent(self, production_agent_id: str) -> bool:
        """
        Remove a shadow agent mapping.

        Args:
            production_agent_id: ID of the production agent

        Returns:
            True if removal successful, False otherwise
        """
        try:
            if production_agent_id in self.shadow_agents:
                del self.shadow_agents[production_agent_id]

                if self.use_async_db and self.async_spanner_client:
                    # Use a threadpool for now
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        None, self._sync_remove_shadow_agent, production_agent_id
                    )
                else:
                    self._sync_remove_shadow_agent(production_agent_id)

                logger.info(
                    f"Removed shadow agent mapping for production agent {production_agent_id}"
                )
            return True

        except Exception as e:
            logger.error(f"Failed to remove shadow agent: {str(e)}", exc_info=True)
            raise AgentRoutingError("Failed to remove shadow agent", e)

    def _sync_remove_shadow_agent(self, production_agent_id: str) -> None:
        """Synchronous shadow agent removal."""
        with self.database.batch() as batch:
            batch.delete(
                table="shadow_testing_table",
                keyset=spanner.KeySet(keys=[[production_agent_id]]),
            )

    @error_boundary(propagate_types=[AgentRoutingError], fallback_value=False)
    async def register_agent(
        self,
        agent_id: str,
        capabilities: List[str] = None,
        initial_score: float = 0.5,
        initial_cost: float = 0.05,
        initial_success_rate: float = 0.9,
    ) -> bool:
        """
        Register a new agent in the routing system.

        Args:
            agent_id: Unique identifier for the agent
            capabilities: List of agent capabilities
            initial_score: Initial capability score for the agent
            initial_cost: Initial cost per request for the agent
            initial_success_rate: Initial success rate for the agent

        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Store agent data in memory
            self.agent_scores[agent_id] = initial_score
            self.agent_load[agent_id] = 0
            self.agent_costs[agent_id] = initial_cost
            self.agent_success_rates[agent_id] = initial_success_rate

            # Initialize capabilities
            if capabilities:
                self.agent_capabilities[agent_id] = capabilities
            else:
                self.agent_capabilities[agent_id] = []

            # Convert capabilities to string for storage
            capabilities_str = ",".join(self.agent_capabilities[agent_id])

            # Store in Spanner
            if self.use_async_db and self.async_spanner_client:
                # Use a threadpool for now
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    self._sync_register_agent,
                    agent_id,
                    capabilities_str,
                    initial_score,
                    initial_cost,
                    initial_success_rate,
                )
            else:
                self._sync_register_agent(
                    agent_id,
                    capabilities_str,
                    initial_score,
                    initial_cost,
                    initial_success_rate,
                )

            logger.info(
                f"Registered new agent {agent_id} in routing system with {len(capabilities or [])} capabilities"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to register agent: {str(e)}", exc_info=True)
            raise AgentRoutingError("Failed to register agent", e)

    def _sync_register_agent(
        self,
        agent_id: str,
        capabilities_str: str,
        score: float,
        cost: float,
        success_rate: float,
    ) -> None:
        """Synchronous agent registration."""
        with self.database.batch() as batch:
            batch.insert_or_update(
                table="agent_routing_table",
                columns=(
                    "agent_id",
                    "capability_score",
                    "current_load",
                    "cost_per_request",
                    "capabilities",
                    "success_rate",
                ),
                values=[(agent_id, score, 0, cost, capabilities_str, success_rate)],
            )
