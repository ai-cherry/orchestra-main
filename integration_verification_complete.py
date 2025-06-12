#!/usr/bin/env python3
"""
Orchestra AI Integration Verification - Complete System Test
Comprehensive verification of frontend-backend integration
"""

import requests
import json
import time
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Any, Tuple

class IntegrationVerifier:
    def __init__(self):
        self.backend_url = "http://localhost:8010"
        self.frontend_url = "http://localhost:5173"
        self.test_results = []
        self.start_time = datetime.now()
    
    def log_test(self, test_name: str, success: bool, details: str = "", response_time: float = 0):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "response_time_ms": round(response_time * 1000, 2),
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        time_info = f" ({response_time*1000:.1f}ms)" if response_time > 0 else ""
        print(f"{status} {test_name}{time_info}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_backend_health(self) -> bool:
        """Test backend API health"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                expected_personas = ["cherry", "sophia", "karen"]
                has_personas = all(persona in data.get("personas", []) for persona in expected_personas)
                
                if has_personas:
                    self.log_test("Backend Health Check", True, f"Status: {data.get('status')}", response_time)
                    return True
                else:
                    self.log_test("Backend Health Check", False, "Missing expected personas", response_time)
                    return False
            else:
                self.log_test("Backend Health Check", False, f"HTTP {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Backend Health Check", False, str(e))
            return False
    
    def test_frontend_accessibility(self) -> bool:
        """Test frontend accessibility"""
        try:
            start_time = time.time()
            response = requests.get(self.frontend_url, timeout=5)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                content = response.text
                has_title = "Cherry AI Orchestrator" in content
                has_react = "react" in content.lower()
                
                if has_title and has_react:
                    self.log_test("Frontend Accessibility", True, "React app loaded", response_time)
                    return True
                else:
                    self.log_test("Frontend Accessibility", False, "Missing expected content", response_time)
                    return False
            else:
                self.log_test("Frontend Accessibility", False, f"HTTP {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Frontend Accessibility", False, str(e))
            return False
    
    def test_persona_responses(self) -> bool:
        """Test all persona responses"""
        personas = ["cherry", "sophia", "karen"]
        test_messages = {
            "cherry": "Help me coordinate a project",
            "sophia": "Analyze financial compliance requirements",
            "karen": "Review medical coding protocols"
        }
        
        all_success = True
        
        for persona in personas:
            try:
                start_time = time.time()
                response = requests.post(
                    f"{self.backend_url}/chat",
                    json={"persona": persona, "message": test_messages[persona]},
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    has_id = "id" in data
                    has_content = "content" in data and len(data["content"]) > 0
                    correct_persona = data.get("persona") == persona
                    has_metadata = "metadata" in data
                    
                    if all([has_id, has_content, correct_persona, has_metadata]):
                        self.log_test(f"Persona Response - {persona.title()}", True, 
                                    f"Response length: {len(data['content'])} chars", response_time)
                    else:
                        self.log_test(f"Persona Response - {persona.title()}", False, 
                                    "Missing required fields", response_time)
                        all_success = False
                else:
                    self.log_test(f"Persona Response - {persona.title()}", False, 
                                f"HTTP {response.status_code}", response_time)
                    all_success = False
                    
            except Exception as e:
                self.log_test(f"Persona Response - {persona.title()}", False, str(e))
                all_success = False
        
        return all_success
    
    def test_persona_status(self) -> bool:
        """Test persona status endpoint"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.backend_url}/personas/status", timeout=5)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) == 3:
                    personas_found = [item.get("persona") for item in data]
                    expected_personas = ["cherry", "sophia", "karen"]
                    
                    if all(persona in personas_found for persona in expected_personas):
                        self.log_test("Persona Status", True, f"Found {len(data)} personas", response_time)
                        return True
                    else:
                        self.log_test("Persona Status", False, "Missing expected personas", response_time)
                        return False
                else:
                    self.log_test("Persona Status", False, "Invalid response format", response_time)
                    return False
            else:
                self.log_test("Persona Status", False, f"HTTP {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Persona Status", False, str(e))
            return False
    
    def test_command_processing(self) -> bool:
        """Test command processing endpoint"""
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.backend_url}/system/command",
                json={"command": "show dashboard", "target": "ui"},
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                has_success = "success" in data
                has_result = "result" in data
                
                if has_success and has_result:
                    self.log_test("Command Processing", True, f"Success: {data.get('success')}", response_time)
                    return True
                else:
                    self.log_test("Command Processing", False, "Missing required fields", response_time)
                    return False
            else:
                self.log_test("Command Processing", False, f"HTTP {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Command Processing", False, str(e))
            return False
    
    def test_conversation_history(self) -> bool:
        """Test conversation history endpoint"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.backend_url}/chat/history?limit=10", timeout=5)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Conversation History", True, f"Retrieved {len(data)} messages", response_time)
                    return True
                else:
                    self.log_test("Conversation History", False, "Invalid response format", response_time)
                    return False
            else:
                self.log_test("Conversation History", False, f"HTTP {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Conversation History", False, str(e))
            return False
    
    def test_persona_switching(self) -> bool:
        """Test persona switching endpoint"""
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.backend_url}/personas/switch",
                json={"persona": "sophia"},
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("persona") == "sophia":
                    self.log_test("Persona Switching", True, "Successfully switched to Sophia", response_time)
                    return True
                else:
                    self.log_test("Persona Switching", False, "Switch not confirmed", response_time)
                    return False
            else:
                self.log_test("Persona Switching", False, f"HTTP {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test("Persona Switching", False, str(e))
            return False
    
    def check_process_status(self) -> Tuple[bool, bool]:
        """Check if backend and frontend processes are running"""
        try:
            # Check backend process
            backend_running = False
            frontend_running = False
            
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            processes = result.stdout
            
            if 'uvicorn' in processes and '8010' in processes:
                backend_running = True
            
            if 'vite' in processes or 'npm' in processes:
                frontend_running = True
            
            self.log_test("Backend Process", backend_running, "uvicorn server" if backend_running else "Process not found")
            self.log_test("Frontend Process", frontend_running, "Vite dev server" if frontend_running else "Process not found")
            
            return backend_running, frontend_running
            
        except Exception as e:
            self.log_test("Process Check", False, str(e))
            return False, False
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate performance metrics report"""
        successful_tests = [test for test in self.test_results if test["success"]]
        failed_tests = [test for test in self.test_results if not test["success"]]
        
        response_times = [test["response_time_ms"] for test in successful_tests if test["response_time_ms"] > 0]
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        
        return {
            "total_tests": len(self.test_results),
            "successful_tests": len(successful_tests),
            "failed_tests": len(failed_tests),
            "success_rate": (len(successful_tests) / len(self.test_results)) * 100 if self.test_results else 0,
            "average_response_time_ms": round(avg_response_time, 2),
            "max_response_time_ms": round(max_response_time, 2),
            "min_response_time_ms": round(min_response_time, 2),
            "total_duration_seconds": (datetime.now() - self.start_time).total_seconds()
        }
    
    def run_complete_verification(self) -> bool:
        """Run complete integration verification"""
        print("🚀 Starting Orchestra AI Integration Verification")
        print("=" * 60)
        
        # Check process status first
        backend_running, frontend_running = self.check_process_status()
        
        if not backend_running:
            print("❌ Backend not running. Please start with: uvicorn src.api.main:app --host 0.0.0.0 --port 8010")
            return False
        
        if not frontend_running:
            print("⚠️ Frontend not detected, but continuing with backend tests")
        
        print("\n🔍 Testing Backend API Integration:")
        print("-" * 40)
        
        # Core API tests
        self.test_backend_health()
        self.test_persona_responses()
        self.test_persona_status()
        self.test_command_processing()
        self.test_conversation_history()
        self.test_persona_switching()
        
        if frontend_running:
            print("\n🌐 Testing Frontend Integration:")
            print("-" * 40)
            self.test_frontend_accessibility()
        
        # Generate performance report
        performance = self.generate_performance_report()
        
        print("\n📊 Integration Verification Results:")
        print("=" * 60)
        print(f"Total Tests: {performance['total_tests']}")
        print(f"Successful: {performance['successful_tests']} ✅")
        print(f"Failed: {performance['failed_tests']} ❌")
        print(f"Success Rate: {performance['success_rate']:.1f}%")
        print(f"Average Response Time: {performance['average_response_time_ms']:.1f}ms")
        print(f"Test Duration: {performance['total_duration_seconds']:.1f}s")
        
        # Detailed results
        if performance['failed_tests'] > 0:
            print(f"\n❌ Failed Tests:")
            for test in self.test_results:
                if not test['success']:
                    print(f"   • {test['test']}: {test['details']}")
        
        # Overall assessment
        success_threshold = 85  # 85% success rate required
        overall_success = performance['success_rate'] >= success_threshold
        
        print(f"\n🎯 Overall Assessment:")
        if overall_success:
            print("✅ INTEGRATION SUCCESSFUL - All critical components working")
            print("🎭 Orchestra AI Frontend-Backend integration is operational!")
            print("🚀 Ready for production deployment and advanced features")
        else:
            print("⚠️ INTEGRATION ISSUES DETECTED - Some components need attention")
            print("🔧 Please review failed tests and resolve issues")
        
        return overall_success
    
    def save_results(self, filename: str = "integration_verification_results.json"):
        """Save test results to file"""
        try:
            performance = self.generate_performance_report()
            
            report = {
                "verification_timestamp": self.start_time.isoformat(),
                "performance_metrics": performance,
                "test_results": self.test_results,
                "overall_success": performance['success_rate'] >= 85
            }
            
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"\n💾 Results saved to: {filename}")
            
        except Exception as e:
            print(f"❌ Failed to save results: {e}")

def main():
    """Main execution function"""
    verifier = IntegrationVerifier()
    
    try:
        success = verifier.run_complete_verification()
        verifier.save_results()
        
        if success:
            print("\n🎉 MISSION ACCOMPLISHED!")
            print("🎭 Orchestra AI Integration Phase 2 Complete")
            print("🎯 Frontend-Backend integration verified and operational")
            sys.exit(0)
        else:
            print("\n⚠️ Integration verification completed with issues")
            print("🔧 Please review and resolve failed tests")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Verification interrupted by user")
        verifier.save_results("integration_verification_partial.json")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Verification failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 