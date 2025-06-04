# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

class MCPIntegrationChecker:
    """Check MCP and AI context integration."""
        """Check AI context files for consistency."""
        print("\n🔍 Checking AI Context Files...")

        context_files = [
            "ai_context_planner.py",
            "ai_context_coder.py",
            "ai_context_reviewer.py",
            "ai_context_debugger.py",
        ]

        forbidden_patterns = [
            (r"Poetry", "Poetry references"),
            (r"Docker Compose", "Docker Compose references"),
            (r"GCP", "GCP references"),
            (r"google\.cloud", "Google Cloud imports"),
            (r"docker compose", "docker compose commands"),
        ]

        required_patterns = [
            (r"Python 3\.10", "Python 3.10 requirement"),
            (r"pip/venv", "pip/venv workflow"),
            (r"MongoDB", "MongoDB reference"),
            (r"External Services", "External services mention"),
        ]

        for filename in context_files:
            filepath = self.root_dir / filename
            if not filepath.exists():
                self.issues.append(f"Missing AI context file: {filename}")
                continue

            with open(filepath, "r") as f:
                content = f.read()

            # Check for forbidden patterns
            for pattern, desc in forbidden_patterns:
                if re.search(pattern, content) and "GCP-Free" not in content:
                    self.issues.append(f"{filename}: Contains {desc} (should be GCP-free)")

            # Check for required patterns
            for pattern, desc in required_patterns:
                if not re.search(pattern, content):
                    self.warnings.append(f"{filename}: Missing {desc}")

            # Check header indicates GCP-Free
            if "GCP-Free Edition" in content:
                self.successes.append(f"{filename}: Properly marked as GCP-Free")
            else:
                self.issues.append(f"{filename}: Not marked as GCP-Free Edition")

    def check_mcp_configuration(self) -> None:
        """Check MCP configuration files."""
        print("\n🔧 Checking MCP Configuration...")

        # Check .mcp.json
        mcp_config_path = self.root_dir / ".mcp.json"
        if not mcp_config_path.exists():
            self.issues.append("Missing .mcp.json configuration file")
            return

        with open(mcp_config_path, "r") as f:
            mcp_config = json.load(f)

        # Check servers
        expected_servers = ["conductor", "memory", "deployment"]
        configured_servers = list(mcp_config.get("servers", {}).keys())

        for server in expected_servers:
            if server in configured_servers:
                self.successes.append(f"MCP server '{server}' is configured")

                # Check if server file exists
                server_file = self.root_dir / "mcp_server" / "servers" / f"{server}_server.py"
                if server_file.exists():
                    self.successes.append(f"MCP server file exists: {server_file.name}")
                else:
                    self.issues.append(f"MCP server file missing: {server_file.name}")
            else:
                self.issues.append(f"MCP server '{server}' not configured")

    def check_integration_files(self) -> None:
        """Check Cursor and Roo integration files."""
        print("\n📋 Checking Integration Files...")

        # Check .cursorrules
        cursorrules_path = self.root_dir / ".cursorrules"
        if cursorrules_path.exists():
            with open(cursorrules_path, "r") as f:
                content = f.read()

            if "ai_context_planner.py" in content:
                self.successes.append(".cursorrules references AI context files")
            else:
                self.issues.append(".cursorrules doesn't reference AI context files")

            if "NO Poetry, Docker, Pipenv" in content:
                self.successes.append(".cursorrules correctly forbids Poetry/Docker")
            else:
                self.warnings.append(".cursorrules should explicitly forbid Poetry/Docker")
        else:
            self.issues.append("Missing .cursorrules file")

        # Check .roomodes
        roomodes_path = self.root_dir / ".roomodes"
        if roomodes_path.exists():
            self.successes.append(".roomodes file exists for Roo integration")
        else:
            self.warnings.append("Missing .roomodes file (optional)")

    def check_mcp_servers_running(self) -> None:
        """Check if MCP servers are running."""
        print("\n🚀 Checking MCP Server Status...")

        try:


            pass
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True, check=False)

            servers_to_check = [
                ("conductor_server", "conductor MCP server"),
                ("memory_server", "Memory MCP server"),
                ("deployment_server", "Deployment MCP server"),
            ]

            for process_name, desc in servers_to_check:
                if process_name in result.stdout:
                    self.successes.append(f"{desc} is running")
                else:
                    self.warnings.append(f"{desc} is not running (run ./start_cherry_ai.sh)")

        except Exception:


            pass
            self.warnings.append(f"Could not check server status: {e}")

    def check_launch_scripts(self) -> None:
        """Check if Cursor launch scripts exist."""
        print("\n🚀 Checking Launch Scripts...")

        launch_scripts = [
            "launch_cursor_with_claude.sh",
            "launch_cursor_with_claude_enhanced.sh",
            "start_cherry_ai.sh",
            "stop_cherry_ai.sh",
        ]

        for script in launch_scripts:
            script_path = self.root_dir / script
            if script_path.exists():
                self.successes.append(f"Launch script exists: {script}")
                if os.access(script_path, os.X_OK):
                    self.successes.append(f"  ✓ {script} is executable")
                else:
                    self.warnings.append(f"  ⚠️  {script} is not executable (run chmod +x)")
            else:
                self.warnings.append(f"Missing launch script: {script}")

    def generate_report(self) -> None:
        """Generate and print the integration report."""
        print("\n" + "=" * 60)
        print("📊 MCP INTEGRATION REPORT")
        print("=" * 60)

        # Summary
        total_issues = len(self.issues)
        total_warnings = len(self.warnings)
        total_successes = len(self.successes)

        print(f"\n✅ Successes: {total_successes}")
        print(f"⚠️  Warnings: {total_warnings}")
        print(f"❌ Issues: {total_issues}")

        # Details
        if self.successes:
            print(f"\n{GREEN}✅ SUCCESSES:{RESET}")
            for success in self.successes:
                print(f"  • {success}")

        if self.warnings:
            print(f"\n{YELLOW}⚠️  WARNINGS:{RESET}")
            for warning in self.warnings:
                print(f"  • {warning}")

        if self.issues:
            print(f"\n{RED}❌ ISSUES:{RESET}")
            for issue in self.issues:
                print(f"  • {issue}")

        # Recommendations
        print("\n📝 RECOMMENDATIONS:")

        if total_issues > 0:
            print("  1. Fix the issues listed above")
            print("  2. Run: python scripts/cherry_ai_complete_setup.py")
            print("  3. Ensure AI context files are updated to GCP-Free edition")

        if any("not running" in w for w in self.warnings):
            print("  • Start MCP servers: ./start_cherry_ai.sh")

        if any("not executable" in w for w in self.warnings):
            print("  • Make scripts executable: chmod +x *.sh")

        if total_issues == 0 and total_warnings == 0:
            print("  🎉 Everything looks great! Your MCP integration is properly configured.")

        # Usage instructions
        print("\n🚀 QUICK START:")
        print("  1. Start services: ./start_cherry_ai.sh")
        print("  2. Launch Cursor: ./launch_cursor_with_claude.sh")
        print("  3. In prompts use: 'Read ai_context_coder.py and implement...'")

    def run(self) -> int:
        """Run all checks and generate report."""
        print("🔍 MCP Integration Checker")
        print("Verifying AI context files and MCP configuration...")

        self.check_ai_context_files()
        self.check_mcp_configuration()
        self.check_integration_files()
        self.check_mcp_servers_running()
        self.check_launch_scripts()

        self.generate_report()

        # Return exit code based on issues
        return 1 if self.issues else 0

def main():
    """Main entry point."""
if __name__ == "__main__":
    main()
