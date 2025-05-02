"""
Incident Reporting for Agent Failures.

This module provides functionality for logging and reporting incidents
when agent failures occur, enabling better visibility and debugging.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import uuid
from google.cloud import logging as cloud_logging

# Configure logging
logger = logging.getLogger(__name__)

class IncidentReporter:
    """
    Reporter for agent failure incidents.
    
    This class provides methods for logging and reporting incidents
    when agent failures occur, with integration to Cloud Logging.
    """
    
    def __init__(self, project_id: str, log_name: str = "agent_incidents"):
        """
        Initialize incident reporter.
        
        Args:
            project_id: GCP project ID
            log_name: Name of the Cloud Logging log
        """
        self.project_id = project_id
        self.log_name = log_name
        
        # Initialize Cloud Logging client
        try:
            self.logging_client = cloud_logging.Client(project=project_id)
            self.logger = self.logging_client.logger(log_name)
            self._gcp_logging_available = True
            logger.info(f"Initialized Cloud Logging client for project {project_id}")
        except Exception as e:
            logger.warning(f"Failed to initialize Cloud Logging client: {str(e)}")
            self._gcp_logging_available = False
    
    def report_incident(
        self, 
        agent_id: str, 
        incident_type: str,
        details: Dict[str, Any],
        severity: str = "ERROR"
    ) -> str:
        """
        Report an incident to Cloud Logging.
        
        Args:
            agent_id: ID of the agent that triggered the incident
            incident_type: Type of incident (e.g., 'agent_failure', 'circuit_trip')
            details: Additional details about the incident
            severity: Severity level (ERROR, WARNING, INFO, etc.)
            
        Returns:
            Incident ID
        """
        # Generate incident ID
        incident_id = str(uuid.uuid4())
        
        # Create incident data
        incident_data = {
            "incident_id": incident_id,
            "agent_id": agent_id,
            "incident_type": incident_type,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        
        # Try to log to Cloud Logging
        if self._gcp_logging_available:
            try:
                self.logger.log_struct(
                    incident_data,
                    severity=severity
                )
                logger.info(f"Reported incident {incident_id} to Cloud Logging")
            except Exception as e:
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
        retry_scheduled_at: Optional[str] = None
    ) -> str:
        """
        Report a circuit trip incident.
        
        Args:
            agent_id: ID of the agent
            failure_count: Number of consecutive failures
            last_error: Last error message
            retry_scheduled_at: ISO timestamp of scheduled retry
            
        Returns:
            Incident ID
        """
        details = {
            "failure_count": failure_count,
            "last_error": last_error,
            "recovery": {
                "retry_scheduled": bool(retry_scheduled_at),
                "retry_scheduled_at": retry_scheduled_at
            }
        }
        
        return self.report_incident(
            agent_id=agent_id,
            incident_type="circuit_trip",
            details=details,
            severity="ERROR"
        )
    
    def report_fallback_activation(
        self, 
        agent_id: str, 
        user_input: str,
        fallback_agent_id: str = "vertex-agent",
        original_error: Optional[str] = None
    ) -> str:
        """
        Report a fallback activation incident.
        
        Args:
            agent_id: ID of the original agent that failed
            user_input: Original user input (truncated if needed)
            fallback_agent_id: ID of the fallback agent
            original_error: Original error message if available
            
        Returns:
            Incident ID
        """
        # Truncate user input if too long
        if len(user_input) > 200:
            truncated_input = user_input[:200] + "..."
        else:
            truncated_input = user_input
        
        details = {
            "original_agent": agent_id,
            "fallback_agent": fallback_agent_id,
            "user_input": truncated_input,
            "original_error": original_error
        }
        
        return self.report_incident(
            agent_id=agent_id,
            incident_type="fallback_activation",
            details=details,
            severity="WARNING"
        )
    
    def report_recovery(
        self, 
        agent_id: str, 
        retry_attempt: int,
        recovery_time_seconds: int
    ) -> str:
        """
        Report an agent recovery incident.
        
        Args:
            agent_id: ID of the agent
            retry_attempt: Retry attempt number
            recovery_time_seconds: Time in seconds from first failure to recovery
            
        Returns:
            Incident ID
        """
        details = {
            "recovery": {
                "retry_attempt": retry_attempt,
                "recovery_time_seconds": recovery_time_seconds
            }
        }
        
        return self.report_incident(
            agent_id=agent_id,
            incident_type="agent_recovery",
            details=details,
            severity="INFO"
        )
    
    def _fallback_logging(self, incident_data: Dict[str, Any], severity: str) -> None:
        """
        Fallback to standard logging if Cloud Logging fails.
        
        Args:
            incident_data: Incident data
            severity: Severity level
        """
        # Map severity to logging level
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        level = level_map.get(severity, logging.ERROR)
        
        # Log to standard logger
        logger.log(
            level,
            f"INCIDENT: {json.dumps(incident_data)}"
        )


# Global instance
_incident_reporter = None

def get_incident_reporter() -> IncidentReporter:
    """
    Get the global incident reporter instance.
    
    Returns:
        Global IncidentReporter instance
    """
    global _incident_reporter
    
    if _incident_reporter is None:
        # Get GCP project ID from environment or config
        import os
        from core.orchestrator.src.config.config import get_settings
        
        settings = get_settings()
        
        project_id = os.environ.get(
            "GCP_PROJECT_ID", 
            getattr(settings, "GCP_PROJECT_ID", "agi-baby-cherry")
        )
        
        log_name = os.environ.get(
            "INCIDENT_LOG_NAME", 
            getattr(settings, "INCIDENT_LOG_NAME", "agent_incidents")
        )
        
        _incident_reporter = IncidentReporter(
            project_id=project_id,
            log_name=log_name
        )
        
        logger.info(f"Created global Incident Reporter for project {project_id}")
    
    return _incident_reporter
