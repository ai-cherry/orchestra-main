"""Reliability Adapter for Factory AI integration.

This adapter bridges the Reliability Droid with the deployment MCP server,
handling incident management and monitoring capabilities.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from .factory_mcp_adapter import FactoryMCPAdapter

logger = logging.getLogger(__name__)


class IncidentSeverity(Enum):
    """Incident severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RemediationStatus(Enum):
    """Remediation action status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ReliabilityAdapter(FactoryMCPAdapter):
    """Adapter for Reliability Droid to deployment MCP server communication.

    Specializes in:
    - Incident detection and management
    - System monitoring and alerting
    - Alert aggregation and correlation
    - Automated remediation triggers
    """

    def __init__(self, mcp_server: Any, droid_config: Dict[str, Any]) -> None:
        """Initialize the Reliability adapter.

        Args:
            mcp_server: The deployment MCP server instance
            droid_config: Configuration for the Reliability droid
        """
        super().__init__(mcp_server, droid_config, "reliability")
        self.supported_methods = [
            "detect_incident",
            "manage_incident",
            "aggregate_alerts",
            "trigger_remediation",
            "analyze_reliability",
            "generate_runbook",
        ]
        self.alert_threshold = droid_config.get("alert_threshold", 5)
        self.auto_remediation = droid_config.get("auto_remediation", True)
        self.incident_cache: Dict[str, Dict[str, Any]] = {}
        self.alert_buffer: List[Dict[str, Any]] = []
        self.remediation_history: List[Dict[str, Any]] = []

    async def translate_to_factory(
        self, mcp_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Translate MCP request to Factory AI Reliability format.

        Args:
            mcp_request: Request in MCP format

        Returns:
            Request in Factory AI Reliability format
        """
        method = mcp_request.get("method", "")
        params = mcp_request.get("params", {})

        # Map MCP methods to Factory AI Reliability capabilities
        factory_request = {
            "droid": "reliability",
            "action": self._map_method_to_action(method),
            "context": {
                "system_state": params.get("system_state", {}),
                "alerts": params.get("alerts", []),
                "metrics": params.get("metrics", {}),
                "topology": params.get("topology", {}),
                "historical_data": params.get("historical_data", {}),
            },
            "options": {
                "severity_threshold": params.get(
                    "severity_threshold", IncidentSeverity.MEDIUM.value
                ),
                "auto_remediate": params.get("auto_remediate", self.auto_remediation),
                "correlation_window": params.get("correlation_window", 300),
                "include_predictions": params.get("include_predictions", True),
                "runbook_format": params.get("runbook_format", "markdown"),
            },
        }

        # Handle specific reliability scenarios
        if method == "manage_incident":
            factory_request["context"]["incident_id"] = params.get("incident_id", "")
            factory_request["context"]["incident_details"] = params.get(
                "incident_details", {}
            )
            factory_request["context"]["affected_services"] = params.get(
                "affected_services", []
            )

        elif method == "aggregate_alerts":
            factory_request["context"]["time_window"] = params.get(
                "time_window", 3600
            )
            factory_request["context"]["grouping_rules"] = params.get(
                "grouping_rules", {}
            )
            factory_request["options"]["deduplication"] = params.get(
                "deduplication", True
            )

        elif method == "trigger_remediation":
            factory_request["context"]["remediation_type"] = params.get(
                "remediation_type", "auto"
            )
            factory_request["context"]["target_resources"] = params.get(
                "resources", []
            )
            factory_request["context"]["playbook"] = params.get("playbook", {})

        logger.debug(f"Translated to Factory request: {factory_request}")
        return factory_request

    async def translate_to_mcp(
        self, factory_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Translate Factory AI Reliability response to MCP format.

        Args:
            factory_response: Response from Factory AI Reliability

        Returns:
            Response in MCP format
        """
        if "error" in factory_response:
            return {
                "error": {
                    "code": -32603,
                    "message": factory_response["error"].get(
                        "message", "Unknown error"
                    ),
                    "data": factory_response["error"].get("details", {}),
                }
            }

        result = factory_response.get("result", {})
        mcp_response = {
            "result": {
                "incidents": self._format_incidents(result.get("incidents", [])),
                "alerts": result.get("alerts", []),
                "remediation_actions": self._format_remediation_actions(
                    result.get("remediation_actions", [])
                ),
                "reliability_score": result.get("reliability_score", 0),
                "recommendations": result.get("recommendations", []),
                "predictions": result.get("predictions", {}),
                "metadata": {
                    "analysis_time": result.get("analysis_time", 0),
                    "correlation_count": result.get("correlation_count", 0),
                    "reliability_version": result.get("version", "1.0.0"),
                },
            }
        }

        # Include runbook if generated
        if "runbook" in result:
            mcp_response["result"]["runbook"] = {
                "content": result["runbook"].get("content", ""),
                "format": result["runbook"].get("format", "markdown"),
                "steps": result["runbook"].get("steps", []),
                "estimated_time": result["runbook"].get("estimated_time", 0),
            }

        # Include aggregation results if present
        if "aggregated_alerts" in result:
            mcp_response["result"]["aggregation"] = {
                "groups": result["aggregated_alerts"],
                "total_alerts": result.get("total_alerts", 0),
                "reduced_count": result.get("reduced_count", 0),
                "correlation_insights": result.get("correlation_insights", []),
            }

        logger.debug(f"Translated to MCP response: {mcp_response}")
        return mcp_response

    async def _call_factory_droid(
        self, factory_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call the Factory AI Reliability droid.

        Args:
            factory_request: Request in Factory AI format

        Returns:
            Response from Factory AI Reliability droid
        """
        try:
            # Import Factory AI client dynamically
            from factory_ai import FactoryAI

            if not self._factory_client:
                self._factory_client = FactoryAI(
                    api_key=self.droid_config.get("api_key"),
                    base_url=self.droid_config.get(
                        "base_url", "https://api.factory.ai"
                    ),
                )

            # Call the Reliability droid
            response = await self._factory_client.droids.reliability.execute(
                action=factory_request["action"],
                context=factory_request["context"],
                options=factory_request["options"],
            )

            # Cache incidents for correlation
            if "incidents" in response:
                for incident in response["incidents"]:
                    self.incident_cache[incident["id"]] = incident

            return {"result": response}

        except ImportError:
            logger.warning("Factory AI SDK not available, using mock response")
            return self._get_mock_response(factory_request)

        except Exception as e:
            logger.error(f"Error calling Reliability droid: {e}", exc_info=True)
            raise

    def _map_method_to_action(self, method: str) -> str:
        """Map MCP method to Factory AI Reliability action.

        Args:
            method: MCP method name

        Returns:
            Factory AI action name
        """
        method_mapping = {
            "detect_incident": "detect",
            "manage_incident": "manage",
            "aggregate_alerts": "aggregate",
            "trigger_remediation": "remediate",
            "analyze_reliability": "analyze",
            "generate_runbook": "generate_runbook",
        }
        return method_mapping.get(method, "detect")

    def _format_incidents(
        self, incidents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Format incidents for MCP response.

        Args:
            incidents: List of incident data from Factory AI

        Returns:
            Formatted incidents for MCP
        """
        formatted_incidents = []
        for incident in incidents:
            formatted_incidents.append(
                {
                    "id": incident.get("id", ""),
                    "title": incident.get("title", ""),
                    "description": incident.get("description", ""),
                    "severity": incident.get("severity", IncidentSeverity.MEDIUM.value),
                    "status": incident.get("status", "open"),
                    "affected_services": incident.get("affected_services", []),
                    "start_time": incident.get("start_time", ""),
                    "detection_time": incident.get("detection_time", ""),
                    "mttr_estimate": incident.get("mttr_estimate", 0),
                    "root_cause": incident.get("root_cause", ""),
                    "impact": incident.get("impact", {}),
                }
            )
        return formatted_incidents

    def _format_remediation_actions(
        self, actions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Format remediation actions for MCP response.

        Args:
            actions: List of remediation action data

        Returns:
            Formatted remediation actions
        """
        formatted_actions = []
        for action in actions:
            formatted_action = {
                "id": action.get("id", ""),
                "type": action.get("type", "manual"),
                "description": action.get("description", ""),
                "target": action.get("target", ""),
                "status": action.get("status", RemediationStatus.PENDING.value),
                "priority": action.get("priority", 0),
                "automated": action.get("automated", False),
                "script": action.get("script", ""),
                "expected_outcome": action.get("expected_outcome", ""),
                "rollback_plan": action.get("rollback_plan", ""),
            }
            formatted_actions.append(formatted_action)
            
            # Track remediation history
            self.remediation_history.append(
                {
                    "action": formatted_action,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        
        return formatted_actions

    def _get_mock_response(
        self, factory_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate mock response for testing.

        Args:
            factory_request: The Factory AI request

        Returns:
            Mock response
        """
        action = factory_request["action"]
        
        if action == "detect":
            return {
                "result": {
                    "incidents": [
                        {
                            "id": "inc-001",
                            "title": "High API Latency Detected",
                            "description": "API response times exceeding SLA thresholds",
                            "severity": IncidentSeverity.HIGH.value,
                            "status": "open",
                            "affected_services": ["api-gateway", "user-service"],
                            "start_time": datetime.now().isoformat(),
                            "detection_time": datetime.now().isoformat(),
                            "mttr_estimate": 30,
                            "root_cause": "Database connection pool exhaustion",
                            "impact": {
                                "users_affected": 1500,
                                "revenue_impact": "$5000/hour",
                            },
                        }
                    ],
                    "reliability_score": 85.5,
                    "recommendations": [
                        "Scale database connection pool",
                        "Implement circuit breaker for user service",
                    ],
                    "predictions": {
                        "next_incident_probability": 0.35,
                        "mttr_trend": "improving",
                    },
                    "analysis_time": 0.8,
                    "version": "1.0.0",
                }
            }
        
        elif action == "aggregate":
            return {
                "result": {
                    "aggregated_alerts": [
                        {
                            "group_id": "grp-001",
                            "pattern": "Database connectivity issues",
                            "alerts": [
                                {
                                    "id": "alert-001",
                                    "message": "Connection timeout to primary DB",
                                    "timestamp": datetime.now().isoformat(),
                                },
                                {
                                    "id": "alert-002",
                                    "message": "Replica lag exceeding threshold",
                                    "timestamp": datetime.now().isoformat(),
                                },
                            ],
                            "severity": IncidentSeverity.HIGH.value,
                            "correlation_score": 0.92,
                        }
                    ],
                    "total_alerts": 15,
                    "reduced_count": 3,
                    "correlation_insights": [
                        "Database issues correlate with deployment events",
                        "Alert storm pattern detected during peak hours",
                    ],
                    "analysis_time": 1.2,
                }
            }
        
        elif action == "remediate":
            return {
                "result": {
                    "remediation_actions": [
                        {
                            "id": "rem-001",
                            "type": "automated",
                            "description": "Scale database connection pool",
                            "target": "postgresql-primary",
                            "status": RemediationStatus.IN_PROGRESS.value,
                            "priority": 1,
                            "automated": True,
                            "script": """#!/bin/bash
# Scale PostgreSQL connection pool
kubectl patch configmap postgres-config \
  -p '{"data":{"max_connections":"200"}}'
kubectl rollout restart deployment/postgres""",
                            "expected_outcome": "Increased connection capacity",
                            "rollback_plan": "Revert configmap and restart",
                        }
                    ],
                    "reliability_score": 92.0,
                    "analysis_time": 0.5,
                }
            }
        
        elif action == "generate_runbook":
            return {
                "result": {
                    "runbook": {
                        "content": """# High API Latency Runbook

## Overview
This runbook addresses high API latency incidents.

## Steps
1. Check database connection pool metrics
2. Verify API gateway health
3. Scale resources if needed
4. Monitor recovery

## Rollback
If issues persist, revert to previous configuration.""",
                        "format": "markdown",
                        "steps": [
                            {
                                "order": 1,
                                "action": "Check metrics",
                                "command": "kubectl top pods -n production",
                            },
                            {
                                "order": 2,
                                "action": "Scale resources",
                                "command": "kubectl scale deployment api-gateway --replicas=5",
                            },
                        ],
                        "estimated_time": 15,
                    },
                    "version": "1.0.0",
                }
            }
        
        return {
            "result": {
                "message": f"Mock response for action: {action}",
                "reliability_score": 90.0,
                "version": "1.0.0",
            }
        }

    async def process_alert_stream(
        self, alerts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process a stream of alerts for correlation and aggregation.

        Args:
            alerts: List of incoming alerts

        Returns:
            Processing results
        """
        # Add to buffer
        self.alert_buffer.extend(alerts)
        
        # Check if we should trigger aggregation
        if len(self.alert_buffer) >= self.alert_threshold:
            request = {
                "method": "aggregate_alerts",
                "params": {
                    "alerts": self.alert_buffer,
                    "time_window": 300,
                    "deduplication": True,
                },
            }
            
            result = await self.process_request(request)
            
            # Clear buffer after processing
            self.alert_buffer.clear()
            
            return result
        
        return {
            "result": {
                "buffered_alerts": len(self.alert_buffer),
                "threshold": self.alert_threshold,
            }
        }