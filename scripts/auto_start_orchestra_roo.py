#!/usr/bin/env python3
"""Auto-start Cherry AI with Roo integration"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional
from typing_extensions import Optional


class cherry_aiRooAutoStarter:
    """Automatically starts and integrates Cherry AI with Roo."""
    
    def __init__(self):
        self.project_root = Path("/root/cherry_ai-main")
        self.venv_python = self.project_root / "venv" / "bin" / "python"
        self.services_started = False
        self.integration_enabled = False
    
    def check_service(self, name: str, check_cmd: List[str]) -> bool:
        """Check if a service is running"""
        try:
            result = subprocess.run(check_cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    async def start_docker_services(self):
        """Start all required Docker services"""
        print("🐳 Starting Docker services...")
        
        # Check if Docker is running
        if not self.check_service("Docker", ["docker", "info"]):
            print("❌ Docker is not running. Please start Docker first.")
            return False
        
        # Start services
        cmd = ["docker-compose", "-f", "docker-compose.local.yml", "up", "-d"]
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Failed to start services: {result.stderr}")
            return False
        
        print("✅ Docker services started")
        
        # Wait for services to be ready
        print("⏳ Waiting for services to be ready...")
        await asyncio.sleep(10)
        
        # Check service health
        services = ["postgres", "redis", "weaviate"]
        for service in services:
            if self.check_service(service, ["docker", "ps", "-q", "-f", f"name={service}"]):
                print(f"✅ {service} is running")
            else:
                print(f"❌ {service} is not running")
                return False
        
        self.services_started = True
        return True
    
    async def enable_cherry_ai_integration(self):
        """Enable Cherry AI integration in Roo"""
        print("🎭 Enabling Cherry AI integration...")
        
        integration_script = self.project_root / "scripts" / "activate_cherry_ai_in_roo.py"
        
        if not integration_script.exists():
            # Create the integration activation script
            content = """
import sys
sys.path.append('/root/cherry_ai-main')

try:
    from .roo.integrations.cherry_ai_ai import initialize_cherry_ai_integration
    initialize_cherry_ai_integration()
    print("✅ Cherry AI integration enabled in Roo")
except Exception as e:
    print(f"❌ Failed to enable integration: {e}")
"""
            integration_script.write_text(content)
        
        # Run the integration script
        result = subprocess.run(
            [sys.executable, str(integration_script)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Cherry AI integration enabled")
            self.integration_enabled = True
            return True
        else:
            print(f"❌ Failed to enable integration: {result.stderr}")
            return False
    
    async def verify_system(self):
        """Verify the entire system is working"""
        print("🔍 Verifying system...")
        
        checks = [
            ("PostgreSQL", ["pg_isready", "-h", "localhost", "-p", "5432"]),
            ("Redis", ["redis-cli", "ping"]),
            ("API Health", ["curl", "-s", "http://localhost:8001/health"])
        ]
        
        all_good = True
        for name, cmd in checks:
            if self.check_service(name, cmd):
                print(f"✅ {name} check passed")
            else:
                print(f"❌ {name} check failed")
                all_good = False
        
        return all_good
    
    async def run(self):
        """Main execution flow"""
        print("🚀 Cherry AI Auto-Starter")
        print("=" * 50)
        
        # Start Docker services
        if not await self.start_docker_services():
            print("❌ Failed to start Docker services")
            return False
        
        # Enable Roo integration
        if not await self.enable_cherry_ai_integration():
            print("❌ Failed to enable Roo integration")
            return False
        
        # Verify system
        if not await self.verify_system():
            print("❌ System verification failed")
            return False
        
        print("\n✅ Cherry AI is ready!")
        print("🌐 Access the UI at: http://localhost:3000")
        print("📚 API docs at: http://localhost:8001/docs")
        print("🎭 Roo integration is active")
        
        return True


async def main():
    """Main entry point"""
    starter = cherry_aiRooAutoStarter()
    success = await starter.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
