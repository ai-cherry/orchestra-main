#!/usr/bin/env python3
"""
"""
logger = logging.getLogger("mcp-performance")

class PerformanceMonitor:
    """Performance monitoring and optimization utilities."""
        """
        """
        self.slow_threshold = self.config.get("slow_threshold_ms", 100)  # ms
        self.max_history = self.config.get("max_history", 1000)
        self.lock = threading.Lock()
        self.enabled = self.config.get("enabled", True)

    def record_operation(self, name: str, duration: float) -> None:
        """
        """
                logger.warning(f"Slow operation detected: {name} took {duration_ms:.2f}ms")

    def monitor(self, name: Optional[str] = None):
        """
        """
                    op_name = name or f"{func.__module__}.{func.__name__}"
                    self.record_operation(op_name, time.time() - start_time)

            return wrapper

        return decorator

    def get_metrics(self) -> Dict[str, Any]:
        """
        """
        metrics = {"uptime_seconds": time.time() - self.start_time, "operations": {}}

        with self.lock:
            for op_name, durations in self.operations.items():
                if not durations:
                    continue

                metrics["operations"][op_name] = {
                    "count": len(durations),
                    "avg_ms": sum(durations) / len(durations),
                    "min_ms": min(durations),
                    "max_ms": max(durations),
                    "latest_ms": durations[-1],
                }

        return metrics

    def get_slow_operations(self, threshold_ms: Optional[float] = None) -> Dict[str, Any]:
        """
        """
                    "total_count": len(durations),
                    "slow_count": slow_count,
                    "slow_percentage": slow_percentage,
                    "avg_ms": sum(durations) / len(durations),
                    "max_ms": max(durations),
                }

        # Sort by slow percentage (highest first)
        return {k: v for k, v in sorted(result.items(), key=lambda x: x[1]["slow_percentage"], reverse=True)}

    def reset(self) -> None:
        """Reset all performance metrics."""
        """
        """
                    "type": "performance",
                    "severity": ("high" if any(op["slow_percentage"] > 50 for op in slow_ops.values()) else "medium"),
                    "message": f"Found {len(slow_ops)} slow operations that exceed {self.slow_threshold}ms threshold",
                    "operations": list(slow_ops.keys()),
                }
            )

        # TODO: Add more recommendations based on patterns

        return recommendations

# Global performance monitor instance
_performance_monitor = None

def get_performance_monitor(
    config: Optional[Dict[str, Any]] = None,
) -> PerformanceMonitor:
    """
    """