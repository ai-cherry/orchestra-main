import logging
logger = logging.getLogger(__name__)

#!/usr/bin/env python3
"""
Test Unified Integration of Single-User Auth and AI Agent Discovery
Ensures no conflicts or redundancies between the two systems
"""

import os
import sys
import json
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, List, Any

class UnifiedIntegrationTest:
    def __init__(self):
        self.api_key = os.getenv("cherry_ai_API_KEY", "")
        self.base_url = "http://localhost:8010"
        self.results = {
            "auth_tests": [],
            "discovery_tests": [],
            "routing_tests": [],
            "performance_tests": [],
            "conflicts": []
        }
    
    async def run_all_tests(self):
        """Run comprehensive integration tests."""
        print("🧪 Testing Unified Integration")
        print("=" * 60)
        
        # Test 1: Authentication works with discovery
        await self.test_auth_discovery_integration()
        
        # Test 2: Smart routing respects auth context
        await self.test_context_aware_routing()
        
        # Test 3: No redundant auth checks
        await self.test_no_redundant_auth()
        
        # Test 4: Performance optimization for single user
        await self.test_single_user_performance()
        
        # Test 5: Check for conflicts
        await self.check_for_conflicts()
        
        # Generate report
        self.generate_report()
    
    async def test_auth_discovery_integration(self):
        """Test that discovery endpoint requires and respects authentication."""
        print("\n1️⃣ Testing Auth + Discovery Integration")
        
        async with aiohttp.ClientSession() as session:
            # Test without auth
            try:
                async with session.get(f"{self.base_url}/discover") as resp:
                    if resp.status == 401:
                        self.results["auth_tests"].append({
                            "test": "discovery_no_auth",
                            "status": "PASS",
                            "message": "Discovery correctly requires authentication"
                        })
                    else:
                        self.results["auth_tests"].append({
                            "test": "discovery_no_auth",
                            "status": "FAIL",
                            "message": f"Expected 401, got {resp.status}"
                        })
            except Exception as e:
                self.results["auth_tests"].append({
                    "test": "discovery_no_auth",
                    "status": "ERROR",
                    "message": str(e)
                })
            
            # Test with auth
            headers = {"X-API-Key": self.api_key}
            try:
                async with session.get(f"{self.base_url}/discover", headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if "mcp_servers" in data and "auth" in data:
                            self.results["auth_tests"].append({
                                "test": "discovery_with_auth",
                                "status": "PASS",
                                "message": "Discovery works with authentication"
                            })
                        else:
                            self.results["auth_tests"].append({
                                "test": "discovery_with_auth",
                                "status": "FAIL",
                                "message": "Discovery data incomplete"
                            })
                    else:
                        self.results["auth_tests"].append({
                            "test": "discovery_with_auth",
                            "status": "FAIL",
                            "message": f"Expected 200, got {resp.status}"
                        })
            except Exception as e:
                self.results["auth_tests"].append({
                    "test": "discovery_with_auth",
                    "status": "ERROR",
                    "message": str(e)
                })
    
    async def test_context_aware_routing(self):
        """Test that routing respects operational context."""
        print("\n2️⃣ Testing Context-Aware Routing")
        
        headers = {"X-API-Key": self.api_key}
        
        # Test different request types
        test_requests = [
            {
                "agent_type": "roo",
                "request_type": "code_analysis"
            },
            {
                "agent_type": "factory-debug",
                "request_type": "error_analysis"
            },
            {
                "agent_type": "cursor",
                "request_type": "code_completion"
            }
        ]
        
        async with aiohttp.ClientSession() as session:
            for test_req in test_requests:
                try:
                    async with session.post(
                        f"{self.base_url}/route",
                        json=test_req,
                        headers=headers
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if "target_server" in data and "auth_required" in data:
                                self.results["routing_tests"].append({
                                    "test": f"route_{test_req['agent_type']}_{test_req['request_type']}",
                                    "status": "PASS",
                                    "message": f"Routed to {data['target_server']}"
                                })
                            else:
                                self.results["routing_tests"].append({
                                    "test": f"route_{test_req['agent_type']}_{test_req['request_type']}",
                                    "status": "FAIL",
                                    "message": "Incomplete routing response"
                                })
                        else:
                            self.results["routing_tests"].append({
                                "test": f"route_{test_req['agent_type']}_{test_req['request_type']}",
                                "status": "FAIL",
                                "message": f"Expected 200, got {resp.status}"
                            })
                except Exception as e:
                    self.results["routing_tests"].append({
                        "test": f"route_{test_req['agent_type']}_{test_req['request_type']}",
                        "status": "ERROR",
                        "message": str(e)
                    })
    
    async def test_no_redundant_auth(self):
        """Ensure no redundant authentication checks."""
        print("\n3️⃣ Testing No Redundant Auth")
        
        # Check configuration files for duplicate auth settings
        config_files = [
            ".roo/mcp.json",
            ".factory/config.yaml",
            "mcp_discovery.json"
        ]
        
        auth_configs = []
        
        for config_file in config_files:
            path = Path(config_file)
            if path.exists():
                with open(path) as f:
                    if path.suffix == ".json":
                        data = json.load(f)
                    else:
                        import yaml
                        data = yaml.safe_load(f)
                    
                    # Look for auth configurations
                    auth_found = self._find_auth_config(data)
                    if auth_found:
                        auth_configs.append({
                            "file": config_file,
                            "auth_config": auth_found
                        })
        
        # Check for redundancy
        if len(auth_configs) > 1:
            # Ensure they all point to the same auth system
            auth_modes = [cfg.get("auth_config", {}).get("mode") for cfg in auth_configs]
            if all(mode == "single_user" for mode in auth_modes if mode):
                self.results["discovery_tests"].append({
                    "test": "auth_redundancy",
                    "status": "PASS",
                    "message": "All configs use consistent single-user auth"
                })
            else:
                self.results["conflicts"].append({
                    "type": "auth_redundancy",
                    "severity": "HIGH",
                    "message": "Inconsistent auth configurations found",
                    "details": auth_configs
                })
    
    def _find_auth_config(self, data: Any, path: str = "") -> Dict:
        """Recursively find auth configuration in data."""
        if isinstance(data, dict):
            if "auth" in data or "authentication" in data:
                return data.get("auth", data.get("authentication"))
            for key, value in data.items():
                result = self._find_auth_config(value, f"{path}.{key}")
                if result:
                    return result
        elif isinstance(data, list):
            for i, item in enumerate(data):
                result = self._find_auth_config(item, f"{path}[{i}]")
                if result:
                    return result
        return None
    
    async def test_single_user_performance(self):
        """Test performance optimizations for single user."""
        print("\n4️⃣ Testing Single-User Performance")
        
        headers = {"X-API-Key": self.api_key}
        
        # Make multiple rapid requests
        start_time = asyncio.get_event_loop().time()
        request_count = 50
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(request_count):
                task = session.get(f"{self.base_url}/health", headers=headers)
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
        end_time = asyncio.get_event_loop().time()
        total_time = end_time - start_time
        avg_time = (total_time / request_count) * 1000  # Convert to ms
        
        # Check if rate limiting is disabled in development
        successful_responses = sum(1 for r in responses if not isinstance(r, Exception) and r.status == 200)
        
        if successful_responses == request_count:
            self.results["performance_tests"].append({
                "test": "rate_limiting",
                "status": "PASS",
                "message": f"No rate limiting in development mode ({request_count} requests)"
            })
        else:
            self.results["performance_tests"].append({
                "test": "rate_limiting",
                "status": "FAIL",
                "message": f"Rate limiting active: {successful_responses}/{request_count} succeeded"
            })
        
        # Check response time
        if avg_time < 50:  # Target: < 50ms average
            self.results["performance_tests"].append({
                "test": "response_time",
                "status": "PASS",
                "message": f"Average response time: {avg_time:.2f}ms"
            })
        else:
            self.results["performance_tests"].append({
                "test": "response_time",
                "status": "WARN",
                "message": f"Average response time: {avg_time:.2f}ms (target: <50ms)"
            })
    
    async def check_for_conflicts(self):
        """Check for any conflicts between systems."""
        print("\n5️⃣ Checking for Conflicts")
        
        # Check for duplicate endpoints
        endpoints = {
            "auth": [],
            "discovery": [],
            "health": []
        }
        
        # Scan for endpoint definitions
        server_files = list(Path("mcp_server/servers").glob("*.py"))
        
        for server_file in server_files:
            with open(server_file) as f:
                content = f.read()
                
                # Look for endpoint definitions
                if "@app.get" in content or "@app.post" in content:
                    # Simple pattern matching for endpoints
                    import re
                    endpoint_pattern = r'@app\.(get|post)\("([^"]+)"\)'
                    matches = re.findall(endpoint_pattern, content)
                    
                    for method, path in matches:
                        if "/health" in path:
                            endpoints["health"].append({
                                "file": str(server_file),
                                "method": method,
                                "path": path
                            })
                        elif "/discover" in path:
                            endpoints["discovery"].append({
                                "file": str(server_file),
                                "method": method,
                                "path": path
                            })
                        elif "auth" in path.lower():
                            endpoints["auth"].append({
                                "file": str(server_file),
                                "method": method,
                                "path": path
                            })
        
        # Check for conflicts
        for endpoint_type, definitions in endpoints.items():
            if len(definitions) > 1:
                # Check if they're on different ports
                unique_files = set(d["file"] for d in definitions)
                if len(unique_files) > 1:
                    self.results["conflicts"].append({
                        "type": "endpoint_conflict",
                        "severity": "MEDIUM",
                        "message": f"Multiple {endpoint_type} endpoints defined",
                        "details": definitions
                    })
    
    def generate_report(self):
        """Generate comprehensive test report."""
        print("\n" + "=" * 60)
        print("📊 INTEGRATION TEST REPORT")
        print("=" * 60)
        
        # Summary
        total_tests = sum(len(v) for k, v in self.results.items() if k != "conflicts")
        passed_tests = sum(
            1 for k, v in self.results.items() 
            if k != "conflicts" 
            for test in v 
            if test.get("status") == "PASS"
        )
        
        print(f"\n✅ Passed: {passed_tests}/{total_tests}")
        
        # Detailed results
        for category, tests in self.results.items():
            if category == "conflicts":
                continue
                
            print(f"\n{category.replace('_', ' ').title()}:")
            for test in tests:
                status_emoji = {
                    "PASS": "✅",
                    "FAIL": "❌",
                    "WARN": "⚠️",
                    "ERROR": "🔥"
                }.get(test["status"], "❓")
                
                print(f"  {status_emoji} {test['test']}: {test['message']}")
        
        # Conflicts
        if self.results["conflicts"]:
            print("\n⚠️  CONFLICTS DETECTED:")
            for conflict in self.results["conflicts"]:
                print(f"  - {conflict['type']} ({conflict['severity']}): {conflict['message']}")
                if "details" in conflict:
                    print(f"    Details: {json.dumps(conflict['details'], indent=6)}")
        else:
            print("\n✅ No conflicts detected!")
        
        # Save report
        report_path = Path("integration_test_report.json")
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Full report saved to: {report_path}")


async def main():
    """Run integration tests."""
    # Check if services are running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8010/health") as resp:
                if resp.status != 200:
                    print("❌ Smart router not running. Start services first:")
                    print("   ./start_unified_cherry_ai.sh")
                    sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print("❌ Services not running. Start them first:")
        print("   ./start_unified_cherry_ai.sh")
        sys.exit(1)
    
    # Run tests
    tester = UnifiedIntegrationTest()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())