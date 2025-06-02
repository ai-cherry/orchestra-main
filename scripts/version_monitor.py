#!/usr/bin/env python3
"""
Version Monitor - Real-time monitoring and alerting for version health
Integrates with Prometheus for metrics and provides health dashboards
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
import aiohttp
from prometheus_client import (
    Counter, Gauge, Histogram, Info,
    start_http_server, REGISTRY
)

from version_manager import (
    VersionRegistry, Dependency, ComponentType,
    Version, Severity
)

logger = logging.getLogger(__name__)

# Prometheus metrics
version_info = Info(
    'dependency_version',
    'Current version information for dependencies',
    ['name', 'type', 'source']
)

vulnerability_gauge = Gauge(
    'dependency_vulnerabilities',
    'Number of known vulnerabilities',
    ['name', 'severity']
)

update_priority_gauge = Gauge(
    'dependency_update_priority',
    'Update priority score (0-10)',
    ['name', 'type']
)

version_age_days = Gauge(
    'dependency_version_age_days',
    'Days since dependency was last updated',
    ['name', 'type']
)

update_operations = Counter(
    'version_update_operations_total',
    'Total number of version update operations',
    ['status', 'type']
)

update_duration = Histogram(
    'version_update_duration_seconds',
    'Duration of version update operations',
    ['type', 'status']
)

health_check_errors = Counter(
    'version_health_check_errors_total',
    'Total number of health check errors',
    ['check_type']
)

class HealthStatus(Enum):
    """Overall health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class HealthCheck:
    """Individual health check result"""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class Alert:
    """Version-related alert"""
    id: str
    level: AlertLevel
    title: str
    description: str
    affected_components: List[str]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = False
    resolution_time: Optional[datetime] = None

class VersionMonitor:
    """Monitors version health and generates alerts"""
    
    def __init__(self, root_path: Path, check_interval: int = 3600):
        self.root_path = root_path
        self.registry = VersionRegistry(root_path)
        self.check_interval = check_interval  # seconds
        self.alerts: Dict[str, Alert] = {}
        self.health_checks: List[HealthCheck] = []
        self.running = False
        
    async def start(self, prometheus_port: int = 9090):
        """Start monitoring service"""
        logger.info(f"Starting version monitor on port {prometheus_port}")
        
        # Start Prometheus metrics server
        start_http_server(prometheus_port)
        
        # Start monitoring loop
        self.running = True
        await self._monitoring_loop()
        
    async def stop(self):
        """Stop monitoring service"""
        logger.info("Stopping version monitor")
        self.running = False
        
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Run health checks
                await self.run_health_checks()
                
                # Update metrics
                await self.update_metrics()
                
                # Check for alerts
                await self.check_alerts()
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                health_check_errors.labels(check_type='monitoring_loop').inc()
                await asyncio.sleep(60)  # Wait a minute before retrying
                
    async def run_health_checks(self) -> List[HealthCheck]:
        """Run all health checks"""
        logger.info("Running health checks")
        self.health_checks = []
        
        # Scan current state
        await self.registry.scan_all()
        await self.registry.check_vulnerabilities()
        
        # Run individual checks
        checks = [
            self._check_vulnerabilities(),
            self._check_outdated_dependencies(),
            self._check_version_conflicts(),
            self._check_license_compliance(),
            self._check_update_frequency()
        ]
        
        results = await asyncio.gather(*checks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, HealthCheck):
                self.health_checks.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Health check failed: {result}")
                health_check_errors.labels(check_type='unknown').inc()
                
        return self.health_checks
    
    async def _check_vulnerabilities(self) -> HealthCheck:
        """Check for security vulnerabilities"""
        vulnerable_deps = [
            dep for dep in self.registry.dependencies.values()
            if dep.vulnerabilities
        ]
        
        critical_count = sum(
            1 for dep in vulnerable_deps
            for vuln in dep.vulnerabilities
            if vuln.severity == Severity.CRITICAL
        )
        
        high_count = sum(
            1 for dep in vulnerable_deps
            for vuln in dep.vulnerabilities
            if vuln.severity == Severity.HIGH
        )
        
        if critical_count > 0:
            status = HealthStatus.CRITICAL
            message = f"Found {critical_count} critical vulnerabilities"
        elif high_count > 0:
            status = HealthStatus.WARNING
            message = f"Found {high_count} high severity vulnerabilities"
        elif vulnerable_deps:
            status = HealthStatus.WARNING
            message = f"Found {len(vulnerable_deps)} dependencies with vulnerabilities"
        else:
            status = HealthStatus.HEALTHY
            message = "No known vulnerabilities"
            
        return HealthCheck(
            name="security_vulnerabilities",
            status=status,
            message=message,
            details={
                "total_vulnerable": len(vulnerable_deps),
                "critical": critical_count,
                "high": high_count,
                "affected_dependencies": [dep.name for dep in vulnerable_deps[:10]]
            }
        )
    
    async def _check_outdated_dependencies(self) -> HealthCheck:
        """Check for outdated dependencies"""
        outdated = [
            dep for dep in self.registry.dependencies.values()
            if dep.update_priority > 0
        ]
        
        high_priority = [dep for dep in outdated if dep.update_priority >= 7]
        
        if len(high_priority) > 10:
            status = HealthStatus.CRITICAL
            message = f"{len(high_priority)} dependencies need urgent updates"
        elif len(outdated) > 50:
            status = HealthStatus.WARNING
            message = f"{len(outdated)} dependencies are outdated"
        elif outdated:
            status = HealthStatus.WARNING
            message = f"{len(outdated)} dependencies have available updates"
        else:
            status = HealthStatus.HEALTHY
            message = "All dependencies are up to date"
            
        return HealthCheck(
            name="outdated_dependencies",
            status=status,
            message=message,
            details={
                "total_outdated": len(outdated),
                "high_priority": len(high_priority),
                "top_priorities": [
                    {
                        "name": dep.name,
                        "current": str(dep.current_version),
                        "priority": dep.update_priority
                    }
                    for dep in sorted(high_priority, 
                                    key=lambda x: x.update_priority, 
                                    reverse=True)[:5]
                ]
            }
        )
    
    async def _check_version_conflicts(self) -> HealthCheck:
        """Check for version conflicts between dependencies"""
        # Simplified conflict detection
        # In production, would use proper dependency resolution
        
        conflicts = []
        deps_by_name = {}
        
        for dep in self.registry.dependencies.values():
            if dep.name not in deps_by_name:
                deps_by_name[dep.name] = []
            deps_by_name[dep.name].append(dep)
            
        for name, deps in deps_by_name.items():
            if len(deps) > 1:
                versions = set(str(d.current_version) for d in deps)
                if len(versions) > 1:
                    conflicts.append({
                        "dependency": name,
                        "versions": list(versions),
                        "sources": [d.source_file for d in deps]
                    })
                    
        if conflicts:
            status = HealthStatus.WARNING
            message = f"Found {len(conflicts)} version conflicts"
        else:
            status = HealthStatus.HEALTHY
            message = "No version conflicts detected"
            
        return HealthCheck(
            name="version_conflicts",
            status=status,
            message=message,
            details={
                "conflicts": conflicts[:10]  # Top 10 conflicts
            }
        )
    
    async def _check_license_compliance(self) -> HealthCheck:
        """Check for license compliance issues"""
        # Check for problematic licenses
        problematic_licenses = ['GPL', 'AGPL', 'LGPL']
        
        issues = []
        for dep in self.registry.dependencies.values():
            if dep.license and any(lic in dep.license for lic in problematic_licenses):
                issues.append({
                    "dependency": dep.name,
                    "license": dep.license,
                    "type": dep.type.value
                })
                
        if issues:
            status = HealthStatus.WARNING
            message = f"Found {len(issues)} potential license compliance issues"
        else:
            status = HealthStatus.HEALTHY
            message = "No license compliance issues detected"
            
        return HealthCheck(
            name="license_compliance",
            status=status,
            message=message,
            details={
                "issues": issues[:10]
            }
        )
    
    async def _check_update_frequency(self) -> HealthCheck:
        """Check if dependencies are being updated regularly"""
        now = datetime.now(timezone.utc)
        stale_threshold = timedelta(days=90)  # 3 months
        
        stale_deps = []
        for dep in self.registry.dependencies.values():
            if dep.last_updated:
                age = now - dep.last_updated
                if age > stale_threshold:
                    stale_deps.append({
                        "name": dep.name,
                        "last_updated": dep.last_updated.isoformat(),
                        "age_days": age.days
                    })
                    
        if len(stale_deps) > 20:
            status = HealthStatus.WARNING
            message = f"{len(stale_deps)} dependencies haven't been reviewed in 90+ days"
        elif stale_deps:
            status = HealthStatus.WARNING
            message = f"{len(stale_deps)} dependencies may need review"
        else:
            status = HealthStatus.HEALTHY
            message = "Dependencies are being reviewed regularly"
            
        return HealthCheck(
            name="update_frequency",
            status=status,
            message=message,
            details={
                "stale_count": len(stale_deps),
                "oldest": sorted(stale_deps, key=lambda x: x['age_days'], reverse=True)[:5]
            }
        )
    
    async def update_metrics(self):
        """Update Prometheus metrics"""
        logger.debug("Updating Prometheus metrics")
        
        for dep in self.registry.dependencies.values():
            # Version info
            version_info.labels(
                name=dep.name,
                type=dep.type.value,
                source=dep.source_file or "unknown"
            ).info({
                'version': str(dep.current_version),
                'constraint': dep.constraint or "none"
            })
            
            # Vulnerability metrics
            for severity in Severity:
                count = sum(
                    1 for v in dep.vulnerabilities 
                    if v.severity == severity
                )
                vulnerability_gauge.labels(
                    name=dep.name,
                    severity=severity.value
                ).set(count)
                
            # Update priority
            update_priority_gauge.labels(
                name=dep.name,
                type=dep.type.value
            ).set(dep.update_priority)
            
            # Version age
            if dep.last_updated:
                age_days = (datetime.now(timezone.utc) - dep.last_updated).days
                version_age_days.labels(
                    name=dep.name,
                    type=dep.type.value
                ).set(age_days)
                
    async def check_alerts(self):
        """Check for conditions that should trigger alerts"""
        logger.debug("Checking for alert conditions")
        
        # Check each health check for alert conditions
        for check in self.health_checks:
            alert_id = f"{check.name}_{check.status.value}"
            
            if check.status == HealthStatus.CRITICAL:
                # Create or update critical alert
                if alert_id not in self.alerts or self.alerts[alert_id].resolved:
                    alert = Alert(
                        id=alert_id,
                        level=AlertLevel.CRITICAL,
                        title=f"Critical: {check.name.replace('_', ' ').title()}",
                        description=check.message,
                        affected_components=self._get_affected_components(check)
                    )
                    self.alerts[alert_id] = alert
                    await self._send_alert(alert)
                    
            elif check.status == HealthStatus.WARNING:
                # Create warning alert if not exists
                if alert_id not in self.alerts or self.alerts[alert_id].resolved:
                    alert = Alert(
                        id=alert_id,
                        level=AlertLevel.WARNING,
                        title=f"Warning: {check.name.replace('_', ' ').title()}",
                        description=check.message,
                        affected_components=self._get_affected_components(check)
                    )
                    self.alerts[alert_id] = alert
                    await self._send_alert(alert)
                    
            elif check.status == HealthStatus.HEALTHY:
                # Resolve any existing alerts for this check
                for alert_key in list(self.alerts.keys()):
                    if alert_key.startswith(check.name):
                        alert = self.alerts[alert_key]
                        if not alert.resolved:
                            alert.resolved = True
                            alert.resolution_time = datetime.now(timezone.utc)
                            await self._send_alert_resolution(alert)
                            
    def _get_affected_components(self, check: HealthCheck) -> List[str]:
        """Extract affected components from health check"""
        affected = []
        
        if 'affected_dependencies' in check.details:
            affected.extend(check.details['affected_dependencies'])
        elif 'top_priorities' in check.details:
            affected.extend([p['name'] for p in check.details['top_priorities']])
        elif 'conflicts' in check.details:
            affected.extend([c['dependency'] for c in check.details['conflicts']])
            
        return affected[:10]  # Limit to 10 components
    
    async def _send_alert(self, alert: Alert):
        """Send alert to configured channels"""
        logger.warning(f"ALERT [{alert.level.value}]: {alert.title} - {alert.description}")
        
        # In production, this would integrate with:
        # - Slack/Discord webhooks
        # - PagerDuty
        # - Email notifications
        # - Custom alerting systems
        
    async def _send_alert_resolution(self, alert: Alert):
        """Send alert resolution notification"""
        duration = alert.resolution_time - alert.timestamp
        logger.info(f"RESOLVED: {alert.title} (duration: {duration})")
        
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status summary"""
        overall_status = HealthStatus.HEALTHY
        
        # Determine overall status from individual checks
        for check in self.health_checks:
            if check.status == HealthStatus.CRITICAL:
                overall_status = HealthStatus.CRITICAL
                break
            elif check.status == HealthStatus.WARNING and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.WARNING
                
        # Count active alerts by level
        active_alerts = [a for a in self.alerts.values() if not a.resolved]
        alerts_by_level = {}
        for level in AlertLevel:
            alerts_by_level[level.value] = sum(
                1 for a in active_alerts if a.level == level
            )
            
        return {
            "status": overall_status.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": [
                {
                    "name": check.name,
                    "status": check.status.value,
                    "message": check.message,
                    "details": check.details
                }
                for check in self.health_checks
            ],
            "active_alerts": len(active_alerts),
            "alerts_by_level": alerts_by_level,
            "dependencies": {
                "total": len(self.registry.dependencies),
                "by_type": self._count_by_type()
            }
        }
    
    def _count_by_type(self) -> Dict[str, int]:
        """Count dependencies by type"""
        counts = {}
        for dep in self.registry.dependencies.values():
            type_name = dep.type.value
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts
    
    async def generate_dashboard_data(self) -> Dict[str, Any]:
        """Generate data for monitoring dashboard"""
        # Get current health status
        health = self.get_health_status()
        
        # Calculate additional metrics
        vulnerable_count = sum(
            1 for dep in self.registry.dependencies.values()
            if dep.vulnerabilities
        )
        
        outdated_count = sum(
            1 for dep in self.registry.dependencies.values()
            if dep.update_priority > 0
        )
        
        # Top issues
        top_vulnerabilities = sorted(
            [d for d in self.registry.dependencies.values() if d.vulnerabilities],
            key=lambda x: len(x.vulnerabilities),
            reverse=True
        )[:5]
        
        top_outdated = sorted(
            [d for d in self.registry.dependencies.values() if d.update_priority > 0],
            key=lambda x: x.update_priority,
            reverse=True
        )[:5]
        
        return {
            "health": health,
            "metrics": {
                "total_dependencies": len(self.registry.dependencies),
                "vulnerable_dependencies": vulnerable_count,
                "outdated_dependencies": outdated_count,
                "active_alerts": len([a for a in self.alerts.values() if not a.resolved])
            },
            "top_issues": {
                "vulnerabilities": [
                    {
                        "name": dep.name,
                        "count": len(dep.vulnerabilities),
                        "severity": max(v.severity.value for v in dep.vulnerabilities)
                    }
                    for dep in top_vulnerabilities
                ],
                "outdated": [
                    {
                        "name": dep.name,
                        "current": str(dep.current_version),
                        "priority": dep.update_priority
                    }
                    for dep in top_outdated
                ]
            },
            "trend_data": await self._get_trend_data()
        }
    
    async def _get_trend_data(self) -> Dict[str, List]:
        """Get trend data for charts"""
        # In production, this would query historical data
        # For now, return empty trends
        return {
            "vulnerability_trend": [],
            "update_trend": [],
            "health_trend": []
        }

class HealthCheckAPI:
    """REST API for health check data"""
    
    def __init__(self, monitor: VersionMonitor):
        self.monitor = monitor
        
    async def handle_health(self, request) -> Dict:
        """Handle /health endpoint"""
        return self.monitor.get_health_status()
        
    async def handle_metrics(self, request) -> Dict:
        """Handle /metrics endpoint"""
        return await self.monitor.generate_dashboard_data()
        
    async def handle_alerts(self, request) -> Dict:
        """Handle /alerts endpoint"""
        active_alerts = [
            {
                "id": alert.id,
                "level": alert.level.value,
                "title": alert.title,
                "description": alert.description,
                "timestamp": alert.timestamp.isoformat(),
                "affected_components": alert.affected_components
            }
            for alert in self.monitor.alerts.values()
            if not alert.resolved
        ]
        
        return {
            "alerts": active_alerts,
            "total": len(active_alerts)
        }

async def main():
    """Main entry point for version monitor"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Orchestra Version Monitor - Real-time dependency health monitoring"
    )
    parser.add_argument(
        '--port',
        type=int,
        default=9090,
        help='Prometheus metrics port (default: 9090)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=3600,
        help='Check interval in seconds (default: 3600)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run checks once and exit'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize monitor
    monitor = VersionMonitor(Path.cwd(), args.interval)
    
    try:
        if args.once:
            # Run checks once
            await monitor.run_health_checks()
            await monitor.update_metrics()
            await monitor.check_alerts()
            
            # Print health status
            health = monitor.get_health_status()
            print(json.dumps(health, indent=2))
        else:
            # Start continuous monitoring
            logger.info(f"Starting version monitor on port {args.port}")
            logger.info(f"Check interval: {args.interval} seconds")
            
            await monitor.start(args.port)
            
    except KeyboardInterrupt:
        logger.info("Shutting down monitor")
        await monitor.stop()
    except Exception as e:
        logger.error(f"Monitor error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())