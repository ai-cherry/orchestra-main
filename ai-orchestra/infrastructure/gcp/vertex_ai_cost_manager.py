"""
Vertex AI cost management utilities for AI Orchestra.

This module provides tools for monitoring and controlling costs
associated with Vertex AI usage in the AI Orchestra project.
"""

import asyncio
import datetime
import logging
from typing import Dict, List, Optional, Union, Any, Tuple

from google.cloud import monitoring_v3
from google.cloud.monitoring_v3 import query
from google.cloud import secretmanager

from ai_orchestra.core.config import settings
from ai_orchestra.utils.logging import log_event, log_start, log_end, log_error

logger = logging.getLogger("ai_orchestra.infrastructure.gcp.vertex_ai_cost_manager")


class VertexAICostManager:
    """
    Cost management utilities for Vertex AI.

    This class provides tools for monitoring and controlling costs
    associated with Vertex AI usage, including budget tracking,
    cost optimization recommendations, and usage quotas.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        budget_limit: float = 100.0,
        alert_threshold: float = 0.8,
        quota_buffer: float = 0.1,
    ):
        """
        Initialize the Vertex AI cost manager.

        Args:
            project_id: GCP project ID (defaults to settings.gcp.project_id)
            budget_limit: Monthly budget limit in USD
            alert_threshold: Alert threshold as a fraction of budget (0.0-1.0)
            quota_buffer: Buffer to maintain below quota limits (0.0-1.0)
        """
        self.project_id = project_id or settings.gcp.project_id
        self.budget_limit = budget_limit
        self.alert_threshold = alert_threshold
        self.quota_buffer = quota_buffer

        # Initialize clients
        self.monitoring_client = monitoring_v3.QueryServiceClient()
        self.secret_manager_client = secretmanager.SecretManagerServiceClient()

        # Project name for monitoring
        self.project_name = f"projects/{self.project_id}"

        log_event(
            logger,
            "vertex_ai_cost_manager",
            "initialized",
            {
                "project_id": self.project_id,
                "budget_limit": self.budget_limit,
                "alert_threshold": self.alert_threshold,
            },
        )

    async def get_current_spend(self, days: int = 30) -> float:
        """
        Get the current Vertex AI spend for the specified time period.

        Args:
            days: Number of days to look back

        Returns:
            Total spend in USD

        Raises:
            Exception: If there was an error retrieving the spend data
        """
        start_time = log_start(logger, "get_current_spend", {"days": days})

        try:
            # Calculate time range
            now = datetime.datetime.utcnow()
            start_date = now - datetime.timedelta(days=days)

            # Format timestamps for query
            start_time_str = start_date.isoformat() + "Z"
            end_time_str = now.isoformat() + "Z"

            # Build query for Vertex AI costs
            query_str = f"""
            fetch billing.googleapis.com/billing_account/cost
            | filter resource.service == 'aiplatform.googleapis.com'
            | filter resource.project_id == '{self.project_id}'
            | group_by 1d
            | within {start_time_str}, {end_time_str}
            | sum
            """

            # Execute query asynchronously
            results = await self._run_async(
                lambda: self.monitoring_client.query_time_series(
                    name=self.project_name, query=query_str
                )
            )

            # Sum up the costs
            total_cost = 0.0
            for time_series in results:
                for point in time_series.points:
                    total_cost += point.value.double_value

            log_end(
                logger,
                "get_current_spend",
                start_time,
                {
                    "days": days,
                    "total_cost": total_cost,
                },
            )

            return total_cost

        except Exception as e:
            log_error(logger, "get_current_spend", e, {"days": days})
            raise

    async def is_within_budget(self) -> bool:
        """
        Check if the current spend is within the budget limit.

        Returns:
            True if within budget, False otherwise
        """
        try:
            current_spend = await self.get_current_spend()
            return current_spend < self.budget_limit
        except Exception as e:
            logger.error(f"Error checking budget: {e}")
            # Default to True to avoid blocking operations unnecessarily
            return True

    async def is_approaching_budget(self) -> bool:
        """
        Check if the current spend is approaching the budget limit.

        Returns:
            True if approaching budget limit, False otherwise
        """
        try:
            current_spend = await self.get_current_spend()
            return current_spend >= (self.budget_limit * self.alert_threshold)
        except Exception as e:
            logger.error(f"Error checking budget threshold: {e}")
            return False

    async def get_model_usage(self, model_id: str, days: int = 7) -> Dict[str, Any]:
        """
        Get usage statistics for a specific model.

        Args:
            model_id: The model identifier
            days: Number of days to look back

        Returns:
            Dictionary with usage statistics
        """
        start_time = log_start(
            logger,
            "get_model_usage",
            {
                "model_id": model_id,
                "days": days,
            },
        )

        try:
            # Calculate time range
            now = datetime.datetime.utcnow()
            start_date = now - datetime.timedelta(days=days)

            # Format timestamps for query
            start_time_str = start_date.isoformat() + "Z"
            end_time_str = now.isoformat() + "Z"

            # Build query for model usage
            query_str = f"""
            fetch aiplatform.googleapis.com/prediction/request_count
            | filter resource.model_id == '{model_id}'
            | filter resource.project_id == '{self.project_id}'
            | group_by 1d
            | within {start_time_str}, {end_time_str}
            | sum
            """

            # Execute query asynchronously
            results = await self._run_async(
                lambda: self.monitoring_client.query_time_series(
                    name=self.project_name, query=query_str
                )
            )

            # Process results
            usage_data = {
                "model_id": model_id,
                "total_requests": 0,
                "daily_requests": [],
                "average_daily_requests": 0,
            }

            daily_counts = []
            for time_series in results:
                for point in time_series.points:
                    count = int(point.value.int64_value)
                    usage_data["total_requests"] += count

                    # Get the day for this point
                    day = datetime.datetime.fromtimestamp(
                        point.interval.end_time.seconds
                    ).strftime("%Y-%m-%d")

                    daily_counts.append(count)
                    usage_data["daily_requests"].append(
                        {
                            "date": day,
                            "count": count,
                        }
                    )

            # Calculate average
            if daily_counts:
                usage_data["average_daily_requests"] = sum(daily_counts) / len(
                    daily_counts
                )

            log_end(
                logger,
                "get_model_usage",
                start_time,
                {
                    "model_id": model_id,
                    "total_requests": usage_data["total_requests"],
                },
            )

            return usage_data

        except Exception as e:
            log_error(logger, "get_model_usage", e, {"model_id": model_id})
            return {
                "model_id": model_id,
                "error": str(e),
                "total_requests": 0,
                "daily_requests": [],
                "average_daily_requests": 0,
            }

    async def get_cost_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get cost optimization recommendations for Vertex AI usage.

        Returns:
            List of recommendation dictionaries
        """
        start_time = log_start(logger, "get_cost_optimization_recommendations", {})

        try:
            recommendations = []

            # Get current spend
            current_spend = await self.get_current_spend(days=30)

            # Check if approaching budget
            if current_spend >= (self.budget_limit * self.alert_threshold):
                recommendations.append(
                    {
                        "type": "budget_alert",
                        "severity": "high",
                        "message": f"Current spend (${current_spend:.2f}) is approaching budget limit (${self.budget_limit:.2f})",
                        "actions": [
                            "Consider increasing budget or reducing usage",
                            "Review model usage patterns for optimization opportunities",
                            "Switch to more cost-effective models for non-critical tasks",
                        ],
                    }
                )

            # Get model usage for common models
            common_models = ["gemini-pro", "text-embedding", "text-bison"]
            model_usage = {}

            for model_id in common_models:
                usage = await self.get_model_usage(model_id)
                model_usage[model_id] = usage

            # Check for high-usage models
            for model_id, usage in model_usage.items():
                if usage["average_daily_requests"] > 1000:
                    recommendations.append(
                        {
                            "type": "high_usage",
                            "severity": "medium",
                            "message": f"High usage detected for model {model_id} (avg {usage['average_daily_requests']:.0f} requests/day)",
                            "actions": [
                                "Implement caching for frequent identical requests",
                                "Consider batching requests where possible",
                                "Review if all requests are necessary",
                            ],
                        }
                    )

            # Add general recommendations
            recommendations.append(
                {
                    "type": "general",
                    "severity": "low",
                    "message": "General cost optimization recommendations",
                    "actions": [
                        "Use model compression techniques for deployed models",
                        "Implement result caching for frequently requested content",
                        "Consider using smaller models for simpler tasks",
                        "Set up budget alerts and monitoring",
                    ],
                }
            )

            log_end(
                logger,
                "get_cost_optimization_recommendations",
                start_time,
                {
                    "recommendation_count": len(recommendations),
                },
            )

            return recommendations

        except Exception as e:
            log_error(logger, "get_cost_optimization_recommendations", e, {})
            return [
                {
                    "type": "error",
                    "severity": "high",
                    "message": f"Error generating recommendations: {str(e)}",
                    "actions": [
                        "Check monitoring API permissions",
                        "Verify project configuration",
                    ],
                }
            ]

    async def get_quota_usage(self) -> Dict[str, float]:
        """
        Get current quota usage for Vertex AI services.

        Returns:
            Dictionary mapping quota metrics to usage percentage
        """
        start_time = log_start(logger, "get_quota_usage", {})

        try:
            # Define quota metrics to check
            quota_metrics = [
                "aiplatform.googleapis.com/online_prediction_requests",
                "aiplatform.googleapis.com/prediction_cpu_hours",
                "aiplatform.googleapis.com/custom_model_training_cpu_hours",
            ]

            quota_usage = {}

            for metric in quota_metrics:
                # Build query for quota usage
                query_str = f"""
                fetch {metric}
                | filter resource.project_id == '{self.project_id}'
                | group_by []
                | every 1d
                | within 1d
                | sum
                """

                # Execute query asynchronously
                results = await self._run_async(
                    lambda: self.monitoring_client.query_time_series(
                        name=self.project_name, query=query_str
                    )
                )

                # Process results
                usage = 0.0
                limit = 1.0  # Default to 1.0 to avoid division by zero

                for time_series in results:
                    for point in time_series.points:
                        usage = point.value.double_value

                        # Try to get the quota limit
                        # This is a simplified approach; in practice, you would need to
                        # query the quota limits separately
                        limit_query = f"""
                        fetch {metric}_limit
                        | filter resource.project_id == '{self.project_id}'
                        | group_by []
                        | every 1d
                        | within 1d
                        | sum
                        """

                        try:
                            limit_results = await self._run_async(
                                lambda: self.monitoring_client.query_time_series(
                                    name=self.project_name, query=limit_query
                                )
                            )

                            for limit_series in limit_results:
                                for limit_point in limit_series.points:
                                    limit = limit_point.value.double_value
                        except Exception:
                            # If we can't get the limit, use a default value
                            pass

                # Calculate usage percentage
                if limit > 0:
                    usage_percent = (usage / limit) * 100.0
                else:
                    usage_percent = 0.0

                # Store in results
                quota_usage[metric] = usage_percent

            log_end(
                logger,
                "get_quota_usage",
                start_time,
                {
                    "quota_count": len(quota_usage),
                },
            )

            return quota_usage

        except Exception as e:
            log_error(logger, "get_quota_usage", e, {})
            return {}

    async def should_throttle_requests(self, model_id: str) -> bool:
        """
        Determine if requests to a specific model should be throttled.

        This is useful for implementing backpressure when approaching
        quota limits or budget constraints.

        Args:
            model_id: The model identifier

        Returns:
            True if requests should be throttled, False otherwise
        """
        # Check if we're approaching budget
        if await self.is_approaching_budget():
            return True

        # Check quota usage
        try:
            quota_usage = await self.get_quota_usage()

            # Check if any quota is approaching limit
            for metric, usage_percent in quota_usage.items():
                if usage_percent > (100.0 * (1.0 - self.quota_buffer)):
                    logger.warning(
                        f"Quota {metric} at {usage_percent:.1f}% - throttling requests"
                    )
                    return True

            return False

        except Exception as e:
            logger.error(f"Error checking quota usage: {e}")
            # Default to False to avoid blocking operations unnecessarily
            return False

    async def get_budget_from_secret_manager(
        self, secret_name: str = "vertex-ai-budget"
    ) -> Optional[float]:
        """
        Retrieve budget limit from Secret Manager.

        Args:
            secret_name: Name of the secret containing the budget

        Returns:
            Budget limit as float, or None if not found
        """
        try:
            # Build the resource name
            name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"

            # Access the secret
            response = await self._run_async(
                lambda: self.secret_manager_client.access_secret_version(name=name)
            )

            # Parse the budget value
            budget_str = response.payload.data.decode("UTF-8")
            budget = float(budget_str)

            logger.info(f"Retrieved budget from Secret Manager: ${budget:.2f}")
            return budget

        except Exception as e:
            logger.error(f"Error retrieving budget from Secret Manager: {e}")
            return None

    async def update_budget_in_secret_manager(
        self, budget: float, secret_name: str = "vertex-ai-budget"
    ) -> bool:
        """
        Update budget limit in Secret Manager.

        Args:
            budget: New budget limit
            secret_name: Name of the secret containing the budget

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if secret exists
            parent = f"projects/{self.project_id}"
            secret_path = f"{parent}/secrets/{secret_name}"

            try:
                await self._run_async(
                    lambda: self.secret_manager_client.get_secret(name=secret_path)
                )
            except Exception:
                # Secret doesn't exist, create it
                await self._run_async(
                    lambda: self.secret_manager_client.create_secret(
                        parent=parent,
                        secret_id=secret_name,
                        secret={"replication": {"automatic": {}}},
                    )
                )

            # Add new version with updated budget
            budget_str = str(budget)
            await self._run_async(
                lambda: self.secret_manager_client.add_secret_version(
                    parent=secret_path,
                    payload={"data": budget_str.encode("UTF-8")},
                )
            )

            logger.info(f"Updated budget in Secret Manager: ${budget:.2f}")
            return True

        except Exception as e:
            logger.error(f"Error updating budget in Secret Manager: {e}")
            return False

    async def _run_async(self, func: Any) -> Any:
        """
        Run a synchronous function asynchronously.

        Args:
            func: The function to run

        Returns:
            The result of the function
        """
        return await asyncio.get_event_loop().run_in_executor(None, func)
