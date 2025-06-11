"""
Monitoring and alerting configuration
"""

import os
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from datetime import datetime
import httpx
from enum import Enum

class AlertSeverity(str, Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class AlertType(str, Enum):
    """Alert types"""
    SECURITY = "security"
    PERFORMANCE = "performance"
    AVAILABILITY = "availability"
    ERROR = "error"
    DEPLOYMENT = "deployment"

class AlertManager:
    """Manage alerts and notifications"""

    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("MONITOR_FROM_EMAIL")
        self.to_email = os.getenv("MONITOR_TO_EMAIL")
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        self.prometheus_url = os.getenv("PROMETHEUS_URL")

    async def send_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        alert_type: AlertType,
        metadata: Optional[Dict] = None
    ):
        """Send alert through configured channels"""
        alert_data = {
            "title": title,
            "message": message,
            "severity": severity.value,
            "type": alert_type.value,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }

        # Send based on severity
        if severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
            await self._send_email(alert_data)
            await self._send_slack(alert_data)
        elif severity == AlertSeverity.MEDIUM:
            await self._send_slack(alert_data)
        
        # Always log to monitoring system
        await self._send_to_prometheus(alert_data)

    async def _send_email(self, alert_data: Dict):
        """Send email alert"""
        if not all([self.smtp_server, self.smtp_password, self.from_email, self.to_email]):
            return

        try:
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = self.to_email
            msg["Subject"] = f"[{alert_data['severity'].upper()}] {alert_data['title']}"

            body = f"""
Alert: {alert_data["title"]}
Severity: {alert_data["severity"]}
Type: {alert_data["type"]}
Time: {alert_data["timestamp"]}

Message:
{alert_data["message"]}

Metadata:
{json.dumps(alert_data["metadata"], indent=2)}
"""
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.from_email, self.smtp_password)
                server.send_message(msg)
        except Exception as e:
            print(f"Failed to send email alert: {e}")

    async def _send_slack(self, alert_data: Dict):
        """Send Slack alert"""
        if not self.slack_webhook:
            return

        try:
            color_map = {
                "critical": "#FF0000",
                "high": "#FF6600",
                "medium": "#FFCC00",
                "low": "#0099FF",
                "info": "#00CC00"
            }

            payload = {
                "attachments": [{
                    "color": color_map.get(alert_data["severity"], "#808080"),
                    "title": alert_data["title"],
                    "text": alert_data["message"],
                    "fields": [
                        {"title": "Severity", "value": alert_data["severity"], "short": True},
                        {"title": "Type", "value": alert_data["type"], "short": True},
                        {"title": "Time", "value": alert_data["timestamp"], "short": False}
                    ],
                    "footer": "MCP Alert System"
                }]
            }

            async with httpx.AsyncClient() as client:
                await client.post(self.slack_webhook, json=payload)
        except Exception as e:
            print(f"Failed to send Slack alert: {e}")

    async def _send_to_prometheus(self, alert_data: Dict):
        """Send metrics to Prometheus"""
        # This would integrate with Prometheus Pushgateway
        # Implementation depends on specific Prometheus setup
        pass
