#!/usr/bin/env python3
"""
Upload IDE Stress Test Metrics to Cloud Monitoring

This script takes the metrics from the IDE stress test and uploads them
to Google Cloud Monitoring as custom metrics. This allows for tracking
performance over time and setting up alerts based on performance degradation.

Usage:
    python3 upload_stress_test_metrics.py --input=path/to/ide_stress_metrics.json [--project-id=your-project-id]

Requirements:
    - google-cloud-monitoring
"""

import argparse
import datetime
import json
import os
import sys
import time
from typing import Dict, Any, List, Tuple

try:
    from google.cloud import monitoring_v3
    from google.api import label_pb2
    from google.api import metric_pb2
    from google.protobuf import timestamp_pb2
except ImportError:
    print("Installing required Google Cloud packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "google-cloud-monitoring"])
    from google.cloud import monitoring_v3
    from google.api import label_pb2
    from google.api import metric_pb2
    from google.protobuf import timestamp_pb2

# Constants
DEFAULT_PROJECT_ID = "agi-baby-cherry"
METRIC_DOMAIN = "custom.googleapis.com"
METRIC_TYPES = {
    "cpu_percent": "ide_stress/cpu_usage",
    "memory_percent": "ide_stress/memory_usage",
    "disk_io_read": "ide_stress/disk_read_bytes",
    "disk_io_write": "ide_stress/disk_write_bytes",
    "network_sent": "ide_stress/network_sent_bytes",
    "network_recv": "ide_stress/network_recv_bytes",
    "thread_count": "ide_stress/thread_count"
}
SUMMARY_METRICS = {
    "cpu_avg": "ide_stress/cpu_avg",
    "cpu_max": "ide_stress/cpu_max",
    "memory_avg": "ide_stress/memory_avg",
    "memory_max": "ide_stress/memory_max",
    "thread_max": "ide_stress/thread_max"
}

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Upload IDE Stress Test metrics to Cloud Monitoring")
    parser.add_argument("--input", required=True, help="Path to the ide_stress_metrics.json file")
    parser.add_argument("--summary-input", help="Path to the ide_stress_summary.json file (optional)")
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID, 
                        help=f"Google Cloud project ID (default: {DEFAULT_PROJECT_ID})")
    parser.add_argument("--test-id", help="Unique test ID to use as a label (default: timestamp)")
    parser.add_argument("--machine-type", help="Machine type that ran the test (e.g., n2d-standard-32)")
    parser.add_argument("--workstation-id", help="ID of the Cloud Workstation that ran the test")
    
    return parser.parse_args()

def load_metrics(metrics_file: str) -> Dict[str, Any]:
    """Load metrics from the JSON file."""
    try:
        with open(metrics_file, 'r') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading metrics file: {e}")
        sys.exit(1)

def create_metric_descriptor(client: monitoring_v3.MetricServiceClient, 
                            project_id: str, 
                            metric_type: str, 
                            display_name: str,
                            description: str,
                            unit: str = "") -> None:
    """Create a custom metric descriptor if it doesn't exist."""
    project_name = f"projects/{project_id}"
    
    descriptor = metric_pb2.MetricDescriptor()
    descriptor.type = f"{METRIC_DOMAIN}/{metric_type}"
    descriptor.display_name = display_name
    descriptor.description = description
    descriptor.metric_kind = metric_pb2.MetricDescriptor.MetricKind.GAUGE
    descriptor.value_type = metric_pb2.MetricDescriptor.ValueType.DOUBLE
    
    if unit:
        descriptor.unit = unit
    
    # Add labels
    label = label_pb2.LabelDescriptor()
    label.key = "test_id"
    label.value_type = label_pb2.LabelDescriptor.ValueType.STRING
    label.description = "Unique identifier for the test run"
    descriptor.labels.append(label)
    
    label = label_pb2.LabelDescriptor()
    label.key = "machine_type"
    label.value_type = label_pb2.LabelDescriptor.ValueType.STRING
    label.description = "Machine type that ran the test"
    descriptor.labels.append(label)
    
    label = label_pb2.LabelDescriptor()
    label.key = "workstation_id"
    label.value_type = label_pb2.LabelDescriptor.ValueType.STRING
    label.description = "ID of the Cloud Workstation"
    descriptor.labels.append(label)
    
    try:
        # Check if descriptor already exists
        existing_descriptor = client.get_metric_descriptor(
            name=f"{project_name}/metricDescriptors/{descriptor.type}")
        print(f"Metric descriptor {descriptor.type} already exists, skipping creation.")
        return
    except Exception:
        # Descriptor doesn't exist, create it
        client.create_metric_descriptor(
            name=project_name,
            metric_descriptor=descriptor
        )
        print(f"Created metric descriptor: {descriptor.type}")

def create_time_series(project_id: str, 
                      metric_type: str, 
                      metric_labels: Dict[str, str],
                      data_points: List[Tuple[datetime.datetime, float]]) -> monitoring_v3.TimeSeries:
    """Create a time series for the given metric and data points."""
    series = monitoring_v3.TimeSeries()
    series.metric.type = f"{METRIC_DOMAIN}/{metric_type}"
    
    for key, value in metric_labels.items():
        if value:  # Only add non-empty labels
            series.metric.labels[key] = value
    
    series.resource.type = "global"
    
    for dt, value in data_points:
        point = monitoring_v3.Point()
        point.value.double_value = value
        
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(dt)
        point.interval.end_time = timestamp
        
        series.points.append(point)
    
    return series

def write_time_series(client: monitoring_v3.MetricServiceClient,
                     project_id: str,
                     time_series_list: List[monitoring_v3.TimeSeries]) -> None:
    """Write time series data to Cloud Monitoring."""
    project_name = f"projects/{project_id}"
    
    # Cloud Monitoring allows a maximum of 200 time series per request
    chunk_size = 200
    for i in range(0, len(time_series_list), chunk_size):
        chunk = time_series_list[i:i + chunk_size]
        try:
            client.create_time_series(
                name=project_name,
                time_series=chunk
            )
            print(f"Uploaded time series chunk {i//chunk_size + 1}/{(len(time_series_list)-1)//chunk_size + 1}")
        except Exception as e:
            print(f"Error uploading time series: {e}")
            # Continue with the next chunk rather than failing entirely

def upload_timeseries_metrics(client: monitoring_v3.MetricServiceClient,
                             project_id: str,
                             metrics: Dict[str, Any],
                             labels: Dict[str, str]) -> None:
    """Upload timeseries metrics from the stress test."""
    if not metrics.get("timestamps"):
        print("No timestamp data found in metrics")
        return
    
    # Process each metric type
    time_series_list = []
    
    for metric_key, metric_type in METRIC_TYPES.items():
        if metric_key not in metrics:
            print(f"Metric {metric_key} not found in the data")
            continue
        
        # Create metric descriptor if needed
        create_metric_descriptor(
            client,
            project_id,
            metric_type,
            f"IDE Stress Test - {metric_key.replace('_', ' ').title()}",
            f"IDE stress test {metric_key} metric",
            "By" if "bytes" in metric_key else ("Count" if "count" in metric_key else "%")
        )
        
        # Process data points
        data_points = []
        for i, ts_str in enumerate(metrics["timestamps"]):
            if i >= len(metrics[metric_key]):
                break
                
            try:
                dt = datetime.datetime.fromisoformat(ts_str)
                value = float(metrics[metric_key][i])
                data_points.append((dt, value))
            except (ValueError, TypeError) as e:
                print(f"Error processing data point {i} for {metric_key}: {e}")
                continue
        
        if data_points:
            time_series = create_time_series(project_id, metric_type, labels, data_points)
            time_series_list.append(time_series)
    
    # Write time series data in chunks
    if time_series_list:
        write_time_series(client, project_id, time_series_list)
        print(f"Uploaded {len(time_series_list)} time series.")
    else:
        print("No time series data to upload.")

def upload_summary_metrics(client: monitoring_v3.MetricServiceClient,
                          project_id: str,
                          summary: Dict[str, Any],
                          labels: Dict[str, str]) -> None:
    """Upload summary metrics from the stress test."""
    if not summary.get("metrics_summary"):
        print("No summary metrics found in the data")
        return
    
    metrics_summary = summary["metrics_summary"]
    timestamp = datetime.datetime.fromisoformat(summary.get("timestamp", datetime.datetime.now().isoformat()))
    
    # Process each summary metric
    time_series_list = []
    
    for metric_key, metric_type in SUMMARY_METRICS.items():
        if metric_key not in metrics_summary:
            print(f"Summary metric {metric_key} not found in the data")
            continue
        
        # Create metric descriptor if needed
        create_metric_descriptor(
            client,
            project_id,
            metric_type,
            f"IDE Stress Test - {metric_key.replace('_', ' ').title()}",
            f"IDE stress test {metric_key} summary metric",
            "%" if "cpu" in metric_key or "memory" in metric_key else "Count"
        )
        
        try:
            value = float(metrics_summary[metric_key])
            data_points = [(timestamp, value)]
            
            time_series = create_time_series(project_id, metric_type, labels, data_points)
            time_series_list.append(time_series)
        except (ValueError, TypeError) as e:
            print(f"Error processing summary metric {metric_key}: {e}")
            continue
    
    # Add additional summary metrics
    if "files_created" in summary:
        metric_type = "ide_stress/files_created"
        create_metric_descriptor(
            client,
            project_id,
            metric_type,
            "IDE Stress Test - Files Created",
            "Number of files created during the IDE stress test",
            "Count"
        )
        
        try:
            value = float(summary["files_created"])
            data_points = [(timestamp, value)]
            
            time_series = create_time_series(project_id, metric_type, labels, data_points)
            time_series_list.append(time_series)
        except (ValueError, TypeError) as e:
            print(f"Error processing files_created metric: {e}")
    
    # Write time series data
    if time_series_list:
        write_time_series(client, project_id, time_series_list)
        print(f"Uploaded {len(time_series_list)} summary metrics.")
    else:
        print("No summary metrics to upload.")

def main():
    """Main entry point."""
    args = parse_args()
    
    # Generate a test ID if not provided
    test_id = args.test_id or datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Set up metric labels
    labels = {
        "test_id": test_id,
        "machine_type": args.machine_type or "unknown",
        "workstation_id": args.workstation_id or "unknown"
    }
    
    # Load metrics data
    metrics = load_metrics(args.input)
    
    # Initialize Cloud Monitoring client
    client = monitoring_v3.MetricServiceClient()
    
    # Upload time series metrics
    upload_timeseries_metrics(client, args.project_id, metrics, labels)
    
    # Upload summary metrics if available
    summary_file = args.summary_input or os.path.join(os.path.dirname(args.input), "ide_stress_summary.json")
    if os.path.exists(summary_file):
        summary = load_metrics(summary_file)
        upload_summary_metrics(client, args.project_id, summary, labels)
    else:
        print(f"Summary file {summary_file} not found, skipping summary metrics upload.")
    
    print(f"Metrics upload complete. Test ID: {test_id}")

if __name__ == "__main__":
    main()
