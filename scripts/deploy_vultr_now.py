#!/usr/bin/env python3
"""
Immediate Vultr deployment with test/demo configuration
"""

import os
import sys
import json
import time
from pathlib import Path

# For testing/demo purposes - replace with actual API key
DEMO_API_KEY = "VULTR_TEST_KEY_REPLACE_WITH_ACTUAL"

def main():
    print("🚀 cherry_ai MCP Vultr Deployment (Demo Mode)")
    print("=" * 50)
    
    # Check for API key
    api_key = os.getenv("VULTR_API_KEY") or DEMO_API_KEY
    
    if api_key == "VULTR_TEST_KEY_REPLACE_WITH_ACTUAL":
        print("\n⚠️  DEMO MODE - No actual resources will be created")
        print("\nTo deploy for real:")
        print("1. Get your Vultr API key from https://my.vultr.com/")
        print("2. Add to .env file: VULTR_API_KEY=your-actual-key")
        print("3. Run this script again")
        
        # Create demo deployment info
        demo_info = {
            "status": "demo",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "message": "Demo deployment - no actual resources created",
            "next_steps": [
                "Add VULTR_API_KEY to .env file",
                "Run deployment script again",
                "Or use manual deployment steps below"
            ],
            "manual_deployment": {
                "vultr_resources": {
                    "vpc": "10.0.0.0/24 in ewr region",
                    "firewall": "Allow 22,80,443,8000,3000 + internal",
                    "database_server": "vc2-4c-8gb (4 vCPU, 8GB RAM)",
                    "app_servers": "2x vc2-2c-4gb (2 vCPU, 4GB RAM)",
                    "load_balancer": "Round-robin HTTP/HTTPS"
                },
                "estimated_cost": "$100-150/month",
                "deployment_time": "~10-15 minutes"
            }
        }
        
        with open("deployment_demo.json", "w") as f:
            json.dump(demo_info, f, indent=2)
            
        print("\n📄 Created deployment_demo.json with deployment details")
        
    else:
        print(f"\n✓ API Key found: {api_key[:10]}...")
        print("\n⚠️  PRODUCTION DEPLOYMENT")
        print("This will create real resources on Vultr")
        print("\nEstimated cost: $100-150/month")
        print("\nResources to create:")
        print("- 1 VPC network")
        print("- 1 Firewall group")
        print("- 3 Servers (1 DB + 2 App)")
        print("- 1 Load balancer")
        
        # For now, just show what would be deployed
        print("\n❌ Actual deployment not implemented in this demo script")
        print("   Use scripts/vultr_direct_deploy.py for real deployment")
        
    # Show local testing option
    print("\n💡 Alternative: Test locally first")
    print("=" * 50)
    print("You can test the entire system locally using Docker:")
    print("\n1. Start services:")
    print("   docker-compose up -d")
    print("\n2. Check status:")
    print("   docker-compose ps")
    print("\n3. Access services:")
    print("   - API: http://localhost:8000")
    print("   - Grafana: http://localhost:3000")
    print("   - Prometheus: http://localhost:9090")
    
    # Create local test script
    local_test = """#!/bin/bash
# Quick local test of cherry_ai MCP

echo "🚀 Starting cherry_ai MCP locally..."
docker-compose up -d

echo "⏳ Waiting for services to start..."
sleep 30

echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🌐 Access Points:"
echo "   API: http://localhost:8000"
echo "   Grafana: http://localhost:3000"
echo "   Prometheus: http://localhost:9090"

echo ""
echo "🧪 Running health checks..."
curl -s http://localhost:8000/health || echo "API not ready yet"

echo ""
echo "✅ Local deployment complete!"
echo "   Use 'docker-compose logs -f' to view logs"
echo "   Use 'docker-compose down' to stop services"
"""
    
    with open("test_local.sh", "w") as f:
        f.write(local_test)
    os.chmod("test_local.sh", 0o755)
    
    print("\n📄 Created test_local.sh for local testing")
    print("   Run: ./test_local.sh")

if __name__ == "__main__":
    main()