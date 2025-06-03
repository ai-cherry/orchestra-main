"""Performance monitoring utilities for the orchestrator."""
    """Decorator to benchmark async function execution time."""
            logger.info(f"{func.__name__} completed in {elapsed:.3f}s")
            return result
        except Exception:

            pass
            elapsed = time.perf_counter() - start_time
            logger.error(f"{func.__name__} failed after {elapsed:.3f}s: {str(e)}")
            raise
    return wrapper


class PerformanceMonitor:
    """Monitor performance metrics for operations."""
        """Record a performance metric."""
        """Get average value for a metric."""
        """Clear all metrics."""