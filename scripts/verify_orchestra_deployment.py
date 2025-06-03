#!/usr/bin/env python3
"""
"""
    """Verifies Orchestra AI deployment and functionality"""
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "issues": [],
            "recommendations": []
        }
    
    def verify_file_structure(self) -> Tuple[bool, List[str]]:
        """Verify all required files and directories exist"""
        logger.info("📁 Verifying file structure...")
        
        required_paths = {
            "directories": [
                "mcp_server/servers",
                "infrastructure",
                "scripts",
                "config",
                "core/shared",
                "core/api",
                "services",
                "tests"
            ],
            "files": [
                "mcp_server/servers/orchestrator_server.py",
                "mcp_server/servers/memory_server.py",
                "mcp_server/servers/weaviate_direct_server.py",
                "mcp_server/servers/tools_server.py",
                "mcp_server/servers/deployment_server.py",
                "infrastructure/orchestra_vultr_stack.py",
                "scripts/deploy_orchestra_system.py",
                "config/orchestrator_config.json",
                "requirements-unified.txt"
            ]
        }
        
        missing = []
        
        for dir_path in required_paths["directories"]:
            if not (self.project_root / dir_path).exists():
                missing.append(f"Directory: {dir_path}")
        
        for file_path in required_paths["files"]:
            if not (self.project_root / file_path).exists():
                missing.append(f"File: {file_path}")
        
        success = len(missing) == 0
        self.verification_results["tests"]["file_structure"] = {
            "passed": success,
            "missing": missing
        }
        
        return success, missing
    
    def verify_python_environment(self) -> Tuple[bool, Dict]:
        """Verify Python environment and dependencies"""
        logger.info("🐍 Verifying Python environment...")
        
        results = {
            "python_version": None,
            "venv_active": False,
            "dependencies_installed": False,
            "issues": []
        }
        
        # Check Python version
        try:

            pass
            result = subprocess.run(
                ["python3", "--version"],
                capture_output=True,
                text=True
            )
            version = result.stdout.strip()
            results["python_version"] = version
            
            # Check if it's 3.10+
            version_parts = version.split()[1].split('.')
            major, minor = int(version_parts[0]), int(version_parts[1])
            if major < 3 or (major == 3 and minor < 10):
                results["issues"].append(f"Python 3.10+ required, found {version}")
        except Exception:

            pass
            results["issues"].append(f"Failed to check Python version: {e}")
        
        # Check virtual environment
        if os.environ.get("VIRTUAL_ENV"):
            results["venv_active"] = True
        elif (self.project_root / "venv").exists():
            results["venv_active"] = True
            results["issues"].append("Virtual environment exists but not activated")
        
        # Check key dependencies
        try:

            pass
            import pulumi
            import weaviate
            import asyncio
            import fastapi
            results["dependencies_installed"] = True
        except Exception:

            pass
            results["issues"].append(f"Missing dependency: {e.name}")
        
        success = len(results["issues"]) == 0
        self.verification_results["tests"]["python_environment"] = results
        
        return success, results
    
    def verify_mcp_servers(self) -> Tuple[bool, Dict]:
        """Verify MCP server configurations"""
        logger.info("🔌 Verifying MCP servers...")
        
        mcp_status = {}
        servers = ["orchestrator", "memory", "weaviate_direct", "tools", "deployment"]
        
        for server in servers:
            server_file = self.project_root / "mcp_server" / "servers" / f"{server}_server.py"
            if server_file.exists():
                # Check if server has required methods
                content = server_file.read_text()
                has_list_tools = "list_tools" in content
                has_call_tool = "call_tool" in content
                has_async_def = "async def" in content
                
                mcp_status[server] = {
                    "exists": True,
                    "has_list_tools": has_list_tools,
                    "has_call_tool": has_call_tool,
                    "is_async": has_async_def,
                    "ready": has_list_tools and has_call_tool and has_async_def
                }
            else:
                mcp_status[server] = {
                    "exists": False,
                    "ready": False
                }
        
        all_ready = all(status["ready"] for status in mcp_status.values())
        self.verification_results["tests"]["mcp_servers"] = mcp_status
        
        return all_ready, mcp_status
    
    def verify_configurations(self) -> Tuple[bool, Dict]:
        """Verify configuration files"""
        logger.info("⚙️ Verifying configurations...")
        
        config_status = {}
        config_files = [
            "config/orchestrator_config.json",
            "config/roo_mode_mappings.yaml",
            "infrastructure/Pulumi.yaml"
        ]
        
        for config_file in config_files:
            file_path = self.project_root / config_file
            if file_path.exists():
                try:

                    pass
                    if config_file.endswith('.json'):
                        with open(file_path) as f:
                            json.load(f)
                        config_status[config_file] = {"exists": True, "valid": True}
                    elif config_file.endswith('.yaml'):
                        # Basic YAML validation
                        content = file_path.read_text()
                        config_status[config_file] = {
                            "exists": True, 
                            "valid": ":" in content  # Simple check
                        }
                except Exception:

                    pass
                    config_status[config_file] = {
                        "exists": True, 
                        "valid": False,
                        "error": str(e)
                    }
            else:
                config_status[config_file] = {"exists": False, "valid": False}
        
        all_valid = all(
            status.get("exists", False) and status.get("valid", False) 
            for status in config_status.values()
        )
        self.verification_results["tests"]["configurations"] = config_status
        
        return all_valid, config_status
    
    def test_basic_functionality(self) -> Tuple[bool, Dict]:
        """Test basic system functionality"""
        logger.info("🧪 Testing basic functionality...")
        
        functionality_tests = {
            "imports": True,
            "async_operations": True,
            "file_operations": True,
            "logging": True
        }
        
        # Test imports
        try:

            pass
            from mcp_server.servers.base_mcp_server import BaseMCPServer
            from core.shared.utils import setup_logging
        except Exception:

            pass
            functionality_tests["imports"] = False
        
        # Test async operations
        try:

            pass
            async def test_async():
                await asyncio.sleep(0.1)
                return True
            
            asyncio.run(test_async())
        except Exception:

            pass
            functionality_tests["async_operations"] = False
        
        # Test file operations
        try:

            pass
            test_file = self.project_root / "test_temp.txt"
            test_file.write_text("test")
            test_file.unlink()
        except Exception:

            pass
            functionality_tests["file_operations"] = False
        
        # Test logging
        try:

            pass
            test_logger = logging.getLogger("test")
            test_logger.info("Test log message")
        except Exception:

            pass
            functionality_tests["logging"] = False
        
        all_passed = all(functionality_tests.values())
        self.verification_results["tests"]["functionality"] = functionality_tests
        
        return all_passed, functionality_tests
    
    def generate_recommendations(self):
        """Generate recommendations based on verification results"""
        if not self.verification_results["tests"].get("file_structure", {}).get("passed", True):
            recommendations.append(
                "Run 'python3 scripts/orchestrated_codebase_fix.py' to fix missing files"
            )
        
        # Check Python environment
        env_results = self.verification_results["tests"].get("python_environment", {})
        if not env_results.get("venv_active", False):
            recommendations.append(
                "Activate virtual environment: source venv/bin/activate"
            )
        if not env_results.get("dependencies_installed", False):
            recommendations.append(
                "Install dependencies: pip install -r requirements-unified.txt"
            )
        
        # Check MCP servers
        mcp_results = self.verification_results["tests"].get("mcp_servers", {})
        for server, status in mcp_results.items():
            if not status.get("ready", False):
                recommendations.append(
                    f"Fix MCP {server} server implementation"
                )
        
        self.verification_results["recommendations"] = recommendations
    
    def generate_report(self) -> str:
        """Generate comprehensive verification report"""
        report = f"""
"""
        for test_category, results in self.verification_results["tests"].items():
            if isinstance(results, dict):
                if "passed" in results:
                    total_tests += 1
                    if results["passed"]:
                        passed_tests += 1
                else:
                    # Count individual sub-tests
                    for key, value in results.items():
                        if isinstance(value, bool):
                            total_tests += 1
                            if value:
                                passed_tests += 1
                        elif isinstance(value, dict) and "ready" in value:
                            total_tests += 1
                            if value["ready"]:
                                passed_tests += 1
        
        report += f"Total Tests: {total_tests}\n"
        report += f"Passed: {passed_tests}\n"
        report += f"Failed: {total_tests - passed_tests}\n"
        report += f"Success Rate: {(passed_tests/total_tests*100):.1f}%\n"
        
        # Detailed results
        report += "\n📋 DETAILED RESULTS\n"
        report += "-" * 20 + "\n"
        
        for test_category, results in self.verification_results["tests"].items():
            report += f"\n{test_category.upper()}:\n"
            report += json.dumps(results, indent=2) + "\n"
        
        # Recommendations
        if self.verification_results["recommendations"]:
            report += "\n💡 RECOMMENDATIONS\n"
            report += "-" * 20 + "\n"
            for i, rec in enumerate(self.verification_results["recommendations"], 1):
                report += f"{i}. {rec}\n"
        
        # Next steps
        report += """
"""
    """Main verification function"""
    logger.info("🔍 Starting Orchestra AI deployment verification...")
    
    verifier = OrchestraVerification()
    
    # Run all verification tests
    tests = [
        ("File Structure", verifier.verify_file_structure),
        ("Python Environment", verifier.verify_python_environment),
        ("MCP Servers", verifier.verify_mcp_servers),
        ("Configurations", verifier.verify_configurations),
        ("Basic Functionality", verifier.test_basic_functionality)
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        logger.info(f"\nRunning {test_name} verification...")
        passed, results = test_func()
        if not passed:
            all_passed = False
            logger.warning(f"⚠️  {test_name} verification found issues")
        else:
            logger.info(f"✅ {test_name} verification passed")
    
    # Generate recommendations
    verifier.generate_recommendations()
    
    # Generate and display report
    report = verifier.generate_report()
    print(report)
    
    # Save report
    report_file = f"verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    Path(report_file).write_text(report)
    logger.info(f"\n💾 Report saved to: {report_file}")
    
    # Save detailed results
    results_file = f"verification_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(verifier.verification_results, f, indent=2)
    logger.info(f"💾 Detailed results saved to: {results_file}")
    
    if all_passed:
        logger.info("\n✅ All verifications passed! Orchestra AI is ready!")
        return 0
    else:
        logger.warning("\n⚠️  Some verifications failed. Please check the report.")
        return 1


if __name__ == "__main__":
    sys.exit(main())