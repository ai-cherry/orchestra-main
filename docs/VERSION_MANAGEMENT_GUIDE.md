# Version Management System - Usage Guide

## Overview

The cherry_ai Version Management System provides comprehensive dependency tracking, security scanning, automated updates, and health monitoring for all components in the platform. This guide covers installation, configuration, and daily usage.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Core Components](#core-components)
4. [Command Reference](#command-reference)
5. [CI/CD Integration](#cicd-integration)
6. [Monitoring & Alerts](#monitoring--alerts)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker (for container scanning)
- Git

### Setup

1. **Install dependencies:**
   ```bash
   pip install -r scripts/requirements-version-management.txt
   ```

2. **Initialize version management:**
   ```bash
   python scripts/version_manager.py init
   ```

3. **Verify installation:**
   ```bash
   python scripts/version_manager.py scan
   ```

## Quick Start

### 1. Check Current State

```bash
# Scan all dependencies
python scripts/version_manager.py scan

# Check for vulnerabilities
python scripts/version_manager.py check

# Generate comprehensive report
python scripts/version_manager.py report --output version-report.json
```

### 2. Update Dependencies

```bash
# Check available updates (minor versions)
python scripts/version_updater.py check --strategy minor

# Apply safe updates (risk <= 5)
python scripts/version_updater.py update --strategy minor --max-risk 5

# Security updates only
python scripts/version_updater.py update --strategy security
```

### 3. Monitor Health

```bash
# Run health checks once
python scripts/version_monitor.py --once

# Start continuous monitoring
python scripts/version_monitor.py --port 9090 --interval 3600
```

## Core Components

### 1. Version Manager (`scripts/version_manager.py`)

The core scanning and registry component that:
- Scans all dependency files (Python, JavaScript, Docker)
- Maintains central version registry (`.versions.yaml`)
- Generates lock files (`.versions.lock`)
- Performs vulnerability scanning
- Creates comprehensive reports

**Key Features:**
- Multi-ecosystem support (Python, npm, Docker)
- Semantic version parsing
- Dependency graph analysis
- Vulnerability database integration

### 2. Version Updater (`scripts/version_updater.py`)

Automated update system with:
- Multiple update strategies (patch, minor, major, security)
- Risk assessment for each update
- Automated testing after updates
- Rollback capabilities
- Update report generation

**Update Strategies:**
- `patch`: Only patch updates (x.x.PATCH)
- `minor`: Minor and patch updates (x.MINOR.x)
- `major`: All updates including major versions
- `security`: Only security-critical updates

### 3. Version Monitor (`scripts/version_monitor.py`)

Real-time monitoring with:
- Prometheus metrics export
- Health check system
- Alert generation
- Dashboard data API
- Trend analysis

**Health Checks:**
- Security vulnerabilities
- Outdated dependencies
- Version conflicts
- License compliance
- Update frequency

## Command Reference

### version_manager.py

```bash
# Initialize version management
python scripts/version_manager.py init

# Scan dependencies
python scripts/version_manager.py scan [--root PATH] [--verbose]

# Check vulnerabilities
python scripts/version_manager.py check [--output FILE]

# Generate report
python scripts/version_manager.py report [--output FILE]

# Create lock file
python scripts/version_manager.py lock
```

### version_updater.py

```bash
# Check for updates
python scripts/version_updater.py check \
  --strategy [patch|minor|major|security] \
  --output FILE

# Apply updates
python scripts/version_updater.py update \
  --strategy [patch|minor|major|security] \
  --max-risk [0-10] \
  --dry-run

# Generate update report
python scripts/version_updater.py report \
  --output FILE
```

### version_monitor.py

```bash
# Run once
python scripts/version_monitor.py --once [--output FILE]

# Start monitoring server
python scripts/version_monitor.py \
  --port 9090 \
  --interval 3600
```

## CI/CD Integration

### GitHub Actions Workflow

The system includes a comprehensive GitHub Actions workflow (`.github/workflows/version-management.yml`) that:

1. **Daily Scans**: Automatic dependency scanning
2. **Security Checks**: Vulnerability detection on every PR
3. **Automated Updates**: Weekly update PRs
4. **Health Monitoring**: Continuous health checks

### Manual Triggers

```yaml
# Trigger workflow manually
gh workflow run version-management.yml \
  -f command=update \
  -f strategy=minor \
  -f max_risk=5
```

### Integration Points

1. **Pre-commit Hooks**:
   ```yaml
   # .pre-commit-config.yaml
   - repo: local
     hooks:
       - id: version-check
         name: Check dependency versions
         entry: python scripts/version_manager.py check
         language: system
         pass_filenames: false
   ```

2. **Pull Request Checks**:
   - Automatic security scanning
   - Version conflict detection
   - Update recommendations

3. **Scheduled Updates**:
   - Daily vulnerability scans
   - Weekly minor updates
   - Monthly comprehensive reports

## Monitoring & Alerts

### Prometheus Metrics

The system exports the following metrics:

```prometheus
# Dependency versions
dependency_version_info{name="fastapi",type="python",source="requirements/base.txt"}

# Vulnerabilities
dependency_vulnerabilities{name="requests",severity="high"} 2

# Update priority
dependency_update_priority{name="django",type="python"} 7

# Version age
dependency_version_age_days{name="react",type="javascript"} 45
```

### Grafana Dashboard

Import the dashboard from `monitoring/version-dashboard.json`:

1. **Overview Panel**: Total dependencies, vulnerabilities, outdated
2. **Security Panel**: Vulnerability trends, severity distribution
3. **Update Panel**: Update priorities, available updates
4. **Health Panel**: Overall health score, active alerts

### Alert Configuration

Configure alerts in `monitoring/alerts.yml`:

```yaml
alerts:
  - name: CriticalVulnerabilities
    condition: dependency_vulnerabilities{severity="critical"} > 0
    action: page
    
  - name: HighPriorityUpdates
    condition: dependency_update_priority > 8
    action: email
    
  - name: VersionConflicts
    condition: version_conflicts_total > 0
    action: slack
```

## Best Practices

### 1. Version Pinning Strategy

**Development**:
- Use exact versions in lock files
- Allow minor updates in development
- Test thoroughly before promoting

**Production**:
- Pin all versions exactly
- Use lock files for deployment
- Automated rollback on failure

### 2. Update Cadence

**Recommended Schedule**:
- **Daily**: Security vulnerability scans
- **Weekly**: Patch updates (automated)
- **Bi-weekly**: Minor updates (with review)
- **Monthly**: Major updates (manual review)
- **Quarterly**: Full dependency audit

### 3. Risk Management

**Update Risk Levels**:
- **0-3**: Safe, automated updates
- **4-6**: Review recommended, automated with tests
- **7-9**: Manual review required
- **10**: Major breaking changes, full testing required

### 4. Security Response

**Vulnerability Response Times**:
- **Critical**: Immediate (< 24 hours)
- **High**: Within 48 hours
- **Medium**: Within 1 week
- **Low**: Next scheduled update

## Troubleshooting

### Common Issues

1. **Scanner Not Finding Dependencies**
   ```bash
   # Verify file paths
   python scripts/version_manager.py scan --verbose
   
   # Check supported file patterns
   ls requirements/*.txt
   find . -name "package.json" -not -path "*/node_modules/*"
   ```

2. **Update Failures**
   ```bash
   # Check backup directory
   ls .version-backups/
   
   # Manual rollback
   cp .version-backups/[timestamp]/requirements/* requirements/
   ```

3. **Version Conflicts**
   ```bash
   # Generate conflict report
   python scripts/version_manager.py report | jq '.conflicts'
   
   # Resolve manually or use
   python scripts/version_updater.py update --strategy security
   ```

4. **Monitor Not Starting**
   ```bash
   # Check port availability
   lsof -i :9090
   
   # Use different port
   python scripts/version_monitor.py --port 9091
   ```

### Debug Mode

Enable verbose logging:

```bash
# Set log level
export VERSION_MANAGER_LOG_LEVEL=DEBUG

# Run with verbose output
python scripts/version_manager.py scan --verbose
```

### Recovery Procedures

1. **Corrupted Lock File**:
   ```bash
   rm .versions.lock
   python scripts/version_manager.py lock
   ```

2. **Failed Update Rollback**:
   ```bash
   # Find backup
   ls -la .version-backups/
   
   # Restore from backup
   ./scripts/restore_version_backup.sh [timestamp]
   ```

3. **Registry Rebuild**:
   ```bash
   rm .versions.yaml
   python scripts/version_manager.py init
   ```

## Advanced Usage

### Custom Scanners

Create custom dependency scanners:

```python
from scripts.version_manager import DependencyScanner, ComponentType

class CustomScanner(DependencyScanner):
    def get_component_type(self) -> ComponentType:
        return ComponentType.CUSTOM
    
    async def scan(self, path: Path) -> Dict[str, Dependency]:
        # Implementation
        pass
```

### Integration with External Tools

1. **Dependabot Integration**:
   ```yaml
   # .github/dependabot.yml
   version: 2
   updates:
     - package-ecosystem: "pip"
       directory: "/"
       schedule:
         interval: "weekly"
   ```

2. **Snyk Integration**:
   ```bash
   snyk test --json | python scripts/import_vulnerabilities.py
   ```

3. **OWASP Dependency Check**:
   ```bash
   dependency-check --project cherry_ai --out . --scan .
   ```

## Conclusion

The cherry_ai Version Management System provides comprehensive dependency management with a focus on security, stability, and automation. Regular use of these tools ensures:

- **Security**: Rapid vulnerability detection and patching
- **Stability**: Controlled updates with testing and rollback
- **Visibility**: Complete dependency tracking and reporting
- **Automation**: Reduced manual overhead for routine updates

For additional support or feature requests, please open an issue in the repository.