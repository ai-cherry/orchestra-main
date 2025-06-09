# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
    """Comprehensive validation of all AI system components"""
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "performance": {},
            "security": {},
            "scalability": {},
            "overall_score": 0,
            "recommendations": []
        }
        
        # MCP server endpoints
        self.mcp_servers = {
            'conductor': 'http://localhost:8002',
            'memory': 'http://localhost:8003',
            'weaviate': 'http://localhost:8001',
            'deployment': 'http://localhost:8005',
            'tools': 'http://localhost:8006'
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        """Async context manager exit"""
        """Run comprehensive validation of all system components"""
        print("🚀 Starting Comprehensive AI System Validation...")
        
        # 1. Test MCP Servers
        print("\n1️⃣ Validating MCP Servers...")
        await self._validate_mcp_servers()
        
        # 2. Test Database Connectivity
        print("\n2️⃣ Validating Database Systems...")
        await self._validate_database_systems()
        
        # 3. Test Cursor AI Integration
        print("\n3️⃣ Validating Cursor AI Integration...")
        await self._validate_cursor_ai()
        
        # 4. Test Claude Integration
        print("\n4️⃣ Validating Claude Integration...")
        await self._validate_claude()
        
        # 5. Test  Code Integration
        print("\n5️⃣ Validating  Code Integration...")
        
        # 6. Test Factory AI Droids
        print("\n6️⃣ Validating Factory AI Droids...")
        await self._validate_factory_ai()
        
        # 7. Test Performance Under Load
        print("\n7️⃣ Testing Performance Under Load...")
        await self._test_performance()
        
        # 8. Test Security
        print("\n8️⃣ Testing Security...")
        await self._test_security()
        
        # 9. Test Scalability
        print("\n9️⃣ Testing Scalability...")
        await self._test_scalability()
        
        # 10. Generate Overall Assessment
        print("\n🔟 Generating Overall Assessment...")
        await self._generate_assessment()
        
        return self.validation_results
    
    async def _validate_mcp_servers(self) -> None:
        """Validate all MCP servers"""
                "url": url,
                "status": "unknown",
                "latency": 0,
                "capabilities": [],
                "errors": []
            }
            
            try:

            
                pass
                start_time = time.time()
                
                async with aiohttp.ClientSession() as session:
                    # Test health endpoint
                    async with session.get(
                        f"{url}/health", 
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        server_result["latency"] = time.time() - start_time
                        
                        if response.status == 200:
                            server_result["status"] = "healthy"
                            health_data = await response.json()
                            server_result["health_data"] = health_data
                        else:
                            server_result["status"] = "unhealthy"
                            server_result["errors"].append(f"Health check failed: {response.status}")
                    
                    # Test capabilities if server is healthy
                    if server_result["status"] == "healthy":
                        try:

                            pass
                            async with session.get(f"{url}/capabilities") as cap_response:
                                if cap_response.status == 200:
                                    capabilities = await cap_response.json()
                                    server_result["capabilities"] = capabilities
                        except Exception:

                            pass
                            server_result["errors"].append(f"Capabilities check failed: {e}")
                
            except Exception:

                
                pass
                server_result["status"] = "error"
                server_result["errors"].append(str(e))
            
            mcp_results[server_name] = server_result
        
        self.validation_results["components"]["mcp_servers"] = mcp_results
        
        # Calculate MCP health score
        healthy_servers = sum(1 for result in mcp_results.values() if result["status"] == "healthy")
        mcp_score = (healthy_servers / len(mcp_results)) * 100
        self.validation_results["performance"]["mcp_health_score"] = mcp_score
    
    async def _validate_database_systems(self) -> None:
        """Validate PostgreSQL and Weaviate"""
            result = await self.db.# TODO: Consider adding EXPLAIN ANALYZE for performance
execute_query("SELECT 1")
            pg_latency = time.time() - start_time
            
            # Test table access
            tables_result = await self.db.execute_query("""
            """
            db_results["postgresql"] = {
                "status": "healthy",
                "latency": pg_latency,
                "tables_count": len(tables_result),
                "version": await self._get_pg_version()
            }
            
        except Exception:

            
            pass
            db_results["postgresql"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Test Weaviate
        try:

            pass
            start_time = time.time()
            schema = self.weaviate_manager.client.schema.get()
            weaviate_latency = time.time() - start_time
            
            db_results["weaviate"] = {
                "status": "healthy",
                "latency": weaviate_latency,
                "classes_count": len(schema.get("classes", [])),
                "schema": schema
            }
            
        except Exception:

            
            pass
            db_results["weaviate"] = {
                "status": "error",
                "error": str(e)
            }
        
        self.validation_results["components"]["databases"] = db_results
    
    async def _validate_cursor_ai(self) -> None:
        """Validate Cursor AI integration"""
            "integration_status": "unknown",
            "api_connectivity": False,
            "mcp_integration": False,
            "performance": {},
            "errors": []
        }
        
        try:

        
            pass
            # Import and test Cursor AI
            from ai_components.cursor_ai.cursor_integration_enhanced import CursorAIClient
            
            async with CursorAIClient() as cursor_client:
                # Test integration
                start_time = time.time()
                test_results = await cursor_client.test_integration()
                cursor_results["performance"]["integration_test_latency"] = time.time() - start_time
                cursor_results["integration_test_results"] = test_results
                
                # Test code analysis
                test_file = __file__
                start_time = time.time()
                analysis_result = await cursor_client.analyze_code(test_file)
                analysis_latency = time.time() - start_time
                
                cursor_results["performance"]["analysis_latency"] = analysis_latency
                cursor_results["api_connectivity"] = not analysis_result.get("fallback", False)
                
                # Test MCP integration
                if "mcp_error" not in str(analysis_result):
                    cursor_results["mcp_integration"] = True
                
                # Get performance metrics
                metrics = await cursor_client.get_performance_metrics()
                cursor_results["performance"].update(metrics)
                
                cursor_results["integration_status"] = "operational"
                
        except Exception:

                
            pass
            cursor_results["integration_status"] = "error"
            cursor_results["errors"].append(str(e))
        
        self.validation_results["components"]["cursor_ai"] = cursor_results
    
    async def _validate_claude(self) -> None:
        """Validate Claude integration"""
            "integration_status": "unknown",
            "api_connectivity": False,
            "performance": {},
            "errors": []
        }
        
        try:

        
            pass
            # Import and test Claude
            from ai_components.claude.claude_analyzer import ClaudeAnalyzer
            
            async with ClaudeAnalyzer() as claude_analyzer:
                # Test code generation
                start_time = time.time()
                generation_result = await claude_analyzer.generate_code(
                    "Create a simple Python function that adds two numbers",
                    {"test": True}
                )
                generation_latency = time.time() - start_time
                
                claude_results["performance"]["code_generation_latency"] = generation_latency
                claude_results["api_connectivity"] = "error" not in generation_result
                
                # Test project analysis
                start_time = time.time()
                analysis_result = await claude_analyzer.analyze_project(".", "quick")
                analysis_latency = time.time() - start_time
                
                claude_results["performance"]["project_analysis_latency"] = analysis_latency
                
                # Get performance metrics
                metrics = await claude_analyzer.get_performance_metrics()
                claude_results["performance"].update(metrics)
                
                # Test comparison with Cursor AI
                comparison = await claude_analyzer.compare_with_cursor_ai(
                    "Create a simple calculator function"
                )
                claude_results["cursor_ai_comparison"] = comparison["comparison"]
                
                claude_results["integration_status"] = "operational"
                
        except Exception:

                
            pass
            claude_results["integration_status"] = "error"
            claude_results["errors"].append(str(e))
        
        self.validation_results["components"]["claude"] = claude_results
    
        """Validate  Code integration"""
            "configuration_status": "unknown",
            "modes_available": 0,
            "mcp_integration": False,
            "errors": []
        }
        
        try:

        
            pass
            # Check  configuration
                
                # Count available modes
                if modes_path.exists():
                    mode_files = list(modes_path.glob("*.json"))
                
                # Check MCP configuration
                if mcp_config_path.exists():
                    
                    with open(mcp_config_path, 'r') as f:
                        mcp_config = json.load(f)
            else:
            
            # Test memory server integration (used by )
            try:

                pass
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                    ) as response:
                        if response.status == 200:
                        else:
            except Exception:

                pass
                
        except Exception:

                
            pass
        
    
    async def _validate_factory_ai(self) -> None:
        """Validate Factory AI Droids"""
            "configuration_status": "unknown",
            "droids_available": 0,
            "adapters_ready": False,
            "errors": []
        }
        
        try:

        
            pass
            # Check Factory AI configuration
            factory_config_path = Path(".factory")
            if factory_config_path.exists():
                factory_results["configuration_status"] = "configured"
                
                # Count available droids
                droids_path = factory_config_path / "droids"
                if droids_path.exists():
                    droid_files = list(droids_path.glob("*.md"))
                    factory_results["droids_available"] = len(droid_files)
                
                # Check config file
                config_file = factory_config_path / "config.yaml"
                if config_file.exists():
                    factory_results["config_file_exists"] = True
            else:
                factory_results["configuration_status"] = "not_configured"
                factory_results["errors"].append("Factory AI configuration directory not found")
            
            # Check MCP adapters
            adapters_path = Path("mcp_server/adapters")
            if adapters_path.exists():
                adapter_files = list(adapters_path.glob("*_adapter.py"))
                factory_results["adapters_count"] = len(adapter_files)
                factory_results["adapters_ready"] = len(adapter_files) >= 5  # 5 droids
            
            # Test if Factory API keys are configured
            factory_api_key = os.environ.get('FACTORY_AI_API_KEY')
            if factory_api_key:
                factory_results["api_key_configured"] = True
            else:
                factory_results["api_key_configured"] = False
                factory_results["errors"].append("FACTORY_AI_API_KEY not configured")
                
        except Exception:

                
            pass
            factory_results["configuration_status"] = "error"
            factory_results["errors"].append(str(e))
        
        self.validation_results["components"]["factory_ai"] = factory_results
    
    async def _test_performance(self) -> None:
        """Test system performance under load"""
            "concurrent_requests": {},
            "database_performance": {},
            "memory_usage": {},
            "response_times": {}
        }
        
        try:

        
            pass
            # Test concurrent requests to MCP servers
            print("   Testing concurrent MCP requests...")
            concurrent_tasks = []
            
            for i in range(10):  # 10 concurrent requests
                for server_name, url in self.mcp_servers.items():
                    task = self._measure_response_time(f"{url}/health")
                    concurrent_tasks.append(task)
            
            start_time = time.time()
            results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
            concurrent_duration = time.time() - start_time
            
            successful_requests = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
            performance_results["concurrent_requests"] = {
                "total_requests": len(concurrent_tasks),
                "successful_requests": successful_requests,
                "success_rate": successful_requests / len(concurrent_tasks),
                "total_duration": concurrent_duration,
                "requests_per_second": len(concurrent_tasks) / concurrent_duration
            }
            
            # Test database performance
            print("   Testing database performance...")
            start_time = time.time()
            for i in range(100):  # 100 simple queries
                await self.db.execute_query("SELECT $1", i)
            db_duration = time.time() - start_time
            
            performance_results["database_performance"] = {
                "queries_count": 100,
                "total_duration": db_duration,
                "queries_per_second": 100 / db_duration,
                "average_query_time": db_duration / 100
            }
            
            # Get system memory usage
            try:

                pass
                import psutil
                memory = psutil.virtual_memory()
                performance_results["memory_usage"] = {
                    "total_gb": memory.total / (1024**3),
                    "used_gb": memory.used / (1024**3),
                    "available_gb": memory.available / (1024**3),
                    "percent_used": memory.percent
                }
            except Exception:

                pass
                performance_results["memory_usage"] = {"error": "psutil not available"}
            
        except Exception:

            
            pass
            performance_results["error"] = str(e)
        
        self.validation_results["performance"].update(performance_results)
    
    async def _test_security(self) -> None:
        """Test security aspects"""
            "api_key_security": {},
            "database_security": {},
            "network_security": {},
            "scores": {}
        }
        
        try:

        
            pass
            # Check API key configuration
            api_keys_configured = []
            api_keys_missing = []
            
            required_keys = [
                'ANTHROPIC_API_KEY', 'CURSOR_AI_API_KEY', 'FACTORY_AI_API_KEY',
                'POSTGRES_PASSWORD', 'WEAVIATE_API_KEY'
            ]
            
            for key in required_keys:
                if os.environ.get(key):
                    api_keys_configured.append(key)
                else:
                    api_keys_missing.append(key)
            
            security_results["api_key_security"] = {
                "configured_keys": api_keys_configured,
                "missing_keys": api_keys_missing,
                "security_score": len(api_keys_configured) / len(required_keys) * 100
            }
            
            # Test database connection security
            try:

                pass
                # Check if connection uses SSL
                ssl_result = await self.db.execute_query("SHOW ssl")
                security_results["database_security"]["ssl_enabled"] = ssl_result[0][0] == 'on' if ssl_result else False
            except Exception:

                pass
                security_results["database_security"]["ssl_enabled"] = "unknown"
            
            # Test network security (basic checks)
            open_ports = []
            for server_name, url in self.mcp_servers.items():
                port = url.split(':')[-1]
                if port.isdigit():
                    open_ports.append(int(port))
            
            security_results["network_security"] = {
                "exposed_ports": open_ports,
                "localhost_only": all("localhost" in url for url in self.mcp_servers.values())
            }
            
            # Calculate overall security score
            api_score = security_results["api_key_security"]["security_score"]
            ssl_score = 100 if security_results["database_security"].get("ssl_enabled") else 50
            network_score = 100 if security_results["network_security"]["localhost_only"] else 70
            
            overall_security_score = (api_score + ssl_score + network_score) / 3
            security_results["scores"]["overall_security_score"] = overall_security_score
            
        except Exception:

            
            pass
            security_results["error"] = str(e)
        
        self.validation_results["security"] = security_results
    
    async def _test_scalability(self) -> None:
        """Test system scalability"""
            "horizontal_scaling": {},
            "vertical_scaling": {},
            "bottlenecks": [],
            "recommendations": []
        }
        
        try:

        
            pass
            # Test MCP server load handling
            print("   Testing MCP server scalability...")
            load_test_results = {}
            
            for server_name, url in self.mcp_servers.items():
                # Test with increasing load
                for load_level in [1, 5, 10, 20]:
                    tasks = [self._measure_response_time(f"{url}/health") for _ in range(load_level)]
                    start_time = time.time()
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    duration = time.time() - start_time
                    
                    success_count = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
                    
                    if server_name not in load_test_results:
                        load_test_results[server_name] = {}
                    
                    load_test_results[server_name][f"load_{load_level}"] = {
                        "success_rate": success_count / load_level,
                        "duration": duration,
                        "avg_response_time": duration / load_level
                    }
            
            scalability_results["horizontal_scaling"]["load_tests"] = load_test_results
            
            # Identify bottlenecks
            for server_name, tests in load_test_results.items():
                for load, result in tests.items():
                    if result["success_rate"] < 0.9:  # Less than 90% success rate
                        scalability_results["bottlenecks"].append(
                            f"{server_name} shows degradation at {load}"
                        )
                    if result["avg_response_time"] > 2.0:  # Longer than 2 seconds
                        scalability_results["bottlenecks"].append(
                            f"{server_name} has high latency at {load}"
                        )
            
            # Generate recommendations
            if not scalability_results["bottlenecks"]:
                scalability_results["recommendations"].append("System handles current load well")
            else:
                scalability_results["recommendations"].extend([
                    "Consider implementing load balancing for high-traffic servers",
                    "Monitor resource usage and scale vertically if needed",
                    "Implement caching for frequently accessed endpoints"
                ])
            
        except Exception:

            
            pass
            scalability_results["error"] = str(e)
        
        self.validation_results["scalability"] = scalability_results
    
    async def _generate_assessment(self) -> None:
        """Generate overall system assessment"""
        components = self.validation_results["components"]
        performance = self.validation_results["performance"]
        security = self.validation_results["security"]
        
        # Calculate component scores
        component_scores = {}
        
        # MCP servers score
        mcp_score = performance.get("mcp_health_score", 0)
        component_scores["mcp_servers"] = mcp_score
        
        # Database score
        db_healthy = all(
            db_info.get("status") == "healthy" 
            for db_info in components.get("databases", {}).values()
        )
        component_scores["databases"] = 100 if db_healthy else 50
        
        # AI tools scores
        cursor_ai_score = 100 if components.get("cursor_ai", {}).get("integration_status") == "operational" else 0
        claude_score = 100 if components.get("claude", {}).get("integration_status") == "operational" else 0
        factory_score = 80 if components.get("factory_ai", {}).get("configuration_status") == "configured" else 20
        
        component_scores["cursor_ai"] = cursor_ai_score
        component_scores["claude"] = claude_score
        component_scores["factory_ai"] = factory_score
        
        # Performance score
        perf_data = performance.get("concurrent_requests", {})
        performance_score = min(100, perf_data.get("success_rate", 0) * 100)
        
        # Security score
        security_score = security.get("scores", {}).get("overall_security_score", 50)
        
        # Calculate overall score
        weights = {
            "components": 0.4,
            "performance": 0.25,
            "security": 0.25,
            "scalability": 0.1
        }
        
        avg_component_score = sum(component_scores.values()) / len(component_scores)
        scalability_score = 90 if not self.validation_results["scalability"].get("bottlenecks") else 70
        
        overall_score = (
            avg_component_score * weights["components"] +
            performance_score * weights["performance"] +
            security_score * weights["security"] +
            scalability_score * weights["scalability"]
        )
        
        self.validation_results["overall_score"] = overall_score
        self.validation_results["component_scores"] = component_scores
        
        # Generate recommendations
        recommendations = []
        
        if overall_score >= 90:
            recommendations.append("System is in excellent condition")
        elif overall_score >= 75:
            recommendations.append("System is performing well with minor improvements needed")
        elif overall_score >= 60:
            recommendations.append("System needs significant improvements")
        else:
            recommendations.append("System requires immediate attention")
        
        # Specific recommendations
        if cursor_ai_score < 100:
            recommendations.append("Configure Cursor AI API key and test integration")
        if claude_score < 100:
            recommendations.append("Configure Claude (Anthropic) API key and test integration")
        if factory_score < 80:
            recommendations.append("Complete Factory AI Droids implementation")
        if security_score < 80:
            recommendations.append("Improve security configuration (API keys, SSL)")
        if performance_score < 80:
            recommendations.append("Optimize system performance")
        
        self.validation_results["recommendations"] = recommendations
    
    async def _measure_response_time(self, url: str) -> Dict:
        """Measure response time for a URL"""
                        "success": response.status == 200,
                        "status_code": response.status,
                        "duration": duration
                    }
        except Exception:

            pass
            return {
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time if 'start_time' in locals() else 0
            }
    
    async def _get_pg_version(self) -> str:
        """Get PostgreSQL version"""
            result = await self.db.execute_query("SELECT version()")
            return result[0][0] if result else "unknown"
        except Exception:

            pass
            return "unknown"
    
    async def save_validation_report(self) -> str:
        """Save validation report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"validation_report_{timestamp}.json"
        
        with open(report_path, 'w') as f:
            json.dump(self.validation_results, f, indent=2, default=str)
        
        # Also save to database
        try:

            pass
            await self.db.execute_query("""
            """
            self.validation_results["overall_score"],
            datetime.now())
        except Exception:

            pass
            logger.warning(f"Could not save report to database: {e}")
        
        return report_path


async def setup_validation_database():
    """Setup database table for validation reports"""
        await db.execute_query("""
        """
        await db.execute_query("""
        """
    """Run comprehensive system validation"""
    print("🚀 Starting Comprehensive AI System Validation...")
    
    # Setup database
    await setup_validation_database()
    
    async with AISystemValidator() as validator:
        # Run validation
        results = await validator.validate_all_components()
        
        # Save report
        report_path = await validator.save_validation_report()
        
        # Display summary
        print("\n" + "="*80)
        print("🎯 VALIDATION SUMMARY")
        print("="*80)
        print(f"\nOverall Score: {results['overall_score']:.1f}/100")
        
        # Component scores
        print(f"\nComponent Scores:")
        for component, score in results.get("component_scores", {}).items():
            status = "✅" if score >= 80 else "⚠️" if score >= 50 else "❌"
            print(f"  {status} {component.replace('_', ' ').title()}: {score:.1f}/100")
        
        # Performance metrics
        if "concurrent_requests" in results["performance"]:
            perf = results["performance"]["concurrent_requests"]
            print(f"\nPerformance:")
            print(f"  Success Rate: {perf.get('success_rate', 0):.1%}")
            print(f"  Requests/sec: {perf.get('requests_per_second', 0):.1f}")
        
        # Security score
        security_score = results["security"].get("scores", {}).get("overall_security_score", 0)
        print(f"\nSecurity Score: {security_score:.1f}/100")
        
        # Recommendations
        print(f"\nRecommendations:")
        for i, rec in enumerate(results["recommendations"], 1):
            print(f"  {i}. {rec}")
        
        print(f"\n📄 Detailed report saved to: {report_path}")
        print("="*80)


if __name__ == "__main__":
    asyncio.run(main()) 