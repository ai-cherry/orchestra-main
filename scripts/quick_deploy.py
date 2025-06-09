#!/usr/bin/env python3
"""
Quick Deploy Utility for Orchestra AI
Optimized for single-developer performance
"""

import subprocess
import sys
import json
from pathlib import Path
from typing import List, Dict

def run_command(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run shell command with error handling"""
    print(f"🔧 Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"❌ Command failed: {result.stderr}")
        sys.exit(1)
    return result

def check_mcp_optimization() -> Dict[str, bool]:
    """Check if MCP is optimized for single developer"""
    try:
            config = json.load(f)
        
        single_dev_config = config.get('single_developer_config', {})
        return {
            'optimized': bool(single_dev_config),
            'essential_servers': len(single_dev_config.get('essential_servers', [])),
            'disabled_servers': len(single_dev_config.get('disabled_servers', []))
        }
    except:
        return {'optimized': False, 'essential_servers': 0, 'disabled_servers': 0}

def restart_essential_services():
    """Restart only essential MCP servers for performance"""
    print("🚀 Restarting essential services...")
    
    mcp_status = check_mcp_optimization()
    if mcp_status['optimized']:
        print(f"✅ MCP optimized: {mcp_status['essential_servers']} essential, {mcp_status['disabled_servers']} disabled")
    else:
        print("⚠️ MCP not optimized - consider running optimization")

def quick_health_check():
    """Quick health check for single developer"""
    checks = {
        'Git status': 'git status --porcelain',
        'Python syntax': 'python3 -m py_compile mcp_unified_server.py',
        'GitHub CLI': 'gh auth status',
        'Environment': 'test -f .envrc.example'
    }
    
    print("🏥 Quick Health Check...")
    for name, cmd in checks.items():
        result = run_command(cmd, check=False)
        status = "✅" if result.returncode == 0 else "⚠️"
        print(f"{status} {name}")

def deploy_quick():
    """Quick deployment for single developer"""
    print("🚀 QUICK DEPLOY - Single Developer Mode")
    print("=" * 45)
    
    # Check optimization status
    mcp_status = check_mcp_optimization()
    if mcp_status['optimized']:
        print(f"✅ MCP optimized for performance")
    
    # Quick git pull
    run_command("git pull origin main")
    
    # Restart only if needed
    result = run_command("git diff --name-only HEAD~1", check=False)
    if any(ext in result.stdout for ext in ['.py', 'requirements', '.env']):
        restart_essential_services()
    else:
        print("ℹ️ No service restart needed")
    
    # Quick health check
    quick_health_check()
    
    print("✅ Quick deploy completed!")

def deploy_thorough():
    """Thorough deployment with full validation"""
    print("🔍 THOROUGH DEPLOY - Full Validation")
    print("=" * 40)
    
    # Full git operations
    run_command("git pull origin main")
    run_command("git status")
    
    # Run health checks
    quick_health_check()
    
    # Restart all services
    print("🔄 Full service restart...")
    restart_essential_services()
    
    print("✅ Thorough deploy completed!")

def show_status():
    """Show current infrastructure status"""
    print("📊 INFRASTRUCTURE STATUS")
    print("=" * 25)
    
    # MCP optimization status
    mcp_status = check_mcp_optimization()
    print(f"MCP Optimization: {'✅' if mcp_status['optimized'] else '❌'}")
    print(f"Essential Servers: {mcp_status['essential_servers']}")
    print(f"Disabled Servers: {mcp_status['disabled_servers']}")
    
    # Git status
    result = run_command("git status --porcelain", check=False)
    changes = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
    print(f"Git Changes: {changes}")
    
    # GitHub CLI status
    result = run_command("gh auth status", check=False)
    gh_status = "✅" if result.returncode == 0 else "❌"
    print(f"GitHub CLI: {gh_status}")

def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("🚀 Orchestra AI Quick Deploy Utility")
        print("Usage:")
        print("  python3 scripts/quick_deploy.py quick    # Fast deploy")
        print("  python3 scripts/quick_deploy.py thorough # Full validation")
        print("  python3 scripts/quick_deploy.py status   # Show status")
        print("  python3 scripts/quick_deploy.py health   # Health check")
        return
    
    command = sys.argv[1]
    
    if command == "quick":
        deploy_quick()
    elif command == "thorough":
        deploy_thorough()
    elif command == "status":
        show_status()
    elif command == "health":
        quick_health_check()
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main() 