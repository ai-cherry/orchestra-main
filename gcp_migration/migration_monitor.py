#!/usr/bin/env python3
"""
AI Orchestra GCP Migration Monitor

This utility monitors and reports on the progress of GCP migration,
tracking resources, validating deployments, and maintaining migration status.

Author: Roo
"""

import argparse
import asyncio
import datetime
import json
import logging
import os
import sys
import time
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Third-party imports
try:
    from google.cloud import monitoring_v3, resourcemanager_v3, run_v2
    from google.cloud.monitoring_v3 import AlertPolicy, MetricServiceClient, NotificationChannel
    from google.cloud.run_v2 import Service, ListServicesRequest
    from rich.console import Console
    from rich.table import Table
except ImportError:
    print("Required packages not found. Installing...")
    import subprocess
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", 
        "google-cloud-monitoring", "google-cloud-resource-manager", 
        "google-cloud-run", "rich"
    ])
    from google.cloud import monitoring_v3, resourcemanager_v3, run_v2
    from google.cloud.monitoring_v3 import AlertPolicy, MetricServiceClient, NotificationChannel
    from google.cloud.run_v2 import Service, ListServicesRequest
    from rich.console import Console
    from rich.table import Table

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("migration_monitor.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("migration-monitor")

# Rich console for prettier output
console = Console()


class ResourceStatus(Enum):
    """Status of a GCP resource."""
    PENDING = "pending"
    PROVISIONING = "provisioning"
    READY = "ready"
    FAILED = "failed"
    UNKNOWN = "unknown"


class MigrationResource:
    """Represents a GCP resource involved in the migration."""
    
    def __init__(
        self,
        name: str,
        type: str,
        status: ResourceStatus = ResourceStatus.UNKNOWN,
        details: Optional[Dict[str, Any]] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize a migration resource.
        
        Args:
            name: Name of the resource
            type: Type of resource (e.g., cloud-run, cloud-sql)
            status: Current status of the resource
            details: Additional details about the resource
            dependencies: List of resource names this resource depends on
            metadata: Additional metadata for the resource
        """
        self.name = name
        self.type = type
        self.status = status
        self.details = details or {}
        self.dependencies = dependencies or []
        self.metadata = metadata or {}
        self.last_updated = datetime.datetime.now()
        self.history: List[Dict[str, Any]] = []
        
        # Record initial status
        self._record_status_change(status)
    
    def update_status(self, new_status: ResourceStatus, details: Optional[Dict[str, Any]] = None):
        """Update the status of the resource and record the change.
        
        Args:
            new_status: New status of the resource
            details: Additional details about the status change
        """
        if new_status != self.status:
            self.status = new_status
            self.last_updated = datetime.datetime.now()
            
            if details:
                self.details.update(details)
                
            self._record_status_change(new_status, details)
    
    def _record_status_change(
        self, 
        status: ResourceStatus, 
        details: Optional[Dict[str, Any]] = None
    ):
        """Record a status change in the history.
        
        Args:
            status: Status to record
            details: Additional details about the status change
        """
        self.history.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "status": status.value,
            "details": details or {}
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the resource to a dictionary.
        
        Returns:
            Dictionary representation of the resource
        """
        return {
            "name": self.name,
            "type": self.type,
            "status": self.status.value,
            "details": self.details,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
            "last_updated": self.last_updated.isoformat(),
            "history": self.history
        }


class MigrationMonitor:
    """Monitor and report on GCP migration progress."""
    
    def __init__(
        self,
        project_id: str,
        region: str = "us-central1",
        state_file: Optional[str] = None
    ):
        """Initialize the migration monitor.
        
        Args:
            project_id: GCP project ID
            region: GCP region
            state_file: Path to state file for persistence
        """
        self.project_id = project_id
        self.region = region
        self.state_file = state_file or f"migration_state_{project_id}.json"
        self.resources: Dict[str, MigrationResource] = {}
        self.notifications: List[Dict[str, Any]] = []
        
        # Load state if exists
        self._load_state()
    
    def _load_state(self):
        """Load state from file if it exists."""
        state_path = Path(self.state_file)
        if state_path.exists():
            try:
                with open(state_path, "r") as f:
                    state = json.load(f)
                
                # Load resources
                for resource_data in state.get("resources", []):
                    resource = MigrationResource(
                        name=resource_data["name"],
                        type=resource_data["type"],
                        status=ResourceStatus(resource_data["status"]),
                        details=resource_data.get("details", {}),
                        dependencies=resource_data.get("dependencies", []),
                        metadata=resource_data.get("metadata", {})
                    )
                    
                    # Restore history
                    resource.history = resource_data.get("history", [])
                    
                    # Parse last updated timestamp
                    last_updated_str = resource_data.get("last_updated")
                    if last_updated_str:
                        try:
                            resource.last_updated = datetime.datetime.fromisoformat(last_updated_str)
                        except ValueError:
                            resource.last_updated = datetime.datetime.now()
                    
                    self.resources[resource.name] = resource
                
                # Load notifications
                self.notifications = state.get("notifications", [])
                
                logger.info(f"Loaded state from {self.state_file}")
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
    
    def _save_state(self):
        """Save current state to file."""
        try:
            state = {
                "resources": [r.to_dict() for r in self.resources.values()],
                "notifications": self.notifications,
                "last_updated": datetime.datetime.now().isoformat(),
                "project_id": self.project_id,
                "region": self.region
            }
            
            with open(self.state_file, "w") as f:
                json.dump(state, f, indent=2)
                
            logger.info(f"State saved to {self.state_file}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def add_resource(
        self,
        name: str,
        type: str,
        status: ResourceStatus = ResourceStatus.PENDING,
        details: Optional[Dict[str, Any]] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MigrationResource:
        """Add a resource to monitor.
        
        Args:
            name: Name of the resource
            type: Type of resource (e.g., cloud-run, cloud-sql)
            status: Initial status of the resource
            details: Additional details about the resource
            dependencies: List of resource names this resource depends on
            metadata: Additional metadata for the resource
            
        Returns:
            The created resource
        """
        resource = MigrationResource(
            name=name,
            type=type,
            status=status,
            details=details,
            dependencies=dependencies,
            metadata=metadata
        )
        
        self.resources[name] = resource
        self._save_state()
        
        logger.info(f"Added resource: {name} ({type}) with status {status.value}")
        return resource
    
    def update_resource_status(
        self,
        name: str,
        status: ResourceStatus,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update the status of a resource.
        
        Args:
            name: Name of the resource
            status: New status of the resource
            details: Additional details about the status change
            
        Returns:
            True if the resource was found and updated, False otherwise
        """
        if name in self.resources:
            self.resources[name].update_status(status, details)
            self._save_state()
            
            logger.info(f"Updated resource {name} status to {status.value}")
            return True
        else:
            logger.warning(f"Resource not found: {name}")
            return False
    
    def add_notification(
        self,
        message: str,
        level: str = "INFO",
        resource_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Add a notification to the log.
        
        Args:
            message: Notification message
            level: Log level (INFO, WARNING, ERROR)
            resource_name: Associated resource name if any
            details: Additional details about the notification
        """
        notification = {
            "timestamp": datetime.datetime.now().isoformat(),
            "message": message,
            "level": level,
            "resource_name": resource_name,
            "details": details or {}
        }
        
        self.notifications.append(notification)
        self._save_state()
        
        # Log to the logger as well
        if level == "INFO":
            logger.info(message)
        elif level == "WARNING":
            logger.warning(message)
        elif level == "ERROR":
            logger.error(message)
    
    async def check_cloud_run_services(self) -> List[MigrationResource]:
        """Check the status of Cloud Run services.
        
        Returns:
            List of updated resources
        """
        try:
            client = run_v2.ServicesClient()
            parent = f"projects/{self.project_id}/locations/{self.region}"
            request = ListServicesRequest(parent=parent)
            
            services = client.list_services(request=request)
            updated_resources = []
            
            for service in services:
                name = service.name.split("/")[-1]
                resource_name = f"cloud-run-{name}"
                
                # Create or update the resource
                if resource_name not in self.resources:
                    resource = self.add_resource(
                        name=resource_name,
                        type="cloud-run",
                        status=ResourceStatus.UNKNOWN,
                        details={"service_name": name, "full_name": service.name},
                        metadata={"traffic_statuses": []}
                    )
                else:
                    resource = self.resources[resource_name]
                
                # Update traffic status
                traffic_statuses = []
                for traffic_target in service.traffic:
                    traffic_statuses.append({
                        "revision": traffic_target.revision,
                        "percent": traffic_target.percent,
                        "latest_revision": traffic_target.latest_revision
                    })
                
                # Determine status
                if service.latest_ready_revision:
                    status = ResourceStatus.READY
                elif service.latest_created_revision:
                    status = ResourceStatus.PROVISIONING
                else:
                    status = ResourceStatus.PENDING
                
                # Update resource status
                resource.update_status(status, {
                    "url": service.uri if hasattr(service, "uri") else None,
                    "traffic_statuses": traffic_statuses,
                    "latest_created_revision": service.latest_created_revision,
                    "latest_ready_revision": service.latest_ready_revision
                })
                
                updated_resources.append(resource)
            
            self._save_state()
            return updated_resources
            
        except Exception as e:
            self.add_notification(
                f"Failed to check Cloud Run services: {str(e)}",
                level="ERROR",
                details={"error": str(e)}
            )
            return []
    
    async def scan_all_resources(self) -> Dict[str, List[MigrationResource]]:
        """Scan all GCP resources related to the migration.
        
        Returns:
            Dictionary mapping resource type to list of resources
        """
        results: Dict[str, List[MigrationResource]] = {}
        
        # Check Cloud Run services
        cloud_run_resources = await self.check_cloud_run_services()
        if cloud_run_resources:
            results["cloud-run"] = cloud_run_resources
        
        # Additional resource checks could be added here
        
        return results
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get the overall migration status.
        
        Returns:
            Dictionary with migration status information
        """
        # Count resources by status
        status_counts = {status.value: 0 for status in ResourceStatus}
        for resource in self.resources.values():
            status_counts[resource.status.value] += 1
        
        # Calculate completion percentage
        total_resources = len(self.resources)
        completed_resources = status_counts[ResourceStatus.READY.value]
        failed_resources = status_counts[ResourceStatus.FAILED.value]
        
        completion_percentage = 0
        if total_resources > 0:
            completion_percentage = (completed_resources / total_resources) * 100
            
        # Determine overall status
        overall_status = "IN_PROGRESS"
        if completion_percentage == 100:
            overall_status = "COMPLETED"
        elif failed_resources > 0:
            overall_status = "ISSUES_DETECTED"
        
        return {
            "status": overall_status,
            "completion_percentage": completion_percentage,
            "resource_counts": status_counts,
            "total_resources": total_resources,
            "completed_resources": completed_resources,
            "failed_resources": failed_resources,
            "last_updated": datetime.datetime.now().isoformat(),
            "recent_notifications": self.notifications[-5:] if self.notifications else []
        }
    
    def display_status(self):
        """Display migration status in a formatted table."""
        status = self.get_migration_status()
        
        console.print()
        console.print(f"[bold blue]AI Orchestra GCP Migration Status[/bold blue]", justify="center")
        console.print(f"Project: [green]{self.project_id}[/green]  Region: [green]{self.region}[/green]")
        console.print(f"Last Updated: [yellow]{status['last_updated']}[/yellow]")
        console.print()
        
        # Status bar
        completed = status["completion_percentage"]
        status_color = "green" if completed == 100 else "yellow" if completed > 50 else "red"
        console.print(f"Progress: [bold {status_color}]{completed:.1f}%[/bold {status_color}]")
        
        bar_width = 50
        completed_chars = int(bar_width * (completed / 100))
        console.print(f"[{status_color}]{'■' * completed_chars}{'□' * (bar_width - completed_chars)}[/{status_color}]")
        
        console.print()
        console.print(f"Status: [bold {'green' if status['status'] == 'COMPLETED' else 'yellow'}]{status['status']}[/bold]")
        
        # Resource counts
        table = Table(title="Resource Status")
        table.add_column("Status", style="cyan")
        table.add_column("Count", justify="right", style="green")
        
        for status_name, count in status["resource_counts"].items():
            if count > 0:
                table.add_row(status_name.upper(), str(count))
                
        console.print(table)
        
        # Resources table
        if self.resources:
            resources_table = Table(title="Resources")
            resources_table.add_column("Name", style="cyan")
            resources_table.add_column("Type", style="blue")
            resources_table.add_column("Status", style="green")
            resources_table.add_column("Last Updated", style="yellow")
            
            for resource in sorted(self.resources.values(), key=lambda r: r.name):
                status_style = "green" if resource.status == ResourceStatus.READY else \
                               "red" if resource.status == ResourceStatus.FAILED else "yellow"
                
                resources_table.add_row(
                    resource.name,
                    resource.type,
                    f"[{status_style}]{resource.status.value.upper()}[/{status_style}]",
                    resource.last_updated.strftime("%Y-%m-%d %H:%M:%S")
                )
                
            console.print(resources_table)
        
        # Recent notifications
        if status["recent_notifications"]:
            console.print("\n[bold]Recent Notifications:[/bold]")
            for notification in status["recent_notifications"]:
                level_style = "green" if notification["level"] == "INFO" else \
                             "yellow" if notification["level"] == "WARNING" else "red"
                
                console.print(f"[{level_style}]{notification['level']}[/{level_style}] "
                             f"{notification['timestamp']}: {notification['message']}")
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate a detailed migration report.
        
        Args:
            output_file: Path to save the report (optional)
            
        Returns:
            Path to the generated report
        """
        status = self.get_migration_status()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = output_file or f"migration_report_{timestamp}.md"
        
        with open(report_file, "w") as f:
            f.write(f"# AI Orchestra GCP Migration Report\n\n")
            f.write(f"**Project:** {self.project_id}  \n")
            f.write(f"**Region:** {self.region}  \n")
            f.write(f"**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n\n")
            
            f.write(f"## Migration Status\n\n")
            f.write(f"**Overall Status:** {status['status']}  \n")
            f.write(f"**Completion:** {status['completion_percentage']:.1f}%  \n")
            f.write(f"**Total Resources:** {status['total_resources']}  \n")
            f.write(f"**Completed Resources:** {status['completed_resources']}  \n")
            f.write(f"**Failed Resources:** {status['failed_resources']}  \n\n")
            
            # Resource status table
            f.write("## Resource Status\n\n")
            f.write("| Status | Count |\n")
            f.write("|--------|-------|\n")
            
            for status_name, count in status["resource_counts"].items():
                if count > 0:
                    f.write(f"| {status_name.upper()} | {count} |\n")
            
            f.write("\n")
            
            # Resources details
            if self.resources:
                f.write("## Resource Details\n\n")
                f.write("| Name | Type | Status | Last Updated |\n")
                f.write("|------|------|--------|-------------|\n")
                
                for resource in sorted(self.resources.values(), key=lambda r: r.name):
                    f.write(f"| {resource.name} | {resource.type} | {resource.status.value.upper()} | "
                           f"{resource.last_updated.strftime('%Y-%m-%d %H:%M:%S')} |\n")
                
                f.write("\n")
            
            # Notifications
            if self.notifications:
                f.write("## Notification History\n\n")
                f.write("| Timestamp | Level | Message |\n")
                f.write("|-----------|-------|--------|\n")
                
                for notification in self.notifications[-20:]:  # Show last 20 notifications
                    f.write(f"| {notification['timestamp']} | {notification['level']} | {notification['message']} |\n")
            
            # Recommendations
            f.write("\n## Recommendations\n\n")
            
            if status["failed_resources"] > 0:
                f.write("- **Critical:** Address failed resources before continuing migration\n")
            
            if status["completion_percentage"] < 50:
                f.write("- Continue with the next migration phase\n")
            elif status["completion_percentage"] < 100:
                f.write("- Verify partially completed resources\n")
                f.write("- Run validation tests on deployed resources\n")
            else:
                f.write("- Run comprehensive end-to-end testing\n")
                f.write("- Set up monitoring and alerts\n")
                f.write("- Document the new architecture\n")
            
            f.write("\n---\n")
            f.write(f"Generated by AI Orchestra GCP Migration Monitor")
        
        logger.info(f"Generated migration report: {report_file}")
        return report_file


async def main():
    """Main entry point for the migration monitor."""
    parser = argparse.ArgumentParser(description="AI Orchestra GCP Migration Monitor")
    parser.add_argument("--project-id", default="cherry-ai-project", help="GCP Project ID")
    parser.add_argument("--region", default="us-central1", help="GCP Region")
    parser.add_argument("--state-file", help="Path to state file")
    parser.add_argument("--scan", action="store_true", help="Scan GCP resources")
    parser.add_argument("--report", action="store_true", help="Generate migration report")
    parser.add_argument("--output", help="Path to save the report")
    parser.add_argument("--add-resource", action="store_true", help="Add a resource to monitor")
    parser.add_argument("--name", help="Resource name")
    parser.add_argument("--type", help="Resource type")
    parser.add_argument("--status", help="Resource status")
    
    args = parser.parse_args()
    
    # Initialize the monitor
    monitor = MigrationMonitor(args.project_id, args.region, args.state_file)
    
    if args.add_resource:
        if not args.name or not args.type:
            parser.error("--add-resource requires --name and --type")
        
        status = ResourceStatus(args.status) if args.status else ResourceStatus.PENDING
        monitor.add_resource(args.name, args.type, status)
    
    if args.scan:
        await monitor.scan_all_resources()
    
    # Always display the status
    monitor.display_status()
    
    if args.report:
        report_file = monitor.generate_report(args.output)
        print(f"\nReport generated: {report_file}")


if __name__ == "__main__":
    asyncio.run(main())