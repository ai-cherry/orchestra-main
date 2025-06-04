# Comprehensive Version Management Architecture

## Executive Summary

This document presents a comprehensive version management strategy for the cherry_ai platform, addressing all components requiring version control including dependencies, libraries, frameworks, APIs, microservices, database schemas, configuration files, build tools, CI/CD pipelines, container images, infrastructure-as-code templates, third-party integrations, runtime environments, and development tools.

## Current State Analysis

### 1. Package Management Systems Identified

#### Python Dependencies
- **Primary**: Requirements files in `requirements/` directory
  - `base.txt`: Core dependencies
  - `dev.txt`: Development dependencies
  - `monitoring.txt`: Monitoring tools
  - `production/requirements.txt`: Production bundle
  - `frozen/`: Locked versions with timestamps
- **Secondary**: `pyproject.toml` with Poetry configuration (minimal usage)
- **Additional**: `phidata_requirements.txt`, `semantic_cache_requirements.txt`

#### JavaScript/TypeScript Dependencies
- **Admin UI**: `admin-ui/package.json` with npm/pnpm
- **Dashboard**: `dashboard/package.json` (if exists)
- **Lock Files**: `package-lock.json`, `pnpm-lock.yaml`

#### Container Management
- **Docker Images**: Multiple Dockerfiles
  - `Dockerfile`: Main application
  - `Dockerfile.dev`: Development environment
  - `Dockerfile.superagi`: SuperAGI integration
  - `Dockerfile.webscraping`: Web scraping service
  - `dashboard/Dockerfile`: Admin UI
- **coordination**: `docker-compose.yml` and variants

#### Infrastructure as Code
- **Pulumi**: 
  - `infrastructure/pulumi/` directory structure
  - `Pulumi.yaml` configuration files
  - TypeScript/Python stacks for Vultr deployment

### 2. Component Inventory

#### Core Services
1. **cherry_ai API** (`agent/`)
   - FastAPI application
   - PostgreSQL schemas
   - Weaviate integrations
   
2. **Admin UI** (`admin-ui/`)
   - React + TypeScript
   - Vite build system
   - TanStack Router/Query

3. **MCP Servers** (`mcp-servers/`)
   - Individual server implementations
   - Shared dependencies

4. **Core Libraries** (`core/`)
   - Memory management
   - LLM routing
   - Shared utilities

### 3. Version Dependencies Matrix

```yaml
# Current Major Dependencies
python: "^3.10"
node: ">=18.0.0"
postgresql: ">=14"
weaviate: ">=1.24"
docker: ">=24.0"
pulumi: ">=3.0"
```

## Proposed Version Management Architecture

### 1. Centralized Version Registry

```yaml
# .versions.yaml - Central version registry
metadata:
  schema_version: "1.0.0"
  last_updated: "2025-01-06"
  
runtime:
  python: "3.10.12"
  node: "18.19.0"
  go: "1.21.5"
  
databases:
  postgresql: "14.10"
  weaviate: "1.24.1"
  redis: "7.2.3"
  
infrastructure:
  docker: "24.0.7"
  pulumi: "3.94.2"
  vultr_cli: "2.19.0"
  
frameworks:
  fastapi: "0.104.1"
  react: "18.2.0"
  vite: "5.0.10"
  
monitoring:
  prometheus: "2.48.0"
  grafana: "10.2.2"
  opentelemetry: "1.21.0"
```

### 2. Dependency Management Strategy

#### Python Dependencies

```python
# requirements/version-manager.py
"""Unified Python dependency management"""

import toml
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class DependencyType(Enum):
    RUNTIME = "runtime"
    DEVELOPMENT = "dev"
    TESTING = "test"
    MONITORING = "monitoring"
    OPTIONAL = "optional"

@dataclass
class Dependency:
    name: str
    version: str
    type: DependencyType
    constraints: Optional[str] = None
    vulnerabilities: List[str] = None
    license: Optional[str] = None
    
class VersionManager:
    """Centralized version management for Python dependencies"""
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.versions_file = root_dir / ".versions.yaml"
        self.lock_file = root_dir / ".versions.lock"
        
    def scan_dependencies(self) -> Dict[str, List[Dependency]]:
        """Scan all Python dependencies across the project"""
        dependencies = {}
        
        # Scan requirements files
        req_dir = self.root_dir / "requirements"
        for req_file in req_dir.glob("*.txt"):
            deps = self._parse_requirements(req_file)
            dependencies[req_file.name] = deps
            
        # Scan pyproject.toml
        if (self.root_dir / "pyproject.toml").exists():
            pyproject_deps = self._parse_pyproject()
            dependencies["pyproject.toml"] = pyproject_deps
            
        return dependencies
    
    def generate_lock_file(self):
        """Generate comprehensive lock file with all dependencies"""
        all_deps = self.scan_dependencies()
        
        lock_data = {
            "generated_at": datetime.utcnow().isoformat(),
            "python_version": sys.version,
            "dependencies": {}
        }
        
        # Resolve and lock all dependencies
        for source, deps in all_deps.items():
            for dep in deps:
                resolved = self._resolve_dependency(dep)
                lock_data["dependencies"][dep.name] = {
                    "version": resolved.version,
                    "hash": resolved.hash,
                    "source": source,
                    "type": dep.type.value,
                    "transitive": resolved.transitive_deps
                }
                
        # Write lock file
        with open(self.lock_file, 'w') as f:
            json.dump(lock_data, f, indent=2)
```

#### JavaScript Dependencies

```typescript
// admin-ui/src/version-manager.ts
/**
 * Unified version management for JavaScript dependencies
 */

interface DependencyInfo {
  name: string;
  version: string;
  resolved: string;
  integrity: string;
  dependencies?: Record<string, string>;
  peerDependencies?: Record<string, string>;
  vulnerabilities?: VulnerabilityInfo[];
}

interface VulnerabilityInfo {
  severity: 'low' | 'moderate' | 'high' | 'critical';
  cve: string;
  description: string;
  fixedIn?: string;
}

export class JSVersionManager {
  private packageJson: any;
  private lockFile: any;
  
  constructor(private projectRoot: string) {
    this.loadPackageFiles();
  }
  
  async auditDependencies(): Promise<Map<string, DependencyInfo>> {
    const deps = new Map<string, DependencyInfo>();
    
    // Scan direct dependencies
    for (const [name, version] of Object.entries(this.packageJson.dependencies || {})) {
      const info = await this.analyzeDependency(name, version as string);
      deps.set(name, info);
    }
    
    // Scan dev dependencies
    for (const [name, version] of Object.entries(this.packageJson.devDependencies || {})) {
      const info = await this.analyzeDependency(name, version as string);
      info.type = 'dev';
      deps.set(name, info);
    }
    
    return deps;
  }
  
  async generateVersionReport(): Promise<VersionReport> {
    const dependencies = await this.auditDependencies();
    
    return {
      timestamp: new Date().toISOString(),
      projectName: this.packageJson.name,
      totalDependencies: dependencies.size,
      vulnerabilities: this.findVulnerabilities(dependencies),
      outdated: await this.findOutdated(dependencies),
      licenses: this.analyzeLicenses(dependencies)
    };
  }
}
```

### 3. Container Version Management

```yaml
# docker/versions.yaml
# Container image version specifications

base_images:
  python:
    tag: "3.10.12-slim-bookworm"
    digest: "sha256:abc123..."
    
  node:
    tag: "18.19.0-alpine3.18"
    digest: "sha256:def456..."
    
  nginx:
    tag: "1.25.3-alpine"
    digest: "sha256:ghi789..."

application_images:
  cherry_ai-api:
    version: "1.0.0"
    base: "python:3.10.12-slim-bookworm"
    
  admin-ui:
    version: "1.0.0"
    base: "node:18.19.0-alpine3.18"
    
  mcp-server:
    version: "1.0.0"
    base: "python:3.10.12-slim-bookworm"
```

### 4. Infrastructure Version Control

```typescript
// infrastructure/pulumi/version-control.ts
/**
 * Infrastructure version management for Pulumi
 */

import * as pulumi from "@pulumi/pulumi";
import * as vultr from "@pulumi/vultr";
import { VersionRegistry } from "./version-registry";

export class InfrastructureVersionManager {
  private registry: VersionRegistry;
  
  constructor() {
    this.registry = new VersionRegistry();
  }
  
  /**
   * Ensure all infrastructure components use approved versions
   */
  async validateVersions(): Promise<ValidationResult> {
    const results: ValidationResult = {
      valid: true,
      issues: []
    };
    
    // Check Vultr instance types
    const instances = await this.getVultrInstances();
    for (const instance of instances) {
      if (!this.registry.isApprovedOS(instance.os)) {
        results.issues.push({
          component: `instance-${instance.id}`,
          issue: `Unapproved OS version: ${instance.os}`,
          severity: 'high'
        });
      }
    }
    
    // Check container versions
    const containers = await this.getRunningContainers();
    for (const container of containers) {
      const approved = this.registry.getApprovedVersion(container.image);
      if (container.tag !== approved) {
        results.issues.push({
          component: container.name,
          issue: `Container using ${container.tag}, approved: ${approved}`,
          severity: 'medium'
        });
      }
    }
    
    results.valid = results.issues.length === 0;
    return results;
  }
}
```

### 5. Database Schema Versioning

```sql
-- migrations/version_control.sql
-- Database schema version tracking

CREATE SCHEMA IF NOT EXISTS version_control;

CREATE TABLE version_control.schema_versions (
    id SERIAL PRIMARY KEY,
    component VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_by VARCHAR(100),
    checksum VARCHAR(64),
    rollback_sql TEXT,
    metadata JSONB
);

CREATE TABLE version_control.migration_history (
    id SERIAL PRIMARY KEY,
    migration_id VARCHAR(100) UNIQUE NOT NULL,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INTEGER,
    status VARCHAR(20) CHECK (status IN ('pending', 'running', 'completed', 'failed', 'rolled_back')),
    error_message TEXT
);

-- Function to check version compatibility
CREATE OR REPLACE FUNCTION version_control.check_compatibility(
    p_component VARCHAR,
    p_required_version VARCHAR
) RETURNS BOOLEAN AS $$
DECLARE
    v_current_version VARCHAR;
BEGIN
    SELECT version INTO v_current_version
    FROM version_control.schema_versions
    WHERE component = p_component
    ORDER BY applied_at DESC
    LIMIT 1;
    
    -- Implement semantic version comparison
    RETURN version_control.compare_versions(v_current_version, p_required_version) >= 0;
END;
$$ LANGUAGE plpgsql;
```

### 6. API Version Management

```python
# core/api_versioning.py
"""API version management and compatibility layer"""

from typing import Dict, List, Optional, Callable
from datetime import datetime
from functools import wraps
import semantic_version

class APIVersion:
    """Represents an API version with compatibility rules"""
    
    def __init__(self, version: str, deprecated: bool = False, 
                 sunset_date: Optional[datetime] = None):
        self.version = semantic_version.Version(version)
        self.deprecated = deprecated
        self.sunset_date = sunset_date
        self.endpoints: Dict[str, EndpointVersion] = {}
        
    def add_endpoint(self, path: str, handler: Callable, 
                    changes: Optional[List[str]] = None):
        """Register an endpoint for this API version"""
        self.endpoints[path] = EndpointVersion(
            path=path,
            handler=handler,
            version=self.version,
            changes=changes or []
        )

class APIVersionManager:
    """Manages multiple API versions and routing"""
    
    def __init__(self):
        self.versions: Dict[str, APIVersion] = {}
        self.current_version = None
        
    def register_version(self, version: str, **kwargs) -> APIVersion:
        """Register a new API version"""
        api_version = APIVersion(version, **kwargs)
        self.versions[version] = api_version
        
        if not self.current_version or api_version.version > self.current_version.version:
            self.current_version = api_version
            
        return api_version
    
    def version_router(self, request_version: Optional[str] = None):
        """Route requests to appropriate version handler"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Determine version from request
                version = request_version or self._extract_version(kwargs.get('request'))
                
                if version not in self.versions:
                    raise ValueError(f"Unsupported API version: {version}")
                    
                api_version = self.versions[version]
                if api_version.deprecated:
                    # Add deprecation warning to response
                    kwargs['deprecation_warning'] = {
                        'deprecated': True,
                        'sunset_date': api_version.sunset_date.isoformat() if api_version.sunset_date else None,
                        'current_version': str(self.current_version.version)
                    }
                    
                return await func(*args, **kwargs)
            return wrapper
        return decorator
```

### 7. Automated Version Tracking

```python
# coordination/version_tracker.py
"""Automated version tracking and dependency graph generation"""

import asyncio
from typing import Dict, List, Set, Tuple
import networkx as nx
from dataclasses import dataclass
import aiofiles
import yaml

@dataclass
class ComponentVersion:
    name: str
    version: str
    type: str  # 'service', 'library', 'database', 'infrastructure'
    dependencies: List[Tuple[str, str]]  # [(name, version_constraint)]
    
class VersionTracker:
    """Track and analyze version dependencies across the system"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.components: Dict[str, ComponentVersion] = {}
        
    async def scan_system(self) -> Dict[str, ComponentVersion]:
        """Scan entire system for version information"""
        tasks = [
            self._scan_python_components(),
            self._scan_javascript_components(),
            self._scan_docker_components(),
            self._scan_database_schemas(),
            self._scan_infrastructure()
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Merge results
        for component_set in results:
            for name, component in component_set.items():
                self.components[name] = component
                self._add_to_graph(component)
                
        return self.components
    
    def _add_to_graph(self, component: ComponentVersion):
        """Add component and its dependencies to the graph"""
        self.graph.add_node(component.name, 
                           version=component.version,
                           type=component.type)
        
        for dep_name, dep_version in component.dependencies:
            self.graph.add_edge(component.name, dep_name, 
                              constraint=dep_version)
    
    def find_version_conflicts(self) -> List[Dict]:
        """Identify version conflicts in the dependency graph"""
        conflicts = []
        
        # Check each node's dependencies
        for node in self.graph.nodes():
            incoming = list(self.graph.in_edges(node, data=True))
            if len(incoming) > 1:
                # Multiple components depend on this one
                constraints = [edge[2]['constraint'] for edge in incoming]
                if not self._are_constraints_compatible(constraints):
                    conflicts.append({
                        'component': node,
                        'conflicting_constraints': constraints,
                        'dependent_components': [edge[0] for edge in incoming]
                    })
                    
        return conflicts
    
    def generate_dependency_report(self) -> Dict:
        """Generate comprehensive dependency report"""
        return {
            'total_components': len(self.components),
            'dependency_graph': {
                'nodes': list(self.graph.nodes(data=True)),
                'edges': list(self.graph.edges(data=True))
            },
            'version_conflicts': self.find_version_conflicts(),
            'update_recommendations': self._generate_update_recommendations(),
            'security_vulnerabilities': self._scan_vulnerabilities(),
            'license_compliance': self._check_license_compatibility()
        }
```

### 8. Version Compatibility Matrix

```yaml
# .compatibility-matrix.yaml
# Version compatibility specifications

compatibility_rules:
  python:
    "3.10":
      compatible_with:
        - fastapi: ">=0.100.0,<0.105.0"
        - pydantic: ">=2.0.0,<3.0.0"
        - sqlalchemy: ">=2.0.0,<3.0.0"
    "3.11":
      compatible_with:
        - fastapi: ">=0.103.0,<0.106.0"
        - pydantic: ">=2.0.0,<3.0.0"
        - sqlalchemy: ">=2.0.0,<3.0.0"
        
  postgresql:
    "14":
      compatible_with:
        - pgvector: ">=0.5.0,<0.6.0"
        - timescaledb: ">=2.11.0,<3.0.0"
    "15":
      compatible_with:
        - pgvector: ">=0.5.0,<0.7.0"
        - timescaledb: ">=2.13.0,<3.0.0"
        
  node:
    "18":
      compatible_with:
        - react: ">=18.0.0,<19.0.0"
        - typescript: ">=5.0.0,<6.0.0"
        - vite: ">=4.0.0,<6.0.0"
```

### 9. Automated Update Workflow

```yaml
# .github/workflows/version-update.yml
name: Automated Version Updates

on:
  schedule:
    - cron: '0 2 * * 1'  # Weekly on Monday at 2 AM
  workflow_dispatch:

jobs:
  scan-updates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          
      - name: Install version management tools
        run: |
          pip install -r requirements/version-management.txt
          npm install -g npm-check-updates
          
      - name: Scan for updates
        run: |
          python scripts/scan_versions.py --output version-report.json
          
      - name: Check security vulnerabilities
        run: |
          pip install safety
          safety check --json > security-report.json
          npm audit --json > npm-security-report.json
          
      - name: Generate update PR
        if: steps.scan.outputs.updates_available == 'true'
        run: |
          python scripts/generate_update_pr.py \
            --version-report version-report.json \
            --security-report security-report.json \
            --branch update/automated-versions-$(date +%Y%m%d)
```

### 10. Version Health Monitoring

```python
# monitoring/version_health.py
"""Monitor version health and compatibility across the system"""

from prometheus_client import Gauge, Counter, Histogram
import asyncio
from typing import Dict, List
import aiohttp

# Prometheus metrics
version_drift_gauge = Gauge('version_drift_score', 
                          'Version drift from recommended versions',
                          ['component', 'type'])
                          
vulnerability_count = Gauge('dependency_vulnerabilities',
                          'Number of known vulnerabilities',
                          ['severity', 'component'])
                          
update_lag_days = Gauge('version_update_lag_days',
                       'Days since last version update',
                       ['component'])

class VersionHealthMonitor:
    """Monitor and report on version health"""
    
    def __init__(self, registry_url: str):
        self.registry_url = registry_url
        self.components = {}
        
    async def check_version_health(self):
        """Perform comprehensive version health check"""
        
        # Scan all components
        components = await self.scan_all_components()
        
        # Check each component
        for component in components:
            # Calculate version drift
            drift = await self.calculate_version_drift(component)
            version_drift_gauge.labels(
                component=component.name,
                type=component.type
            ).set(drift)
            
            # Check vulnerabilities
            vulns = await self.check_vulnerabilities(component)
            for severity, count in vulns.items():
                vulnerability_count.labels(
                    severity=severity,
                    component=component.name
                ).set(count)
            
            # Check update lag
            lag = await self.calculate_update_lag(component)
            update_lag_days.labels(
                component=component.name
            ).set(lag)
            
    async def calculate_version_drift(self, component) -> float:
        """Calculate how far a component has drifted from recommended version"""
        current = component.version
        recommended = await self.get_recommended_version(component.name)
        
        # Semantic version comparison
        return self.version_distance(current, recommended)
        
    async def generate_health_report(self) -> Dict:
        """Generate comprehensive version health report"""
        await self.check_version_health()
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_health': self.calculate_overall_health(),
            'components': {
                name: {
                    'current_version': comp.version,
                    'recommended_version': await self.get_recommended_version(name),
                    'drift_score': await self.calculate_version_drift(comp),
                    'vulnerabilities': await self.check_vulnerabilities(comp),
                    'update_priority': self.calculate_update_priority(comp)
                }
                for name, comp in self.components.items()
            },
            'recommendations': self.generate_recommendations()
        }
```

## Implementation Plan

### Phase 1: Foundation (Week 1-2)
1. Implement central version registry (`.versions.yaml`)
2. Create version scanning tools for all package managers
3. Set up automated dependency tracking
4. Establish version compatibility matrix

### Phase 2: Automation (Week 3-4)
1. Implement automated version scanning workflows
2. Create vulnerability scanning integration
3. Set up automated update PR generation
4. Implement version conflict detection

### Phase 3: Monitoring (Week 5-6)
1. Deploy version health monitoring
2. Create Grafana dashboards for version metrics
3. Implement alerting for critical updates
4. Set up compliance reporting

### Phase 4: Integration (Week 7-8)
1. Integrate with CI/CD pipelines
2. Implement pre-deployment version validation
3. Create rollback mechanisms
4. Document version management procedures

## Success Metrics

1. **Version Currency**: 90% of dependencies within 2 minor versions of latest
2. **Security Response**: Critical vulnerabilities patched within 48 hours
3. **Compatibility**: Zero version conflicts in production
4. **Automation**: 95% of version updates automated
5. **Visibility**: Real-time version health dashboard available

## Governance Policies

### Version Update Policy
- **Patch versions**: Automatic updates after passing tests
- **Minor versions**: Automatic PR generation, manual approval
- **Major versions**: Requires architecture review and migration plan

### Security Policy
- **Critical vulnerabilities**: Immediate patching required
- **High vulnerabilities**: Patch within 7 days
- **Medium/Low**: Include in next scheduled update

### Deprecation Policy
- **Announcement**: 90 days before deprecation
- **Migration guide**: Required for all deprecations
- **Support period**: 6 months after deprecation

## Conclusion

This comprehensive version management architecture provides:
- Complete visibility into all system dependencies
- Automated tracking and updating mechanisms
- Security vulnerability management
- Performance impact analysis
- Compliance tracking
- Continuous health monitoring

The system is designed to scale with the cherry_ai platform while maintaining stability and security through automated governance and monitoring.