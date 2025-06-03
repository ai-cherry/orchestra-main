# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
    """Verify MCP services and AI orchestrator connections"""
            "timestamp": datetime.now().isoformat(),
            "mcp_servers": {},
            "orchestrator_config": {},
            "roo_integration": {},
            "connections": {},
            "errors": []
        }
    
    def check_mcp_configuration(self) -> Dict:
        """Check MCP configuration file"""
        print("🔍 Checking MCP configuration...")
        
        mcp_config_path = Path(".mcp.json")
        if not mcp_config_path.exists():
            self.results["errors"].append("MCP configuration file not found")
            return {}
        
        try:

        
            pass
            with open(mcp_config_path, 'r') as f:
                mcp_config = json.load(f)
            
            # Extract server configurations
            servers = mcp_config.get("servers", {})
            self.results["mcp_servers"] = {
                "configured": list(servers.keys()),
                "count": len(servers),
                "details": {}
            }
            
            # Check each server configuration
            for server_name, server_config in servers.items():
                self.results["mcp_servers"]["details"][server_name] = {
                    "command": server_config.get("command"),
                    "args": server_config.get("args", []),
                    "capabilities": server_config.get("capabilities", {}),
                    "env_vars": list(server_config.get("env", {}).keys())
                }
            
            print(f"✓ Found {len(servers)} MCP servers configured")
            return mcp_config
            
        except Exception:

            
            pass
            self.results["errors"].append(f"Failed to parse MCP config: {str(e)}")
            print(f"✗ Error reading MCP config: {str(e)}")
            return {}
    
    def check_orchestrator_config(self) -> Dict:
        """Check orchestrator configuration"""
        print("\n🔍 Checking orchestrator configuration...")
        
        config_path = Path("config/orchestrator_config.json")
        if not config_path.exists():
            self.results["errors"].append("Orchestrator config not found")
            return {}
        
        try:

        
            pass
            with open(config_path, 'r') as f:
                orch_config = json.load(f)
            
            # Extract Roo integration settings
            roo_integration = orch_config.get("roo_integration", {})
            self.results["roo_integration"] = {
                "enabled": roo_integration.get("enabled", False),
                "modes": list(roo_integration.get("mode_mappings", {}).keys()),
                "api_routing": {
                    "circuit_breaker": roo_integration.get("api_routing", {}).get("circuit_breaker", {}).get("failure_threshold"),
                    "retry_strategy": roo_integration.get("api_routing", {}).get("retry_strategy", {}).get("max_retries")
                },
                "weaviate_integration": roo_integration.get("weaviate_integration", {}).get("enabled", False)
            }
            
            print(f"✓ Roo integration: {'Enabled' if roo_integration.get('enabled') else 'Disabled'}")
            print(f"✓ Configured modes: {len(self.results['roo_integration']['modes'])}")
            
            return orch_config
            
        except Exception:

            
            pass
            self.results["errors"].append(f"Failed to parse orchestrator config: {str(e)}")
            print(f"✗ Error reading orchestrator config: {str(e)}")
            return {}
    
    def test_mcp_server_syntax(self) -> Dict[str, bool]:
        """Test MCP server Python files for syntax errors"""
        print("\n🔍 Testing MCP server syntax...")
        
        server_results = {}
        mcp_server_dir = Path("mcp_server/servers")
        
        if not mcp_server_dir.exists():
            self.results["errors"].append("MCP server directory not found")
            return server_results
        
        # Find all server Python files
        server_files = list(mcp_server_dir.glob("*_server.py"))
        
        for server_file in server_files:
            server_name = server_file.stem
            
            # Test Python syntax
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(server_file)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                server_results[server_name] = True
                print(f"  ✓ {server_name}: Valid syntax")
            else:
                server_results[server_name] = False
                self.results["errors"].append(f"{server_name}: {result.stderr}")
                print(f"  ✗ {server_name}: Syntax error")
        
        self.results["mcp_servers"]["syntax_check"] = server_results
        return server_results
    
    def check_environment_variables(self) -> Dict[str, bool]:
        """Check required environment variables"""
        print("\n🔍 Checking environment variables...")
        
        required_vars = {
            "OPENROUTER_API_KEY": "Roo Coder API access",
            "POSTGRES_HOST": "Database connection",
            "POSTGRES_DB": "Database name",
            "WEAVIATE_HOST": "Vector store connection",
            "API_URL": "API endpoint",
            "API_KEY": "API authentication"
        }
        
        env_status = {}
        for var, description in required_vars.items():
            value = os.environ.get(var)
            is_set = bool(value and value.strip())
            env_status[var] = is_set
            
            if is_set:
                print(f"  ✓ {var}: Set ({description})")
            else:
                print(f"  ✗ {var}: Not set ({description})")
        
        self.results["environment"] = env_status
        return env_status
    
    def test_mcp_server_connections(self) -> Dict[str, Dict]:
        """Test actual MCP server connections"""
        print("\n🔍 Testing MCP server connections...")
        
        connection_results = {}
        
        # Test each configured MCP server
        for server_name in self.results["mcp_servers"].get("configured", []):
            print(f"\n  Testing {server_name}...")
            
            server_details = self.results["mcp_servers"]["details"].get(server_name, {})
            command = server_details.get("command")
            args = server_details.get("args", [])
            
            if not command or not args:
                connection_results[server_name] = {
                    "status": "error",
                    "message": "Invalid server configuration"
                }
                continue
            
            # Try to import and test the server module
            try:

                pass
                # Extract module path from args
                if args and args[0].endswith('.py'):
                    module_path = args[0].replace('/', '.').replace('.py', '')
                    
                    # Test if module can be imported
                    import importlib.util
                    spec = importlib.util.spec_from_file_location(server_name, args[0])
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        connection_results[server_name] = {
                            "status": "importable",
                            "message": "Module can be imported",
                            "has_server_class": hasattr(module, 'OrchestratorServer') or hasattr(module, 'Server')
                        }
                        print(f"    ✓ Module imports successfully")
                    else:
                        connection_results[server_name] = {
                            "status": "error",
                            "message": "Cannot load module"
                        }
                        print(f"    ✗ Cannot load module")
                else:
                    connection_results[server_name] = {
                        "status": "unknown",
                        "message": "Non-Python server"
                    }
                    
            except Exception:

                    
                pass
                connection_results[server_name] = {
                    "status": "error",
                    "message": str(e)
                }
                print(f"    ✗ Error: {str(e)}")
        
        self.results["connections"] = connection_results
        return connection_results
    
    def check_roo_mode_availability(self) -> Dict[str, bool]:
        """Check if Roo modes are properly configured"""
        print("\n🔍 Checking Roo mode availability...")
        
        mode_status = {}
        modes = self.results["roo_integration"].get("modes", [])
        
        # Load the actual orchestrator config to check mode mappings
        config_path = Path("config/orchestrator_config.json")
        if config_path.exists():
            with open(config_path, 'r') as f:
                orch_config = json.load(f)
            mode_mappings = orch_config.get("roo_integration", {}).get("mode_mappings", {})
        else:
            mode_mappings = {}
        
        for mode in modes:
            # Check if mode has proper configuration
            mode_config = mode_mappings.get(mode, {})
            
            has_agent_id = bool(mode_config.get("agent_id"))
            has_capabilities = bool(mode_config.get("capabilities"))
            has_model = bool(mode_config.get("model"))
            
            is_configured = has_agent_id and has_capabilities and has_model
            mode_status[mode] = is_configured
            
            if is_configured:
                print(f"  ✓ {mode}: Fully configured")
                print(f"    - Agent: {mode_config.get('agent_id')}")
                print(f"    - Model: {mode_config.get('model')}")
            else:
                print(f"  ✗ {mode}: Missing configuration")
        
        self.results["roo_modes"] = mode_status
        return mode_status
    
    def verify_orchestrator_components(self) -> Dict[str, bool]:
        """Verify orchestrator components are available"""
        print("\n🔍 Verifying orchestrator components...")
        
        components = {
            "orchestration_module": Path("ai_components/orchestration/ai_orchestrator.py"),
            "cli_tool": Path("ai_components/orchestrator_cli_enhanced.py"),
            "agent_control": Path("agent/app/services/agent_control.py"),
            "workflow_runner": Path("agent/app/services/workflow_runner.py"),
            "real_agents": Path("agent/app/services/real_agents.py")
        }
        
        component_status = {}
        for name, path in components.items():
            exists = path.exists()
            component_status[name] = exists
            
            if exists:
                print(f"  ✓ {name}: Found at {path}")
            else:
                print(f"  ✗ {name}: Not found at {path}")
        
        self.results["components"] = component_status
        return component_status
    
    def generate_report(self) -> Dict:
        """Generate comprehensive verification report"""
        print("\n📊 Generating verification report...")
        
        # Calculate overall status
        mcp_configured = len(self.results["mcp_servers"].get("configured", [])) > 0
        roo_enabled = self.results["roo_integration"].get("enabled", False)
        syntax_valid = all(self.results["mcp_servers"].get("syntax_check", {}).values()) if self.results["mcp_servers"].get("syntax_check") else False
        env_complete = all(self.results.get("environment", {}).values()) if self.results.get("environment") else False
        modes_configured = all(self.results.get("roo_modes", {}).values()) if self.results.get("roo_modes") else False
        components_present = all(self.results.get("components", {}).values()) if self.results.get("components") else False
        
        self.results["summary"] = {
            "mcp_servers_configured": mcp_configured,
            "roo_integration_enabled": roo_enabled,
            "syntax_validation_passed": syntax_valid,
            "environment_complete": env_complete,
            "all_modes_configured": modes_configured,
            "components_present": components_present,
            "overall_status": all([
                mcp_configured,
                roo_enabled,
                syntax_valid,
                env_complete,
                modes_configured,
                components_present
            ])
        }
        
        # Save report
        report_path = Path("orchestrator_mcp_verification_report.json")
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n✓ Report saved to: {report_path}")
        
        return self.results
    
    def print_summary(self):
        """Print verification summary"""
        print("\n" + "="*60)
        print("VERIFICATION SUMMARY")
        print("="*60)
        
        summary = self.results.get("summary", {})
        
        print(f"\n🔌 MCP Servers Configured: {'✓' if summary.get('mcp_servers_configured') else '✗'}")
        print(f"🤖 Roo Integration Enabled: {'✓' if summary.get('roo_integration_enabled') else '✗'}")
        print(f"📝 Syntax Validation: {'✓ Passed' if summary.get('syntax_validation_passed') else '✗ Failed'}")
        print(f"🔐 Environment Variables: {'✓ Complete' if summary.get('environment_complete') else '✗ Incomplete'}")
        print(f"🎭 All Modes Configured: {'✓' if summary.get('all_modes_configured') else '✗'}")
        print(f"📦 Components Present: {'✓' if summary.get('components_present') else '✗'}")
        
        print(f"\n{'✅ OVERALL STATUS: CONNECTED' if summary.get('overall_status') else '❌ OVERALL STATUS: NOT FULLY CONNECTED'}")
        
        if self.results.get("errors"):
            print(f"\n⚠️  Errors found: {len(self.results['errors'])}")
            for error in self.results["errors"][:3]:  # Show first 3 errors
                print(f"  - {error}")
        
        print("\n" + "="*60)


def main():
    """Main verification function"""
    print("🚀 Verifying Roo Coder MCP Service and AI Orchestrator Connection")
    print("="*60)
    
    verifier = OrchestratorMCPVerifier()
    
    # Run all checks
    verifier.check_mcp_configuration()
    verifier.check_orchestrator_config()
    verifier.test_mcp_server_syntax()
    verifier.check_environment_variables()
    verifier.test_mcp_server_connections()
    verifier.check_roo_mode_availability()
    verifier.verify_orchestrator_components()
    
    # Generate report and summary
    verifier.generate_report()
    verifier.print_summary()
    
    # Return exit code based on overall status
    return 0 if verifier.results.get("summary", {}).get("overall_status") else 1


if __name__ == "__main__":
    sys.exit(main())