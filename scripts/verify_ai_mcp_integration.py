#!/usr/bin/env python3
"""
AI Coding Helpers MCP Integration Verification Script
Ensures all AI services (, Cursor, Factory AI, Claude, OpenAI) are properly configured 
to leverage MCP server setup for optimal contextualization.
"""

import json
import os
import sys
import subprocess
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
import time
from dataclasses import dataclass

@dataclass
class MCPServerConfig:
    name: str
    port: int
    endpoint: str
    capabilities: List[str]
    description: str
    is_running: bool = False
    health_status: str = "unknown"

@dataclass
class AIServiceConfig:
    name: str
    config_file: str
    mcp_integration: Dict[str, Any]
    status: str = "unknown"

class MCPIntegrationVerifier:
    def __init__(self):
        self.mcp_servers: List[MCPServerConfig] = []
        self.ai_services: List[AIServiceConfig] = []
        self.issues: List[str] = []
        self.recommendations: List[str] = []
        
    def load_configurations(self) -> None:
        """Load all MCP and AI service configurations."""
        print("🔍 Loading configurations...")
        
        # Load main MCP configuration
        if main_mcp_config.exists():
            with open(main_mcp_config) as f:
                config = json.load(f)
                self._parse_mcp_servers(config)
        
        # Load AI service configurations
        self._load_ai_service_configs()
    
    def _parse_mcp_servers(self, config: Dict[str, Any]) -> None:
        """Parse MCP server configurations."""
        servers = config.get("servers", {})
        
        # Define server port mappings
        port_mappings = {
            "conductor": 8002,
            "memory": 8003,
            "weaviate": 8001,
            "deployment": 8005,
            "tools": 8006,
            "code-intelligence": 8007,
            "git-intelligence": 8008
        }
        
        for server_name, server_config in servers.items():
            port = port_mappings.get(server_name, 8000)
            capabilities = server_config.get("capabilities", {})
            capability_list = []
            
            if isinstance(capabilities, dict):
                capability_list = [k for k, v in capabilities.items() if v]
            elif isinstance(capabilities, list):
                capability_list = capabilities
                
            server = MCPServerConfig(
                name=server_name,
                port=port,
                endpoint=f"http://localhost:{port}",
                capabilities=capability_list,
                description=server_config.get("description", f"{server_name} MCP server")
            )
            self.mcp_servers.append(server)
    
    def _load_ai_service_configs(self) -> None:
        """Load AI service configurations."""
        ai_configs = [
            ("Claude", "claude_mcp_config.json"),
            ("OpenAI", "openai_mcp_config.json"), 
            ("Cursor", ".cursor/mcp.json"),
            ("Factory AI", ".factory-ai-config")
        ]
        
        for service_name, config_file in ai_configs:
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        config_data = json.load(f)
                    
                    service = AIServiceConfig(
                        name=service_name,
                        config_file=config_file,
                        mcp_integration=config_data
                    )
                    self.ai_services.append(service)
                except json.JSONDecodeError as e:
                    self.issues.append(f"❌ Invalid JSON in {config_file}: {e}")
            else:
                self.issues.append(f"⚠️  Missing configuration file: {config_file}")
    
    def check_mcp_servers_status(self) -> None:
        """Check if MCP servers are running and healthy."""
        print("\n🏥 Checking MCP server health...")
        
        for server in self.mcp_servers:
            # Check if port is listening
            try:
                result = subprocess.run(
                    ["lsof", "-Pi", f":{server.port}", "-sTCP:LISTEN"], 
                    capture_output=True, text=True, timeout=5
                )
                server.is_running = result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                server.is_running = False
            
            # Check health endpoint if running
            if server.is_running:
                try:
                    response = requests.get(f"{server.endpoint}/health", timeout=3)
                    server.health_status = "healthy" if response.status_code == 200 else "unhealthy"
                except requests.RequestException:
                    server.health_status = "unreachable"
            else:
                server.health_status = "not_running"
    
    def verify_ai_service_integrations(self) -> None:
        """Verify AI service MCP integrations."""
        print("\n🤖 Verifying AI service integrations...")
        
        for service in self.ai_services:
            status_checks = []
            
            # Check if service has MCP server references
            config = service.mcp_integration
            
            if service.name == "Claude":
                servers = config.get("mcp_servers", {})
                status_checks.append(len(servers) > 0)
                status_checks.append("memory" in servers)
                status_checks.append("code-intelligence" in servers)
                
            elif service.name == "OpenAI":
                integration = config.get("mcp_integration", {})
                status_checks.append(integration.get("enabled", False))
                servers = integration.get("servers", {})
                status_checks.append(len(servers) > 0)
                
            elif service.name == "Cursor":
                servers = config.get("mcp-servers", {})
                status_checks.append(len(servers) > 0)
                status_checks.append("memory" in servers)
                status_checks.append("tools" in servers)
                
            elif service.name == "":
                servers = config.get("mcpServers", {})
                status_checks.append(len(servers) > 0)
                status_checks.append("memory" in servers)
                status_checks.append("conductor" in servers)
                
            elif service.name == "Factory AI":
                # Factory AI uses workspace configuration
                status_checks.append("workspace" in config)
                status_checks.append("python_executable" in config)
            
            service.status = "configured" if all(status_checks) else "incomplete"
    
    def analyze_integration_completeness(self) -> None:
        """Analyze the completeness of MCP integrations."""
        print("\n📊 Analyzing integration completeness...")
        
        # Check if all critical MCP servers are configured
        critical_servers = {"memory", "conductor", "tools", "code-intelligence"}
        configured_servers = {server.name for server in self.mcp_servers}
        missing_servers = critical_servers - configured_servers
        
        if missing_servers:
            self.issues.append(f"❌ Missing critical MCP servers: {', '.join(missing_servers)}")
        
        # Check if all AI services have proper MCP integration
        properly_configured = [s for s in self.ai_services if s.status == "configured"]
        incomplete_services = [s for s in self.ai_services if s.status == "incomplete"]
        
        if incomplete_services:
            self.issues.append(f"⚠️  Incomplete AI service configurations: {', '.join(s.name for s in incomplete_services)}")
        
        # Generate recommendations
        if not any(server.is_running for server in self.mcp_servers):
            self.recommendations.append("🚀 Start MCP servers: Run ./start_mcp_system.sh")
        
        unhealthy_servers = [s for s in self.mcp_servers if s.is_running and s.health_status != "healthy"]
        if unhealthy_servers:
            self.recommendations.append(f"🔧 Fix unhealthy servers: {', '.join(s.name for s in unhealthy_servers)}")
        
        if len(properly_configured) < len(self.ai_services):
            self.recommendations.append("⚙️  Update AI service configurations to include all MCP servers")
    
    def generate_startup_script(self) -> None:
        """Generate optimized startup script for all services."""
        startup_script = """#!/bin/bash
# Comprehensive AI + MCP System Startup
# Generated by verify_ai_mcp_integration.py

set -e

echo "🚀 Starting Comprehensive AI + MCP System..."

# Colors
GREEN='\\033[0;32m'
BLUE='\\033[0;34m'
RED='\\033[0;31m'
NC='\\033[0m'

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo -e "${GREEN}✅ Virtual environment active${NC}"
else
    echo -e "${BLUE}Activating virtual environment...${NC}"
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo -e "${RED}❌ Virtual environment not found${NC}"
        exit 1
    fi
fi

# Start MCP servers
echo -e "${BLUE}Starting MCP servers...${NC}"
./start_mcp_system.sh

# Wait for servers to be ready
echo -e "${BLUE}Waiting for MCP servers to be ready...${NC}"
sleep 10

# Verify all servers are running
echo -e "${BLUE}Verifying server health...${NC}"
python scripts/verify_ai_mcp_integration.py --health-check-only

echo -e "${GREEN}🎉 All systems ready for AI coding assistance!${NC}"
echo ""
echo "Available MCP servers:"
echo "  - Memory (context storage): http://localhost:8003"
echo "  - Conductor (orchestration): http://localhost:8002"
echo "  - Tools (tool execution): http://localhost:8006"
echo "  - Code Intelligence: http://localhost:8007"
echo "  - Git Intelligence: http://localhost:8008"
echo ""
echo "AI Services configured:"
echo "  - Claude (via claude_mcp_config.json)"
echo "  - OpenAI (via openai_mcp_config.json)"
echo "  - Cursor (via .cursor/mcp.json)"
echo "  - Factory AI (via .factory-ai-config)"
echo ""
echo "Ready for enhanced AI coding with full contextualization! 🤖✨"
"""
        
        with open(script_path, 'w') as f:
            f.write(startup_script)
        os.chmod(script_path, 0o755)
        
        self.recommendations.append(f"📝 Generated startup script: {script_path}")
    
    def print_report(self) -> None:
        """Print comprehensive status report."""
        print("\n" + "="*80)
        print("🎯 AI CODING HELPERS MCP INTEGRATION STATUS REPORT")
        print("="*80)
        
        # MCP Servers Status
        print("\n🖥️  MCP SERVERS STATUS:")
        print("-" * 40)
        for server in self.mcp_servers:
            status_icon = "✅" if server.is_running else "❌"
            health_icon = {"healthy": "💚", "unhealthy": "🟡", "unreachable": "🔴", "not_running": "⚫"}.get(
                server.health_status,
                "❓"
            )
            print(f"{status_icon} {server.name:20} | Port {server.port:4} | {health_icon} {server.health_status:12} | {server.description}")
        
        # AI Services Status
        print("\n🤖 AI SERVICES CONFIGURATION:")
        print("-" * 40)
        for service in self.ai_services:
            status_icon = "✅" if service.status == "configured" else "⚠️"
            print(f"{status_icon} {service.name:15} | {service.status:12} | {service.config_file}")
        
        # Issues
        if self.issues:
            print("\n⚠️  ISSUES FOUND:")
            print("-" * 40)
            for issue in self.issues:
                print(f"  {issue}")
        
        # Recommendations
        if self.recommendations:
            print("\n💡 RECOMMENDATIONS:")
            print("-" * 40)
            for rec in self.recommendations:
                print(f"  {rec}")
        else:
            print("\n🎉 ALL SYSTEMS PROPERLY CONFIGURED!")
        
        # Summary
        running_servers = sum(1 for s in self.mcp_servers if s.is_running)
        total_servers = len(self.mcp_servers)
        configured_services = sum(1 for s in self.ai_services if s.status == "configured")
        total_services = len(self.ai_services)
        
        print(f"\n📈 SUMMARY:")
        print(f"  MCP Servers: {running_servers}/{total_servers} running")
        print(f"  AI Services: {configured_services}/{total_services} properly configured")
        
        if running_servers == total_servers and configured_services == total_services:
            print("\n🚀 READY FOR OPTIMAL AI CODING WITH FULL CONTEXTUALIZATION!")
        else:
            print("\n🔧 SYSTEM NEEDS ATTENTION - Follow recommendations above")

def main():
    """Main verification function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--health-check-only":
        # Quick health check mode
        verifier = MCPIntegrationVerifier()
        verifier.load_configurations()
        verifier.check_mcp_servers_status()
        
        all_healthy = all(s.health_status == "healthy" for s in verifier.mcp_servers if s.is_running)
        if all_healthy and any(s.is_running for s in verifier.mcp_servers):
            print("✅ All MCP servers are healthy")
            sys.exit(0)
        else:
            print("❌ Some MCP servers are not healthy")
            sys.exit(1)
    
    # Full verification
    verifier = MCPIntegrationVerifier()
    verifier.load_configurations()
    verifier.check_mcp_servers_status()
    verifier.verify_ai_service_integrations()
    verifier.analyze_integration_completeness()
    verifier.generate_startup_script()
    verifier.print_report()

if __name__ == "__main__":
    main() 