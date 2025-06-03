#!/usr/bin/env python3
"""
    python scripts/orchestra.py query "your question"  # Query agents
    python scripts/orchestra.py health       # Run health checks
"""
    """Unified CLI for Orchestra AI platform with real agents."""
        self.api_url = "http://localhost:8000"
        self.os.getenv("API_KEY")
        self.project_root = Path(__file__).parent.parent
        self.venv_path = self.project_root / "venv"
        self.python_cmd = str(self.venv_path / "bin" / "python")

    def check_python_version(self) -> bool:
        """Check if Python version is 3.10+."""
            print(f"❌ Python 3.10+ required (found {sys.version})")
            return False
        return True

    def check_venv(self) -> bool:
        """Check if virtual environment exists."""
            print("❌ Virtual environment not found")
            print("   Create with: python -m venv venv")
            return False
        return True

    def run_command(self, cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a shell command."""
        """Check status of all services."""
            "api_server": False,
            "redis": False,
        }

        # Check API server
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:

                pass
                cmdline = proc.info.get("cmdline", [])
                if cmdline and "uvicorn" in str(cmdline) and "agent.app.main" in str(cmdline):
                    status["api_server"] = True
                    break
            except Exception:

                pass
                pass

        # Check Redis
        try:

            pass
            result = self.run_command(["redis-cli", "ping"], check=False)
            status["redis"] = result.stdout.strip() == "PONG"
        except Exception:

            pass
            status["redis"] = False

        return status

    def cmd_status(self) -> int:
        """Show status of all services."""
        print("🔍 Orchestra AI Status")
        print("=" * 50)

        # Python version
        if not self.check_python_version():
            return 1

        # Virtual environment
        venv_ok = self.check_venv()
        print(f"Virtual Environment: {'✅' if venv_ok else '❌'}")

        # Services
        status = self.get_service_status()
        print("\nServices:")
        print(f"  API Server: {'✅ Running' if status['api_server'] else '❌ Not running'}")
        print(f"  Redis:      {'✅ Running' if status['redis'] else '❌ Not running'}")

        # API health check
        if status["api_server"]:
            try:

                pass
                response = requests.get(f"{self.api_url}/health", timeout=5)
                if response.status_code == 200:
                    print("\nAPI Health: ✅ Healthy")
                else:
                    print(f"\nAPI Health: ⚠️  Status {response.status_code}")
            except Exception:

                pass
                print("\nAPI Health: ❌ Cannot connect")

        return 0

    def cmd_start(self) -> int:
        """Start all services."""
        print("🚀 Starting Orchestra AI...")

        if not self.check_python_version() or not self.check_venv():
            return 1

        # Stop any existing services
        self.cmd_stop()

        # Start API server
        print("Starting API server...")
        os.chdir(self.project_root)
        subprocess.Popen(
            [self.python_cmd, "-m", "uvicorn", "agent.app.main:app", "--host", "0.0.0.0", "--port", "8000"],
            stdout=open("api.log", "w"),
            stderr=subprocess.STDOUT,
        )

        # Wait for services to start
        print("Waiting for services to start...")
        time.sleep(3)

        # Check status
        status = self.get_service_status()
        if status["api_server"]:
            print("\n✅ Orchestra AI started successfully!")
            print(f"   API URL: {self.api_url}")
            print(f"   API Docs: {self.api_url}/docs")
            print("   Logs: tail -f api.log")
            return 0
        else:
            print("\n❌ Failed to start services")
            return 1

    def cmd_stop(self) -> int:
        """Stop all services."""
        print("🛑 Stopping Orchestra AI...")

        # Stop API server
        self.run_command(["pkill", "-f", "uvicorn agent.app.main"], check=False)
        time.sleep(1)

        print("✅ All services stopped")
        return 0

    def cmd_query(self, query: str) -> int:
        """Query the agents."""
            headers = {"X-API-Key": self.api_key}
            response = requests.post(f"{self.api_url}/api/query", json={"query": query}, headers=headers, timeout=30)

            if response.status_code == 200:
                result = response.json()
                print(f"\n🤖 Agent: {result.get('agent_id', 'Unknown')}")
                print(f"💬 Response: {result.get('response', 'No response')}")
                return 0
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return 1
        except Exception:

            pass
            print("❌ Cannot connect to API. Is the server running?")
            print("   Run: python scripts/orchestra.py start")
            return 1
        except Exception:

            pass
            print(f"❌ Error: {e}")
            return 1

    def cmd_health(self) -> int:
        """Run health checks."""
        print("🏥 Running health checks...")

        checks = {
            "Python Version": self.check_python_version(),
            "Virtual Environment": self.check_venv(),
            "API Server": self.get_service_status()["api_server"],
            "Redis": self.get_service_status()["redis"],
        }

        # API endpoint check
        if checks["API Server"]:
            try:

                pass
                response = requests.get(f"{self.api_url}/health", timeout=5)
                checks["API Health Endpoint"] = response.status_code == 200
            except Exception:

                pass
                checks["API Health Endpoint"] = False

        # Agent check
        if checks["API Server"]:
            try:

                pass
                headers = {"X-API-Key": self.api_key}
                response = requests.get(f"{self.api_url}/api/agents", headers=headers, timeout=5)
                checks["Real Agents"] = response.status_code == 200 and len(response.json()) > 0
            except Exception:

                pass
                checks["Real Agents"] = False

        # Display results
        print("\nHealth Check Results:")
        print("=" * 50)
        all_good = True
        for check, passed in checks.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{check:.<40} {status}")
            if not passed:
                all_good = False

        print("\n" + ("✅ All checks passed!" if all_good else "❌ Some checks failed"))
        return 0 if all_good else 1

def main():
    """Main entry point."""
        description="Orchestra AI Unified CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
  python scripts/orchestra.py query "What is the CPU usage?"
  python scripts/orchestra.py health
        """
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Status command
    subparsers.add_parser("status", help="Show status of all services")

    # Start command
    subparsers.add_parser("start", help="Start all services")

    # Stop command
    subparsers.add_parser("stop", help="Stop all services")

    # Query command
    query_parser = subparsers.add_parser("query", help="Query the agents")
    query_parser.add_argument("query", help="Query to send to agents")

    # Health command
    subparsers.add_parser("health", help="Run health checks")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute command
    if args.command == "status":
        return cli.cmd_status()
    elif args.command == "start":
        return cli.cmd_start()
    elif args.command == "stop":
        return cli.cmd_stop()
    elif args.command == "query":
        return cli.cmd_query(args.query)
    elif args.command == "health":
        return cli.cmd_health()
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
