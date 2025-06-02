#!/usr/bin/env python3
"""
Version Manager - Core implementation for Orchestra platform version management
Provides centralized dependency tracking, security scanning, and update automation
"""

import json
import yaml
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
import hashlib
import subprocess
import re
from abc import ABC, abstractmethod

# Configure logging with structured format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComponentType(Enum):
    """Enumeration of component types in the system"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    DOCKER = "docker"
    DATABASE = "database"
    INFRASTRUCTURE = "infrastructure"
    API = "api"
    TOOL = "tool"

class Severity(Enum):
    """Security vulnerability severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class Version:
    """Represents a semantic version with metadata"""
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None
    
    @classmethod
    def parse(cls, version_string: str) -> 'Version':
        """Parse a version string into Version object"""
        # Remove common prefixes
        version_string = version_string.lstrip('v^~>=')
        
        # Handle pre-release and build metadata
        parts = version_string.split('-', 1)
        main_version = parts[0]
        prerelease = parts[1] if len(parts) > 1 else None
        
        # Split build metadata
        if prerelease and '+' in prerelease:
            prerelease, build = prerelease.split('+', 1)
        else:
            build = None
            
        # Parse main version numbers
        version_parts = main_version.split('.')
        major = int(version_parts[0]) if len(version_parts) > 0 else 0
        minor = int(version_parts[1]) if len(version_parts) > 1 else 0
        patch = int(version_parts[2]) if len(version_parts) > 2 else 0
        
        return cls(major, minor, patch, prerelease, build)
    
    def __str__(self) -> str:
        """String representation of version"""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version
    
    def __lt__(self, other: 'Version') -> bool:
        """Compare versions for ordering"""
        if not isinstance(other, Version):
            return NotImplemented
            
        # Compare main version numbers
        if (self.major, self.minor, self.patch) != (other.major, other.minor, other.patch):
            return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
            
        # Pre-release versions are less than normal versions
        if self.prerelease and not other.prerelease:
            return True
        if not self.prerelease and other.prerelease:
            return False
            
        # Compare pre-release versions
        if self.prerelease and other.prerelease:
            return self.prerelease < other.prerelease
            
        return False

@dataclass
class Vulnerability:
    """Security vulnerability information"""
    id: str
    severity: Severity
    description: str
    affected_versions: str
    fixed_version: Optional[str] = None
    cve: Optional[str] = None
    published_date: Optional[datetime] = None
    
    def affects_version(self, version: Version) -> bool:
        """Check if vulnerability affects given version"""
        # Simplified check - would need proper version range parsing
        return True  # Placeholder implementation

@dataclass
class Dependency:
    """Represents a dependency with full metadata"""
    name: str
    current_version: Version
    latest_version: Optional[Version] = None
    constraint: Optional[str] = None
    type: ComponentType = ComponentType.PYTHON
    source_file: Optional[str] = None
    dependencies: Dict[str, str] = field(default_factory=dict)
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    license: Optional[str] = None
    last_updated: Optional[datetime] = None
    update_priority: int = 0
    
    def calculate_update_priority(self) -> None:
        """Calculate update priority based on multiple factors"""
        priority = 0
        
        # Critical vulnerabilities get highest priority
        critical_vulns = sum(1 for v in self.vulnerabilities if v.severity == Severity.CRITICAL)
        high_vulns = sum(1 for v in self.vulnerabilities if v.severity == Severity.HIGH)
        priority += critical_vulns * 4 + high_vulns * 2
        
        # Version age factor
        if self.current_version and self.latest_version:
            major_diff = self.latest_version.major - self.current_version.major
            minor_diff = self.latest_version.minor - self.current_version.minor
            priority += min(major_diff * 2 + minor_diff, 3)
        
        # Cap priority at 10
        self.update_priority = min(priority, 10)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'current_version': str(self.current_version),
            'latest_version': str(self.latest_version) if self.latest_version else None,
            'constraint': self.constraint,
            'type': self.type.value,
            'source_file': self.source_file,
            'vulnerabilities': len(self.vulnerabilities),
            'update_priority': self.update_priority,
            'license': self.license,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

class DependencyScanner(ABC):
    """Abstract base class for dependency scanners"""
    
    @abstractmethod
    async def scan(self, path: Path) -> Dict[str, Dependency]:
        """Scan for dependencies at given path"""
        pass
    
    @abstractmethod
    def get_component_type(self) -> ComponentType:
        """Get the component type this scanner handles"""
        pass

class PythonScanner(DependencyScanner):
    """Scanner for Python dependencies"""
    
    def get_component_type(self) -> ComponentType:
        return ComponentType.PYTHON
    
    async def scan(self, path: Path) -> Dict[str, Dependency]:
        """Scan Python dependencies from requirements files"""
        dependencies = {}
        
        # Scan requirements directory
        req_dir = path / "requirements"
        if req_dir.exists():
            for req_file in req_dir.glob("*.txt"):
                deps = await self._scan_requirements_file(req_file)
                dependencies.update(deps)
        
        # Scan pyproject.toml
        pyproject_path = path / "pyproject.toml"
        if pyproject_path.exists():
            deps = await self._scan_pyproject(pyproject_path)
            dependencies.update(deps)
            
        return dependencies
    
    async def _scan_requirements_file(self, file_path: Path) -> Dict[str, Dependency]:
        """Parse requirements.txt file"""
        dependencies = {}
        
        try:
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse requirement line
                    dep = self._parse_requirement(line, file_path.name, line_num)
                    if dep:
                        dependencies[dep.name] = dep
                        
        except Exception as e:
            logger.error(f"Error scanning {file_path}: {e}")
            
        return dependencies
    
    def _parse_requirement(self, line: str, source_file: str, line_num: int) -> Optional[Dependency]:
        """Parse a single requirement line"""
        # Regex patterns for different requirement formats
        patterns = [
            r'^([a-zA-Z0-9\-_\[\]]+)==([^\s;]+)',  # package==version
            r'^([a-zA-Z0-9\-_\[\]]+)>=([^\s,;]+)',  # package>=version
            r'^([a-zA-Z0-9\-_\[\]]+)~=([^\s;]+)',   # package~=version
            r'^([a-zA-Z0-9\-_\[\]]+)<([^\s;]+)',    # package<version
            r'^([a-zA-Z0-9\-_\[\]]+)>([^\s;]+)',    # package>version
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                name = match.group(1).split('[')[0]  # Remove extras
                version_str = match.group(2)
                
                try:
                    version = Version.parse(version_str)
                    return Dependency(
                        name=name,
                        current_version=version,
                        constraint=line,
                        type=ComponentType.PYTHON,
                        source_file=f"{source_file}:{line_num}",
                        last_updated=datetime.now(timezone.utc)
                    )
                except Exception as e:
                    logger.warning(f"Failed to parse version '{version_str}' for {name}: {e}")
                    
        # Handle packages without version constraints
        if not any(op in line for op in ['==', '>=', '<=', '~=', '!=', '<', '>']):
            return Dependency(
                name=line.strip(),
                current_version=Version(0, 0, 0),
                constraint="*",
                type=ComponentType.PYTHON,
                source_file=f"{source_file}:{line_num}",
                last_updated=datetime.now(timezone.utc)
            )
            
        return None
    
    async def _scan_pyproject(self, file_path: Path) -> Dict[str, Dependency]:
        """Parse pyproject.toml file"""
        dependencies = {}
        
        try:
            with open(file_path, 'r') as f:
                # Simple parsing - would use toml library in production
                content = f.read()
                # Extract dependencies section
                # This is simplified - real implementation would use proper TOML parser
                
        except Exception as e:
            logger.error(f"Error scanning {file_path}: {e}")
            
        return dependencies

class JavaScriptScanner(DependencyScanner):
    """Scanner for JavaScript/npm dependencies"""
    
    def get_component_type(self) -> ComponentType:
        return ComponentType.JAVASCRIPT
    
    async def scan(self, path: Path) -> Dict[str, Dependency]:
        """Scan JavaScript dependencies from package.json files"""
        dependencies = {}
        
        # Find all package.json files
        for package_json in path.glob("**/package.json"):
            # Skip node_modules
            if "node_modules" in str(package_json):
                continue
                
            deps = await self._scan_package_json(package_json)
            dependencies.update(deps)
            
        return dependencies
    
    async def _scan_package_json(self, file_path: Path) -> Dict[str, Dependency]:
        """Parse package.json file"""
        dependencies = {}
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Process both dependencies and devDependencies
            for dep_type in ['dependencies', 'devDependencies']:
                for name, version_spec in data.get(dep_type, {}).items():
                    # Clean version specification
                    version_str = version_spec.lstrip('^~>=')
                    
                    try:
                        version = Version.parse(version_str)
                        dep = Dependency(
                            name=name,
                            current_version=version,
                            constraint=version_spec,
                            type=ComponentType.JAVASCRIPT,
                            source_file=str(file_path.relative_to(file_path.parent.parent)),
                            last_updated=datetime.fromtimestamp(file_path.stat().st_mtime, timezone.utc)
                        )
                        dependencies[f"npm:{name}"] = dep
                    except Exception as e:
                        logger.warning(f"Failed to parse version '{version_str}' for {name}: {e}")
                        
        except Exception as e:
            logger.error(f"Error scanning {file_path}: {e}")
            
        return dependencies

class DockerScanner(DependencyScanner):
    """Scanner for Docker images"""
    
    def get_component_type(self) -> ComponentType:
        return ComponentType.DOCKER
    
    async def scan(self, path: Path) -> Dict[str, Dependency]:
        """Scan Docker images from Dockerfiles"""
        dependencies = {}
        
        # Find all Dockerfiles
        for dockerfile in path.glob("**/Dockerfile*"):
            deps = await self._scan_dockerfile(dockerfile)
            dependencies.update(deps)
            
        return dependencies
    
    async def _scan_dockerfile(self, file_path: Path) -> Dict[str, Dependency]:
        """Parse Dockerfile for base images"""
        dependencies = {}
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Extract FROM statements
            from_pattern = r'FROM\s+([^\s]+)(?:\s+AS\s+\w+)?'
            matches = re.findall(from_pattern, content, re.MULTILINE)
            
            for image_spec in matches:
                # Parse image:tag format
                if ':' in image_spec:
                    image, tag = image_spec.rsplit(':', 1)
                else:
                    image, tag = image_spec, 'latest'
                
                # Skip build stage references
                if image.startswith('--'):
                    continue
                    
                try:
                    # Docker tags aren't always semver, so handle gracefully
                    if re.match(r'^\d+\.\d+', tag):
                        version = Version.parse(tag)
                    else:
                        # Use 0.0.0 for non-semver tags
                        version = Version(0, 0, 0, prerelease=tag)
                        
                    dep = Dependency(
                        name=image,
                        current_version=version,
                        constraint=image_spec,
                        type=ComponentType.DOCKER,
                        source_file=str(file_path.relative_to(path)),
                        last_updated=datetime.fromtimestamp(file_path.stat().st_mtime, timezone.utc)
                    )
                    dependencies[f"docker:{image}"] = dep
                except Exception as e:
                    logger.warning(f"Failed to parse Docker tag '{tag}' for {image}: {e}")
                    
        except Exception as e:
            logger.error(f"Error scanning {file_path}: {e}")
            
        return dependencies

class VersionRegistry:
    """Central registry for all version information"""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.registry_path = root_path / ".versions.yaml"
        self.lock_path = root_path / ".versions.lock"
        self.dependencies: Dict[str, Dependency] = {}
        self.scanners: List[DependencyScanner] = [
            PythonScanner(),
            JavaScriptScanner(),
            DockerScanner()
        ]
    
    async def scan_all(self) -> None:
        """Scan entire codebase for dependencies"""
        logger.info("Starting comprehensive dependency scan...")
        
        # Run all scanners in parallel
        tasks = [scanner.scan(self.root_path) for scanner in self.scanners]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Merge results
        for result in results:
            if isinstance(result, dict):
                self.dependencies.update(result)
            elif isinstance(result, Exception):
                logger.error(f"Scanner error: {result}")
        
        # Calculate update priorities
        for dep in self.dependencies.values():
            dep.calculate_update_priority()
            
        logger.info(f"Scan complete. Found {len(self.dependencies)} dependencies.")
    
    async def check_vulnerabilities(self) -> None:
        """Check all dependencies for known vulnerabilities"""
        logger.info("Checking for security vulnerabilities...")
        
        # This would integrate with real vulnerability databases
        # For now, simulate with some example vulnerabilities
        vulnerable_packages = {
            'requests': ['2.31.0', 'CVE-2023-32681'],
            'cryptography': ['41.0.6', 'CVE-2023-49083'],
            'aiohttp': ['3.9.0', 'CVE-2023-49081']
        }
        
        for dep_key, dep in self.dependencies.items():
            if dep.name in vulnerable_packages:
                fixed_version, cve = vulnerable_packages[dep.name]
                
                # Check if current version is vulnerable
                try:
                    fixed = Version.parse(fixed_version)
                    if dep.current_version < fixed:
                        vuln = Vulnerability(
                            id=f"{dep.name}-{cve}",
                            severity=Severity.HIGH,
                            description=f"Known vulnerability in {dep.name}",
                            affected_versions=f"< {fixed_version}",
                            fixed_version=fixed_version,
                            cve=cve,
                            published_date=datetime.now(timezone.utc)
                        )
                        dep.vulnerabilities.append(vuln)
                        dep.calculate_update_priority()
                except Exception as e:
                    logger.warning(f"Error checking vulnerability for {dep.name}: {e}")
    
    def save_registry(self) -> None:
        """Save version registry to file"""
        registry_data = {
            'version': '1.0.0',
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'total_dependencies': len(self.dependencies),
            'dependencies': {}
        }
        
        # Group by component type
        for component_type in ComponentType:
            type_deps = {
                k: v.to_dict() 
                for k, v in self.dependencies.items() 
                if v.type == component_type
            }
            if type_deps:
                registry_data['dependencies'][component_type.value] = type_deps
        
        # Write registry file
        with open(self.registry_path, 'w') as f:
            yaml.dump(registry_data, f, default_flow_style=False, sort_keys=False)
            
        logger.info(f"Registry saved to {self.registry_path}")
    
    def generate_lock_file(self) -> None:
        """Generate lock file with exact versions and hashes"""
        lock_data = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'dependencies': {}
        }
        
        for key, dep in sorted(self.dependencies.items()):
            # Generate hash for dependency
            dep_string = f"{dep.name}:{dep.current_version}:{dep.constraint or ''}"
            dep_hash = hashlib.sha256(dep_string.encode()).hexdigest()[:16]
            
            lock_data['dependencies'][key] = {
                'name': dep.name,
                'version': str(dep.current_version),
                'constraint': dep.constraint,
                'hash': dep_hash,
                'source': dep.source_file,
                'type': dep.type.value
            }
        
        # Write lock file
        with open(self.lock_path, 'w') as f:
            json.dump(lock_data, f, indent=2, sort_keys=True)
            
        logger.info(f"Lock file generated at {self.lock_path}")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive version report"""
        # Calculate statistics
        total_deps = len(self.dependencies)
        vulnerable_deps = sum(1 for d in self.dependencies.values() if d.vulnerabilities)
        high_priority_deps = sum(1 for d in self.dependencies.values() if d.update_priority >= 7)
        
        # Group by type
        by_type = {}
        for dep in self.dependencies.values():
            type_name = dep.type.value
            if type_name not in by_type:
                by_type[type_name] = []
            by_type[type_name].append(dep)
        
        # Find outdated dependencies
        outdated = [d for d in self.dependencies.values() if d.update_priority > 0]
        outdated.sort(key=lambda x: x.update_priority, reverse=True)
        
        report = {
            'summary': {
                'total_dependencies': total_deps,
                'vulnerable_dependencies': vulnerable_deps,
                'high_priority_updates': high_priority_deps,
                'scan_timestamp': datetime.now(timezone.utc).isoformat()
            },
            'by_type': {
                type_name: {
                    'count': len(deps),
                    'vulnerable': sum(1 for d in deps if d.vulnerabilities),
                    'outdated': sum(1 for d in deps if d.update_priority > 0)
                }
                for type_name, deps in by_type.items()
            },
            'critical_updates': [
                {
                    'name': d.name,
                    'current': str(d.current_version),
                    'priority': d.update_priority,
                    'vulnerabilities': len(d.vulnerabilities),
                    'source': d.source_file
                }
                for d in outdated[:10]  # Top 10 priorities
            ],
            'recommendations': self._generate_recommendations(vulnerable_deps, high_priority_deps)
        }
        
        return report
    
    def _generate_recommendations(self, vulnerable_count: int, high_priority_count: int) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if vulnerable_count > 0:
            recommendations.append(
                f"CRITICAL: Address {vulnerable_count} dependencies with known vulnerabilities immediately"
            )
        
        if high_priority_count > 0:
            recommendations.append(
                f"HIGH: Update {high_priority_count} dependencies with priority >= 7"
            )
        
        if not self.lock_path.exists():
            recommendations.append(
                "Generate lock file for reproducible builds: python version_manager.py lock"
            )
        
        # Check for mixed package managers
        js_deps = [d for d in self.dependencies.values() if d.type == ComponentType.JAVASCRIPT]
        if js_deps:
            sources = set(d.source_file for d in js_deps if d.source_file)
            if any('package-lock.json' in s for s in sources) and any('pnpm-lock.yaml' in s for s in sources):
                recommendations.append(
                    "Standardize on single JavaScript package manager (npm or pnpm)"
                )
        
        if not recommendations:
            recommendations.append("All dependencies appear to be in good health")
        
        return recommendations

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Orchestra Version Manager - Comprehensive dependency management"
    )
    parser.add_argument(
        'command',
        choices=['scan', 'report', 'lock', 'check', 'init'],
        help='Command to execute'
    )
    parser.add_argument(
        '--root',
        default='.',
        help='Project root directory (default: current directory)'
    )
    parser.add_argument(
        '--output',
        help='Output file for reports (JSON format)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize registry
    root_path = Path(args.root).resolve()
    registry = VersionRegistry(root_path)
    
    try:
        if args.command == 'init':
            # Initialize version management
            logger.info("Initializing version management system...")
            await registry.scan_all()
            await registry.check_vulnerabilities()
            registry.save_registry()
            registry.generate_lock_file()
            logger.info("Version management initialized successfully")
            
        elif args.command == 'scan':
            # Scan dependencies
            await registry.scan_all()
            logger.info(f"Found {len(registry.dependencies)} dependencies")
            
            # Show summary
            by_type = {}
            for dep in registry.dependencies.values():
                by_type[dep.type.value] = by_type.get(dep.type.value, 0) + 1
            
            for type_name, count in sorted(by_type.items()):
                logger.info(f"  {type_name}: {count}")
                
        elif args.command == 'check':
            # Check for vulnerabilities
            await registry.scan_all()
            await registry.check_vulnerabilities()
            
            vulnerable = [d for d in registry.dependencies.values() if d.vulnerabilities]
            if vulnerable:
                logger.warning(f"Found {len(vulnerable)} vulnerable dependencies:")
                for dep in sorted(vulnerable, key=lambda x: x.update_priority, reverse=True)[:10]:
                    logger.warning(f"  {dep.name} {dep.current_version} - {len(dep.vulnerabilities)} vulnerabilities")
            else:
                logger.info("No known vulnerabilities found")
                
        elif args.command == 'report':
            # Generate report
            await registry.scan_all()
            await registry.check_vulnerabilities()
            report = registry.generate_report()
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(report, f, indent=2)
                logger.info(f"Report saved to {args.output}")
            else:
                print(json.dumps(report, indent=2))
                
        elif args.command == 'lock':
            # Generate lock file
            await registry.scan_all()
            registry.generate_lock_file()
            logger.info("Lock file generated successfully")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())