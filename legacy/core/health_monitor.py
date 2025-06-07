"""
"""
    """Overall health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class ComponentHealth:
    """Health status for a single component"""
    """
    """
        """
        """
        """Start health monitoring"""
            logger.info("Health monitoring started")

    async def stop(self):
        """Stop health monitoring"""
            logger.info("Health monitoring stopped")

    def register_health_check(self, name: str, check_func: Callable):
        """
        """
        logger.info(f"Registered health check for {name}")

    async def check_provider_health(self, provider: str, test_url: str) -> Tuple[bool, Optional[str]]:
        """
        """
                async with conn_manager.request(provider, "GET", test_url) as response:
                    return True, None

        except Exception:


            pass
            return False, "Health check timed out"
        except Exception:

            pass
            return False, str(e)

    async def _monitor_loop(self):
        """Background monitoring loop"""
                logger.error(f"Health monitor error: {e}")

    async def _run_health_checks(self):
        """Run all registered health checks"""
        providers = {"portkey": "/models", "openrouter": "/models"}

        for provider, test_url in providers.items():
            task = asyncio.create_task(self._check_and_update_provider(provider, test_url))
            tasks.append(task)

        # Run custom health checks
        for name, check_func in self._health_checks.items():
            task = asyncio.create_task(self._check_and_update_component(name, check_func))
            tasks.append(task)

        # Wait for all checks
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_and_update_provider(self, provider: str, test_url: str):
        """Check and update provider health status"""
            self._components[f"provider_{provider}"] = ComponentHealth(
                name=f"provider_{provider}",
                status=status,
                last_check=time.time(),
                error_message=error_msg,
                metadata={"failure_count": self._provider_failures[provider]},
            )

    async def _check_and_update_component(self, name: str, check_func: Callable):
        """Check and update component health status"""
        """Get overall system health status"""
                if name.startswith("provider_"):
                    provider_name = name.replace("provider_", "")
                    providers.append(
                        ProviderStatus(
                            name=provider_name,
                            available=component.status == HealthStatus.HEALTHY,
                            last_check=datetime.fromtimestamp(component.last_check).isoformat(),
                            error_rate=component.metadata.get("failure_count", 0) / self.failure_threshold,
                        )
                    )

            # Get metrics from connection manager
            conn_manager = await get_connection_manager()
            conn_metrics = conn_manager.get_metrics()

            # Get cache metrics
            from core.cache_manager import get_cache_manager

            cache_manager = await get_cache_manager()
            cache_metrics = cache_manager.get_metrics()

            return RouterHealth(
                status=overall_status.value,
                providers=providers,
                cache_hit_rate=cache_metrics["hit_rate"],
                total_requests=conn_metrics["requests"],
                success_rate=conn_metrics["success_rate"],
                uptime_seconds=time.time() - self._start_time,
            )

    async def get_detailed_status(self) -> Dict[str, Any]:
        """Get detailed health information"""
                    "status": comp.status.value,
                    "last_check": datetime.fromtimestamp(comp.last_check).isoformat(),
                    "error": comp.error_message,
                    "metadata": comp.metadata,
                }
                for name, comp in self._components.items()
            }

        # Get connection manager status
        conn_manager = await get_connection_manager()
        circuit_breakers = conn_manager.get_circuit_breaker_status()

        return {
            "overall": health.dict(),
            "components": components,
            "circuit_breakers": circuit_breakers,
            "last_check": datetime.utcnow().isoformat(),
        }

# Global health monitor instance
_health_monitor: Optional[HealthMonitor] = None

async def get_health_monitor(
    check_interval: Optional[int] = None, check_timeout: Optional[int] = None
) -> HealthMonitor:
    """
    """