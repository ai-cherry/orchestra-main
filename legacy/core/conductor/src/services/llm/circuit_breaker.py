"""
        result = await breaker.call_provider("openai", some_async_function, arg1, arg2)
    except Exception:

        pass
        # Handle provider being unavailable
        result = await fallback_provider()
"""
T = TypeVar("T")
SyncOrAsyncCallable = Callable[..., Union[T, Awaitable[T]]]
SyncOrAsyncResult = Union[T, Awaitable[T]]

class CircuitState(Enum):
    """Possible states for a circuit breaker."""
    CLOSED = "closed"  # Normal operation, requests go through
    OPEN = "open"  # Circuit is open, requests are blocked
    HALF_OPEN = "half_open"  # Testing if service is healthy again

class ProviderCircuitOpenError(Exception):
    """Exception raised when a provider circuit is open."""
        message = f"Circuit for provider '{provider}' is open due to too many failures"
        super().__init__(message)

class CircuitBreaker:
    """
    """
        """
        """
                "llm_provider_failures_total",
                "Number of failures per provider",
                ["provider"],
            )
            self.circuit_state_gauge = prom.Gauge(
                "llm_provider_circuit_state",
                "Circuit state per provider (0=closed, 1=half-open, 2=open)",
                ["provider"],
            )
            self.request_latency = prom.Histogram(
                "llm_provider_request_seconds",
                "Request latency in seconds per provider",
                ["provider"],
            )
        else:
            logger.warning("Prometheus client not available - metrics disabled")
            logger.warning("Install with: pip install prometheus-client")

    def _get_circuit_state(self, provider: str) -> CircuitState:
        """Get the current circuit state for a provider."""
                logger.info(f"Circuit for {provider} transitioning from OPEN to HALF_OPEN")
                self.circuit_state[provider] = CircuitState.HALF_OPEN
                self.half_open_calls[provider] = 0

                # Update prometheus metric if available
                if PROMETHEUS_AVAILABLE:
                    self.circuit_state_gauge.labels(provider=provider).set(1)  # 1 = half-open

            return self.circuit_state[provider]

    def record_success(self, provider: str) -> None:
        """Record a successful call to a provider."""
                logger.info(f"Circuit for {provider} transitioning from HALF_OPEN to CLOSED after success")
                self.circuit_state[provider] = CircuitState.CLOSED

                # Update prometheus metric if available
                if PROMETHEUS_AVAILABLE:
                    self.circuit_state_gauge.labels(provider=provider).set(0)  # 0 = closed

    def record_failure(self, provider: str) -> None:
        """Record a failed call to a provider."""
            logger.warning(f"Recorded failure for {provider} (count: {self.failures[provider]})")

            # Check if we need to open the circuit
            if self.failures[provider] >= self.max_failures:
                current_state = self._get_circuit_state(provider)

                if current_state == CircuitState.CLOSED:
                    logger.warning(f"Circuit for {provider} transitioning from CLOSED to OPEN")
                    self.circuit_state[provider] = CircuitState.OPEN

                    # Update prometheus metric if available
                    if PROMETHEUS_AVAILABLE:
                        self.circuit_state_gauge.labels(provider=provider).set(2)  # 2 = open

                elif current_state == CircuitState.HALF_OPEN:
                    logger.warning(f"Circuit for {provider} transitioning from HALF_OPEN back to OPEN after failure")
                    self.circuit_state[provider] = CircuitState.OPEN

                    # Update prometheus metric if available
                    if PROMETHEUS_AVAILABLE:
                        self.circuit_state_gauge.labels(provider=provider).set(2)  # 2 = open

    def _can_make_request(self, provider: str) -> bool:
        """Check if a request can be made to the provider."""
        """
            provider: Name of the provider (e.g., "openai", "anthropic")
            func: Async function to call
            *args, **kwargs: Arguments to pass to the function

        Returns:
            The result of the function call

        Raises:
            ProviderCircuitOpenError: If the circuit is open for this provider
            Exception: Any exception raised by the function
        """
                    logger.warning(f"Provider {provider} call failed: {str(e)}")

                    # Record metrics
                    if PROMETHEUS_AVAILABLE:
                        self.request_latency.labels(provider=provider).observe(elapsed)

                    # Record failure
                    self.record_failure(provider)
                    raise

            try:


                pass
                return await _wrapped_call()
            except Exception:

                pass
                # All retries failed
                self.record_failure(provider)
                raise
        else:
            # Without tenacity, just make a single call
            start_time = time.time()
            try:

                pass
                result = await func(*args, **kwargs)
                elapsed = time.time() - start_time

                # Record metrics
                if PROMETHEUS_AVAILABLE:
                    self.request_latency.labels(provider=provider).observe(elapsed)

                # Record success
                self.record_success(provider)
                return result
            except Exception:

                pass
                elapsed = time.time() - start_time
                logger.warning(f"Provider {provider} call failed: {str(e)}")

                # Record metrics
                if PROMETHEUS_AVAILABLE:
                    self.request_latency.labels(provider=provider).observe(elapsed)

                # Record failure
                self.record_failure(provider)
                raise

    def call_provider_sync(self, provider: str, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        """
                    logger.warning(f"Provider {provider} call failed: {str(e)}")

                    # Record metrics
                    if PROMETHEUS_AVAILABLE:
                        self.request_latency.labels(provider=provider).observe(elapsed)

                    # Record failure
                    self.record_failure(provider)
                    raise

            try:


                pass
                return _wrapped_call()
            except Exception:

                pass
                # All retries failed
                self.record_failure(provider)
                raise
        else:
            # Without tenacity, just make a single call
            start_time = time.time()
            try:

                pass
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time

                # Record metrics
                if PROMETHEUS_AVAILABLE:
                    self.request_latency.labels(provider=provider).observe(elapsed)

                # Record success
                self.record_success(provider)
                return result
            except Exception:

                pass
                elapsed = time.time() - start_time
                logger.warning(f"Provider {provider} call failed: {str(e)}")

                # Record metrics
                if PROMETHEUS_AVAILABLE:
                    self.request_latency.labels(provider=provider).observe(elapsed)

                # Record failure
                self.record_failure(provider)
                raise

    async def call_provider(self, provider: str, func: SyncOrAsyncCallable[T], *args: Any, **kwargs: Any) -> T:
        """
        """
        """
        """
    """
    """