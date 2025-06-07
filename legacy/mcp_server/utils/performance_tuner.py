import asyncio
#!/usr/bin/env python3
"""
"""
    """Performance optimization manager for MCP Server."""
        """
        """
            "memory_usage": 0,
            "cpu_usage": 0,
            "request_count": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_response_time": 0,
        }
        self._start_time = time.time()
        self._total_response_time = 0

        # Apply environment-based settings
        self._apply_environment_settings()

        # Start monitoring thread if optimizations are enabled
        if self.enable_optimizations:
            self._start_monitoring()

    def _apply_environment_settings(self) -> None:
        """Apply settings from environment variables."""
        if os.environ.get("OPTIMIZE_PERFORMANCE", "").lower() == "true":
            self.enable_optimizations = True

        if "MEMORY_LIMIT" in os.environ:
            try:

                pass
                # Parse memory limit (e.g., "512M" or "1G")
                memory_limit = os.environ["MEMORY_LIMIT"]
                if memory_limit.endswith("G"):
                    self.memory_limit_mb = int(float(memory_limit[:-1]) * 1024)
                elif memory_limit.endswith("M"):
                    self.memory_limit_mb = int(memory_limit[:-1])
                else:
                    self.memory_limit_mb = int(memory_limit)
            except Exception:

                pass
                logger.warning(f"Invalid MEMORY_LIMIT: {os.environ['MEMORY_LIMIT']}")

        if "CPU_LIMIT" in os.environ:
            try:

                pass
                self.cpu_limit = int(os.environ["CPU_LIMIT"])
            except Exception:

                pass
                logger.warning(f"Invalid CPU_LIMIT: {os.environ['CPU_LIMIT']}")

        if "CACHE_TTL" in os.environ:
            try:

                pass
                self.cache_ttl_seconds = int(os.environ["CACHE_TTL"])
            except Exception:

                pass
                logger.warning(f"Invalid CACHE_TTL: {os.environ['CACHE_TTL']}")

        if "MAX_CONCURRENT_REQUESTS" in os.environ:
            try:

                pass
                self.max_concurrent_requests = int(os.environ["MAX_CONCURRENT_REQUESTS"])
                self.request_semaphore = asyncio.Semaphore(self.max_concurrent_requests)
            except Exception:

                pass
                logger.warning(f"Invalid MAX_CONCURRENT_REQUESTS: {os.environ['MAX_CONCURRENT_REQUESTS']}")

    def _start_monitoring(self) -> None:
        """Start a background thread to monitor resource usage."""
                    self.metrics["memory_usage"] = process.memory_info().rss / (1024 * 1024)  # MB
                    self.metrics["cpu_usage"] = process.cpu_percent() / psutil.cpu_count()

                    # Check if memory usage exceeds limit
                    if self.metrics["memory_usage"] > self.memory_limit_mb * 0.9:
                        logger.warning(
                            f"Memory usage ({self.metrics['memory_usage']:.2f} MB) approaching limit ({self.memory_limit_mb} MB)"
                        )
                        self._reduce_memory_usage()

                    await asyncio.sleep(5)  # Check every 5 seconds
                except Exception:

                    pass
                    logger.error(f"Error in resource monitoring: {e}")
                    await asyncio.sleep(10)  # Wait longer on error

        threading.Thread(target=monitor_resources, daemon=True).start()

    def _reduce_memory_usage(self) -> None:
        """Attempt to reduce memory usage."""
        if hasattr(self, "_cache"):
            self._cache.clear()

        # Log memory usage after reduction attempts
        process = psutil.Process(os.getpid())
        memory_usage = process.memory_info().rss / (1024 * 1024)  # MB
        logger.info(f"Memory usage after reduction: {memory_usage:.2f} MB")

    async def limit_concurrency(self, func: Callable) -> Callable:
        """Decorator to limit concurrency of async functions."""
        """Decorator to cache function results with TTL."""
                        self.metrics["cache_hits"] += 1
                        return result

                # Call the function and cache the result
                self.metrics["cache_misses"] += 1
                result = func(*args, **kwargs)
                cache[key] = (time.time(), result)

                # Clean up expired cache entries
                for k in list(cache.keys()):
                    if time.time() - cache[k][0] > ttl:
                        del cache[k]

                return result

            return wrapper

        return decorator

    async def async_cache_result(self, ttl: Optional[int] = None) -> Callable:
        """Decorator to cache async function results with TTL."""
                        self.metrics["cache_hits"] += 1
                        return result

                # Call the function and cache the result
                self.metrics["cache_misses"] += 1
                result = await func(*args, **kwargs)
                cache[key] = (time.time(), result)

                # Clean up expired cache entries
                for k in list(cache.keys()):
                    if time.time() - cache[k][0] > ttl:
                        del cache[k]

                return result

            return wrapper

        return decorator

    def track_performance(self, func: Callable) -> Callable:
        """Decorator to track function performance."""
            self.metrics["request_count"] += 1
            self._total_response_time += elapsed_time
            self.metrics["average_response_time"] = self._total_response_time / self.metrics["request_count"]

            # Log slow operations
            if elapsed_time > 1.0:
                logger.warning(f"Slow operation: {func.__name__} took {elapsed_time:.2f} seconds")

            return result

        return wrapper

    async def async_track_performance(self, func: Callable) -> Callable:
        """Decorator to track async function performance."""
            self.metrics["request_count"] += 1
            self._total_response_time += elapsed_time
            self.metrics["average_response_time"] = self._total_response_time / self.metrics["request_count"]

            # Log slow operations
            if elapsed_time > 1.0:
                logger.warning(f"Slow operation: {func.__name__} took {elapsed_time:.2f} seconds")

            return result

        return wrapper

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        self.metrics["memory_usage"] = process.memory_info().rss / (1024 * 1024)  # MB
        self.metrics["cpu_usage"] = process.cpu_percent() / psutil.cpu_count()

        # Add uptime
        self.metrics["uptime_seconds"] = time.time() - self._start_time

        return self.metrics

    def optimize_batch_size(self, data_size: int, max_batch_size: int = 100) -> int:
        """
        """
        memory_usage_percent = self.metrics["memory_usage"] / self.memory_limit_mb
        if memory_usage_percent > 0.8:
            # Reduce batch size proportionally to memory pressure
            reduction_factor = 1 - (memory_usage_percent - 0.8) * 5  # Scale from 1.0 to 0.0
            batch_size = max(1, int(batch_size * reduction_factor))

        # Reduce batch size if CPU usage is high
        if self.metrics["cpu_usage"] > 80:
            # Reduce batch size proportionally to CPU pressure
            reduction_factor = 1 - (self.metrics["cpu_usage"] - 80) / 20  # Scale from 1.0 to 0.0
            batch_size = max(1, int(batch_size * reduction_factor))

        # Ensure batch size is not larger than data size
        batch_size = min(batch_size, data_size)

        return batch_size

# Singleton instance for global use
_default_instance: Optional[PerformanceTuner] = None

def get_performance_tuner() -> PerformanceTuner:
    """Get the default PerformanceTuner instance."""
    """Decorator to cache function results with TTL."""
    """Decorator to cache async function results with TTL."""
    """Decorator to track function performance."""
    """Decorator to track async function performance."""
    """Decorator to limit concurrency of async functions."""
    """Get current performance metrics."""