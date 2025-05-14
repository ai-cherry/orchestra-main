#!/usr/bin/env python3
"""
AI Orchestra GCP Migration Status Report Generator

This script generates comprehensive status reports for the GCP migration process,
formats them for easy readability, and distributes them to stakeholders through
configurable channels (email, file, Cloud Storage).

The reports include progress tracking, recent activities, upcoming tasks,
potential risks, and performance metrics. It can be scheduled to run daily
via cron or similar task schedulers.

Usage:
    python generate_status_report.py --output=email
    python generate_status_report.py --output=file --path=reports/
    python generate_status_report.py --output=gcs --bucket=status-reports
"""

import argparse
import json
import logging
import os
import smtplib
import sys
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("migration_status_report")

try:
    # Google Cloud Storage imports (optional)
    from google.cloud import storage
except ImportError:
    logger.warning("Google Cloud Storage not available, GCS output disabled")


class StatusReportGenerator:
    """Generator for migration status reports."""
    
    def __init__(self, base_dir: Path):
        """Initialize the report generator.
        
        Args:
            base_dir: Base directory for migration files
        """
        self.base_dir = base_dir
        self.status_file = base_dir / "migration_status.json"
        self.log_file = base_dir / "migration.log"
        self.metrics_file = base_dir / "migration_metrics.json"
        
        self.today = datetime.now().date()
        self.yesterday = self.today - timedelta(days=1)
    
    def get_status_data(self) -> Dict[str, Any]:
        """Get the current migration status.
        
        Returns:
            Status data as a dictionary
        """
        if not self.status_file.exists():
            logger.warning(f"Status file {self.status_file} not found")
            return {}
            
        try:
            with open(self.status_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading status file: {str(e)}")
            return {}
    
    def get_metrics_data(self) -> Dict[str, Any]:
        """Get performance metrics data.
        
        Returns:
            Metrics data as a dictionary
        """
        if not self.metrics_file.exists():
            logger.warning(f"Metrics file {self.metrics_file} not found")
            return {}
            
        try:
            with open(self.metrics_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading metrics file: {str(e)}")
            return {}
    
    def get_recent_log_entries(self, days: int = 1) -> List[str]:
        """Get recent log entries.
        
        Args:
            days: Number of days of logs to retrieve
            
        Returns:
            List of recent log entries
        """
        if not self.log_file.exists():
            logger.warning(f"Log file {self.log_file} not found")
            return []
            
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_entries = []
        
        try:
            with open(self.log_file, "r") as f:
                for line in f:
                    # Parse timestamp from log line
                    timestamp_match = line.split(" [", 1)[0] if " [" in line else None
                    if not timestamp_match:
                        continue
                        
                    try:
                        timestamp = datetime.strptime(timestamp_match, "%Y-%m-%d %H:%M:%S,%f")
                        if timestamp >= cutoff_date:
                            recent_entries.append(line.strip())
                    except ValueError:
                        continue
        except Exception as e:
            logger.error(f"Error reading log file: {str(e)}")
        
        return recent_entries
    
    def generate_report(self, include_metrics: bool = True) -> str:
        """Generate a status report.
        
        Args:
            include_metrics: Whether to include performance metrics
            
        Returns:
            Status report as a string
        """
        status_data = self.get_status_data()
        metrics_data = self.get_metrics_data() if include_metrics else {}
        recent_logs = self.get_recent_log_entries(days=1)
        
        # Start building the report
        report = []
        report.append("# AI Orchestra GCP Migration Status Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Migration progress summary
        current_phase = status_data.get("current_phase", "Unknown")
        phases = status_data.get("phases", {})
        
        total_phases = len(phases)
        completed_phases = sum(1 for p in phases.values() if p.get("status") == "COMPLETED")
        in_progress_phases = sum(1 for p in phases.values() if p.get("status") == "IN_PROGRESS")
        
        progress_percentage = (completed_phases / total_phases) * 100 if total_phases > 0 else 0
        
        report.append("## Migration Progress Summary")
        report.append("")
        report.append(f"* **Current Status**: {progress_percentage:.1f}% Complete")
        report.append(f"* **Current Phase**: {current_phase}")
        report.append(f"* **Phases Completed**: {completed_phases}/{total_phases}")
        report.append("")
        
        # Phase status table
        report.append("### Phase Status")
        report.append("")
        report.append("| Phase | Status | Started | Duration |")
        report.append("|-------|--------|---------|----------|")
        
        for phase_name, phase_data in phases.items():
            status = phase_data.get("status", "PENDING")
            started = phase_data.get("started_at", "Not started")
            duration = phase_data.get("duration", "N/A")
            
            report.append(f"| {phase_name} | {status} | {started} | {duration} |")
        
        report.append("")
        
        # Recent activities
        report.append("## Recent Activities")
        report.append("")
        
        if recent_logs:
            # Group by hour for better readability
            hour_groups: Dict[str, List[str]] = {}
            for log in recent_logs[-50:]:  # Limit to last 50 entries for readability
                try:
                    timestamp_str = log.split(" [", 1)[0]
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
                    hour_key = timestamp.strftime("%Y-%m-%d %H:00")
                    
                    if hour_key not in hour_groups:
                        hour_groups[hour_key] = []
                    
                    # Format the log entry for better readability
                    message = log.split("] ", 1)[1] if "] " in log else log
                    hour_groups[hour_key].append(
                        f"* {timestamp.strftime('%H:%M:%S')} - {message}"
                    )
                except Exception:
                    continue
            
            # Add groups in reverse chronological order
            for hour in sorted(hour_groups.keys(), reverse=True):
                report.append(f"### {hour}")
                report.append("")
                report.extend(hour_groups[hour][-10:])  # Last 10 entries per hour
                report.append("")
        else:
            report.append("No recent activities recorded.")
            report.append("")
        
        # Potential risks
        conflicts = status_data.get("conflicts", [])
        if conflicts:
            report.append("## Potential Risks")
            report.append("")
            for conflict in conflicts:
                report.append(f"* ⚠️ {conflict}")
            report.append("")
        
        # Performance metrics
        if include_metrics and metrics_data:
            report.append("## Performance Metrics")
            report.append("")
            
            # Vector search metrics
            vector_metrics = metrics_data.get("vector_search", {})
            if vector_metrics:
                report.append("### Vector Search Performance")
                report.append("")
                report.append(f"* **Average Latency**: {vector_metrics.get('avg_latency_ms', 'N/A')} ms")
                report.append(f"* **P95 Latency**: {vector_metrics.get('p95_latency_ms', 'N/A')} ms")
                report.append(f"* **Throughput**: {vector_metrics.get('throughput', 'N/A')} queries/sec")
                report.append("")
            
            # API metrics
            api_metrics = metrics_data.get("api", {})
            if api_metrics:
                report.append("### API Performance")
                report.append("")
                report.append(f"* **Average Response Time**: {api_metrics.get('avg_response_time_ms', 'N/A')} ms")
                report.append(f"* **Cold Start Latency**: {api_metrics.get('cold_start_latency_ms', 'N/A')} ms")
                report.append("")
            
            # Circuit breaker metrics
            circuit_metrics = metrics_data.get("circuit_breaker", {})
            if circuit_metrics:
                report.append("### Circuit Breaker Status")
                report.append("")
                report.append(f"* **State**: {circuit_metrics.get('state', 'N/A')}")
                report.append(f"* **Failures**: {circuit_metrics.get('failure_count', 'N/A')}")
                report.append(f"* **Success Rate**: {circuit_metrics.get('success_rate', 'N/A')}%")
                report.append("")
        
        # Upcoming tasks
        report.append("## Upcoming Tasks")
        report.append("")
        
        found_next = False
        for phase_name, phase_data in phases.items():
            if phase_data.get("status") == "PENDING":
                if not found_next:
                    report.append(f"### Next Phase: {phase_name}")
                    report.append("")
                    found_next = True
                
                report.append(f"* {phase_name}")
        
        if not found_next:
            report.append("All phases are complete or in progress.")
        
        report.append("")
        
        # Return the report as a string
        return "\n".join(report)
    
    def save_report_to_file(self, report: str, output_dir: Path) -> Path:
        """Save the report to a file.
        
        Args:
            report: The report content
            output_dir: Directory to save the report in
            
        Returns:
            Path to the saved report file
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a filename with the current date
        filename = f"migration_status_{datetime.now().strftime('%Y%m%d')}.md"
        output_path = output_dir / filename
        
        with open(output_path, "w") as f:
            f.write(report)
        
        logger.info(f"Report saved to {output_path}")
        return output_path
    
    def upload_report_to_gcs(self, report: str, bucket_name: str) -> str:
        """Upload the report to Google Cloud Storage.
        
        Args:
            report: The report content
            bucket_name: GCS bucket name
            
        Returns:
            GCS object URL
        """
        try:
            # Check if Google Cloud Storage is available
            if "storage" not in globals():
                raise ImportError("Google Cloud Storage not available")
            
            # Create a client
            client = storage.Client()
            
            # Get the bucket
            bucket = client.bucket(bucket_name)
            
            # Create a blob name with the current date
            blob_name = f"migration_status_{datetime.now().strftime('%Y%m%d')}.md"
            
            # Create a blob
            blob = bucket.blob(blob_name)
            
            # Upload the report
            blob.upload_from_string(report, content_type="text/markdown")
            
            # Generate URL
            url = f"gs://{bucket_name}/{blob_name}"
            
            logger.info(f"Report uploaded to {url}")
            return url
        
        except Exception as e:
            logger.error(f"Error uploading report to GCS: {str(e)}")
            raise
    
    def send_report_by_email(
        self,
        report: str,
        recipients: List[str],
        smtp_server: str = "localhost",
        smtp_port: int = 25,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        sender: str = "migration-status@ai-orchestra.example.com",
        subject: Optional[str] = None,
    ) -> bool:
        """Send the report by email.
        
        Args:
            report: The report content
            recipients: List of email recipients
            smtp_server: SMTP server hostname
            smtp_port: SMTP server port
            smtp_user: SMTP username (if authentication is required)
            smtp_password: SMTP password (if authentication is required)
            sender: Sender email address
            subject: Email subject (default: generated based on current phase)
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Get the current phase for the subject
            status_data = self.get_status_data()
            current_phase = status_data.get("current_phase", "Unknown")
            
            # Create a default subject if none provided
            if subject is None:
                subject = f"AI Orchestra GCP Migration Status Report - {current_phase} Phase"
            
            # Create the email message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = ", ".join(recipients)
            
            # Convert the Markdown report to HTML for better email viewing
            html_report = self._markdown_to_html(report)
            
            # Attach the report in both plaintext and HTML formats
            msg.attach(MIMEText(report, "plain"))
            msg.attach(MIMEText(html_report, "html"))
            
            # Connect to the SMTP server and send the email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if smtp_user and smtp_password:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                
                server.send_message(msg)
            
            logger.info(f"Report sent to {', '.join(recipients)}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
    
    def _markdown_to_html(self, markdown: str) -> str:
        """Convert markdown to HTML.
        
        Args:
            markdown: Markdown text
            
        Returns:
            HTML version of the markdown
        """
        try:
            # Try to use the markdown library if available
            import markdown
            return markdown.markdown(markdown)
        except ImportError:
            # Simple fallback conversion if markdown library is not available
            html = []
            html.append("<html><body>")
            
            for line in markdown.splitlines():
                # Convert headers
                if line.startswith("# "):
                    html.append(f"<h1>{line[2:]}</h1>")
                elif line.startswith("## "):
                    html.append(f"<h2>{line[3:]}</h2>")
                elif line.startswith("### "):
                    html.append(f"<h3>{line[4:]}</h3>")
                # Convert bullet points
                elif line.startswith("* "):
                    html.append(f"<li>{line[2:]}</li>")
                # Convert tables (simple approach)
                elif line.startswith("|") and line.endswith("|"):
                    if "---" in line:
                        continue  # Skip table separators
                    html.append("<tr>")
                    cells = line.strip("|").split("|")
                    for cell in cells:
                        html.append(f"<td>{cell.strip()}</td>")
                    html.append("</tr>")
                # Handle empty lines
                elif not line.strip():
                    html.append("<br>")
                # Regular text
                else:
                    html.append(f"<p>{line}</p>")
            
            html.append("</body></html>")
            return "\n".join(html)


def setup_argparse() -> argparse.ArgumentParser:
    """Set up the argument parser.
    
    Returns:
        Argument parser
    """
    parser = argparse.ArgumentParser(
        description="Generate and distribute migration status reports"
    )
    
    parser.add_argument(
        "--output",
        choices=["file", "email", "gcs"],
        default="file",
        help="Output method for the report"
    )
    
    parser.add_argument(
        "--path",
        type=str,
        default="reports",
        help="Output directory for file output"
    )
    
    parser.add_argument(
        "--bucket",
        type=str,
        help="GCS bucket name for GCS output"
    )
    
    parser.add_argument(
        "--recipients",
        type=str,
        help="Comma-separated list of email recipients for email output"
    )
    
    parser.add_argument(
        "--smtp-server",
        type=str,
        default="localhost",
        help="SMTP server for email output"
    )
    
    parser.add_argument(
        "--smtp-port",
        type=int,
        default=25,
        help="SMTP port for email output"
    )
    
    parser.add_argument(
        "--smtp-user",
        type=str,
        help="SMTP username for email output"
    )
    
    parser.add_argument(
        "--smtp-password",
        type=str,
        help="SMTP password for email output"
    )
    
    parser.add_argument(
        "--sender",
        type=str,
        default="migration-status@ai-orchestra.example.com",
        help="Sender email address for email output"
    )
    
    parser.add_argument(
        "--subject",
        type=str,
        help="Email subject for email output"
    )
    
    parser.add_argument(
        "--metrics",
        action="store_true",
        help="Include performance metrics in the report"
    )
    
    parser.add_argument(
        "--base-dir",
        type=str,
        default="gcp_migration",
        help="Base directory for migration files"
    )
    
    return parser


def main() -> int:
    """Main entry point.
    
    Returns:
        Exit code
    """
    # Parse command line arguments
    parser = setup_argparse()
    args = parser.parse_args()
    
    try:
        # Create the report generator
        base_dir = Path(args.base_dir)
        generator = StatusReportGenerator(base_dir)
        
        # Generate the report
        report = generator.generate_report(include_metrics=args.metrics)
        
        # Handle output based on selected method
        if args.output == "file":
            output_dir = Path(args.path)
            generator.save_report_to_file(report, output_dir)
        
        elif args.output == "email":
            if not args.recipients:
                logger.error("No recipients specified for email output")
                return 1
                
            recipients = [r.strip() for r in args.recipients.split(",")]
            success = generator.send_report_by_email(
                report=report,
                recipients=recipients,
                smtp_server=args.smtp_server,
                smtp_port=args.smtp_port,
                smtp_user=args.smtp_user,
                smtp_password=args.smtp_password,
                sender=args.sender,
                subject=args.subject,
            )
            
            if not success:
                return 1
        
        elif args.output == "gcs":
            if not args.bucket:
                logger.error("No bucket specified for GCS output")
                return 1
                
            generator.upload_report_to_gcs(report, args.bucket)
        
        return 0
    
    except Exception as e:
        logger.exception(f"Error generating status report: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())