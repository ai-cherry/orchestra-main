#!/usr/bin/env python3
"""
Orchestra AI Port Manager
Dynamically manages port allocation and prevents conflicts
"""

import socket
import json
import os
import subprocess
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

class ServiceCategory(Enum):
    """Service categories for port range allocation"""
    SYSTEM = (1000, 1999)
    DEVELOPMENT = (2000, 2999)
    FRONTEND = (3000, 3999)
    MICROSERVICES = (4000, 4999)
    DATABASE = (5000, 5999)
    CACHE = (6000, 6999)
    CUSTOM = (7000, 7999)
    API = (8000, 8999)
    MONITORING = (9000, 9999)
    DYNAMIC = (10000, 65535)

@dataclass
class ServicePort:
    """Port configuration for a service"""
    name: str
    default_port: int
    category: ServiceCategory
    protocol: str = "tcp"
    alternatives: List[int] = None
    description: str = ""

class PortManager:
    """Manages port allocation for Orchestra AI services"""
    
    # Default service port configurations
    DEFAULT_SERVICES = [
        ServicePort("postgres", 5432, ServiceCategory.DATABASE, 
                   alternatives=[5433, 5434], 
                   description="PostgreSQL Database"),
        ServicePort("redis", 6379, ServiceCategory.CACHE, 
                   alternatives=[6380, 6381], 
                   description="Redis Cache"),
        ServicePort("weaviate", 8080, ServiceCategory.API, 
                   alternatives=[8081, 8082], 
                   description="Weaviate Vector DB"),
        ServicePort("api", 8000, ServiceCategory.API, 
                   alternatives=[8010, 8020], 
                   description="Main API Server"),
        ServicePort("mcp_conductor", 8002, ServiceCategory.API, 
                   description="MCP Conductor Service"),
        ServicePort("mcp_memory", 8003, ServiceCategory.API, 
                   description="MCP Memory Service"),
        ServicePort("mcp_tools", 8006, ServiceCategory.API, 
                   description="MCP Tools Service"),
        ServicePort("mcp_weaviate", 8001, ServiceCategory.API, 
                   description="MCP Weaviate Bridge"),
        ServicePort("admin_ui", 3000, ServiceCategory.FRONTEND, 
                   alternatives=[3001, 3002], 
                   description="Admin Interface"),
        ServicePort("grafana", 3001, ServiceCategory.FRONTEND, 
                   alternatives=[3002, 3003], 
                   description="Grafana Dashboard"),
        ServicePort("prometheus", 9090, ServiceCategory.MONITORING, 
                   description="Prometheus Metrics"),
        ServicePort("nginx_http", 80, ServiceCategory.SYSTEM, 
                   description="Nginx HTTP"),
        ServicePort("nginx_https", 443, ServiceCategory.SYSTEM, 
                   description="Nginx HTTPS"),
    ]
    
    def __init__(self, config_file: str = "port_config.json"):
        self.config_file = Path(config_file)
        self.services = {s.name: s for s in self.DEFAULT_SERVICES}
        self.allocated_ports: Dict[int, str] = {}
        self.load_config()
    
    def load_config(self):
        """Load port configuration from file"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.allocated_ports = {int(k): v for k, v in config.get('allocated', {}).items()}
    
    def save_config(self):
        """Save port configuration to file"""
        config = {
            'allocated': {str(k): v for k, v in self.allocated_ports.items()},
            'services': {
                name: {
                    'port': service.default_port,
                    'category': service.category.name,
                    'description': service.description
                }
                for name, service in self.services.items()
            }
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def is_port_available(self, port: int, host: str = '') -> bool:
        """Check if a port is available for binding"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((host, port))
                return True
        except OSError:
            return False
    
    def get_process_using_port(self, port: int) -> Optional[str]:
        """Get the process using a specific port"""
        try:
            # Try lsof first
            result = subprocess.run(
                ['lsof', '-i', f':{port}'], 
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    # Parse the output to get process name
                    parts = lines[1].split()
                    return f"{parts[0]} (PID: {parts[1]})"
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        return None
    
    def find_available_port(self, 
                          category: ServiceCategory, 
                          preferred: List[int] = None) -> Optional[int]:
        """Find an available port in a category range"""
        start, end = category.value
        
        # Check preferred ports first
        if preferred:
            for port in preferred:
                if self.is_port_available(port) and port not in self.allocated_ports:
                    return port
        
        # Search in category range
        for port in range(start, min(end + 1, 65536)):
            if self.is_port_available(port) and port not in self.allocated_ports:
                return port
        
        return None
    
    def allocate_port(self, service_name: str, port: int = None) -> Tuple[int, bool]:
        """Allocate a port for a service"""
        service = self.services.get(service_name)
        if not service:
            raise ValueError(f"Unknown service: {service_name}")
        
        # If specific port requested
        if port:
            if self.is_port_available(port):
                self.allocated_ports[port] = service_name
                self.save_config()
                return port, True
            else:
                return port, False
        
        # Try default port
        if self.is_port_available(service.default_port):
            self.allocated_ports[service.default_port] = service_name
            self.save_config()
            return service.default_port, True
        
        # Try alternatives
        if service.alternatives:
            for alt_port in service.alternatives:
                if self.is_port_available(alt_port):
                    self.allocated_ports[alt_port] = service_name
                    self.save_config()
                    return alt_port, True
        
        # Find any available port in category
        available = self.find_available_port(service.category)
        if available:
            self.allocated_ports[available] = service_name
            self.save_config()
            return available, True
        
        return 0, False
    
    def release_port(self, port: int):
        """Release an allocated port"""
        if port in self.allocated_ports:
            del self.allocated_ports[port]
            self.save_config()
    
    def get_service_port(self, service_name: str) -> Optional[int]:
        """Get the allocated port for a service"""
        for port, service in self.allocated_ports.items():
            if service == service_name:
                return port
        return None
    
    def generate_env_file(self, environment: str = "production") -> str:
        """Generate environment file with port assignments"""
        env_lines = [
            f"# Orchestra AI Port Configuration - {environment}",
            f"# Generated by PortManager",
            ""
        ]
        
        # Add allocated ports
        for service_name, service in self.services.items():
            port = self.get_service_port(service_name)
            if not port:
                port, _ = self.allocate_port(service_name)
            
            env_var = f"{service_name.upper()}_PORT"
            env_lines.append(f"{env_var}={port}")
        
        return "\n".join(env_lines)
    
    def check_conflicts(self) -> List[Dict]:
        """Check for port conflicts"""
        conflicts = []
        
        for service_name, service in self.services.items():
            # Check default port
            if not self.is_port_available(service.default_port):
                process = self.get_process_using_port(service.default_port)
                conflicts.append({
                    'service': service_name,
                    'port': service.default_port,
                    'status': 'in_use',
                    'process': process or 'Unknown',
                    'alternatives': service.alternatives or []
                })
        
        return conflicts
    
    def generate_docker_compose_override(self) -> str:
        """Generate docker-compose override for port mappings"""
        override = {
            'version': '3.8',
            'services': {}
        }
        
        # Map of service names to docker service names
        docker_services = {
            'postgres': 'postgres',
            'redis': 'redis',
            'weaviate': 'weaviate',
            'api': 'api',
            'admin_ui': 'admin',
            'grafana': 'grafana',
            'prometheus': 'prometheus'
        }
        
        for service_name, docker_name in docker_services.items():
            port = self.get_service_port(service_name)
            if port and port != self.services[service_name].default_port:
                # Need to override the port
                internal_port = self.services[service_name].default_port
                override['services'][docker_name] = {
                    'ports': [f"{port}:{internal_port}"]
                }
        
        import yaml
        return yaml.dump(override, default_flow_style=False)
    
    def status_report(self) -> str:
        """Generate a status report of port allocations"""
        lines = [
            "Orchestra AI Port Status Report",
            "=" * 40,
            ""
        ]
        
        # Check each service
        for service_name, service in sorted(self.services.items()):
            allocated_port = self.get_service_port(service_name)
            default_available = self.is_port_available(service.default_port)
            
            status = "✅" if allocated_port or default_available else "❌"
            port_info = f"{allocated_port or service.default_port}"
            
            if allocated_port and allocated_port != service.default_port:
                port_info += f" (default: {service.default_port})"
            
            lines.append(f"{status} {service_name:<20} Port {port_info:<10} {service.description}")
            
            if not allocated_port and not default_available:
                process = self.get_process_using_port(service.default_port)
                lines.append(f"   ⚠️  Port {service.default_port} in use by: {process or 'Unknown'}")
                if service.alternatives:
                    lines.append(f"   💡 Alternatives: {', '.join(map(str, service.alternatives))}")
        
        return "\n".join(lines)


def main():
    """CLI interface for port manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Orchestra AI Port Manager")
    parser.add_argument('command', choices=['status', 'check', 'allocate', 'env', 'override'],
                       help='Command to execute')
    parser.add_argument('--service', help='Service name')
    parser.add_argument('--port', type=int, help='Specific port to allocate')
    parser.add_argument('--environment', default='production', help='Environment name')
    
    args = parser.parse_args()
    
    pm = PortManager()
    
    if args.command == 'status':
        print(pm.status_report())
    
    elif args.command == 'check':
        conflicts = pm.check_conflicts()
        if conflicts:
            print("⚠️  Port conflicts detected:")
            for conflict in conflicts:
                print(f"\n{conflict['service']}:")
                print(f"  Port {conflict['port']} in use by: {conflict['process']}")
                if conflict['alternatives']:
                    print(f"  Alternatives: {', '.join(map(str, conflict['alternatives']))}")
        else:
            print("✅ No port conflicts detected")
    
    elif args.command == 'allocate':
        if not args.service:
            print("Error: --service required for allocate command")
            return
        
        port, success = pm.allocate_port(args.service, args.port)
        if success:
            print(f"✅ Allocated port {port} for {args.service}")
        else:
            print(f"❌ Failed to allocate port for {args.service}")
    
    elif args.command == 'env':
        print(pm.generate_env_file(args.environment))
    
    elif args.command == 'override':
        print(pm.generate_docker_compose_override())


if __name__ == "__main__":
    main() 