"""
"""
    """Circuit breaker state for a provider"""
    """
    """
        """
        """
            "requests": 0,
            "successes": 0,
            "failures": 0,
            "retries": 0,
            "circuit_breaks": 0,
            "total_latency_ms": 0,
        }

        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def get_client(
        self, provider: str, base_url: str, headers: Optional[Dict[str, str]] = None
    ) -> httpx.AsyncClient:
        """
            provider: Provider name (e.g., "portkey", "openrouter")
            base_url: Base URL for the provider
            headers: Default headers for requests

        Returns:
            Configured HTTP client
        """
                logger.info(f"Created HTTP client for {provider}")

            return self._clients[provider]

    @asynccontextmanager
    async def request(self, provider: str, method: str, url: str, **kwargs):
        """
        """
                self.metrics["circuit_breaks"] += 1
                raise Exception(f"Circuit breaker open for {provider}")
            else:
                # Try half-open state
                breaker.is_open = False
                breaker.half_open_requests = 0
                breaker.half_open_successes = 0

        start_time = time.time()
        self.metrics["requests"] += 1

        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
            before_sleep=before_sleep_log(logger, logging.WARNING),
        )
        async def _make_request():
            """Inner function with retry logic"""
            self.metrics["retries"] += 1

            client = self._clients.get(provider)
            if not client:
                raise ValueError(f"No client configured for {provider}")

            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response

        try:


            pass
            response = await _make_request()

            # Update metrics
            latency_ms = (time.time() - start_time) * 1000
            self.metrics["successes"] += 1
            self.metrics["total_latency_ms"] += latency_ms

            # Update circuit breaker on success
            if breaker:
                breaker.failure_count = 0
                if not breaker.is_open:
                    breaker.half_open_successes += 1
                    if breaker.half_open_successes >= breaker.half_open_max:
                        # Fully close circuit
                        breaker.half_open_requests = 0
                        breaker.half_open_successes = 0

            yield response

        except Exception:


            pass
            # Update metrics
            self.metrics["failures"] += 1

            # Update circuit breaker on failure
            if breaker:
                breaker.failure_count += 1
                breaker.last_failure = time.time()

                if breaker.failure_count >= breaker.failure_threshold:
                    breaker.is_open = True
                    breaker.half_open_retry_time = time.time() + breaker.recovery_timeout
                    logger.warning(f"Circuit breaker opened for {provider}")

            raise

    async def close(self):
        """Close all HTTP clients"""
                logger.info(f"Closed HTTP client for {provider}")

            self._clients.clear()
            self._circuit_breakers.clear()

    def get_metrics(self) -> Dict[str, Any]:
        """Get connection manager metrics"""
            self.metrics["total_latency_ms"] / self.metrics["successes"] if self.metrics["successes"] > 0 else 0
        )

        success_rate = self.metrics["successes"] / self.metrics["requests"] if self.metrics["requests"] > 0 else 0

        return {
            **self.metrics,
            "avg_latency_ms": avg_latency,
            "success_rate": success_rate,
            "active_clients": len(self._clients),
            "open_circuits": sum(1 for cb in self._circuit_breakers.values() if cb.is_open),
        }

    def get_circuit_breaker_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers"""
                "is_open": breaker.is_open,
                "failure_count": breaker.failure_count,
                "last_failure": (
                    datetime.fromtimestamp(breaker.last_failure).isoformat() if breaker.last_failure else None
                ),
                "recovery_time": (
                    datetime.fromtimestamp(breaker.half_open_retry_time).isoformat()
                    if breaker.half_open_retry_time
                    else None
                ),
            }

        return status

# Global connection manager instance
_connection_manager: Optional[ConnectionManager] = None

async def get_connection_manager(
    pool_size: Optional[int] = None,
    pool_overflow: Optional[int] = None,
    timeout: Optional[int] = None,
    max_retries: Optional[int] = None,
) -> ConnectionManager:
    """
    """