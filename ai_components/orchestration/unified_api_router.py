"""Unified API Router for intelligent routing between OpenRouter and orchestrator services."""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import httpx
from pydantic import BaseModel, Field

from shared.utils.error_handling import handle_errors
from shared.utils.performance import benchmark

logger = logging.getLogger(__name__)


class ServiceType(str, Enum):
    """Available service types."""

    OPENROUTER = "openrouter"
    ORCHESTRATOR = "orchestrator"
    FALLBACK = "fallback"


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Service unavailable
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class ServiceMetrics:
    """Metrics for a service."""

    total_requests: int = 0
    failed_requests: int = 0
    success_rate: float = 1.0
    average_latency: float = 0.0
    last_failure: Optional[datetime] = None
    consecutive_failures: int = 0


class RoutingDecision(BaseModel):
    """Routing decision details."""

    service: ServiceType
    reason: str
    confidence: float = Field(ge=0.0, le=1.0)
    fallback_options: List[ServiceType] = Field(default_factory=list)


class CircuitBreaker:
    """Circuit breaker for service protection."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_requests: int = 3,
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before attempting recovery
            half_open_requests: Test requests in half-open state
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_requests = half_open_requests
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_successes = 0

    def record_success(self) -> None:
        """Record a successful request."""
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_successes += 1
            if self.half_open_successes >= self.half_open_requests:
                self.state = CircuitState.CLOSED
                self.failures = 0
                logger.info("Circuit breaker closed after recovery")
        elif self.state == CircuitState.CLOSED:
            self.failures = 0

    def record_failure(self) -> None:
        """Record a failed request."""
        self.failures += 1
        self.last_failure_time = datetime.utcnow()

        if self.state == CircuitState.CLOSED:
            if self.failures >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker opened after {self.failures} failures")
        elif self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.half_open_successes = 0
            logger.warning("Circuit breaker reopened during recovery")

    def can_request(self) -> bool:
        """Check if requests are allowed."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if self.last_failure_time:
                time_since_failure = (
                    datetime.utcnow() - self.last_failure_time
                ).total_seconds()
                if time_since_failure >= self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_successes = 0
                    logger.info("Circuit breaker entering half-open state")
                    return True
            return False

        # Half-open state
        return True


class RetryStrategy:
    """Retry strategy with exponential backoff."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
    ):
        """Initialize retry strategy.

        Args:
            max_retries: Maximum retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt.

        Args:
            attempt: Current attempt number (0-based)

        Returns:
            Delay in seconds
        """
        delay = self.base_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)


class UnifiedAPIRouter:
    """Intelligent router for API requests."""

    def __init__(
        self,
        openrouter_api_key: str,
        orchestrator_url: str,
        openrouter_base_url: str = "https://openrouter.ai/api/v1",
    ):
        """Initialize the router.

        Args:
            openrouter_api_key: API key for OpenRouter
            orchestrator_url: URL for orchestrator service
            openrouter_base_url: Base URL for OpenRouter API
        """
        self.openrouter_api_key = openrouter_api_key
        self.orchestrator_url = orchestrator_url
        self.openrouter_base_url = openrouter_base_url

        # HTTP clients with connection pooling
        self.openrouter_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
                keepalive_expiry=30.0
            ),
            headers={
                "User-Agent": "Orchestra-AI/1.0"
            }
        )
        self.orchestrator_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
                keepalive_expiry=30.0
            ),
            headers={
                "User-Agent": "Orchestra-AI/1.0"
            }
        )

        # Circuit breakers
        self.circuit_breakers = {
            ServiceType.OPENROUTER: CircuitBreaker(),
            ServiceType.ORCHESTRATOR: CircuitBreaker(),
        }

        # Retry strategies
        self.retry_strategies = {
            ServiceType.OPENROUTER: RetryStrategy(max_retries=3),
            ServiceType.ORCHESTRATOR: RetryStrategy(max_retries=5),
        }

        # Service metrics
        self.metrics: Dict[ServiceType, ServiceMetrics] = {
            ServiceType.OPENROUTER: ServiceMetrics(),
            ServiceType.ORCHESTRATOR: ServiceMetrics(),
        }

        # Request routing rules
        self.routing_rules = self._initialize_routing_rules()

    def _initialize_routing_rules(self) -> Dict[str, ServiceType]:
        """Initialize routing rules based on request patterns."""
        return {
            # Route to orchestrator for multi-agent tasks
            "multi_agent": ServiceType.ORCHESTRATOR,
            "workflow": ServiceType.ORCHESTRATOR,
            "coordinate": ServiceType.ORCHESTRATOR,
            # Route to OpenRouter for direct model calls
            "completion": ServiceType.OPENROUTER,
            "chat": ServiceType.OPENROUTER,
            "embedding": ServiceType.OPENROUTER,
        }

    @benchmark
    async def route_request(
        self, request_type: str, payload: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], RoutingDecision]:
        """Route request to appropriate service.

        Args:
            request_type: Type of request
            payload: Request payload

        Returns:
            Tuple of (response, routing_decision)
        """
        # Determine primary service
        decision = self._make_routing_decision(request_type, payload)

        # Try primary service
        if self.circuit_breakers[decision.service].can_request():
            try:
                response = await self._execute_with_retry(
                    decision.service, request_type, payload
                )
                return response, decision
            except Exception as e:
                logger.error(f"Primary service {decision.service} failed: {e}")

        # Try fallback services
        for fallback in decision.fallback_options:
            if self.circuit_breakers[fallback].can_request():
                try:
                    response = await self._execute_with_retry(
                        fallback, request_type, payload
                    )
                    decision.service = fallback
                    decision.reason = f"Fallback to {fallback}"
                    return response, decision
                except Exception as e:
                    logger.error(f"Fallback service {fallback} failed: {e}")

        raise Exception("All services unavailable")

    def _make_routing_decision(
        self, request_type: str, payload: Dict[str, Any]
    ) -> RoutingDecision:
        """Make intelligent routing decision.

        Args:
            request_type: Type of request
            payload: Request payload

        Returns:
            Routing decision
        """
        # Check routing rules
        if request_type in self.routing_rules:
            primary = self.routing_rules[request_type]
        else:
            # Default routing based on payload analysis
            if self._requires_orchestration(payload):
                primary = ServiceType.ORCHESTRATOR
            else:
                primary = ServiceType.OPENROUTER

        # Determine fallback options
        fallbacks = []
        if primary == ServiceType.OPENROUTER:
            fallbacks.append(ServiceType.ORCHESTRATOR)
        else:
            fallbacks.append(ServiceType.OPENROUTER)

        # Calculate confidence based on metrics
        confidence = self._calculate_confidence(primary)

        return RoutingDecision(
            service=primary,
            reason=f"Routed based on request type: {request_type}",
            confidence=confidence,
            fallback_options=fallbacks,
        )

    def _requires_orchestration(self, payload: Dict[str, Any]) -> bool:
        """Check if request requires orchestration.

        Args:
            payload: Request payload

        Returns:
            True if orchestration needed
        """
        # Check for multi-agent indicators
        if "agents" in payload or "workflow" in payload:
            return True

        # Check for complex task indicators
        if "steps" in payload or "coordination" in payload:
            return True

        # Check task complexity
        task = payload.get("task", "")
        complex_keywords = [
            "coordinate",
            "multiple",
            "workflow",
            "pipeline",
            "orchestrate",
        ]
        return any(keyword in task.lower() for keyword in complex_keywords)

    def _calculate_confidence(self, service: ServiceType) -> float:
        """Calculate confidence in service.

        Args:
            service: Service type

        Returns:
            Confidence score (0-1)
        """
        metrics = self.metrics[service]

        # Base confidence on success rate
        confidence = metrics.success_rate

        # Adjust for circuit breaker state
        breaker = self.circuit_breakers[service]
        if breaker.state == CircuitState.OPEN:
            confidence *= 0.1
        elif breaker.state == CircuitState.HALF_OPEN:
            confidence *= 0.5

        # Adjust for recent failures
        if metrics.last_failure:
            time_since_failure = (
                datetime.utcnow() - metrics.last_failure
            ).total_seconds()
            if time_since_failure < 300:  # 5 minutes
                confidence *= 0.8

        return confidence

    async def _execute_with_retry(
        self, service: ServiceType, request_type: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute request with retry logic.

        Args:
            service: Service to use
            request_type: Type of request
            payload: Request payload

        Returns:
            Response data
        """
        strategy = self.retry_strategies[service]
        breaker = self.circuit_breakers[service]
        metrics = self.metrics[service]

        for attempt in range(strategy.max_retries + 1):
            try:
                start_time = time.time()

                # Execute request
                if service == ServiceType.OPENROUTER:
                    response = await self._call_openrouter(request_type, payload)
                else:
                    response = await self._call_orchestrator(request_type, payload)

                # Update metrics
                latency = time.time() - start_time
                metrics.total_requests += 1
                metrics.average_latency = (
                    metrics.average_latency * (metrics.total_requests - 1) + latency
                ) / metrics.total_requests
                metrics.success_rate = (
                    metrics.total_requests - metrics.failed_requests
                ) / metrics.total_requests

                # Record success
                breaker.record_success()
                metrics.consecutive_failures = 0

                return response

            except Exception as e:
                logger.warning(
                    f"Request failed on attempt {attempt + 1}: {e}"
                )

                # Update metrics
                metrics.total_requests += 1
                metrics.failed_requests += 1
                metrics.last_failure = datetime.utcnow()
                metrics.consecutive_failures += 1
                metrics.success_rate = (
                    metrics.total_requests - metrics.failed_requests
                ) / metrics.total_requests

                # Record failure
                breaker.record_failure()

                # Retry if attempts remain
                if attempt < strategy.max_retries:
                    delay = strategy.get_delay(attempt)
                    logger.info(f"Retrying after {delay}s delay")
                    await asyncio.sleep(delay)
                else:
                    raise

    @handle_errors
    async def _call_openrouter(
        self, request_type: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call OpenRouter API.

        Args:
            request_type: Type of request
            payload: Request payload

        Returns:
            Response data
        """
        # Map request types to proper endpoints
        endpoint_map = {
            "completion": "chat/completions",
            "chat": "chat/completions",
            "embedding": "embeddings",
        }
        
        endpoint_path = endpoint_map.get(request_type, request_type)
        endpoint = f"{self.openrouter_base_url}/{endpoint_path}"

        # Mask API key in logs
        masked_key = f"{self.openrouter_api_key[:8]}...{self.openrouter_api_key[-4:]}" if len(self.openrouter_api_key) > 12 else "***"
        logger.debug(f"Calling OpenRouter endpoint: {endpoint} with key: {masked_key}")

        response = await self.openrouter_client.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/orchestra-ai",
                "X-Title": "Orchestra AI Integration",
            },
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    @handle_errors
    async def _call_orchestrator(
        self, request_type: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call orchestrator service.

        Args:
            request_type: Type of request
            payload: Request payload

        Returns:
            Response data
        """
        endpoint = f"{self.orchestrator_url}/api/{request_type}"

        response = await self.orchestrator_client.post(
            endpoint,
            headers={"Content-Type": "application/json"},
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    def get_service_health(self) -> Dict[str, Any]:
        """Get health status of all services.

        Returns:
            Health status dictionary
        """
        health = {}

        for service in ServiceType:
            if service == ServiceType.FALLBACK:
                continue

            breaker = self.circuit_breakers.get(service)
            metrics = self.metrics.get(service)

            if breaker and metrics:
                health[service.value] = {
                    "circuit_state": breaker.state.value,
                    "success_rate": metrics.success_rate,
                    "average_latency": metrics.average_latency,
                    "total_requests": metrics.total_requests,
                    "failed_requests": metrics.failed_requests,
                    "consecutive_failures": metrics.consecutive_failures,
                    "last_failure": (
                        metrics.last_failure.isoformat()
                        if metrics.last_failure
                        else None
                    ),
                }

        return health

    async def close(self) -> None:
        """Close router and clean up resources."""
        await self.openrouter_client.aclose()
        await self.orchestrator_client.aclose()