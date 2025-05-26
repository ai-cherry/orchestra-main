#!/usr/bin/env python3
"""
deploy_monitoring.py - Deploy monitoring configuration to Cloud Monitoring

This script deploys the monitoring configuration defined in monitoring.yaml
to Google Cloud Monitoring. It creates custom metrics, dashboards, and alerts
for the MCP server.
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List

import yaml

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

try:
    from google.api_core.exceptions import AlreadyExists
    from google.cloud.monitoring_dashboard import v1 as dashboard

    HAS_GCP = True
except ImportError:
    logger.warning(
        "Google Cloud libraries not installed. Install with 'pip install google-cloud-monitoring google-cloud-monitoring-dashboards'"
    )
    HAS_GCP = False


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Deploy monitoring configuration to Cloud Monitoring"
    )
    parser.add_argument(
        "--config",
        default="monitoring/monitoring.yaml",
        help="Path to monitoring configuration file",
    )
    parser.add_argument(
        "--project-id",
        default=os.environ.get("GCP_PROJECT_ID", "cherry-ai-project"),
        help="GCP project ID",
    )
    parser.add_argument(
        "--service-name",
        default=os.environ.get("SERVICE_NAME", "mcp-server"),
        help="Cloud Run service name",
    )
    parser.add_argument(
        "--environment",
        default=os.environ.get("ENVIRONMENT", "dev"),
        help="Deployment environment (dev, staging, prod)",
    )
    parser.add_argument(
        "--notification-channel",
        default=os.environ.get("NOTIFICATION_CHANNEL_ID", ""),
        help="Notification channel ID",
    )
    parser.add_argument(
        "--service-url",
        default=os.environ.get("SERVICE_URL", ""),
        help="Cloud Run service URL",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run (don't actually create resources)",
    )
    return parser.parse_args()


def load_config(config_path: str) -> Dict[str, Any]:
    """Load monitoring configuration from YAML file."""
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        sys.exit(1)


def replace_variables(text: str, variables: Dict[str, str]) -> str:
    """Replace variables in text with their values."""
    result = text
    for key, value in variables.items():
        result = result.replace(f"${{{key}}}", value)
    return result


def create_custom_metrics(
    project_id: str, metrics: List[Dict[str, Any]], dry_run: bool = False
) -> None:
    """Create custom metrics in Cloud Monitoring."""
    if not HAS_GCP or dry_run:
        for metric in metrics:
            logger.info(f"Would create metric: {metric['name']}")
        return

    client = monitoring_v3.MetricServiceClient()
    project_path = f"projects/{project_id}"

    for metric_def in metrics:
        descriptor = monitoring_v3.MetricDescriptor()
        descriptor.type = metric_def["name"]
        descriptor.description = metric_def["description"]
        descriptor.metric_kind = monitoring_v3.MetricDescriptor.MetricKind[
            metric_def["metricKind"]
        ]
        descriptor.value_type = monitoring_v3.MetricDescriptor.ValueType[
            metric_def["valueType"]
        ]
        descriptor.unit = metric_def["unit"]

        # Add labels
        for label in metric_def.get("labels", []):
            label_descriptor = monitoring_v3.LabelDescriptor()
            label_descriptor.key = label["key"]
            label_descriptor.description = label["description"]
            label_descriptor.value_type = monitoring_v3.LabelDescriptor.ValueType.STRING
            descriptor.labels.append(label_descriptor)

        try:
            client.create_metric_descriptor(
                name=project_path, metric_descriptor=descriptor
            )
            logger.info(f"Created metric: {metric_def['name']}")
        except AlreadyExists:
            logger.info(f"Metric already exists: {metric_def['name']}")
        except Exception as e:
            logger.error(f"Error creating metric {metric_def['name']}: {e}")


def create_alert_policies(
    project_id: str,
    policies: List[Dict[str, Any]],
    variables: Dict[str, str],
    dry_run: bool = False,
) -> None:
    """Create alert policies in Cloud Monitoring."""
    if not HAS_GCP or dry_run:
        for policy in policies:
            logger.info(f"Would create alert policy: {policy['displayName']}")
        return

    client = monitoring_v3.AlertPolicyServiceClient()
    project_path = f"projects/{project_id}"

    for policy_def in policies:
        # Replace variables in display name
        display_name = replace_variables(policy_def["displayName"], variables)

        # Create alert policy
        policy = monitoring_v3.AlertPolicy()
        policy.display_name = display_name
        policy.combiner = monitoring_v3.AlertPolicy.ConditionCombinerType[
            policy_def["combiner"]
        ]

        # Add conditions
        for condition_def in policy_def["conditions"]:
            condition = monitoring_v3.AlertPolicy.Condition()
            condition.display_name = replace_variables(
                condition_def["displayName"], variables
            )

            # Create condition
            condition_filter = replace_variables(
                condition_def["condition"]["filter"], variables
            )

            if "aggregations" in condition_def["condition"]:
                aggregations = []
                for agg in condition_def["condition"]["aggregations"]:
                    aggregation = monitoring_v3.Aggregation()
                    aggregation.alignment_period = agg["alignmentPeriod"]
                    aggregation.per_series_aligner = monitoring_v3.Aggregation.Aligner[
                        agg["perSeriesAligner"]
                    ]
                    if "crossSeriesReducer" in agg:
                        aggregation.cross_series_reducer = (
                            monitoring_v3.Aggregation.Reducer[agg["crossSeriesReducer"]]
                        )
                    if "groupByFields" in agg:
                        aggregation.group_by_fields.extend(agg["groupByFields"])
                    aggregations.append(aggregation)

                # Create metric threshold condition
                threshold = monitoring_v3.AlertPolicy.Condition.MetricThreshold()
                threshold.filter = condition_filter
                threshold.aggregations.extend(aggregations)
                threshold.comparison = (
                    monitoring_v3.AlertPolicy.Condition.ComparisonType[
                        condition_def["condition"]["comparison"]
                    ]
                )
                threshold.threshold_value = condition_def["condition"]["thresholdValue"]
                threshold.duration = condition_def["condition"]["duration"]

                # Add denominator if present
                if "denominatorFilter" in condition_def["condition"]:
                    threshold.denominator_filter = replace_variables(
                        condition_def["condition"]["denominatorFilter"], variables
                    )
                    if "denominatorAggregations" in condition_def["condition"]:
                        denominator_aggregations = []
                        for agg in condition_def["condition"][
                            "denominatorAggregations"
                        ]:
                            aggregation = monitoring_v3.Aggregation()
                            aggregation.alignment_period = agg["alignmentPeriod"]
                            aggregation.per_series_aligner = (
                                monitoring_v3.Aggregation.Aligner[
                                    agg["perSeriesAligner"]
                                ]
                            )
                            if "crossSeriesReducer" in agg:
                                aggregation.cross_series_reducer = (
                                    monitoring_v3.Aggregation.Reducer[
                                        agg["crossSeriesReducer"]
                                    ]
                                )
                            if "groupByFields" in agg:
                                aggregation.group_by_fields.extend(agg["groupByFields"])
                            denominator_aggregations.append(aggregation)
                        threshold.denominator_aggregations.extend(
                            denominator_aggregations
                        )

                condition.condition_threshold = threshold

            policy.conditions.append(condition)

        # Add notification channels if specified
        if "notificationChannels" in policy_def and variables.get(
            "NOTIFICATION_CHANNEL_ID"
        ):
            for channel in policy_def["notificationChannels"]:
                channel_name = replace_variables(channel["channel"], variables)
                policy.notification_channels.append(channel_name)

        # Add alert strategy if specified
        if "alertStrategy" in policy_def:
            strategy = monitoring_v3.AlertPolicy.AlertStrategy()
            if "autoClose" in policy_def["alertStrategy"]:
                strategy.auto_close = policy_def["alertStrategy"]["autoClose"]
            policy.alert_strategy = strategy

        try:
            client.create_alert_policy(name=project_path, alert_policy=policy)
            logger.info(f"Created alert policy: {display_name}")
        except AlreadyExists:
            logger.info(f"Alert policy already exists: {display_name}")
        except Exception as e:
            logger.error(f"Error creating alert policy {display_name}: {e}")


def create_dashboards(
    project_id: str,
    dashboards_config: List[Dict[str, Any]],
    variables: Dict[str, str],
    dry_run: bool = False,
) -> None:
    """Create dashboards in Cloud Monitoring."""
    if not HAS_GCP or dry_run:
        for dashboard_def in dashboards_config:
            logger.info(f"Would create dashboard: {dashboard_def['displayName']}")
        return

    client = dashboard.DashboardsServiceClient()
    project_path = f"projects/{project_id}"

    for dashboard_def in dashboards_config:
        # Replace variables in dashboard JSON
        dashboard_json = json.dumps(dashboard_def)
        dashboard_json = replace_variables(dashboard_json, variables)
        dashboard_dict = json.loads(dashboard_json)

        # Create dashboard
        dashboard_obj = dashboard.Dashboard()
        dashboard_obj.display_name = dashboard_dict["displayName"]

        # Add grid layout
        if "gridLayout" in dashboard_dict:
            grid = dashboard.GridLayout()
            grid.columns = dashboard_dict["gridLayout"]["columns"]

            # Add widgets
            for widget_def in dashboard_dict["gridLayout"]["widgets"]:
                widget = dashboard.Widget()
                widget.title = widget_def["title"]

                # Add chart
                if "xyChart" in widget_def:
                    xy_chart = dashboard.XyChart()

                    # Add datasets
                    for dataset_def in widget_def["xyChart"]["dataSets"]:
                        dataset = dashboard.XyChart.DataSet()

                        # Add time series query
                        if "timeSeriesQuery" in dataset_def:
                            query = dashboard.TimeSeriesQuery()

                            # Add time series filter
                            if "timeSeriesFilter" in dataset_def["timeSeriesQuery"]:
                                filter_def = dataset_def["timeSeriesQuery"][
                                    "timeSeriesFilter"
                                ]
                                ts_filter = dashboard.TimeSeriesFilter()
                                ts_filter.filter = filter_def["filter"]

                                # Add aggregations
                                if "aggregation" in filter_def:
                                    agg_def = filter_def["aggregation"]
                                    agg = dashboard.Aggregation()
                                    agg.alignment_period = agg_def["alignmentPeriod"]
                                    agg.per_series_aligner = agg_def["perSeriesAligner"]
                                    if "crossSeriesReducer" in agg_def:
                                        agg.cross_series_reducer = agg_def[
                                            "crossSeriesReducer"
                                        ]
                                    if "groupByFields" in agg_def:
                                        agg.group_by_fields.extend(
                                            agg_def["groupByFields"]
                                        )
                                    ts_filter.aggregation = agg

                                query.time_series_filter = ts_filter

                            dataset.time_series_query = query

                        xy_chart.data_sets.append(dataset)

                    widget.xy_chart = xy_chart

                grid.widgets.append(widget)

            dashboard_obj.grid_layout = grid

        try:
            client.create_dashboard(parent=project_path, dashboard=dashboard_obj)
            logger.info(f"Created dashboard: {dashboard_dict['displayName']}")
        except AlreadyExists:
            logger.info(f"Dashboard already exists: {dashboard_dict['displayName']}")
        except Exception as e:
            logger.error(
                f"Error creating dashboard {dashboard_dict['displayName']}: {e}"
            )


def create_uptime_checks(
    project_id: str,
    uptime_checks: List[Dict[str, Any]],
    variables: Dict[str, str],
    dry_run: bool = False,
) -> None:
    """Create uptime checks in Cloud Monitoring."""
    if not HAS_GCP or dry_run:
        for check in uptime_checks:
            logger.info(f"Would create uptime check: {check['displayName']}")
        return

    client = monitoring_v3.UptimeCheckServiceClient()
    project_path = f"projects/{project_id}"

    for check_def in uptime_checks:
        # Replace variables in display name
        display_name = replace_variables(check_def["displayName"], variables)

        # Create uptime check
        check = monitoring_v3.UptimeCheckConfig()
        check.display_name = display_name

        # Set HTTP check
        if "httpCheck" in check_def:
            http_check = monitoring_v3.UptimeCheckConfig.HttpCheck()
            http_check.path = check_def["httpCheck"]["path"]
            http_check.port = check_def["httpCheck"]["port"]
            http_check.use_ssl = check_def["httpCheck"]["useSsl"]
            http_check.validate_ssl = check_def["httpCheck"]["validateSsl"]
            check.http_check = http_check

        # Set monitored resource
        if "monitoredResource" in check_def:
            resource = monitoring_v3.MonitoredResource()
            resource.type = check_def["monitoredResource"]["type"]

            # Replace variables in labels
            for key, value in check_def["monitoredResource"]["labels"].items():
                resource.labels[key] = replace_variables(value, variables)

            check.monitored_resource = resource

        # Set period and timeout
        check.period = check_def["period"]
        check.timeout = check_def["timeout"]

        # Set content matchers
        if "contentMatchers" in check_def:
            for matcher_def in check_def["contentMatchers"]:
                matcher = monitoring_v3.UptimeCheckConfig.ContentMatcher()
                matcher.content = matcher_def["content"]
                matcher.matcher = (
                    monitoring_v3.UptimeCheckConfig.ContentMatcher.ContentMatcherOption[
                        matcher_def["matcher"]
                    ]
                )
                check.content_matchers.append(matcher)

        try:
            client.create_uptime_check_config(
                parent=project_path, uptime_check_config=check
            )
            logger.info(f"Created uptime check: {display_name}")
        except AlreadyExists:
            logger.info(f"Uptime check already exists: {display_name}")
        except Exception as e:
            logger.error(f"Error creating uptime check {display_name}: {e}")


def create_log_metrics(
    project_id: str,
    log_metrics: List[Dict[str, Any]],
    variables: Dict[str, str],
    dry_run: bool = False,
) -> None:
    """Create log-based metrics in Cloud Monitoring."""
    if not HAS_GCP or dry_run:
        for metric in log_metrics:
            logger.info(f"Would create log metric: {metric['name']}")
        return

    client = monitoring_v3.MetricServiceClient()
    project_path = f"projects/{project_id}"

    for metric_def in log_metrics:
        # Replace variables in filter
        replace_variables(metric_def["filter"], variables)

        # Create log metric
        descriptor = monitoring_v3.MetricDescriptor()
        descriptor.type = f"logging.googleapis.com/user/{metric_def['name']}"
        descriptor.description = metric_def["description"]
        descriptor.metric_kind = monitoring_v3.MetricDescriptor.MetricKind[
            metric_def["metricDescriptor"]["metricKind"]
        ]
        descriptor.value_type = monitoring_v3.MetricDescriptor.ValueType[
            metric_def["metricDescriptor"]["valueType"]
        ]
        descriptor.unit = metric_def["metricDescriptor"]["unit"]

        # Add labels
        for label in metric_def["metricDescriptor"].get("labels", []):
            label_descriptor = monitoring_v3.LabelDescriptor()
            label_descriptor.key = label["key"]
            label_descriptor.description = label["description"]
            label_descriptor.value_type = monitoring_v3.LabelDescriptor.ValueType[
                label["valueType"]
            ]
            descriptor.labels.append(label_descriptor)

        try:
            client.create_metric_descriptor(
                name=project_path, metric_descriptor=descriptor
            )
            logger.info(f"Created log metric: {metric_def['name']}")
        except AlreadyExists:
            logger.info(f"Log metric already exists: {metric_def['name']}")
        except Exception as e:
            logger.error(f"Error creating log metric {metric_def['name']}: {e}")


def main() -> None:
    """Main function."""
    args = parse_args()

    # Load configuration
    config = load_config(args.config)

    # Set up variables for replacement
    variables = {
        "PROJECT_ID": args.project_id,
        "SERVICE_NAME": args.service_name,
        "ENVIRONMENT": args.environment,
        "NOTIFICATION_CHANNEL_ID": args.notification_channel,
        "SERVICE_URL": args.service_url,
    }

    # Create custom metrics
    if "metrics" in config:
        logger.info("Creating custom metrics...")
        create_custom_metrics(args.project_id, config["metrics"], args.dry_run)

    # Create alert policies
    if "alertPolicies" in config:
        logger.info("Creating alert policies...")
        create_alert_policies(
            args.project_id, config["alertPolicies"], variables, args.dry_run
        )

    # Create dashboards
    if "dashboards" in config:
        logger.info("Creating dashboards...")
        create_dashboards(
            args.project_id, config["dashboards"], variables, args.dry_run
        )

    # Create uptime checks
    if "uptimeChecks" in config:
        logger.info("Creating uptime checks...")
        create_uptime_checks(
            args.project_id, config["uptimeChecks"], variables, args.dry_run
        )

    # Create log-based metrics
    if "logMetrics" in config:
        logger.info("Creating log-based metrics...")
        create_log_metrics(
            args.project_id, config["logMetrics"], variables, args.dry_run
        )

    logger.info("Monitoring configuration deployment complete!")


if __name__ == "__main__":
    main()
