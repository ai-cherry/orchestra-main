# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
    """Comprehensive system validation"""
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "integrations": {},
            "workflows": {},
            "performance": {},
            "security": {},
            "overall_status": "pending"
        }
        self.db_logger = None
        self.weaviate_manager = None
    
    async def validate_all(self) -> Dict:
        """Run all validation tests"""
        print("Starting Comprehensive System Validation")
        print("=" * 60)
        
        # Component validation
        await self.validate_components()
        
        # Integration validation
        await self.validate_integrations()
        
        # Workflow validation
        await self.validate_workflows()
        
        # Performance validation
        await self.validate_performance()
        
        # Security validation
        await self.validate_security()
        
        # CI/CD validation
        await self.validate_cicd()
        
        # Monitoring validation
        await self.validate_monitoring()
        
        # Calculate overall status
        self.calculate_overall_status()
        
        return self.results
    
    async def validate_components(self):
        """Validate individual components"""
        print("\n1. Validating Components...")
        
        components = {
            "eigencode": self.validate_eigencode,
            "cursor_ai": self.validate_cursor_ai,
            "roo_code": self.validate_roo_code,
            "mcp_server": self.validate_mcp_server,
            "postgresql": self.validate_postgresql,
            "conductor": self.validate_conductor
        }
        
        for name, validator in components.items():
            print(f"   Checking {name}...", end=" ")
            try:

                pass
                result = await validator()
                self.results["components"][name] = result
                status = "✓" if result["status"] == "healthy" else "✗"
                print(f"{status} {result.get('message', '')}")
            except Exception:

                pass
                self.results["components"][name] = {
                    "status": "error",
                    "error": str(e)
                }
                print(f"✗ Error: {str(e)}")
    
    async def validate_eigencode(self) -> Dict:
        """Validate EigenCode installation and functionality"""
        result = {"status": "unhealthy", "checks": {}}
        
        # Check installation
        eigencode_paths = [
            "/usr/local/bin/eigencode",
            "/usr/bin/eigencode",
            os.path.expanduser("~/.eigencode/bin/eigencode"),
            "/root/.eigencode/bin/eigencode"
        ]
        
        found = False
        for path in eigencode_paths:
            if os.path.exists(path):
                result["checks"]["installation"] = {
                    "found": True,
                    "path": path
                }
                found = True
                
                # Check version
                try:

                    pass
                    version_result = subprocess.run(
                        [path, "version"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if version_result.returncode == 0:
                        result["checks"]["version"] = version_result.stdout.strip()
                        result["status"] = "healthy"
                except Exception:

                    pass
                    pass
                break
        
        if not found:
            result["checks"]["installation"] = {"found": False}
            result["message"] = "EigenCode not installed"
        
        # Check API connectivity
        try:

            pass
            response = requests.get("https://api.eigencode.dev/health", timeout=5)
            result["checks"]["api"] = {
                "reachable": response.status_code == 200,
                "status_code": response.status_code
            }
        except Exception:

            pass
            result["checks"]["api"] = {"reachable": False}
        
        return result
    
    async def validate_cursor_ai(self) -> Dict:
        """Validate Cursor AI integration"""
        result = {"status": "healthy", "checks": {}}
        
        # Check API key
        api_key = os.environ.get('CURSOR_AI_API_KEY')
        result["checks"]["api_key"] = "configured" if api_key else "missing"
        
        # Check module
        try:

            pass
            from ai_components.cursor_ai.cursor_integration import CursorAIClient
            result["checks"]["module"] = "available"
            
            # Test client initialization
            client = CursorAIClient(api_key)
            result["checks"]["client"] = "initialized"
            
        except Exception:

            
            pass
            result["checks"]["module"] = "missing"
            result["status"] = "unhealthy"
        
        return result
    
    async def validate_roo_code(self) -> Dict:
        """Validate Roo Code integration"""
        result = {"status": "healthy", "checks": {}}
        
        # Check API key
        api_key = os.environ.get('ROO_CODE_API_KEY')
        result["checks"]["api_key"] = "configured" if api_key else "missing"
        
        # Check module
        try:

            pass
            from ai_components.roo_code.roo_integration import RooCodeClient
            result["checks"]["module"] = "available"
            
            # Test client initialization
            client = RooCodeClient(api_key)
            result["checks"]["client"] = "initialized"
            
        except Exception:

            
            pass
            result["checks"]["module"] = "missing"
            result["status"] = "unhealthy"
        
        return result
    
    async def validate_mcp_server(self) -> Dict:
        """Validate MCP server"""
        result = {"status": "unhealthy", "checks": {}}
        
        mcp_url = os.environ.get('MCP_SERVER_URL', 'http://localhost:8080')
        
        # Check health endpoint
        try:

            pass
            response = requests.get(f"{mcp_url}/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("message") == "AI conductor MCP Server":
                    result["status"] = "healthy"
                    result["checks"]["health"] = "ok"
        except Exception:

            pass
            result["checks"]["health"] = f"error: {str(e)}"
        
        # Check task endpoints
        try:

            pass
            # Test task creation
            test_task = {
                "task_id": f"validation_test_{int(time.time())}",
                "name": "Validation Test",
                "agent_role": "analyzer",
                "inputs": {}
            }
            
            response = requests.post(
                f"{mcp_url}/tasks",
                json=test_task,
                timeout=5
            )
            
            if response.status_code == 200:
                result["checks"]["task_creation"] = "ok"
                
                # Clean up test task
                task_id = response.json()["task_id"]
                requests.delete(f"{mcp_url}/tasks/{task_id}")
            else:
                result["checks"]["task_creation"] = f"failed: {response.status_code}"
        except Exception:

            pass
            result["checks"]["task_creation"] = f"error: {str(e)}"
        
        return result
    
    async def validate_postgresql(self) -> Dict:
        """Validate PostgreSQL database"""
        result = {"status": "unhealthy", "checks": {}}
        
        try:

        
            pass
            # Initialize database logger
            self.db_logger = DatabaseLogger()
            
            # Test connection
            with self.db_logger._get_connection() as conn:
                result["checks"]["connection"] = "ok"
                
                # Check tables
                with conn.cursor() as cur:
                    cur.execute("""
                    """
                    if "coordination_logs" in tables:
                        result["checks"]["tables"] = "ok"
                        result["status"] = "healthy"
                    else:
                        result["checks"]["tables"] = "missing coordination_logs"
                    
                    # Check recent logs
                    cur.execute("""
                    """
                    result["checks"]["recent_logs"] = count
                    
        except Exception:

                    
            pass
            result["checks"]["connection"] = f"error: {str(e)}"
        
        return result
    
    async def validate_conductor(self) -> Dict:
        """Validate conductor core functionality"""
        result = {"status": "unhealthy", "checks": {}}
        
        try:

        
            pass
            # Test workflow creation
            conductor = Workflowconductor()
            workflow_id = f"validation_{int(time.time())}"
            context = await conductor.create_workflow(workflow_id)
            
            if context.workflow_id == workflow_id:
                result["checks"]["workflow_creation"] = "ok"
                
                # Test simple task execution
                task = TaskDefinition(
                    task_id="validation_task",
                    name="Validation Task",
                    agent_role=AgentRole.ANALYZER,
                    inputs={"test": True}
                )
                
                workflow_result = await conductor.execute_workflow(workflow_id, [task])
                
                if workflow_result.status.value == "completed":
                    result["checks"]["task_execution"] = "ok"
                    result["status"] = "healthy"
                else:
                    result["checks"]["task_execution"] = f"failed: {workflow_result.status.value}"
            else:
                result["checks"]["workflow_creation"] = "failed"
                
        except Exception:

                
            pass
            result["checks"]["error"] = str(e)
        
        return result
    
    async def validate_integrations(self):
        """Validate service integrations"""
        print("\n2. Validating Integrations...")
        
        integrations = {
            "weaviate_cloud": self.validate_weaviate,
            "airbyte_cloud": self.validate_airbyte,
            "github_secrets": self.validate_github_secrets
        }
        
        for name, validator in integrations.items():
            print(f"   Checking {name}...", end=" ")
            try:

                pass
                result = await validator()
                self.results["integrations"][name] = result
                status = "✓" if result["status"] == "connected" else "✗"
                print(f"{status} {result.get('message', '')}")
            except Exception:

                pass
                self.results["integrations"][name] = {
                    "status": "error",
                    "error": str(e)
                }
                print(f"✗ Error: {str(e)}")
    
    async def validate_weaviate(self) -> Dict:
        """Validate Weaviate Cloud integration"""
        result = {"status": "disconnected", "checks": {}}
        
        try:

        
            pass
            # Initialize Weaviate manager
            self.weaviate_manager = WeaviateManager()
            
            # Check if client is ready
            if self.weaviate_manager.client.is_ready():
                result["checks"]["connection"] = "ok"
                
                # Check schema
                schema = self.weaviate_manager.client.schema.get()
                classes = [c["class"] for c in schema.get("classes", [])]
                
                if "coordinationContext" in classes:
                    result["checks"]["schema"] = "ok"
                    result["status"] = "connected"
                    
                    # Test store and retrieve
                    test_id = f"validation_{int(time.time())}"
                    self.weaviate_manager.store_context(
                        workflow_id=test_id,
                        task_id="test",
                        context_type="validation",
                        content="test content"
                    )
                    
                    results = self.weaviate_manager.retrieve_context(test_id, limit=1)
                    if results:
                        result["checks"]["operations"] = "ok"
                else:
                    result["checks"]["schema"] = "missing coordinationContext"
            else:
                result["checks"]["connection"] = "not ready"
                
        except Exception:

                
            pass
            result["checks"]["error"] = str(e)
        
        return result
    
    async def validate_airbyte(self) -> Dict:
        """Validate Airbyte Cloud integration"""
        result = {"status": "disconnected", "checks": {}}
        
        api_url = os.environ.get('AIRBYTE_API_URL')
        api_key = os.environ.get('AIRBYTE_API_KEY')
        
        if not api_url or not api_key:
            result["checks"]["credentials"] = "missing"
            return result
        
        try:

        
            pass
            # Check API connectivity
            headers = {'Authorization': f'Bearer {api_key}'}
            response = requests.get(
                f"{api_url}/v1/health",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                result["checks"]["api"] = "ok"
                result["status"] = "connected"
                
                # Check workspace
                workspace_id = os.environ.get('AIRBYTE_WORKSPACE_ID')
                if workspace_id:
                    workspace_response = requests.get(
                        f"{api_url}/v1/workspaces/{workspace_id}",
                        headers=headers
                    , timeout=30)
                    if workspace_response.status_code == 200:
                        result["checks"]["workspace"] = "ok"
                    else:
                        result["checks"]["workspace"] = f"error: {workspace_response.status_code}"
            else:
                result["checks"]["api"] = f"error: {response.status_code}"
                
        except Exception:

                
            pass
            result["checks"]["error"] = str(e)
        
        return result
    
    async def validate_github_secrets(self) -> Dict:
        """Validate GitHub Secrets configuration"""
        result = {"status": "unconfigured", "checks": {}}
        
        # Check for required secrets in environment
        required_secrets = [
            "POSTGRES_HOST",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "WEAVIATE_URL",
            "WEAVIATE_API_KEY"
        ]
        
        configured = 0
        for secret in required_secrets:
            if os.environ.get(secret):
                configured += 1
        
        result["checks"]["configured"] = f"{configured}/{len(required_secrets)}"
        
        if configured == len(required_secrets):
            result["status"] = "connected"
        elif configured > 0:
            result["status"] = "partial"
        
        return result
    
    async def validate_workflows(self):
        """Validate workflow execution"""
        print("\n3. Validating Workflows...")
        
        workflows = {
            "simple_workflow": self.validate_simple_workflow,
            "parallel_workflow": self.validate_parallel_workflow,
            "error_recovery": self.validate_error_recovery
        }
        
        for name, validator in workflows.items():
            print(f"   Testing {name}...", end=" ")
            try:

                pass
                result = await validator()
                self.results["workflows"][name] = result
                status = "✓" if result["status"] == "passed" else "✗"
                print(f"{status} {result.get('message', '')}")
            except Exception:

                pass
                self.results["workflows"][name] = {
                    "status": "error",
                    "error": str(e)
                }
                print(f"✗ Error: {str(e)}")
    
    async def validate_simple_workflow(self) -> Dict:
        """Test simple sequential workflow"""
        result = {"status": "failed", "metrics": {}}
        
        conductor = Workflowconductor()
        workflow_id = f"simple_validation_{int(time.time())}"
        
        start_time = time.time()
        
        try:

        
            pass
            context = await conductor.create_workflow(workflow_id)
            
            # Create simple task
            task = TaskDefinition(
                task_id="simple_task",
                name="Simple Validation Task",
                agent_role=AgentRole.ANALYZER,
                inputs={"data": "test"}
            )
            
            workflow_result = await conductor.execute_workflow(workflow_id, [task])
            
            if workflow_result.status.value == "completed":
                result["status"] = "passed"
                result["metrics"]["duration"] = time.time() - start_time
                result["metrics"]["tasks_completed"] = 1
        except Exception:

            pass
            result["error"] = str(e)
        
        return result
    
    async def validate_parallel_workflow(self) -> Dict:
        """Test parallel task execution"""
        result = {"status": "failed", "metrics": {}}
        
        conductor = Workflowconductor()
        workflow_id = f"parallel_validation_{int(time.time())}"
        
        start_time = time.time()
        
        try:

        
            pass
            context = await conductor.create_workflow(workflow_id)
            
            # Create parallel tasks
            tasks = []
            for i in range(3):
                task = TaskDefinition(
                    task_id=f"parallel_task_{i}",
                    name=f"Parallel Task {i}",
                    agent_role=AgentRole.ANALYZER,
                    inputs={"index": i}
                )
                tasks.append(task)
            
            workflow_result = await conductor.execute_workflow(workflow_id, tasks)
            
            if workflow_result.status.value == "completed":
                result["status"] = "passed"
                result["metrics"]["duration"] = time.time() - start_time
                result["metrics"]["tasks_completed"] = len(tasks)
                result["metrics"]["parallelism_efficiency"] = len(tasks) / result["metrics"]["duration"]
        except Exception:

            pass
            result["error"] = str(e)
        
        return result
    
    async def validate_error_recovery(self) -> Dict:
        """Test error recovery mechanisms"""
        result = {"status": "failed", "checks": {}}
        
        try:

        
            pass
            from scripts.error_handling_enhancements import ErrorRecoveryconductor
            
            recovery = ErrorRecoveryconductor()
            
            # Test retry logic
            retry_count = 0
            async def flaky_function():
                nonlocal retry_count
                retry_count += 1
                if retry_count < 2:
                    raise ConnectionError("Test error")
                return "success"
            
            retry_result = await recovery.execute_with_recovery(
                flaky_function,
                {"workflow_id": "test", "task_id": "retry_test"}
            )
            
            if retry_result == "success" and retry_count == 2:
                result["checks"]["retry"] = "passed"
                result["status"] = "passed"
            else:
                result["checks"]["retry"] = "failed"
                
        except Exception:

                
            pass
            result["error"] = str(e)
        
        return result
    
    async def validate_performance(self):
        """Validate performance metrics"""
        print("\n4. Validating Performance...")
        
        result = {"status": "unknown", "metrics": {}}
        
        try:

        
            pass
            from scripts.performance_analyzer import PerformanceAnalyzer
            
            analyzer = PerformanceAnalyzer()
            
            # Run quick performance analysis
            print("   Running performance analysis...", end=" ")
            
            # Test workflow execution time
            workflow_times = await analyzer.analyze_workflow_execution_times()
            if workflow_times:
                result["metrics"]["avg_workflow_duration"] = workflow_times.get("average_duration", 0)
                result["metrics"]["workflow_count"] = workflow_times.get("total_workflows", 0)
            
            # Test database performance
            db_perf = await analyzer.analyze_database_performance()
            if db_perf and "connection_stats" in db_perf:
                result["metrics"]["db_cache_hit_ratio"] = db_perf["connection_stats"].get("cache_hit_ratio", 0)
            
            # Determine status based on metrics
            if result["metrics"].get("avg_workflow_duration", float('inf')) < 60:
                result["status"] = "good"
                print("✓ Performance is good")
            else:
                result["status"] = "needs_optimization"
                print("⚠️  Performance needs optimization")
                
        except Exception:

                
            pass
            result["error"] = str(e)
            print(f"✗ Error: {str(e)}")
        
        self.results["performance"] = result
    
    async def validate_security(self):
        """Validate security configuration"""
        print("\n5. Validating Security...")
        
        result = {"status": "unknown", "score": 0, "issues": []}
        
        try:

        
            pass
            from scripts.security_audit import SecurityAuditor
            
            auditor = SecurityAuditor()
            
            print("   Running security audit...", end=" ")
            
            # Quick security checks
            api_secrets = auditor.check_api_secret_handling()
            
            # Count issues
            hardcoded_count = len(api_secrets.get("hardcoded_secrets", []))
            if hardcoded_count > 0:
                result["issues"].append(f"{hardcoded_count} hardcoded secrets found")
            
            # Calculate score
            result["score"] = 100 - (hardcoded_count * 10)
            result["score"] = max(0, result["score"])
            
            if result["score"] >= 80:
                result["status"] = "secure"
                print(f"✓ Security score: {result['score']}/100")
            else:
                result["status"] = "vulnerable"
                print(f"✗ Security score: {result['score']}/100")
                
        except Exception:

                
            pass
            result["error"] = str(e)
            print(f"✗ Error: {str(e)}")
        
        self.results["security"] = result
    
    async def validate_cicd(self):
        """Validate CI/CD pipeline"""
        print("\n6. Validating CI/CD Pipeline...")
        
        result = {"status": "unknown", "checks": {}}
        
        # Check GitHub Actions workflow
        workflow_file = Path(".github/workflows/ai_conductor_deployment.yml")
        
        if workflow_file.exists():
            result["checks"]["workflow_file"] = "exists"
            
            # Validate workflow syntax
            try:

                pass
                with open(workflow_file, 'r') as f:
                    workflow = yaml.safe_load(f)
                
                if "jobs" in workflow:
                    result["checks"]["syntax"] = "valid"
                    result["checks"]["jobs"] = list(workflow["jobs"].keys())
                    result["status"] = "configured"
                    print("   ✓ GitHub Actions workflow configured")
                else:
                    result["checks"]["syntax"] = "invalid"
                    print("   ✗ Invalid workflow syntax")
            except Exception:

                pass
                result["checks"]["syntax"] = f"error: {str(e)}"
                print(f"   ✗ Error parsing workflow: {str(e)}")
        else:
            result["checks"]["workflow_file"] = "missing"
            print("   ✗ GitHub Actions workflow not found")
        
        self.results["integrations"]["cicd"] = result
    
    async def validate_monitoring(self):
        """Validate monitoring stack"""
        print("\n7. Validating Monitoring Stack...")
        
        result = {"status": "unknown", "checks": {}}
        
        # Check Prometheus
        try:

            pass
            response = requests.get("http://localhost:9090/-/healthy", timeout=2)
            if response.status_code == 200:
                result["checks"]["prometheus"] = "healthy"
            else:
                result["checks"]["prometheus"] = f"unhealthy: {response.status_code}"
        except Exception:

            pass
            result["checks"]["prometheus"] = "not running"
        
        # Check Grafana
        try:

            pass
            response = requests.get("http://localhost:3000/api/health", timeout=2)
            if response.status_code == 200:
                result["checks"]["grafana"] = "healthy"
            else:
                result["checks"]["grafana"] = f"unhealthy: {response.status_code}"
        except Exception:

            pass
            result["checks"]["grafana"] = "not running"
        
        # Determine overall status
        if all(v == "healthy" for v in result["checks"].values()):
            result["status"] = "operational"
            print("   ✓ Monitoring stack operational")
        else:
            result["status"] = "degraded"
            print("   ⚠️  Monitoring stack degraded")
        
        self.results["integrations"]["monitoring"] = result
    
    def calculate_overall_status(self):
        """Calculate overall system status"""
        for component, result in self.results["components"].items():
            total_checks += 1
            if result.get("status") == "healthy":
                passed_checks += 1
        
        # Count integration checks
        for integration, result in self.results["integrations"].items():
            total_checks += 1
            if result.get("status") in ["connected", "configured", "operational"]:
                passed_checks += 1
        
        # Count workflow checks
        for workflow, result in self.results["workflows"].items():
            total_checks += 1
            if result.get("status") == "passed":
                passed_checks += 1
        
        # Calculate percentage
        if total_checks > 0:
            success_rate = (passed_checks / total_checks) * 100
            
            if success_rate >= 90:
                self.results["overall_status"] = "healthy"
            elif success_rate >= 70:
                self.results["overall_status"] = "degraded"
            else:
                self.results["overall_status"] = "unhealthy"
            
            self.results["summary"] = {
                "total_checks": total_checks,
                "passed_checks": passed_checks,
                "success_rate": success_rate
            }
        else:
            self.results["overall_status"] = "unknown"


async def main():
    """Main validation function"""
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    if "summary" in results:
        print(f"Total Checks: {results['summary']['total_checks']}")
        print(f"Passed: {results['summary']['passed_checks']}")
        print(f"Success Rate: {results['summary']['success_rate']:.1f}%")
    
    print(f"\nOverall Status: {results['overall_status'].upper()}")
    
    # Print issues
    issues = []
    
    # Check components
    for component, result in results["components"].items():
        if result.get("status") != "healthy":
            issues.append(f"Component '{component}': {result.get('status', 'unknown')}")
    
    # Check integrations
    for integration, result in results["integrations"].items():
        if result.get("status") not in ["connected", "configured", "operational"]:
            issues.append(f"Integration '{integration}': {result.get('status', 'unknown')}")
    
    # Check workflows
    for workflow, result in results["workflows"].items():
        if result.get("status") != "passed":
            issues.append(f"Workflow '{workflow}': {result.get('status', 'unknown')}")
    
    if issues:
        print("\nIssues Found:")
        for issue in issues:
            print(f"  - {issue}")
    
    # Save detailed report
    report_path = f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_path}")
    
    # Store in Weaviate if available
    if validator.weaviate_manager:
        try:

            pass
            validator.weaviate_manager.store_context(
                workflow_id="system_validation",
                task_id=f"validation_{int(time.time())}",
                context_type="validation_report",
                content=json.dumps(results),
                metadata={
                    "timestamp": results["timestamp"],
                    "overall_status": results["overall_status"]
                }
            )
            print("Report stored in Weaviate Cloud")
        except Exception:

            pass
            pass
    
    # Return exit code based on status
    if results["overall_status"] == "healthy":
        return 0
    elif results["overall_status"] == "degraded":
        return 1
    else:
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)