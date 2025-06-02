#!/usr/bin/env python3
"""
Version Management Implementation Tools
Comprehensive tooling for version tracking, analysis, and management
"""

import json
import yaml
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
import semantic_version
import networkx as nx
import aiohttp
import hashlib
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComponentType(Enum):
    """Types of components in the system"""
    PYTHON_PACKAGE = "python_package"
    NPM_PACKAGE = "npm_package"
    DOCKER_IMAGE = "docker_image"
    DATABASE_SCHEMA = "database_schema"
    API_VERSION = "api_version"
    INFRASTRUCTURE = "infrastructure"
    RUNTIME = "runtime"
    TOOL = "tool"

@dataclass
class Version:
    """Represents a version with metadata"""
    version: str
    release_date: Optional[datetime] = None
    deprecated: bool = False
    sunset_date: Optional[datetime] = None
    security_fixes: List[str] = field(default_factory=list)
    breaking_changes: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate and parse version"""
        try:
            self.semver = semantic_version.Version(self.version)
        except:
            # Handle non-semver versions
            self.semver = None
            
    def is_compatible_with(self, constraint: str) -> bool:
        """Check if version satisfies constraint"""
        if not self.semver:
            return True  # Can't validate non-semver
        
        try:
            spec = semantic_version.Spec(constraint)
            return self.semver in spec
        except:
            return False

@dataclass
class Component:
    """Represents a versioned component"""
    name: str
    type: ComponentType
    current_version: Version
    available_versions: List[Version] = field(default_factory=list)
    dependencies: Dict[str, str] = field(default_factory=dict)
    vulnerabilities: List[Dict] = field(default_factory=list)
    last_updated: Optional[datetime] = None
    update_priority: int = 0  # 0-10, higher is more urgent
    
    def calculate_update_priority(self):
        """Calculate update priority based on various factors"""
        priority = 0
        
        # Security vulnerabilities
        critical_vulns = sum(1 for v in self.vulnerabilities if v.get('severity') == 'critical')
        high_vulns = sum(1 for v in self.vulnerabilities if v.get('severity') == 'high')
        priority += critical_vulns * 3 + high_vulns * 2
        
        # Version age
        if self.current_version.semver and self.available_versions:
            latest = max(v.semver for v in self.available_versions if v.semver)
            if latest > self.current_version.semver:
                major_diff = latest.major - self.current_version.semver.major
                minor_diff = latest.minor - self.current_version.semver.minor
                priority += major_diff * 2 + minor_diff
                
        # Deprecation
        if self.current_version.deprecated:
            priority += 3
            
        self.update_priority = min(priority, 10)

class VersionScanner:
    """Scans the codebase for all versioned components"""
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.components: Dict[str, Component] = {}
        
    async def scan_all(self) -> Dict[str, Component]:
        """Perform comprehensive version scan"""
        tasks = [
            self.scan_python_packages(),
            self.scan_npm_packages(),
            self.scan_docker_images(),
            self.scan_database_schemas(),
            self.scan_infrastructure()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, dict):
                self.components.update(result)
            elif isinstance(result, Exception):
                logger.error(f"Scan error: {result}")
                
        return self.components
    
    async def scan_python_packages(self) -> Dict[str, Component]:
        """Scan Python dependencies"""
        components = {}
        
        # Scan requirements files
        req_dir = self.root_dir / "requirements"
        if req_dir.exists():
            for req_file in req_dir.glob("*.txt"):
                with open(req_file) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            name, version = self._parse_requirement(line)
                            if name:
                                components[f"python:{name}"] = Component(
                                    name=name,
                                    type=ComponentType.PYTHON_PACKAGE,
                                    current_version=Version(version),
                                    last_updated=datetime.fromtimestamp(req_file.stat().st_mtime)
                                )
        
        # Scan pyproject.toml
        pyproject_path = self.root_dir / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path) as f:
                data = yaml.safe_load(f)  # toml would be better but using yaml for simplicity
                # Parse dependencies from pyproject.toml
                
        return components
    
    async def scan_npm_packages(self) -> Dict[str, Component]:
        """Scan JavaScript/npm dependencies"""
        components = {}
        
        # Check admin-ui
        package_json = self.root_dir / "admin-ui" / "package.json"
        if package_json.exists():
            with open(package_json) as f:
                data = json.load(f)
                
            for dep_type in ["dependencies", "devDependencies"]:
                for name, version in data.get(dep_type, {}).items():
                    components[f"npm:{name}"] = Component(
                        name=name,
                        type=ComponentType.NPM_PACKAGE,
                        current_version=Version(version.lstrip("^~")),
                        last_updated=datetime.fromtimestamp(package_json.stat().st_mtime)
                    )
                    
        return components
    
    async def scan_docker_images(self) -> Dict[str, Component]:
        """Scan Docker images from Dockerfiles"""
        components = {}
        
        for dockerfile in self.root_dir.glob("**/Dockerfile*"):
            with open(dockerfile) as f:
                content = f.read()
                
            # Extract FROM statements
            import re
            from_pattern = r'FROM\s+([^\s]+)'
            matches = re.findall(from_pattern, content)
            
            for image in matches:
                if ":" in image:
                    name, tag = image.rsplit(":", 1)
                else:
                    name, tag = image, "latest"
                    
                components[f"docker:{name}"] = Component(
                    name=name,
                    type=ComponentType.DOCKER_IMAGE,
                    current_version=Version(tag),
                    last_updated=datetime.fromtimestamp(dockerfile.stat().st_mtime)
                )
                
        return components
    
    async def scan_database_schemas(self) -> Dict[str, Component]:
        """Scan database schema versions"""
        components = {}
        
        # Check migration files
        migrations_dir = self.root_dir / "migrations"
        if migrations_dir.exists():
            versions = []
            for migration in migrations_dir.glob("*.sql"):
                # Extract version from filename (e.g., 001_initial.sql)
                match = re.match(r'(\d+)_.*\.sql', migration.name)
                if match:
                    versions.append(match.group(1))
                    
            if versions:
                latest_version = max(versions)
                components["db:postgresql"] = Component(
                    name="postgresql_schema",
                    type=ComponentType.DATABASE_SCHEMA,
                    current_version=Version(f"0.0.{latest_version}")
                )
                
        return components
    
    async def scan_infrastructure(self) -> Dict[str, Component]:
        """Scan infrastructure versions (Pulumi, etc.)"""
        components = {}
        
        # Check Pulumi files
        for pulumi_yaml in self.root_dir.glob("**/Pulumi.yaml"):
            with open(pulumi_yaml) as f:
                data = yaml.safe_load(f)
                
            runtime = data.get("runtime", {})
            if isinstance(runtime, dict):
                name = runtime.get("name", "unknown")
                version = runtime.get("version", "unknown")
                
                components[f"infra:{pulumi_yaml.parent.name}"] = Component(
                    name=f"pulumi-{pulumi_yaml.parent.name}",
                    type=ComponentType.INFRASTRUCTURE,
                    current_version=Version(version)
                )
                
        return components
    
    def _parse_requirement(self, line: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse a requirements.txt line"""
        import re
        
        # Handle different requirement formats
        patterns = [
            r'^([a-zA-Z0-9\-_]+)==([^\s]+)',  # exact version
            r'^([a-zA-Z0-9\-_]+)>=([^\s,]+)',  # minimum version
            r'^([a-zA-Z0-9\-_]+)~=([^\s]+)',   # compatible version
            r'^([a-zA-Z0-9\-_]+)\[.*\]==([^\s]+)',  # with extras
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                return match.group(1), match.group(2)
                
        # Handle package without version
        if not any(op in line for op in ['==', '>=', '<=', '~=', '!=']):
            return line.strip(), "unknown"
            
        return None, None

class DependencyGraph:
    """Manages dependency relationships between components"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        
    def add_component(self, component: Component):
        """Add component to dependency graph"""
        self.graph.add_node(
            component.name,
            type=component.type.value,
            version=component.current_version.version,
            component=component
        )
        
        # Add dependencies
        for dep_name, dep_version in component.dependencies.items():
            self.graph.add_edge(
                component.name,
                dep_name,
                constraint=dep_version
            )
            
    def find_conflicts(self) -> List[Dict]:
        """Find version conflicts in the dependency graph"""
        conflicts = []
        
        # Check each node that has multiple incoming edges
        for node in self.graph.nodes():
            in_edges = list(self.graph.in_edges(node, data=True))
            if len(in_edges) > 1:
                constraints = [edge[2].get('constraint', '*') for edge in in_edges]
                
                # Check if constraints are compatible
                if not self._are_constraints_compatible(constraints):
                    conflicts.append({
                        'component': node,
                        'constraints': constraints,
                        'dependents': [edge[0] for edge in in_edges]
                    })
                    
        return conflicts
    
    def _are_constraints_compatible(self, constraints: List[str]) -> bool:
        """Check if version constraints are compatible"""
        try:
            specs = [semantic_version.Spec(c) for c in constraints if c != '*']
            if not specs:
                return True
                
            # Find intersection of all specs
            # This is a simplified check
            return True  # Would need proper implementation
        except:
            return False
            
    def get_update_order(self) -> List[str]:
        """Get safe update order respecting dependencies"""
        try:
            return list(nx.topological_sort(self.graph))
        except nx.NetworkXUnfeasible:
            # Graph has cycles
            logger.warning("Dependency graph has cycles")
            return list(self.graph.nodes())

class VersionManager:
    """Main version management orchestrator"""
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.scanner = VersionScanner(root_dir)
        self.graph = DependencyGraph()
        self.registry_path = root_dir / ".versions.yaml"
        self.lock_path = root_dir / ".versions.lock"
        
    async def initialize(self):
        """Initialize version management system"""
        # Scan all components
        components = await self.scanner.scan_all()
        
        # Build dependency graph
        for component in components.values():
            self.graph.add_component(component)
            
        # Calculate priorities
        for component in components.values():
            component.calculate_update_priority()
            
        # Save to registry
        await self.save_registry(components)
        
    async def save_registry(self, components: Dict[str, Component]):
        """Save version registry"""
        registry = {
            'version': '1.0.0',
            'generated_at': datetime.utcnow().isoformat(),
            'components': {}
        }
        
        for key, component in components.items():
            registry['components'][key] = {
                'name': component.name,
                'type': component.type.value,
                'current_version': component.current_version.version,
                'update_priority': component.update_priority,
                'vulnerabilities': len(component.vulnerabilities),
                'last_updated': component.last_updated.isoformat() if component.last_updated else None
            }
            
        with open(self.registry_path, 'w') as f:
            yaml.dump(registry, f, default_flow_style=False)
            
    async def generate_lock_file(self):
        """Generate comprehensive lock file"""
        components = await self.scanner.scan_all()
        
        lock_data = {
            'generated_at': datetime.utcnow().isoformat(),
            'components': {}
        }
        
        for key, component in components.items():
            # Calculate hash for component
            component_str = f"{component.name}:{component.current_version.version}"
            component_hash = hashlib.sha256(component_str.encode()).hexdigest()
            
            lock_data['components'][key] = {
                'version': component.current_version.version,
                'hash': component_hash,
                'dependencies': component.dependencies
            }
            
        with open(self.lock_path, 'w') as f:
            json.dump(lock_data, f, indent=2)
            
    async def check_updates(self) -> Dict[str, Dict]:
        """Check for available updates"""
        components = await self.scanner.scan_all()
        updates = {}
        
        for key, component in components.items():
            # This would normally check against package registries
            # For now, we'll simulate
            if component.update_priority > 0:
                updates[key] = {
                    'current': component.current_version.version,
                    'priority': component.update_priority,
                    'type': component.type.value
                }
                
        return updates
    
    async def generate_report(self) -> Dict:
        """Generate comprehensive version report"""
        components = await self.scanner.scan_all()
        conflicts = self.graph.find_conflicts()
        updates = await self.check_updates()
        
        return {
            'summary': {
                'total_components': len(components),
                'components_needing_update': len(updates),
                'version_conflicts': len(conflicts),
                'critical_updates': sum(1 for u in updates.values() if u['priority'] >= 7)
            },
            'components_by_type': self._group_by_type(components),
            'conflicts': conflicts,
            'updates': updates,
            'recommendations': self._generate_recommendations(components, conflicts, updates)
        }
    
    def _group_by_type(self, components: Dict[str, Component]) -> Dict:
        """Group components by type"""
        grouped = {}
        for component in components.values():
            type_name = component.type.value
            if type_name not in grouped:
                grouped[type_name] = []
            grouped[type_name].append({
                'name': component.name,
                'version': component.current_version.version,
                'priority': component.update_priority
            })
        return grouped
    
    def _generate_recommendations(self, components, conflicts, updates) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Critical updates
        critical = [k for k, v in updates.items() if v['priority'] >= 7]
        if critical:
            recommendations.append(f"CRITICAL: Update {len(critical)} components immediately: {', '.join(critical[:3])}")
            
        # Version conflicts
        if conflicts:
            recommendations.append(f"Resolve {len(conflicts)} version conflicts before updating")
            
        # Outdated components
        outdated = [c for c in components.values() if c.update_priority >= 5]
        if outdated:
            recommendations.append(f"Plan updates for {len(outdated)} outdated components")
            
        # Lock file
        if not self.lock_path.exists():
            recommendations.append("Generate version lock file for reproducible builds")
            
        return recommendations

async def main():
    """Main entry point for version management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Orchestra Version Management")
    parser.add_argument('command', choices=['scan', 'report', 'lock', 'update', 'init'])
    parser.add_argument('--root', default='.', help='Project root directory')
    parser.add_argument('--output', help='Output file for reports')
    
    args = parser.parse_args()
    
    root_dir = Path(args.root).resolve()
    manager = VersionManager(root_dir)
    
    if args.command == 'init':
        await manager.initialize()
        print("Version management initialized")
        
    elif args.command == 'scan':
        components = await manager.scanner.scan_all()
        print(f"Scanned {len(components)} components")
        for key, comp in list(components.items())[:10]:
            print(f"  {comp.name}: {comp.current_version.version}")
            
    elif args.command == 'report':
        report = await manager.generate_report()
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
        else:
            print(json.dumps(report, indent=2))
            
    elif args.command == 'lock':
        await manager.generate_lock_file()
        print(f"Lock file generated: {manager.lock_path}")
        
    elif args.command == 'update':
        updates = await manager.check_updates()
        print(f"Found {len(updates)} components needing updates")
        for key, info in list(updates.items())[:10]:
            print(f"  {key}: {info['current']} (priority: {info['priority']})")

if __name__ == "__main__":
    asyncio.run(main())