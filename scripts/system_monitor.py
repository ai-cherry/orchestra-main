import logging
logger = logging.getLogger(__name__)

#!/usr/bin/env python3
"""
Comprehensive System Monitor and Manager
Shows real-time status of all services and provides management options
"""

import os
import sys
import time
import json
import subprocess
import psutil
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# ANSI color codes
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
MAGENTA = '\033[0;35m'
CYAN = '\033[0;36m'
WHITE = '\033[1;37m'
NC = '\033[0m'  # No Color

class SystemMonitor:
    def __init__(self):
        self.services = {
            "PostgreSQL": {"port": 5432, "container": "orchestra_postgres"},
            "Redis": {"port": 6379, "container": "orchestra_redis"},
            "Weaviate": {"port": 8080, "container": "orchestra_weaviate"}
        }
        self.mcp_servers = {
            "memory": {"port": 8003, "module": "mcp_server.servers.memory_server"},
            "tools": {"port": 8006, "module": "mcp_server.servers.tools_server"},
            "orchestrator": {"port": 8000, "module": "mcp_server.servers.orchestrator_server"}
        }
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
    def run_command(self, cmd: List[str]) -> Tuple[int, str, str]:
        """Run command and return exit code, stdout, stderr"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return -1, "", str(e)
            
    def check_port(self, port: int) -> Optional[Dict]:
        """Check what's running on a port"""
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == 'LISTEN':
                try:
                    proc = psutil.Process(conn.pid)
                    return {
                        'pid': conn.pid,
                        'name': proc.name(),
                        'cmdline': ' '.join(proc.cmdline()[:50])
                    }
                except:
                    pass
        return None
        
    def check_docker_service(self, container_name: str) -> Dict:
        """Check Docker container status"""
        code, out, err = self.run_command([
            "docker", "inspect", container_name, 
            "--format", '{{json .State}}'
        ])
        
        if code == 0:
            try:
                state = json.loads(out)
                return {
                    "running": state.get("Running", False),
                    "status": state.get("Status", "unknown"),
                    "health": state.get("Health", {}).get("Status", "unknown") if state.get("Health") else "no healthcheck"
                }
            except:
                pass
                
        return {"running": False, "status": "not found", "health": "unknown"}
        
    def check_service_endpoint(self, port: int, endpoint: str = "/") -> bool:
        """Check if service endpoint is responding"""
        try:
            response = requests.get(f"http://localhost:{port}{endpoint}", timeout=2)
            return response.status_code < 500
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False
            
    def get_container_logs(self, container_name: str, lines: int = 10) -> List[str]:
        """Get last N lines of container logs"""
        code, out, err = self.run_command([
            "docker", "logs", "--tail", str(lines), container_name
        ])
        return out.strip().split('\n') if code == 0 else []
        
    def start_mcp_server(self, name: str, config: Dict) -> bool:
        """Start an MCP server"""
        # Kill existing process if any
        port_info = self.check_port(config["port"])
        if port_info:
            try:
                os.kill(port_info["pid"], 9)
                # TODO: Replace with asyncio.sleep() for async code
                time.sleep(1)
            except:
                pass
                
        # Start new process
        
        code, out, err = self.run_command(["bash", "-c", cmd])
        
        return code == 0
        
    def display_header(self):
        """Display header"""
        print(f"{CYAN}╔══════════════════════════════════════════════════════════════╗{NC}")
        print(f"{CYAN}║{WHITE}          🍒 ORCHESTRA SYSTEM MONITOR & MANAGER 🍒            {CYAN}║{NC}")
        print(f"{CYAN}╚══════════════════════════════════════════════════════════════╝{NC}")
        print(f"{WHITE}Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}{NC}")
        print("=" * 64)
        
    def display_docker_services(self):
        """Display Docker services status"""
        print(f"\n{BLUE}🐳 DOCKER SERVICES{NC}")
        print("-" * 40)
        
        for name, config in self.services.items():
            status = self.check_docker_service(config["container"])
            port_info = self.check_port(config["port"])
            endpoint_ok = self.check_service_endpoint(config["port"])
            
            if status["running"] and endpoint_ok:
                icon = f"{GREEN}✅{NC}"
                health = f"{GREEN}HEALTHY{NC}"
            elif status["running"]:
                icon = f"{YELLOW}⚠️{NC}"
                health = f"{YELLOW}RUNNING (no response){NC}"
            else:
                icon = f"{RED}❌{NC}"
                health = f"{RED}DOWN{NC}"
                
            print(f"{icon} {name:12} | Port: {config['port']:5} | Status: {health}")
            
            # Show recent logs if service is having issues
            if status["running"] and not endpoint_ok:
                logs = self.get_container_logs(config["container"], 3)
                if logs:
                    print(f"   {YELLOW}Recent logs:{NC}")
                    for log in logs[-2:]:
                        if log.strip():
                            print(f"   {log[:80]}...")
                            
    def display_mcp_servers(self):
        """Display MCP servers status"""
        print(f"\n{MAGENTA}🤖 MCP SERVERS{NC}")
        print("-" * 40)
        
        for name, config in self.mcp_servers.items():
            port_info = self.check_port(config["port"])
            
            if port_info:
                icon = f"{GREEN}✅{NC}"
                status = f"{GREEN}RUNNING{NC} (PID: {port_info['pid']})"
            else:
                icon = f"{RED}❌{NC}"
                status = f"{RED}NOT RUNNING{NC}"
                
            print(f"{icon} {name:12} | Port: {config['port']:5} | Status: {status}")
            
    def display_system_resources(self):
        """Display system resource usage"""
        print(f"\n{YELLOW}📊 SYSTEM RESOURCES{NC}")
        print("-" * 40)
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_color = GREEN if cpu_percent < 70 else YELLOW if cpu_percent < 90 else RED
        print(f"CPU Usage:    {cpu_color}{cpu_percent:5.1f}%{NC} {'█' * int(cpu_percent/5)}")
        
        # Memory
        mem = psutil.virtual_memory()
        mem_color = GREEN if mem.percent < 70 else YELLOW if mem.percent < 90 else RED
        print(f"Memory Usage: {mem_color}{mem.percent:5.1f}%{NC} {'█' * int(mem.percent/5)}")
        print(f"              {mem.used/1024/1024/1024:.1f}GB / {mem.total/1024/1024/1024:.1f}GB")
        
        # Disk
        disk = psutil.disk_usage('/')
        disk_color = GREEN if disk.percent < 70 else YELLOW if disk.percent < 90 else RED
        print(f"Disk Usage:   {disk_color}{disk.percent:5.1f}%{NC} {'█' * int(disk.percent/5)}")
        
    def display_menu(self):
        """Display action menu"""
        print(f"\n{CYAN}📋 ACTIONS{NC}")
        print("-" * 40)
        print("1. Start all MCP servers")
        print("2. Stop all MCP servers")
        print("3. Restart Docker services")
        print("4. View detailed logs")
        print("5. Run system tests")
        print("6. Export status report")
        print("0. Exit")
        print()
        
    def start_all_mcp_servers(self):
        """Start all MCP servers"""
        print(f"\n{YELLOW}Starting MCP servers...{NC}")
        
        # Create logs directory
        logs_dir.mkdir(exist_ok=True)
        
        for name, config in self.mcp_servers.items():
            print(f"Starting {name} server...", end=" ")
            if self.start_mcp_server(name, config):
                print(f"{GREEN}✓{NC}")
            else:
                # TODO: Replace with asyncio.sleep() for async code
                print(f"{RED}✗{NC}")
            time.sleep(2)
            
    def stop_all_mcp_servers(self):
        """Stop all MCP servers"""
        print(f"\n{YELLOW}Stopping MCP servers...{NC}")
        
        for name, config in self.mcp_servers.items():
            port_info = self.check_port(config["port"])
            if port_info:
                print(f"Stopping {name} server (PID: {port_info['pid']})...", end=" ")
                try:
                    os.kill(port_info["pid"], 9)
                    print(f"{GREEN}✓{NC}")
                except:
                    print(f"{RED}✗{NC}")
                    
    def restart_docker_services(self):
        """Restart Docker services"""
        print(f"\n{YELLOW}Restarting Docker services...{NC}")
        
        # Stop services
        # TODO: Replace with asyncio.sleep() for async code
        print("Stopping services...")
        self.run_command(["docker-compose", "down"])
        time.sleep(2)
        
        # Start services
        print("Starting services...")
        self.run_command(["docker-compose", "up", "-d"])
         # TODO: Replace with asyncio.sleep() for async code
        
        # Wait for services to be ready
        print("Waiting for services to be ready...")
        time.sleep(10)
        
        print(f"{GREEN}Docker services restarted{NC}")
        
    def view_logs(self):
        """View detailed logs"""
        print(f"\n{CYAN}Select log to view:{NC}")
        print("1. PostgreSQL logs")
        print("2. Redis logs")
        print("3. Weaviate logs")
        print("4. MCP Memory server logs")
        print("5. MCP Tools server logs")
        print("6. MCP Orchestrator server logs")
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == "1":
            logs = self.get_container_logs("orchestra_postgres", 50)
        elif choice == "2":
            logs = self.get_container_logs("orchestra_redis", 50)
        elif choice == "3":
            logs = self.get_container_logs("orchestra_weaviate", 50)
        elif choice in ["4", "5", "6"]:
            log_files = {
                "4": "logs/mcp_memory.log",
                "5": "logs/mcp_tools.log",
                "6": "logs/mcp_orchestrator.log"
            }
            if log_file.exists():
                with open(log_file) as f:
                    logs = f.readlines()[-50:]
            else:
                logs = ["Log file not found"]
        else:
            return
            
        print(f"\n{YELLOW}Last 50 lines:{NC}")
        print("-" * 80)
        for line in logs:
            print(line.rstrip())
            
    def run_tests(self):
        """Run system tests"""
        print(f"\n{YELLOW}Running system tests...{NC}")
        
        if test_script.exists():
            code, out, err = self.run_command(["python3", str(test_script)])
            print(out)
            if code == 0:
                print(f"\n{GREEN}All tests passed!{NC}")
            else:
                print(f"\n{RED}Some tests failed{NC}")
        else:
            print(f"{RED}Test script not found{NC}")
            
    def export_status_report(self):
        """Export detailed status report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "docker_services": {},
            "mcp_servers": {},
            "system_resources": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            }
        }
        
        # Docker services
        for name, config in self.services.items():
            status = self.check_docker_service(config["container"])
            report["docker_services"][name] = {
                "container": config["container"],
                "port": config["port"],
                "running": status["running"],
                "health": status["health"],
                "endpoint_responding": self.check_service_endpoint(config["port"])
            }
            
        # MCP servers
        for name, config in self.mcp_servers.items():
            port_info = self.check_port(config["port"])
            report["mcp_servers"][name] = {
                "port": config["port"],
                "running": port_info is not None,
                "pid": port_info["pid"] if port_info else None
            }
            
        # Save report
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
            
        print(f"\n{GREEN}Status report exported to: {report_file}{NC}")
        
    def run(self):
        """Main monitoring loop"""
        while True:
            self.clear_screen()
            self.display_header()
            self.display_docker_services()
            self.display_mcp_servers()
            self.display_system_resources()
            self.display_menu()
            
            try:
                choice = input(f"{WHITE}Enter choice (0-6, or Enter to refresh): {NC}").strip()
                
                if choice == "0":
                    print(f"\n{GREEN}Goodbye!{NC}")
                    break
                elif choice == "1":
                    self.start_all_mcp_servers()
                    input(f"\n{WHITE}Press Enter to continue...{NC}")
                elif choice == "2":
                    self.stop_all_mcp_servers()
                    input(f"\n{WHITE}Press Enter to continue...{NC}")
                elif choice == "3":
                    self.restart_docker_services()
                    input(f"\n{WHITE}Press Enter to continue...{NC}")
                elif choice == "4":
                    self.view_logs()
                    input(f"\n{WHITE}Press Enter to continue...{NC}")
                elif choice == "5":
                    self.run_tests()
                    input(f"\n{WHITE}Press Enter to continue...{NC}")
                elif choice == "6":
                    self.export_status_report()
                    input(f"\n{WHITE}Press Enter to continue...{NC}")
                # TODO: Replace with asyncio.sleep() for async code
                elif choice == "":
                    continue  # Refresh
                else:
                    print(f"{RED}Invalid choice{NC}")
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                print(f"\n\n{GREEN}Goodbye!{NC}")
                break
                
if __name__ == "__main__":
    monitor = SystemMonitor()
    monitor.run()