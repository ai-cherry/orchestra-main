#!/usr/bin/env python3
"""
AI Metrics Collector Implementation
Collects, aggregates, and analyzes AI performance metrics with buffering
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics
import json
import logging
from dataclasses import dataclass, field
from enum import Enum

from ..interfaces import IMetricsCollector, IDatabase, ICache
from ..models.entities import AIMetric
from ..models.enums import MetricType, AIAgentType
from ..models.value_objects import MetricValue
from ..exceptions import MetricsError


logger = logging.getLogger(__name__)


class AggregationWindow(Enum):
    """Time windows for metric aggregation"""
    MINUTE = 60
    FIVE_MINUTES = 300
    HOUR = 3600
    DAY = 86400


@dataclass
class MetricBuffer:
    """Buffer for storing metrics before batch processing"""
    metrics: deque = field(default_factory=lambda: deque(maxlen=10000))
    last_flush: float = field(default_factory=time.time)
    
    def add(self, metric: AIMetric) -> None:
        """Add metric to buffer"""
        self.metrics.append(metric)
    
    def should_flush(self, max_size: int = 1000, max_age: float = 5.0) -> bool:
        """Check if buffer should be flushed"""
        return (
            len(self.metrics) >= max_size or
            time.time() - self.last_flush >= max_age
        )
    
    def flush(self) -> List[AIMetric]:
        """Flush and return all metrics"""
        metrics = list(self.metrics)
        self.metrics.clear()
        self.last_flush = time.time()
        return metrics


@dataclass
class MetricStats:
    """Statistical summary of metrics"""
    count: int = 0
    sum: float = 0.0
    min: float = float('inf')
    max: float = float('-inf')
    values: List[float] = field(default_factory=list)
    
    def add_value(self, value: float) -> None:
        """Add value to statistics"""
        self.count += 1
        self.sum += value
        self.min = min(self.min, value)
        self.max = max(self.max, value)
        self.values.append(value)
    
    @property
    def mean(self) -> float:
        """Calculate mean value"""
        return self.sum / self.count if self.count > 0 else 0.0
    
    @property
    def median(self) -> float:
        """Calculate median value"""
        if not self.values:
            return 0.0
        return statistics.median(self.values)
    
    @property
    def p95(self) -> float:
        """Calculate 95th percentile"""
        if not self.values:
            return 0.0
        sorted_values = sorted(self.values)
        index = int(0.95 * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    @property
    def p99(self) -> float:
        """Calculate 99th percentile"""
        if not self.values:
            return 0.0
        sorted_values = sorted(self.values)
        index = int(0.99 * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            "count": self.count,
            "sum": self.sum,
            "min": self.min if self.min != float('inf') else 0.0,
            "max": self.max if self.max != float('-inf') else 0.0,
            "mean": self.mean,
            "median": self.median,
            "p95": self.p95,
            "p99": self.p99
        }


class AIMetricsCollector(IMetricsCollector):
    """
    Production-ready metrics collector with buffering and aggregation
    
    Features:
    - Asynchronous metric collection with buffering
    - Multi-window aggregation (1m, 5m, 1h, 1d)
    - Statistical analysis (mean, median, p95, p99)
    - Anomaly detection
    - Performance optimization with batch processing
    - Automatic cleanup of old metrics
    """
    
    def __init__(
        self,
        database: IDatabase,
        cache: ICache,
        buffer_size: int = 1000,
        flush_interval: float = 5.0,
        retention_days: int = 30
    ):
        self.database = database
        self.cache = cache
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.retention_days = retention_days
        
        # Metric buffers by type
        self.buffers: Dict[MetricType, MetricBuffer] = {
            metric_type: MetricBuffer()
            for metric_type in MetricType
        }
        
        # In-memory aggregations for fast queries
        self.aggregations: Dict[str, Dict[AggregationWindow, MetricStats]] = defaultdict(
            lambda: {window: MetricStats() for window in AggregationWindow}
        )
        
        # Background tasks
        self._flush_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._aggregation_task: Optional[asyncio.Task] = None
        
        # Performance metrics
        self.collection_count = 0
        self.flush_count = 0
        self.error_count = 0
    
    async def start(self) -> None:
        """Start background tasks"""
        self._flush_task = asyncio.create_task(self._flush_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._aggregation_task = asyncio.create_task(self._aggregation_loop())
        logger.info("Metrics collector started")
    
    async def stop(self) -> None:
        """Stop background tasks"""
        tasks = [
            task for task in [self._flush_task, self._cleanup_task, self._aggregation_task]
            if task
        ]
        
        for task in tasks:
            task.cancel()
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Final flush
        await self._flush_all_buffers()
        
        logger.info("Metrics collector stopped")
    
    async def collect(self, metric: AIMetric) -> None:
        """
        Collect a metric with buffering
        
        Args:
            metric: Metric to collect
        """
        try:
            # Add to buffer
            buffer = self.buffers[metric.type]
            buffer.add(metric)
            
            # Update in-memory aggregations
            self._update_aggregations(metric)
            
            # Increment counter
            self.collection_count += 1
            
            # Check if immediate flush needed
            if buffer.should_flush(self.buffer_size, self.flush_interval):
                await self._flush_buffer(metric.type)
                
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error collecting metric: {e}")
            raise MetricsError(f"Failed to collect metric: {e}")
    
    async def get_metrics(
        self,
        agent_id: Optional[str] = None,
        metric_type: Optional[MetricType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AIMetric]:
        """
        Retrieve metrics with filtering
        
        Args:
            agent_id: Filter by agent ID
            metric_type: Filter by metric type
            start_time: Start time filter
            end_time: End time filter
            limit: Maximum number of results
            
        Returns:
            List of metrics matching filters
        """
        try:
            # Build query
            query = "SELECT * FROM ai_metrics WHERE 1=1"
            params = []
            
            if agent_id:
                query += " AND agent_id = %s"
                params.append(agent_id)
            
            if metric_type:
                query += " AND type = %s"
                params.append(metric_type.value)
            
            if start_time:
                query += " AND timestamp >= %s"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= %s"
                params.append(end_time)
            
            query += " ORDER BY timestamp DESC LIMIT %s"
            params.append(limit)
            
            # Execute query
            rows = await self.database.fetch_many(query, params)
            
            # Convert to entities
            metrics = []
            for row in rows:
                metric = AIMetric(
                    id=row["id"],
                    agent_id=row["agent_id"],
                    type=MetricType(row["type"]),
                    value=MetricValue(
                        value=row["value"],
                        unit=row["unit"],
                        metadata=json.loads(row["metadata"]) if row["metadata"] else {}
                    ),
                    timestamp=row["timestamp"]
                )
                metrics.append(metric)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error retrieving metrics: {e}")
            raise MetricsError(f"Failed to retrieve metrics: {e}")
    
    async def get_aggregated_metrics(
        self,
        agent_id: str,
        metric_type: MetricType,
        window: AggregationWindow = AggregationWindow.HOUR
    ) -> Dict[str, float]:
        """
        Get aggregated metrics for an agent
        
        Args:
            agent_id: Agent ID
            metric_type: Type of metric
            window: Aggregation window
            
        Returns:
            Statistical summary of metrics
        """
        try:
            # Check cache first
            cache_key = f"metrics:aggregated:{agent_id}:{metric_type.value}:{window.value}"
            cached = await self.cache.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Get from in-memory aggregations
            key = f"{agent_id}:{metric_type.value}"
            if key in self.aggregations:
                stats = self.aggregations[key][window]
                result = stats.to_dict()
                
                # Cache result
                await self.cache.set(cache_key, json.dumps(result), ttl=60)
                
                return result
            
            # Fallback to database query
            cutoff_time = datetime.utcnow() - timedelta(seconds=window.value)
            
            query = """
                SELECT 
                    COUNT(*) as count,
                    SUM(value) as sum,
                    MIN(value) as min,
                    MAX(value) as max,
                    AVG(value) as mean,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY value) as median,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY value) as p95,
                    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY value) as p99
                FROM ai_metrics
                WHERE agent_id = %s 
                    AND type = %s 
                    AND timestamp >= %s
            """
            
            row = await self.database.fetch_one(
                query,
                [agent_id, metric_type.value, cutoff_time]
            )
            
            if row:
                result = {
                    "count": row["count"] or 0,
                    "sum": float(row["sum"] or 0),
                    "min": float(row["min"] or 0),
                    "max": float(row["max"] or 0),
                    "mean": float(row["mean"] or 0),
                    "median": float(row["median"] or 0),
                    "p95": float(row["p95"] or 0),
                    "p99": float(row["p99"] or 0)
                }
            else:
                result = MetricStats().to_dict()
            
            # Cache result
            await self.cache.set(cache_key, json.dumps(result), ttl=60)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting aggregated metrics: {e}")
            raise MetricsError(f"Failed to get aggregated metrics: {e}")
    
    async def detect_anomalies(
        self,
        agent_id: str,
        metric_type: MetricType,
        threshold_stddev: float = 3.0
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in metrics using statistical methods
        
        Args:
            agent_id: Agent ID
            metric_type: Type of metric
            threshold_stddev: Number of standard deviations for anomaly threshold
            
        Returns:
            List of detected anomalies
        """
        try:
            # Get recent metrics
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)
            
            metrics = await self.get_metrics(
                agent_id=agent_id,
                metric_type=metric_type,
                start_time=start_time,
                end_time=end_time,
                limit=1000
            )
            
            if len(metrics) < 10:
                return []  # Not enough data
            
            # Calculate statistics
            values = [m.value.value for m in metrics]
            mean = statistics.mean(values)
            stddev = statistics.stdev(values)
            
            # Detect anomalies
            anomalies = []
            threshold_upper = mean + (threshold_stddev * stddev)
            threshold_lower = mean - (threshold_stddev * stddev)
            
            for metric in metrics:
                if metric.value.value > threshold_upper or metric.value.value < threshold_lower:
                    anomalies.append({
                        "metric_id": metric.id,
                        "timestamp": metric.timestamp.isoformat(),
                        "value": metric.value.value,
                        "mean": mean,
                        "stddev": stddev,
                        "deviation": abs(metric.value.value - mean) / stddev,
                        "type": "high" if metric.value.value > mean else "low"
                    })
            
            # Sort by deviation
            anomalies.sort(key=lambda x: x["deviation"], reverse=True)
            
            return anomalies[:10]  # Return top 10 anomalies
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            raise MetricsError(f"Failed to detect anomalies: {e}")
    
    def _update_aggregations(self, metric: AIMetric) -> None:
        """Update in-memory aggregations"""
        key = f"{metric.agent_id}:{metric.type.value}"
        
        # Update all windows
        for window in AggregationWindow:
            self.aggregations[key][window].add_value(metric.value.value)
        
        # Cleanup old values periodically (keep last 1000 per window)
        for window_stats in self.aggregations[key].values():
            if len(window_stats.values) > 1000:
                window_stats.values = window_stats.values[-1000:]
    
    async def _flush_buffer(self, metric_type: MetricType) -> None:
        """Flush a specific metric buffer to database"""
        buffer = self.buffers[metric_type]
        metrics = buffer.flush()
        
        if not metrics:
            return
        
        try:
            # Batch insert
            values = []
            for metric in metrics:
                values.append((
                    metric.id,
                    metric.agent_id,
                    metric.type.value,
                    metric.value.value,
                    metric.value.unit,
                    json.dumps(metric.value.metadata) if metric.value.metadata else None,
                    metric.timestamp
                ))
            
            await self.database.execute_many(
                """
                INSERT INTO ai_metrics (id, agent_id, type, value, unit, metadata, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                values
            )
            
            self.flush_count += 1
            logger.debug(f"Flushed {len(metrics)} {metric_type.value} metrics")
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error flushing metrics: {e}")
            # Re-add metrics to buffer on failure
            for metric in metrics:
                buffer.add(metric)
    
    async def _flush_all_buffers(self) -> None:
        """Flush all metric buffers"""
        for metric_type in MetricType:
            await self._flush_buffer(metric_type)
    
    async def _flush_loop(self) -> None:
        """Background task to periodically flush buffers"""
        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_all_buffers()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in flush loop: {e}")
    
    async def _cleanup_loop(self) -> None:
        """Background task to cleanup old metrics"""
        while True:
            try:
                # Run cleanup daily
                await asyncio.sleep(86400)
                
                cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
                
                deleted = await self.database.execute(
                    "DELETE FROM ai_metrics WHERE timestamp < %s",
                    [cutoff_date]
                )
                
                logger.info(f"Cleaned up {deleted} old metrics")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def _aggregation_loop(self) -> None:
        """Background task to maintain aggregations"""
        while True:
            try:
                # Update aggregations every minute
                await asyncio.sleep(60)
                
                # Cleanup old aggregation data
                cutoff_times = {
                    window: datetime.utcnow() - timedelta(seconds=window.value * 2)
                    for window in AggregationWindow
                }
                
                # Remove old entries from in-memory aggregations
                keys_to_remove = []
                for key, windows in self.aggregations.items():
                    agent_id, metric_type = key.split(":")
                    
                    # Check if agent has recent metrics
                    recent_metrics = await self.get_metrics(
                        agent_id=agent_id,
                        metric_type=MetricType(metric_type),
                        start_time=cutoff_times[AggregationWindow.HOUR],
                        limit=1
                    )
                    
                    if not recent_metrics:
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    del self.aggregations[key]
                
                logger.debug(f"Cleaned up {len(keys_to_remove)} stale aggregations")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in aggregation loop: {e}")
    
    async def get_performance_report(
        self,
        agent_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive performance report
        
        Args:
            agent_id: Optional agent filter
            start_time: Report start time
            end_time: Report end time
            
        Returns:
            Performance report with statistics and trends
        """
        try:
            if not end_time:
                end_time = datetime.utcnow()
            if not start_time:
                start_time = end_time - timedelta(hours=24)
            
            report = {
                "period": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "summary": {},
                "by_metric_type": {},
                "by_agent": {},
                "anomalies": []
            }
            
            # Get all metric types
            for metric_type in MetricType:
                metrics = await self.get_metrics(
                    agent_id=agent_id,
                    metric_type=metric_type,
                    start_time=start_time,
                    end_time=end_time,
                    limit=10000
                )
                
                if not metrics:
                    continue
                
                # Calculate statistics
                values = [m.value.value for m in metrics]
                stats = {
                    "count": len(values),
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "min": min(values),
                    "max": max(values),
                    "stddev": statistics.stdev(values) if len(values) > 1 else 0
                }
                
                report["by_metric_type"][metric_type.value] = stats
                
                # Group by agent
                agent_metrics = defaultdict(list)
                for metric in metrics:
                    agent_metrics[metric.agent_id].append(metric.value.value)
                
                for aid, agent_values in agent_metrics.items():
                    if aid not in report["by_agent"]:
                        report["by_agent"][aid] = {}
                    
                    report["by_agent"][aid][metric_type.value] = {
                        "count": len(agent_values),
                        "mean": statistics.mean(agent_values),
                        "median": statistics.median(agent_values),
                        "min": min(agent_values),
                        "max": max(agent_values)
                    }
                
                # Detect anomalies
                if agent_id:
                    anomalies = await self.detect_anomalies(
                        agent_id=agent_id,
                        metric_type=metric_type
                    )
                    if anomalies:
                        report["anomalies"].extend(anomalies[:5])
            
            # Overall summary
            report["summary"] = {
                "total_metrics": sum(
                    stats["count"] 
                    for stats in report["by_metric_type"].values()
                ),
                "unique_agents": len(report["by_agent"]),
                "metric_types": len(report["by_metric_type"]),
                "anomaly_count": len(report["anomalies"])
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            raise MetricsError(f"Failed to generate performance report: {e}")