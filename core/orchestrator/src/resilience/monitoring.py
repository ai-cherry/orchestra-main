"""
Cloud Monitoring Integration for Agent Resilience.

This module provides integration with Google Cloud Monitoring for tracking
agent failure metrics and setting up alerting, and uses OpenTelemetry for tracing.
"""

import logging
import threading
import time
from datetime import datetime
from typing import Any, Dict, Optional

from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Optional: Google Cloud Monitoring and Logging integration
try:
    import monitoring_v3
except ImportError:
    monitoring_v3 = None
try:
    import cloud_logging
except ImportError:
    cloud_logging = None

# Configure logging
logger = logging.getLogger(__name__)


class GCPMonitoringClient:
    """
    Client for reporting metrics to Google Cloud Monitoring and tracing with Cloud Trace.

    This class provides methods for creating and writing custom metrics
    to Cloud Monitoring for tracking agent failures and circuit breaker state,
    and sets up tracing with OpenTelemetry.
    """

    def __init__(self, project_id: str, metric_prefix: str = "agent_resilience"):
        """
        Initialize monitoring client.

        Args:
            project_id: GCP project ID
            metric_prefix: Prefix for all custom metrics
        """
        self.project_id = project_id
        self.metric_prefix = metric_prefix
        self.client = monitoring_v3.MetricServiceClient()
        self.project_name = f"projects/{project_id}"

        # Cache metric descriptors to avoid excessive API calls
        self._metric_descriptors: Dict[str, Any] = {}
        self._metric_descriptors_lock = threading.RLock()

        # Initialize OpenTelemetry tracing
        self._setup_tracing()

        logger.info(f"GCP Monitoring client initialized for project {project_id}")

    def _setup_tracing(self):
        """Set up OpenTelemetry tracing with Cloud Trace exporter."""
        trace.get_tracer(
            "agent-orchestrator",
            resource=Resource.create({"service.name": "vertex-agent"}),
        )

        # Export to Cloud Trace
        trace.get_tracer_provider().add_span_processor(
            BatchSpanProcessor(CloudTraceSpanExporter(project_id=self.project_id))
        )

        logger.info("OpenTelemetry tracing initialized with Cloud Trace exporter")

    def report_metric(
        self, metric_name: str, value: Any, labels: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Report a metric to Cloud Monitoring.

        Args:
            metric_name: Name of the metric (will be prefixed)
            value: Value to report
            labels: Optional labels for the metric

        Returns:
            True if successful, False otherwise
        """
        full_metric_name = f"custom.googleapis.com/{self.metric_prefix}/{metric_name}"

        try:
            # Ensure metric descriptor exists
            if not self._metric_descriptor_exists(full_metric_name):
                self._create_metric_descriptor(full_metric_name)

            # Create time series
            series = monitoring_v3.TimeSeries()
            series.metric.type = full_metric_name

            # Add labels if provided
            if labels:
                for key, value in labels.items():
                    series.metric.labels[key] = str(value)

            # Create data point
            now = time.time()
            seconds = int(now)
            nanos = int((now - seconds) * 10**9)

            point = monitoring_v3.Point()
            point.interval.end_time.seconds = seconds
            point.interval.end_time.nanos = nanos

            # Determine value type
            if isinstance(value, bool):
                point.value.bool_value = value
            elif isinstance(value, int):
                point.value.int64_value = value
            elif isinstance(value, float):
                point.value.double_value = value
            else:
                point.value.string_value = str(value)

            series.points.append(point)

            # Write time series
            self.client.create_time_series(name=self.project_name, time_series=[series])

            return True

        except Exception as e:
            logger.error(f"Failed to report metric {metric_name}: {str(e)}")
            return False

    def _metric_descriptor_exists(self, metric_name: str) -> bool:
        """
        Check if a metric descriptor exists.

        Args:
            metric_name: Full metric name including prefix

        Returns:
            True if exists, False otherwise
        """
        with self._metric_descriptors_lock:
            if metric_name in self._metric_descriptors:
                return True

            try:
                descriptor_name = f"{self.project_name}/metricDescriptors/{metric_name}"
                descriptor = self.client.get_metric_descriptor(name=descriptor_name)
                self._metric_descriptors[metric_name] = descriptor
                return True
            except Exception:
                return False

    def _create_metric_descriptor(self, metric_name: str) -> None:
        """
        Create a metric descriptor in Cloud Monitoring.

        Args:
            metric_name: Full metric name including prefix

        Raises:
            Exception: If creation fails
        """
        descriptor = monitoring_v3.MetricDescriptor()
        descriptor.type = metric_name
        descriptor.metric_kind = monitoring_v3.MetricDescriptor.MetricKind.GAUGE
        descriptor.value_type = monitoring_v3.MetricDescriptor.ValueType.INT64
        descriptor.description = f"Agent resilience metric: {metric_name}"

        try:
            created = self.client.create_metric_descriptor(
                name=self.project_name, metric_descriptor=descriptor
            )

            with self._metric_descriptors_lock:
                self._metric_descriptors[metric_name] = created

            logger.info(f"Created metric descriptor: {metric_name}")
        except Exception as e:
            logger.error(f"Failed to create metric descriptor {metric_name}: {str(e)}")
            raise

    def create_incident_report(
        self, agent_id: str, incident_data: Dict[str, Any]
    ) -> None:
        """
        Create an incident report in Cloud Logging.

        Args:
            agent_id: ID of the agent that triggered the incident
            incident_data: Incident details
        """
        # Use structured logging for better integration with Cloud Logging

        try:
            logging_client = cloud_logging.Client(project=self.project_id)
            logger = logging_client.logger("agent_incidents")

            # Add timestamp
            incident_data["timestamp"] = datetime.now().isoformat()
            incident_data["agent_id"] = agent_id

            # Create structured log entry
            logger.log_struct(incident_data, severity="ERROR")

            logger.info(f"Created incident report for agent {agent_id}")
        except Exception as e:
            # Fall back to standard logging if Cloud Logging fails
            logger.error(f"Failed to create incident report: {str(e)}")
            logger.error(f"Incident details: {incident_data}")


# Global instance
_monitoring_client = None
_monitoring_client_lock = threading.RLock()


def get_monitoring_client() -> GCPMonitoringClient:
    """
    Get the global monitoring client instance.

    Returns:
        Global GCPMonitoringClient instance
    """
    global _monitoring_client

    with _monitoring_client_lock:
        if _monitoring_client is None:
            # Get GCP project ID from environment or config
            import os

            from core.orchestrator.src.config.config import get_settings

            settings = get_settings()
            project_id = os.environ.get(
                "GCP_PROJECT_ID",
                getattr(settings, "GCP_PROJECT_ID", "cherry-ai-project"),
            )

            _monitoring_client = GCPMonitoringClient(project_id)

            logger.info(
                f"Created global GCP Monitoring client for project {project_id}"
            )

        return _monitoring_client
