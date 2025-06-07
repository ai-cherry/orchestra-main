"""
"""
    """
    """
    def __init__(self, project_id: str, metric_prefix: str = "agent_resilience"):
        """
        """
        self.project_name = f"projects/{project_id}"

        # Cache metric descriptors to avoid excessive API calls
        self._metric_descriptors: Dict[str, Any] = {}
        self._metric_descriptors_lock = threading.RLock()

        # Initialize OpenTelemetry tracing
        self._setup_tracing()

        logger.info(f"GCP Monitoring client initialized for project {project_id}")

    def _setup_tracing(self):
        """Set up OpenTelemetry tracing with Cloud Trace exporter."""
            "agent-conductor",
            resource=Resource.create({"service.name": "vertex-agent"}),
        )

        # Export to Cloud Trace
        trace.get_tracer_provider().add_span_processor(
            BatchSpanProcessor(CloudTraceSpanExporter(project_id=self.project_id))
        )


    def report_metric(self, metric_name: str, value: Any, labels: Optional[Dict[str, str]] = None) -> bool:
        """
        """
        full_metric_name = f"custom.googleapis.com/{self.metric_prefix}/{metric_name}"

        try:


            pass
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

        except Exception:


            pass
            logger.error(f"Failed to report metric {metric_name}: {str(e)}")
            return False

    def _metric_descriptor_exists(self, metric_name: str) -> bool:
        """
        """
                descriptor_name = f"{self.project_name}/metricDescriptors/{metric_name}"
                descriptor = self.client.get_metric_descriptor(name=descriptor_name)
                self._metric_descriptors[metric_name] = descriptor
                return True
            except Exception:

                pass
                return False

    def _create_metric_descriptor(self, metric_name: str) -> None:
        """
        """
        descriptor.description = f"Agent resilience metric: {metric_name}"

        try:


            pass
            created = self.client.create_metric_descriptor(name=self.project_name, metric_descriptor=descriptor)

            with self._metric_descriptors_lock:
                self._metric_descriptors[metric_name] = created

            logger.info(f"Created metric descriptor: {metric_name}")
        except Exception:

            pass
            logger.error(f"Failed to create metric descriptor {metric_name}: {str(e)}")
            raise

    def create_incident_report(self, agent_id: str, incident_data: Dict[str, Any]) -> None:
        """
        """
            logger = logging_client.logger("agent_incidents")

            # Add timestamp
            incident_data["timestamp"] = datetime.now().isoformat()
            incident_data["agent_id"] = agent_id

            # Create structured log entry
            logger.log_struct(incident_data, severity="ERROR")

            logger.info(f"Created incident report for agent {agent_id}")
        except Exception:

            pass
            # Fall back to standard logging if Cloud Logging fails
            logger.error(f"Failed to create incident report: {str(e)}")
            logger.error(f"Incident details: {incident_data}")

# Global instance
_monitoring_client = None
_monitoring_client_lock = threading.RLock()

def get_monitoring_client() -> PrometheusClient:
    """
    """
                "LAMBDA_PROJECT_ID",
                getattr(settings, "LAMBDA_PROJECT_ID", "cherry-ai-project"),
            )

            _monitoring_client = PrometheusClient(project_id)

            logger.info(f"Created global GCP Monitoring client for project {project_id}")

        return _monitoring_client
