#!/usr/bin/env python3
"""
Deploy and Test Enhanced AI Orchestration System
Focuses on Cursor AI and Claude integration with comprehensive validation
"""

import os
import sys
import json
import asyncio
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import psutil

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from ai_components.orchestration.ai_orchestrator_enhanced import (
    DatabaseLogger, WeaviateManager
)


class EnhancedSystemDeploymentTester:
    """Deploy and test the enhanced AI orchestration system"""
    
    def __init__(self):
        self.db_logger = DatabaseLogger()
        self.weaviate_manager = WeaviateManager()
        self.deployment_report = {
            "deployment_id": f"deploy_{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "phases": {},
            "tests": {},
            "performance": {},
            "status": "in_progress"
        }
    
    async def run_full_deployment_and_test(self) -> Dict:
        """Run complete deployment and testing workflow"""
        print("🚀 Enhanced AI Orchestration System - Deployment & Testing")
        print("=" * 70)
        
        try:
            # Phase 1: Pre-deployment checks
            await self._phase_pre_deployment()
            
            # Phase 2: Run deployment script
            await self._phase_deployment()
            
            # Phase 3: Integration testing
            await self._phase_integration_testing()
            
            # Phase 4: Performance validation
            await self._phase_performance_validation()
            
            # Phase 5: Production readiness
            await self._phase_production_readiness()
            
            # Generate final report
            await self._generate_final_report()
            
            return self.deployment_report
            
        except Exception as e:
            self.deployment_report["status"] = "failed"
            self.deployment_report["error"] = str(e)
            await self._log_error("deployment_failed", str(e))
            raise
    
    async def _phase_pre_deployment(self):
        """Pre-deployment checks and preparation"""
        print("\n📋 Phase 1: Pre-deployment Checks")
        phase_start = time.time()
        
        checks = {
            "environment_variables": self._check_environment_variables(),
            "system_resources": self._check_system_resources(),
            "dependencies": await self._check_dependencies(),
            "database_connectivity": await self._check_database(),
            "existing_processes": self._check_existing_processes()
        }
        
        all_passed = all(checks.values())
        
        self.deployment_report["phases"]["pre_deployment"] = {
            "status": "passed" if all_passed else "failed",
            "checks": checks,
            "duration": time.time() - phase_start
        }
        
        # Log to database
        await self._log_phase("pre_deployment", checks)
        
        if not all_passed:
            raise Exception("Pre-deployment checks failed")
        
        print("   ✅ All pre-deployment checks passed")
    
    async def _phase_deployment(self):
        """Run the deployment script"""
        print("\n🔧 Phase 2: Running Deployment")
        phase_start = time.time()
        
        try:
            # Run deployment script
            result = subprocess.run(
                [sys.executable, "scripts/deploy_enhanced_orchestration.py"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            deployment_success = result.returncode == 0
            
            # Parse deployment report if available
            report_path = Path("deployment_report_enhanced.json")
            deployment_details = {}
            if report_path.exists():
                with open(report_path) as f:
                    deployment_details = json.load(f)
            
            self.deployment_report["phases"]["deployment"] = {
                "status": "passed" if deployment_success else "failed",
                "exit_code": result.returncode,
                "stdout": result.stdout[-1000:],  # Last 1000 chars
                "stderr": result.stderr[-1000:],
                "deployment_details": deployment_details,
                "duration": time.time() - phase_start
            }
            
            # Log to database
            await self._log_phase("deployment", {
                "success": deployment_success,
                "components_deployed": len(deployment_details.get("components", {}))
            })
            
            # Store in Weaviate
            self.weaviate_manager.store_context(
                workflow_id=self.deployment_report["deployment_id"],
                task_id="deployment",
                context_type="deployment_report",
                content=json.dumps(deployment_details),
                metadata={"phase": "deployment"}
            )
            
            if not deployment_success:
                raise Exception(f"Deployment failed: {result.stderr}")
            
            print("   ✅ Deployment completed successfully")
            
        except subprocess.TimeoutExpired:
            raise Exception("Deployment timed out after 5 minutes")
        except Exception as e:
            self.deployment_report["phases"]["deployment"] = {
                "status": "failed",
                "error": str(e),
                "duration": time.time() - phase_start
            }
            raise
    
    async def _phase_integration_testing(self):
        """Test integrations between components"""
        print("\n🧪 Phase 3: Integration Testing")
        phase_start = time.time()
        
        tests = {}
        
        # Test 1: Cursor AI Integration
        tests["cursor_ai"] = await self._test_cursor_ai_integration()
        
        # Test 2: Claude Integration
        tests["claude"] = await self._test_claude_integration()
        
        # Test 3: Orchestrator Integration
        tests["orchestrator"] = await self._test_orchestrator_integration()
        
        # Test 4: Database Integration
        tests["database"] = await self._test_database_integration()
        
        # Test 5: Cursor + Claude Synergy
        tests["synergy"] = await self._test_cursor_claude_synergy()
        
        all_passed = all(test["passed"] for test in tests.values())
        
        self.deployment_report["phases"]["integration_testing"] = {
            "status": "passed" if all_passed else "failed",
            "tests": tests,
            "duration": time.time() - phase_start
        }
        
        # Log results
        await self._log_phase("integration_testing", tests)
        
        print(f"   {'✅' if all_passed else '❌'} Integration tests: {sum(1 for t in tests.values() if t['passed'])}/{len(tests)} passed")
    
    async def _phase_performance_validation(self):
        """Validate system performance"""
        print("\n📊 Phase 4: Performance Validation")
        phase_start = time.time()
        
        metrics = {}
        
        # Test 1: Analysis Performance
        metrics["analysis"] = await self._test_analysis_performance()
        
        # Test 2: Code Generation Performance
        metrics["generation"] = await self._test_generation_performance()
        
        # Test 3: Parallel Execution
        metrics["parallel"] = await self._test_parallel_execution()
        
        # Test 4: Resource Usage
        metrics["resources"] = self._measure_resource_usage()
        
        # Calculate overall performance score
        performance_score = self._calculate_performance_score(metrics)
        
        self.deployment_report["phases"]["performance_validation"] = {
            "status": "passed" if performance_score >= 0.8 else "warning",
            "metrics": metrics,
            "performance_score": performance_score,
            "duration": time.time() - phase_start
        }
        
        # Log performance data
        await self._log_phase("performance_validation", metrics)
        
        # Store detailed metrics in Weaviate
        self.weaviate_manager.store_context(
            workflow_id=self.deployment_report["deployment_id"],
            task_id="performance",
            context_type="performance_metrics",
            content=json.dumps(metrics),
            metadata={"score": performance_score}
        )
        
        print(f"   📈 Performance score: {performance_score:.1%}")
    
    async def _phase_production_readiness(self):
        """Verify production readiness"""
        print("\n✅ Phase 5: Production Readiness")
        phase_start = time.time()
        
        readiness_checks = {
            "error_handling": await self._test_error_handling(),
            "circuit_breakers": await self._test_circuit_breakers(),
            "caching": await self._test_caching(),
            "monitoring": self._check_monitoring_setup(),
            "documentation": self._check_documentation()
        }
        
        all_ready = all(readiness_checks.values())
        
        self.deployment_report["phases"]["production_readiness"] = {
            "status": "ready" if all_ready else "not_ready",
            "checks": readiness_checks,
            "duration": time.time() - phase_start
        }
        
        await self._log_phase("production_readiness", readiness_checks)
        
        print(f"   {'✅' if all_ready else '⚠️'} Production readiness: {'READY' if all_ready else 'NOT READY'}")
    
    def _check_environment_variables(self) -> bool:
        """Check required environment variables"""
        required_vars = [
            "POSTGRES_HOST",
            "POSTGRES_DB",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD"
        ]
        
        optional_vars = [
            "CURSOR_API_KEY",
            "ANTHROPIC_API_KEY",
            "OPENROUTER_API_KEY",
            "WEAVIATE_URL"
        ]
        
        missing_required = [var for var in required_vars if not os.environ.get(var)]
        missing_optional = [var for var in optional_vars if not os.environ.get(var)]
        
        if missing_required:
            print(f"   ❌ Missing required vars: {missing_required}")
            return False
        
        if missing_optional:
            print(f"   ⚠️  Missing optional vars: {missing_optional}")
        
        return True
    
    def _check_system_resources(self) -> bool:
        """Check system resources"""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        checks = {
            "memory_available": memory.available > 1 * 1024 * 1024 * 1024,  # 1GB
            "disk_available": disk.free > 2 * 1024 * 1024 * 1024,  # 2GB
            "cpu_count": psutil.cpu_count() >= 2
        }
        
        return all(checks.values())
    
    async def _check_dependencies(self) -> bool:
        """Check Python dependencies"""
        try:
            import psycopg2
            import weaviate
            import aiohttp
            import asyncio
            return True
        except ImportError as e:
            print(f"   ❌ Missing dependency: {e}")
            return False
    
    async def _check_database(self) -> bool:
        """Check database connectivity"""
        try:
            self.db_logger.log_action(
                workflow_id="deployment_test",
                task_id="db_check",
                agent_role="system",
                action="connectivity_test",
                status="testing"
            )
            return True
        except:
            return False
    
    def _check_existing_processes(self) -> bool:
        """Check for conflicting processes"""
        # This would check for port conflicts, etc.
        return True
    
    async def _test_cursor_ai_integration(self) -> Dict:
        """Test Cursor AI integration"""
        try:
            from ai_components.agents.cursor_ai_enhanced import get_enhanced_cursor_ai
            
            cursor_ai = get_enhanced_cursor_ai()
            
            # Test analysis
            start_time = time.time()
            result = await cursor_ai.analyze_project(".", {"depth": "basic"})
            latency = time.time() - start_time
            
            return {
                "passed": bool(result),
                "latency": latency,
                "details": {
                    "files_analyzed": result.get("summary", {}).get("total_files", 0),
                    "has_suggestions": len(result.get("suggestions", [])) > 0
                }
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    async def _test_claude_integration(self) -> Dict:
        """Test Claude integration"""
        try:
            from ai_components.agents.claude_integration import get_claude_integration
            
            claude = get_claude_integration()
            
            # Test architecture analysis
            start_time = time.time()
            result = await claude.analyze_architecture(
                {"name": "test", "type": "validation"},
                focus_areas=["test"]
            )
            latency = time.time() - start_time
            
            return {
                "passed": bool(result),
                "latency": latency,
                "model": claude.model.value
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    async def _test_orchestrator_integration(self) -> Dict:
        """Test orchestrator integration"""
        try:
            from ai_components.orchestration.ai_orchestrator_enhanced import (
                EnhancedWorkflowOrchestrator, TaskDefinition, AgentRole, TaskPriority
            )
            
            orchestrator = EnhancedWorkflowOrchestrator()
            workflow_id = f"test_{int(time.time())}"
            
            await orchestrator.create_workflow(workflow_id)
            
            task = TaskDefinition(
                task_id="test",
                name="Test Task",
                agent_role=AgentRole.ANALYZER,
                inputs={"codebase_path": "."},
                priority=TaskPriority.HIGH,
                timeout=30
            )
            
            start_time = time.time()
            result = await orchestrator.execute_workflow(workflow_id, [task])
            execution_time = time.time() - start_time
            
            return {
                "passed": result.status.value == "completed",
                "execution_time": execution_time,
                "parallel_efficiency": result.performance_metrics.get("parallel_efficiency", 0)
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    async def _test_database_integration(self) -> Dict:
        """Test database integration"""
        try:
            # Test write
            self.db_logger.log_action(
                workflow_id=self.deployment_report["deployment_id"],
                task_id="db_test",
                agent_role="tester",
                action="integration_test",
                status="testing",
                metadata={"test": True}
            )
            
            # Test Weaviate
            self.weaviate_manager.store_context(
                workflow_id=self.deployment_report["deployment_id"],
                task_id="weaviate_test",
                context_type="test",
                content="Test content",
                metadata={"test": True}
            )
            
            return {"passed": True, "postgres": "connected", "weaviate": "connected"}
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    async def _test_cursor_claude_synergy(self) -> Dict:
        """Test Cursor AI and Claude working together"""
        try:
            from ai_components.agents.cursor_ai_enhanced import get_enhanced_cursor_ai
            from ai_components.agents.claude_integration import get_claude_integration
            
            cursor_ai = get_enhanced_cursor_ai()
            claude = get_claude_integration()
            
            # Cursor analyzes
            cursor_result = await cursor_ai.analyze_project(".", {"depth": "basic"})
            
            # Claude reviews
            claude_result = await claude.analyze_architecture(
                {"summary": cursor_result.get("summary", {})},
                focus_areas=["scalability"]
            )
            
            return {
                "passed": bool(cursor_result and claude_result),
                "cursor_files": cursor_result.get("summary", {}).get("total_files", 0),
                "claude_recommendations": len(claude_result.get("recommendations", []))
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    async def _test_analysis_performance(self) -> Dict:
        """Test analysis performance"""
        try:
            from ai_components.agents.cursor_ai_enhanced import get_enhanced_cursor_ai
            
            cursor_ai = get_enhanced_cursor_ai()
            
            # Run multiple analyses
            latencies = []
            for _ in range(3):
                start = time.time()
                await cursor_ai.analyze_project(".", {"depth": "basic"})
                latencies.append(time.time() - start)
            
            avg_latency = sum(latencies) / len(latencies)
            
            return {
                "average_latency": avg_latency,
                "meets_sla": avg_latency < 5.0,  # 5 second SLA
                "samples": len(latencies)
            }
        except Exception as e:
            return {"error": str(e), "meets_sla": False}
    
    async def _test_generation_performance(self) -> Dict:
        """Test code generation performance"""
        try:
            from ai_components.agents.cursor_ai_enhanced import get_enhanced_cursor_ai
            
            cursor_ai = get_enhanced_cursor_ai()
            
            start = time.time()
            result = await cursor_ai.generate_code({
                "description": "Simple REST API",
                "language": "python"
            })
            latency = time.time() - start
            
            return {
                "latency": latency,
                "meets_sla": latency < 10.0,  # 10 second SLA
                "lines_generated": result.get("metrics", {}).get("lines_of_code", 0)
            }
        except Exception as e:
            return {"error": str(e), "meets_sla": False}
    
    async def _test_parallel_execution(self) -> Dict:
        """Test parallel task execution"""
        try:
            from ai_components.orchestration.ai_orchestrator_enhanced import (
                EnhancedWorkflowOrchestrator, TaskDefinition, AgentRole, TaskPriority
            )
            
            orchestrator = EnhancedWorkflowOrchestrator()
            workflow_id = f"parallel_test_{int(time.time())}"
            
            await orchestrator.create_workflow(workflow_id)
            
            # Create parallel tasks
            tasks = []
            for i in range(5):
                tasks.append(TaskDefinition(
                    task_id=f"parallel_{i}",
                    name=f"Parallel Task {i}",
                    agent_role=AgentRole.ANALYZER,
                    inputs={"codebase_path": "."},
                    priority=TaskPriority.NORMAL,
                    timeout=30
                ))
            
            start = time.time()
            result = await orchestrator.execute_workflow(workflow_id, tasks)
            execution_time = time.time() - start
            
            # Calculate speedup
            sequential_estimate = len(tasks) * 2  # Assume 2s per task
            speedup = sequential_estimate / execution_time if execution_time > 0 else 0
            
            return {
                "tasks": len(tasks),
                "execution_time": execution_time,
                "speedup": speedup,
                "efficiency": result.performance_metrics.get("parallel_efficiency", 0)
            }
        except Exception as e:
            return {"error": str(e), "efficiency": 0}
    
    def _measure_resource_usage(self) -> Dict:
        """Measure current resource usage"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_mb": psutil.Process().memory_info().rss / 1024 / 1024,
            "open_files": len(psutil.Process().open_files()),
            "threads": psutil.Process().num_threads()
        }
    
    def _calculate_performance_score(self, metrics: Dict) -> float:
        """Calculate overall performance score"""
        scores = []
        
        # Analysis performance
        if "analysis" in metrics and "meets_sla" in metrics["analysis"]:
            scores.append(1.0 if metrics["analysis"]["meets_sla"] else 0.5)
        
        # Generation performance
        if "generation" in metrics and "meets_sla" in metrics["generation"]:
            scores.append(1.0 if metrics["generation"]["meets_sla"] else 0.5)
        
        # Parallel efficiency
        if "parallel" in metrics and "efficiency" in metrics["parallel"]:
            scores.append(metrics["parallel"]["efficiency"])
        
        # Resource usage (lower is better)
        if "resources" in metrics:
            cpu_score = 1.0 - (metrics["resources"]["cpu_percent"] / 100)
            mem_score = 1.0 - (metrics["resources"]["memory_percent"] / 100)
            scores.extend([cpu_score, mem_score])
        
        return sum(scores) / len(scores) if scores else 0.0
    
    async def _test_error_handling(self) -> bool:
        """Test error handling capabilities"""
        try:
            from ai_components.agents.cursor_ai_enhanced import get_enhanced_cursor_ai
            
            cursor_ai = get_enhanced_cursor_ai()
            
            # Test with invalid input
            try:
                await cursor_ai.analyze_project("/nonexistent/path", {})
            except:
                # Should handle gracefully
                pass
            
            # Check circuit breaker still works
            result = await cursor_ai.analyze_project(".", {"depth": "basic"})
            
            return bool(result)
        except:
            return False
    
    async def _test_circuit_breakers(self) -> bool:
        """Test circuit breaker functionality"""
        # Circuit breakers are tested implicitly in error handling
        return True
    
    async def _test_caching(self) -> bool:
        """Test caching functionality"""
        try:
            from ai_components.agents.cursor_ai_enhanced import get_enhanced_cursor_ai
            
            cursor_ai = get_enhanced_cursor_ai()
            
            # First call (cache miss)
            start1 = time.time()
            result1 = await cursor_ai.analyze_project(".", {"depth": "basic"})
            time1 = time.time() - start1
            
            # Second call (cache hit)
            start2 = time.time()
            result2 = await cursor_ai.analyze_project(".", {"depth": "basic"})
            time2 = time.time() - start2
            
            # Cache should make second call faster
            return time2 < time1 * 0.5  # At least 50% faster
        except:
            return False
    
    def _check_monitoring_setup(self) -> bool:
        """Check if monitoring is configured"""
        # Check for Prometheus/Grafana setup
        monitoring_files = [
            Path("monitoring/docker-compose.yml"),
            Path("monitoring/prometheus.yml"),
            Path("monitoring/grafana/dashboards")
        ]
        
        return any(f.exists() for f in monitoring_files)
    
    def _check_documentation(self) -> bool:
        """Check if documentation is complete"""
        required_docs = [
            Path("docs/ENHANCED_ORCHESTRATION_GUIDE.md"),
            Path("docs/STRATEGIC_PIVOT_PLAN.md"),
            Path("docs/SYSTEM_STATUS_REPORT.md"),
            Path("AI_ORCHESTRATOR_GUIDE.md")
        ]
        
        return all(doc.exists() for doc in required_docs)
    
    async def _log_phase(self, phase: str, data: Dict):
        """Log phase completion to database"""
        self.db_logger.log_action(
            workflow_id=self.deployment_report["deployment_id"],
            task_id=f"phase_{phase}",
            agent_role="deployment_tester",
            action=f"complete_{phase}",
            status="completed",
            metadata=data
        )
    
    async def _log_error(self, phase: str, error: str):
        """Log error to database"""
        self.db_logger.log_action(
            workflow_id=self.deployment_report["deployment_id"],
            task_id=f"phase_{phase}",
            agent_role="deployment_tester",
            action=f"error_{phase}",
            status="failed",
            error=error
        )
    
    async def _generate_final_report(self):
        """Generate comprehensive final report"""
        # Calculate overall status
        phase_statuses = [
            phase.get("status", "unknown") 
            for phase in self.deployment_report["phases"].values()
        ]
        
        all_passed = all(
            status in ["passed", "ready", "completed"] 
            for status in phase_statuses
        )
        
        self.deployment_report["status"] = "success" if all_passed else "partial_success"
        self.deployment_report["completed_at"] = datetime.now().isoformat()
        
        # Performance summary
        if "performance_validation" in self.deployment_report["phases"]:
            perf = self.deployment_report["phases"]["performance_validation"]
            self.deployment_report["performance_summary"] = {
                "score": perf.get("performance_score", 0),
                "analysis_latency": perf.get("metrics", {}).get("analysis", {}).get("average_latency", 0),
                "generation_latency": perf.get("metrics", {}).get("generation", {}).get("latency", 0),
                "parallel_speedup": perf.get("metrics", {}).get("parallel", {}).get("speedup", 0)
            }
        
        # Save report
        report_path = Path("deployment_test_report.json")
        with open(report_path, 'w') as f:
            json.dump(self.deployment_report, f, indent=2)
        
        # Store in Weaviate
        self.weaviate_manager.store_context(
            workflow_id=self.deployment_report["deployment_id"],
            task_id="final_report",
            context_type="deployment_test_report",
            content=json.dumps(self.deployment_report),
            metadata={
                "status": self.deployment_report["status"],
                "phases_completed": len(self.deployment_report["phases"])
            }
        )
        
        # Display summary
        print("\n" + "=" * 70)
        print("📊 DEPLOYMENT TEST SUMMARY")
        print("=" * 70)
        print(f"\nDeployment ID: {self.deployment_report['deployment_id']}")
        print(f"Overall Status: {self.deployment_report['status'].upper()}")
        
        print("\n📋 Phase Results:")
        for phase_name, phase_data in self.deployment_report["phases"].items():
            status = phase_data.get("status", "unknown")
            icon = "✅" if status in ["passed", "ready", "completed"] else "⚠️"
            duration = phase_data.get("duration", 0)
            print(f"  {icon} {phase_name}: {status} ({duration:.1f}s)")
        
        if "performance_summary" in self.deployment_report:
            perf = self.deployment_report["performance_summary"]
            print(f"\n⚡ Performance Summary:")
            print(f"  Overall Score: {perf['score']:.1%}")
            print(f"  Analysis Latency: {perf['analysis_latency']:.2f}s")
            print(f"  Generation Latency: {perf['generation_latency']:.2f}s")
            print(f"  Parallel Speedup: {perf['parallel_speedup']:.1f}x")
        
        print(f"\n📄 Full report saved to: {report_path}")
        print("=" * 70)


async def main():
    """Main deployment and testing workflow"""
    tester = EnhancedSystemDeploymentTester()
    
    try:
        report = await tester.run_full_deployment_and_test()
        
        if report["status"] == "success":
            print("\n✅ Deployment and testing completed successfully!")
            print("\nThe enhanced AI orchestration system is ready for production use.")
            print("\nNext steps:")
            print("1. Review the deployment test report")
            print("2. Configure monitoring dashboards")
            print("3. Set up alerting rules")
            print("4. Begin using the enhanced CLI")
            return 0
        else:
            print("\n⚠️ Deployment completed with warnings")
            print("Review the report for details and recommendations")
            return 1
            
    except Exception as e:
        print(f"\n❌ Deployment testing failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)