#!/usr/bin/env python3
"""
Comprehensive System Audit - Shows EVERYTHING that's running
"""

import subprocess
import psutil
import json
import os
from datetime import datetime
from pathlib import Path

def run_cmd(cmd):
    """Run command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else None
    except:
        return None

def check_port(port):
    """Check what's running on a port"""
    for conn in psutil.net_connections():
        if conn.laddr.port == port and conn.status == 'LISTEN':
            try:
                proc = psutil.Process(conn.pid)
                return {'pid': conn.pid, 'name': proc.name(), 'cmdline': ' '.join(proc.cmdline())}
            except:
                pass
    return None

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║        🍒 CHERRY AI COMPREHENSIVE SYSTEM AUDIT 🍒            ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    print(f"📅 Audit Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("="*60)
    
    # 1. Web Services
    print("\n🌐 WEB SERVICES:")
    print("-"*40)
    
    # Check port 80
    port80 = check_port(80)
    if port80:
        print(f"✅ Port 80: {port80['name']} (PID: {port80['pid']})")
        print(f"   Command: {port80['cmdline'][:60]}...")
    else:
        print("❌ Port 80: Nothing listening")
    
    # Check port 8080
    port8080 = check_port(8080)
    if port8080:
        print(f"✅ Port 8080: {port8080['name']} (PID: {port8080['pid']})")
    else:
        print("❌ Port 8080: Nothing listening")
    
    # Check nginx
    nginx_status = run_cmd("systemctl is-active nginx")
    print(f"📦 Nginx: {nginx_status or 'not installed'}")
    
    # Test website
    web_test = run_cmd("curl -s -o /dev/null -w '%{http_code}' http://localhost")
    print(f"🔗 Website Test: HTTP {web_test}")
    
    # 2. Docker Services
    print("\n\n🐳 DOCKER SERVICES:")
    print("-"*40)
    
    docker_ps = run_cmd("docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E '(postgres|redis|weaviate|api)'")
    if docker_ps:
        for line in docker_ps.split('\n'):
            if 'healthy' in line:
                print(f"✅ {line}")
            elif 'starting' in line:
                print(f"⏳ {line}")
            else:
                print(f"❌ {line}")
    else:
        print("❌ No Docker services found")
    
    # 3. MCP Servers
    print("\n\n🤖 MCP SERVERS:")
    print("-"*40)
    
    mcp_servers = {
        'memory_server': 'Memory Server',
        'tools_server': 'Tools Server',
        'code_intelligence_server': 'Code Intelligence',
        'git_intelligence_server': 'Git Intelligence'
    }
    
    for server_file, server_name in mcp_servers.items():
        # Check if process is running
        procs = [p for p in psutil.process_iter(['pid', 'name', 'cmdline']) 
                 if server_file in ' '.join(p.info['cmdline'])]
        
        if procs:
            print(f"✅ {server_name}: Running (PID: {procs[0].info['pid']})")
        else:
            print(f"❌ {server_name}: Not running")
    
    # 4. Monitoring Services
    print("\n\n🔄 MONITORING SERVICES:")
    print("-"*40)
    
    services = [
        ('orchestra.service', 'Orchestra Daemon'),
        ('cherry-ai-monitor.service', 'Cherry AI Monitor'),
        ('cherry-ai-web.service', 'Cherry AI Web'),
        ('master-monitor.service', 'Master Monitor')
    ]
    
    for service, name in services:
        status = run_cmd(f"systemctl is-active {service}")
        if status == 'active':
            print(f"✅ {name}: Active")
        elif status:
            print(f"⚠️ {name}: {status}")
        else:
            print(f"❌ {name}: Not found")
    
    # 5. System Resources
    print("\n\n📊 SYSTEM RESOURCES:")
    print("-"*40)
    
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    print(f"🖥️ CPU Usage: {cpu_percent}%")
    print(f"💾 Memory: {memory.percent}% used ({memory.used//1024//1024}MB / {memory.total//1024//1024}MB)")
    print(f"💿 Disk: {disk.percent}% used ({disk.used//1024//1024//1024}GB / {disk.total//1024//1024//1024}GB)")
    
    # 6. Recent Logs
    print("\n\n📜 RECENT MONITOR LOGS:")
    print("-"*40)
    
    if os.path.exists('/var/log/cherry-ai-monitor.log'):
        logs = run_cmd("tail -5 /var/log/cherry-ai-monitor.log")
        if logs:
            print(logs)
    else:
        print("No monitor logs found")
    
    # 7. Recommendations
    print("\n\n💡 RECOMMENDATIONS:")
    print("-"*40)
    
    issues = []
    
    if not all(check_port(p) for p in [80]):
        issues.append("Web server not running on port 80")
    
            status["message"] = str(e)
            
        return status
    
    def check_weaviate(self) -> Dict[str, Any]:
        """Deep check of Weaviate status"""
        print("🔍 Checking Weaviate...")
        status = {
            "healthy": False,
            "issues": [],
            "config": {},
            "logs": []
        }
        
        # Check basic health
        health = self.check_service_health("weaviate", 8080, "/v1/.well-known/ready")
        status["healthy"] = health["healthy"]
        
        if not health["healthy"]:
            status["issues"].append(f"Weaviate not responding: {health['message']}")
            
            # Get container logs
            code, out, err = self.run_command([
                "docker", "logs", "--tail", "50", 
                "orchestra-main_weaviate_1"
            ])
            if code == 0:
                status["logs"] = out.strip().split('\n')[-10:]  # Last 10 lines
                
                # Analyze logs for common issues
                log_text = out.lower()
                if "raft" in log_text and "failed" in log_text:
                    status["issues"].append("Raft clustering issues detected")
                if "memory" in log_text and "limit" in log_text:
                    status["issues"].append("Memory limit issues detected")
        
        return status
    
    def check_postgres(self) -> Dict[str, Any]:
        """Check PostgreSQL status"""
        print("🔍 Checking PostgreSQL...")
        status = {"healthy": False, "issues": [], "config": {}}
        
        # Check if container is running
        containers = self.check_containers()
        postgres_running = any(
            "postgres" in c["name"].lower() and c["state"] == "running" 
            for c in containers["running"]
        )
        
        if not postgres_running:
            status["issues"].append("PostgreSQL container not running")
        else:
            # Check connection
            code, out, err = self.run_command([
                "docker", "exec", "orchestra-main_postgres_1",
                "pg_isready", "-U", "postgres"
            ])
            if code == 0:
                status["healthy"] = True
            else:
                status["issues"].append("PostgreSQL not accepting connections")
        
        return status
    
    def check_redis(self) -> Dict[str, Any]:
        """Check Redis status"""
        print("🔍 Checking Redis...")
        status = {"healthy": False, "issues": []}
        
        # Check if container is running
        containers = self.check_containers()
        redis_running = any(
            "redis" in c["name"].lower() and c["state"] == "running"
            for c in containers["running"]
        )
        
        if not redis_running:
            status["issues"].append("Redis container not running")
        else:
            # Check connection
            code, out, err = self.run_command([
                "docker", "exec", "orchestra-main_redis_1",
                "redis-cli", "ping"
            ])
            if code == 0 and out.strip() == "PONG":
                status["healthy"] = True
            else:
                status["issues"].append("Redis not responding to ping")
        
        return status
    
    def check_mcp_servers(self) -> Dict[str, Any]:
        """Check MCP server status"""
        print("🔍 Checking MCP servers...")
        status = {"servers": {}, "issues": []}
        
        # Check for MCP server processes
        code, out, err = self.run_command(["ps", "aux"])
        if code == 0:
            mcp_processes = [line for line in out.split('\n') if 'mcp' in line.lower() and 'grep' not in line]
            status["running_processes"] = len(mcp_processes)
        
        # Check MCP server endpoints from config
        mcp_config_path = self.project_root / "claude_mcp_config.json"
        if mcp_config_path.exists():
            try:
                with open(mcp_config_path) as f:
                    config = json.load(f)
                    
                for server_name, server_config in config.get("mcp_servers", {}).items():
                    endpoint = server_config.get("endpoint", "")
                    if endpoint:
                        # Extract port from endpoint
                        try:
                            port = int(endpoint.split(":")[-1])
                            health = self.check_service_health(server_name, port, "/health")
                            status["servers"][server_name] = {
                                "endpoint": endpoint,
                                "healthy": health["healthy"],
                                "message": health["message"]
                            }
                            if not health["healthy"]:
                                status["issues"].append(f"MCP server '{server_name}' not responding")
                        except:
                            status["issues"].append(f"Invalid endpoint for MCP server '{server_name}'")
            except Exception as e:
                status["issues"].append(f"Failed to read MCP config: {e}")
        
        return status
    
    def fix_weaviate_clustering(self):
        """Fix Weaviate clustering issues"""
        print("🔧 Fixing Weaviate clustering...")
        
        # Stop existing Weaviate container
        self.run_command(["docker", "stop", "orchestra-main_weaviate_1"])
        self.run_command(["docker", "rm", "orchestra-main_weaviate_1"])
        
        # Clear Weaviate data volume to reset state
        self.run_command(["docker", "volume", "rm", "orchestra-main_weaviate_data"])
        
        # Create simplified Weaviate config without clustering
        weaviate_fix = {
            "version": "3.8",
            "services": {
                "weaviate": {
                    "image": "semitechnologies/weaviate:latest",
                    "container_name": "orchestra_weaviate",
                    "restart": "unless-stopped",
                    "ports": ["8080:8080"],
                    "environment": {
                        "QUERY_DEFAULTS_LIMIT": "25",
                        "AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED": "true",
                        "PERSISTENCE_DATA_PATH": "/var/lib/weaviate",
                        "DEFAULT_VECTORIZER_MODULE": "none",
                        "ENABLE_MODULES": "text2vec-openai,generative-openai",
                        "STANDALONE_MODE": "true",  # Disable clustering
                        "GOMAXPROCS": "2",
                        "PERSISTENCE_LSM_ACCESS_STRATEGY": "mmap",
                        "TRACK_VECTOR_DIMENSIONS": "false",
                        "LOG_LEVEL": "warning"
                    },
                    "volumes": ["weaviate_data:/var/lib/weaviate"],
                    "healthcheck": {
                        "test": ["CMD", "wget", "--spider", "-q", "http://localhost:8080/v1/.well-known/ready"],
                        "interval": "10s",
                        "timeout": "5s",
                        "retries": 5
                    }
                }
            },
            "volumes": {
                "weaviate_data": {}
            }
        }
        
        # Write fixed config
        with open(self.project_root / "docker-compose.weaviate-fixed.yml", "w") as f:
            yaml.dump(weaviate_fix, f)
        
        self.fixes_applied.append("Created simplified Weaviate configuration")
        
    def fix_docker_services(self):
        """Fix all Docker services"""
        print("🔧 Fixing Docker services...")
        
        # Stop all containers
        print("  Stopping all containers...")
        self.run_command(["docker-compose", "-f", "docker-compose.local.yml", "down"])
        
        # Clean up volumes
        print("  Cleaning up volumes...")
        self.run_command(["docker", "volume", "prune", "-f"])
        
        # Create optimized local config
        optimized_config = {
            "version": "3.8",
            "services": {
                "postgres": {
                    "image": "postgres:15-alpine",
                    "container_name": "orchestra_postgres",
                    "restart": "unless-stopped",
                    "environment": {
                        "POSTGRES_USER": "postgres",
                        "POSTGRES_PASSWORD": "postgres",
                        "POSTGRES_DB": "conductor"
                    },
                    "ports": ["5432:5432"],
                    "volumes": [
                        "postgres_data:/var/lib/postgresql/data",
                        "./init-scripts:/docker-entrypoint-initdb.d"
                    ],
                    "healthcheck": {
                        "test": ["CMD-SHELL", "pg_isready -U postgres"],
                        "interval": "10s",
                        "timeout": "5s",
                        "retries": 5
                    }
                },
                "redis": {
                    "image": "redis:7-alpine",
                    "container_name": "orchestra_redis",
                    "restart": "unless-stopped",
                    "ports": ["6379:6379"],
                    "volumes": ["redis_data:/data"],
                    "healthcheck": {
                        "test": ["CMD", "redis-cli", "ping"],
                        "interval": "10s",
                        "timeout": "5s",
                        "retries": 5
                    }
                },
                "weaviate": {
                    "image": "semitechnologies/weaviate:latest",
                    "container_name": "orchestra_weaviate",
                    "restart": "unless-stopped",
                    "ports": ["8080:8080"],
                    "environment": {
                        "QUERY_DEFAULTS_LIMIT": "25",
                        "AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED": "true",
                        "PERSISTENCE_DATA_PATH": "/var/lib/weaviate",
                        "DEFAULT_VECTORIZER_MODULE": "none",
                        "STANDALONE_MODE": "true",
                        "GOMAXPROCS": "2",
                        "LOG_LEVEL": "warning"
                    },
                    "volumes": ["weaviate_data:/var/lib/weaviate"],
                    "healthcheck": {
                        "test": ["CMD", "wget", "--spider", "-q", "http://localhost:8080/v1/.well-known/ready"],
                        "interval": "10s",
                        "timeout": "5s",
                        "retries": 5
                    }
                }
            },
            "volumes": {
                "postgres_data": {},
                "redis_data": {},
                "weaviate_data": {}
            },
            "networks": {
                "default": {
                    "name": "orchestra_network"
                }
            }
        }
        
        # Write optimized config
        with open(self.project_root / "docker-compose.optimized.yml", "w") as f:
            yaml.dump(optimized_config, f)
        
        self.fixes_applied.append("Created optimized Docker Compose configuration")
        
    def generate_remediation_script(self):
        """Generate executable remediation script"""
        print("📝 Generating remediation script...")
        
        script_content = '''#!/bin/bash
# Orchestra System Remediation Script
# Generated: {timestamp}

set -e

echo "🚀 Starting Orchestra System Remediation..."

# Function to check command success
check_status() {
    if [ $? -eq 0 ]; then
        echo "✅ $1 successful"
    else
        echo "❌ $1 failed"
        exit 1
    fi
}

# 1. Stop all services
echo "🛑 Stopping all services..."
docker-compose -f docker-compose.local.yml down -v
docker-compose -f docker-compose.production.yml down -v
check_status "Service shutdown"

# 2. Clean up Docker
echo "🧹 Cleaning up Docker..."
docker system prune -f
docker volume prune -f
check_status "Docker cleanup"

# 3. Start core services with optimized config
echo "🚀 Starting core services..."
docker-compose -f docker-compose.optimized.yml up -d postgres redis
sleep 10
check_status "Core services startup"

# 4. Start Weaviate separately
echo "🚀 Starting Weaviate..."
docker-compose -f docker-compose.optimized.yml up -d weaviate
sleep 15
check_status "Weaviate startup"

# 5. Verify services
echo "🔍 Verifying services..."
docker exec orchestra_postgres pg_isready -U postgres
check_status "PostgreSQL verification"

docker exec orchestra_redis redis-cli ping
check_status "Redis verification"

curl -s http://localhost:8080/v1/.well-known/ready
check_status "Weaviate verification"

# 6. Initialize database
echo "📊 Initializing database..."
docker exec orchestra_postgres psql -U postgres -c "CREATE DATABASE IF NOT EXISTS conductor;"
docker exec orchestra_postgres psql -U postgres -c "CREATE DATABASE IF NOT EXISTS orchestrator;"
check_status "Database initialization"

# 7. Start MCP servers
echo "🔧 Starting MCP servers..."
cd /root/orchestra-main

# Kill any existing MCP processes
pkill -f "mcp_server" || true

# Start MCP servers in background
nohup python3 -m mcp_server.servers.memory_server > logs/mcp_memory.log 2>&1 &
echo $! > logs/mcp_memory.pid

nohup python3 -m mcp_server.servers.tools_server > logs/mcp_tools.log 2>&1 &
echo $! > logs/mcp_tools.pid

nohup python3 -m mcp_server.servers.orchestrator_server > logs/mcp_orchestrator.log 2>&1 &
echo $! > logs/mcp_orchestrator.pid

sleep 5
check_status "MCP servers startup"

# 8. Final status check
echo "📊 Final system status:"
python3 scripts/orchestra_system_status.py

echo "✅ Remediation complete!"
'''.format(timestamp=datetime.now().isoformat())
        
        script_path = self.project_root / "scripts" / "remediate_system.sh"
        with open(script_path, "w") as f:
            f.write(script_content)
        
        # Make executable
        os.chmod(script_path, 0o755)
        
        self.fixes_applied.append(f"Generated remediation script: {script_path}")
        
    def run_audit(self):
        """Run complete system audit"""
        print("🔍 Starting Comprehensive System Audit...")
        print("=" * 60)
        
        # 1. Docker daemon check
        self.audit_results["components"]["docker_daemon"] = self.check_docker_daemon()
        
        # 2. Docker Compose analysis
        self.audit_results["components"]["docker_compose"] = self.check_docker_compose()
        
        # 3. Container status
        self.audit_results["components"]["containers"] = self.check_containers()
        
        # 4. Service-specific checks
        self.audit_results["components"]["postgres"] = self.check_postgres()
        self.audit_results["components"]["redis"] = self.check_redis()
        self.audit_results["components"]["weaviate"] = self.check_weaviate()
        
        # 5. MCP servers
        self.audit_results["components"]["mcp_servers"] = self.check_mcp_servers()
        
        # Compile issues
        for component, status in self.audit_results["components"].items():
            if isinstance(status, dict) and "issues" in status:
                for issue in status["issues"]:
                    self.audit_results["issues"].append({
                        "component": component,
                        "issue": issue,
                        "severity": "critical" if "not running" in issue else "warning"
                    })
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Apply fixes
        self.apply_fixes()
        
        # Generate remediation script
        self.generate_remediation_script()
        
        # Save audit results
        audit_file = self.project_root / f"audit_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(audit_file, "w") as f:
            json.dump(self.audit_results, f, indent=2)
        
        print(f"\n📄 Audit results saved to: {audit_file}")
        
        # Print summary
        self.print_summary()
        
    def generate_recommendations(self):
        """Generate recommendations based on audit findings"""
        recs = self.audit_results["recommendations"]
        
        # Weaviate issues
        if any("weaviate" in issue["component"].lower() for issue in self.audit_results["issues"]):
            recs.append({
                "priority": "high",
                "component": "weaviate",
                "action": "Disable Raft clustering and use standalone mode",
                "reason": "Raft clustering causing startup failures"
            })
        
        # Docker compose inconsistencies
        if any("inconsistent" in issue["issue"] for issue in self.audit_results["issues"]):
            recs.append({
                "priority": "high",
                "component": "docker-compose",
                "action": "Consolidate to single docker-compose.yml",
                "reason": "Multiple compose files causing configuration conflicts"
            })
        
        # MCP server issues
        if any("mcp" in issue["component"].lower() for issue in self.audit_results["issues"]):
            recs.append({
                "priority": "medium",
                "component": "mcp_servers",
                "action": "Implement systemd services for MCP servers",
                "reason": "Ensure automatic restart and proper logging"
            })
        
    def apply_fixes(self):
        """Apply automated fixes for detected issues"""
        print("\n🔧 Applying automated fixes...")
        
        # Fix Weaviate if needed
        weaviate_issues = [i for i in self.audit_results["issues"] if "weaviate" in i["component"].lower()]
        if weaviate_issues:
            self.fix_weaviate_clustering()
        
        # Fix Docker services
        docker_issues = [i for i in self.audit_results["issues"] if "not running" in i["issue"]]
        if docker_issues:
            self.fix_docker_services()
        
        self.audit_results["fixes"] = self.fixes_applied
        
    def print_summary(self):
        """Print audit summary"""
        print("\n" + "=" * 60)
        print("📊 AUDIT SUMMARY")
        print("=" * 60)
        
        # Component status
        print("\n🔧 Component Status:")
        for component, status in self.audit_results["components"].items():
            if isinstance(status, dict):
                health = "✅" if status.get("healthy", False) else "❌"
                print(f"  {health} {component}")
        
        # Issues
        print(f"\n⚠️  Total Issues Found: {len(self.audit_results['issues'])}")
        critical = [i for i in self.audit_results["issues"] if i["severity"] == "critical"]
        if critical:
            print(f"  🔴 Critical: {len(critical)}")
            for issue in critical[:3]:  # Show first 3
                print(f"     - {issue['component']}: {issue['issue']}")
        
        # Fixes applied
        if self.fixes_applied:
            print(f"\n🔧 Fixes Applied: {len(self.fixes_applied)}")
            for fix in self.fixes_applied:
                print(f"  ✅ {fix}")
        
        # Recommendations
        if self.audit_results["recommendations"]:
            print(f"\n💡 Recommendations:")
            for rec in self.audit_results["recommendations"][:3]:  # Show first 3
                print(f"  • [{rec['priority'].upper()}] {rec['component']}: {rec['action']}")
        
        print("\n" + "=" * 60)
        print("✅ Audit complete. Run 'scripts/remediate_system.sh' to apply all fixes.")
        print("=" * 60)


if __name__ == "__main__":
    auditor = SystemAuditor()
    auditor.run_audit()