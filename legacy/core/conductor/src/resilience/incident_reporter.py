"""
"""
    """
    """
    def __init__(self, project_id: str, log_name: str = "agent_incidents"):
        """
        """
            logger.info(f"Initialized Cloud Logging client for project {project_id}")
        except Exception:

            pass
            logger.warning(f"Failed to initialize Cloud Logging client: {str(e)}")
            self._gcp_logging_available = False

    def report_incident(
        self,
        agent_id: str,
        incident_type: str,
        details: Dict[str, Any],
        severity: str = "ERROR",
    ) -> str:
        """
        """
            "incident_id": incident_id,
            "agent_id": agent_id,
            "incident_type": incident_type,
            "timestamp": datetime.now().isoformat(),
            "details": details,
        }

        # Try to log to Cloud Logging
        if self._gcp_logging_available:
            try:

                pass
                self.logger.log_struct(incident_data, severity=severity)
                logger.info(f"Reported incident {incident_id} to Cloud Logging")
            except Exception:

                pass
                logger.error(f"Failed to report incident to Cloud Logging: {str(e)}")
                self._fallback_logging(incident_data, severity)
        else:
            # Fall back to standard logging
            self._fallback_logging(incident_data, severity)

        return incident_id

    def report_circuit_trip(
        self,
        agent_id: str,
        failure_count: int,
        last_error: str,
        retry_scheduled_at: Optional[str] = None,
    ) -> str:
        """
        """
            "failure_count": failure_count,
            "last_error": last_error,
            "recovery": {
                "retry_scheduled": bool(retry_scheduled_at),
                "retry_scheduled_at": retry_scheduled_at,
            },
        }

        return self.report_incident(
            agent_id=agent_id,
            incident_type="circuit_trip",
            details=details,
            severity="ERROR",
        )

    def report_fallback_activation(
        self,
        agent_id: str,
        user_input: str,
        fallback_agent_id: str = "vertex-agent",
        original_error: Optional[str] = None,
    ) -> str:
        """
        """
            truncated_input = user_input[:200] + "..."
        else:
            truncated_input = user_input

        details = {
            "original_agent": agent_id,
            "fallback_agent": fallback_agent_id,
            "user_input": truncated_input,
            "original_error": original_error,
        }

        return self.report_incident(
            agent_id=agent_id,
            incident_type="fallback_activation",
            details=details,
            severity="WARNING",
        )

    def report_recovery(self, agent_id: str, retry_attempt: int, recovery_time_seconds: int) -> str:
        """
        """
            "recovery": {
                "retry_attempt": retry_attempt,
                "recovery_time_seconds": recovery_time_seconds,
            }
        }

        return self.report_incident(
            agent_id=agent_id,
            incident_type="agent_recovery",
            details=details,
            severity="INFO",
        )

    def _fallback_logging(self, incident_data: Dict[str, Any], severity: str) -> None:
        """
        """
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        level = level_map.get(severity, logging.ERROR)

        # Log to standard logger
        logger.log(level, f"INCIDENT: {json.dumps(incident_data)}")

# Global instance
_incident_reporter = None

def get_incident_reporter() -> IncidentReporter:
    """
    """
        project_id = os.environ.get("LAMBDA_PROJECT_ID", getattr(settings, "LAMBDA_PROJECT_ID", "cherry-ai-project"))

        log_name = os.environ.get(
            "INCIDENT_LOG_NAME",
            getattr(settings, "INCIDENT_LOG_NAME", "agent_incidents"),
        )

        _incident_reporter = IncidentReporter(project_id=project_id, log_name=log_name)

        logger.info(f"Created global Incident Reporter for project {project_id}")

    return _incident_reporter
