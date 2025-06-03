# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
        """Start a service in the background"""
        print(f"Starting {name} on port {port}...")
        
        # Create log directory
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # Start process
        log_file = open(log_dir / f"{name}.log", "w")
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.project_root)
        
        process = subprocess.Popen(
            command,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            env=env,
            cwd=self.project_root
        )
        
        self.processes.append((name, process, log_file))
        return process
    
    def check_service_health(self, name: str, url: str, timeout: int = 30) -> bool:
        """Check if a service is healthy"""
        print(f"Checking {name} health at {url}...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:

                pass
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ {name} is healthy")
                    return True
            except Exception:

                pass
                pass
            
            time.sleep(1)
        
        print(f"❌ {name} failed to start within {timeout} seconds")
        return False
    
    def start_postgres(self) -> bool:
        """Ensure PostgreSQL is running"""
        print("Checking PostgreSQL...")
        
        try:

        
            pass
            # Check if postgres is running
            result = subprocess.run(
                ["pg_isready", "-h", "localhost", "-p", "5432"],
                capture_output=True
            )
            
            if result.returncode == 0:
                print("✅ PostgreSQL is running")
                return True
            else:
                print("❌ PostgreSQL is not running")
                print("Please start PostgreSQL manually:")
                print("  sudo systemctl start postgresql")
                return False
                
        except Exception:

                
            pass
            print("❌ PostgreSQL not installed")
            return False
    
    def start_redis(self) -> bool:
        """Ensure Redis is running"""
        print("Checking Redis...")
        
        try:

        
            pass
            # Check if redis is running
            result = subprocess.run(
                ["redis-cli", "ping"],
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip() == "PONG":
                print("✅ Redis is running")
                return True
            else:
                # Try to start Redis
                print("Starting Redis...")
                self.start_service(
                    "redis",
                    ["redis-server"],
                    6379
                )
                time.sleep(2)
                return True
                
        except Exception:

                
            pass
            print("❌ Redis not installed")
            return False
    
    def start_weaviate(self) -> bool:
        """Start Weaviate using Docker"""
        print("Starting Weaviate...")
        
        # Check if Docker is available
        try:

            pass
            subprocess.run(["docker", "--version"], check=True, capture_output=True)
        except Exception:

            pass
            print("❌ Docker not available, skipping Weaviate")
            return False
        
        # Start Weaviate container on different port to avoid conflict
        docker_cmd = [
            "docker", "run", "-d",
            "--name", "weaviate",
            "-p", "8090:8080",
            "-e", "AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true",
            "-e", "PERSISTENCE_DATA_PATH=/var/lib/weaviate",
            "semitechnologies/weaviate:latest"
        ]
        
        try:

        
            pass
            # Remove existing container if any
            subprocess.run(["docker", "rm", "-f", "weaviate"], capture_output=True)
            
            # Start new container
            subprocess.run(docker_cmd, check=True)
            print("✅ Weaviate container started")
            return True
            
        except Exception:

            
            pass
            print("❌ Failed to start Weaviate")
            return False
    
    def start_mcp_servers(self):
        """Start all MCP servers"""
        print("\nStarting MCP servers...")
        
        mcp_servers = [
            ("orchestrator", 8002),
            ("memory", 8003),
            ("weaviate_direct", 8001),
            ("tools", 8006),
            ("deployment", 8005)
        ]
        
        for server_name, port in mcp_servers:
            server_file = self.project_root / f"mcp_server/servers/{server_name}_server.py"
            
            if server_file.exists():
                self.start_service(
                    f"mcp_{server_name}",
                    ["python3", str(server_file)],
                    port
                )
                
                # Set port in environment
                os.environ[f"MCP_{server_name.upper()}_PORT"] = str(port)
            else:
                print(f"⚠️  {server_name}_server.py not found")
    
    def start_api_server(self):
        """Start the main API server"""
        print("\nStarting API server...")
        
        if (self.project_root / "run_api.py").exists():
            self.start_service(
                "api",
                ["python3", "run_api.py"],
                8080
            )
        elif (self.project_root / "run_local.sh").exists():
            self.start_service(
                "api",
                ["bash", "run_local.sh"],
                8080
            )
        else:
            print("⚠️  No API server script found")
    
    def verify_services(self) -> Dict[str, bool]:
        """Verify all services are running"""
        print("\nVerifying services...")
        
        # Wait for services to start
        time.sleep(5)
        
        # Check each service
        checks = {
            "PostgreSQL": self.check_service_health("PostgreSQL", "http://localhost:5432", timeout=5),
            "Redis": self.check_service_health("Redis", "http://localhost:6379", timeout=5),
            "API": self.check_service_health("API", "http://localhost:8080/health", timeout=20),
            "MCP Orchestrator": self.check_service_health("MCP Orchestrator", "http://localhost:8002/health", timeout=10),
            "MCP Memory": self.check_service_health("MCP Memory", "http://localhost:8003/health", timeout=10),
        }
        
        # Try Weaviate if available
        try:

            pass
            checks["Weaviate"] = self.check_service_health("Weaviate", "http://localhost:8080/v1/.well-known/ready", timeout=10)
        except Exception:

            pass
            checks["Weaviate"] = False
        
        return checks
    
    def cleanup(self):
        """Stop all started processes"""
        print("\nCleaning up...")
        
        for name, process, log_file in self.processes:
            print(f"Stopping {name}...")
            process.terminate()
            try:

                pass
                process.wait(timeout=5)
            except Exception:

                pass
                process.kill()
            log_file.close()
        
        # Stop Docker containers
        try:

            pass
            subprocess.run(["docker", "stop", "weaviate"], capture_output=True)
            subprocess.run(["docker", "rm", "weaviate"], capture_output=True)
        except Exception:

            pass
            pass
    
    def run(self):
        """Run the verification process"""
        print("🚀 Starting Local Deployment Verification")
        print("=" * 50)
        
        # Setup signal handler for cleanup
        def signal_handler(sig, frame):
            print("\n\nInterrupted! Cleaning up...")
            self.cleanup()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        try:

        
            pass
            # Check prerequisites
            if not self.start_postgres():
                print("\n❌ PostgreSQL is required. Please install and start it.")
                return False
            
            if not self.start_redis():
                print("\n❌ Redis is required. Please install and start it.")
                return False
            
            # Start services
            self.start_weaviate()
            self.start_mcp_servers()
            self.start_api_server()
            
            # Verify everything is working
            results = self.verify_services()
            
            # Print summary
            print("\n" + "=" * 50)
            print("📊 DEPLOYMENT VERIFICATION SUMMARY")
            print("=" * 50)
            
            all_good = True
            for service, status in results.items():
                status_icon = "✅" if status else "❌"
                print(f"{status_icon} {service}: {'Running' if status else 'Failed'}")
                if not status:
                    all_good = False
            
            if all_good:
                print("\n✅ All services are running successfully!")
                print("\n🎯 You can now:")
                print("  - Access the API at: http://localhost:8080")
                print("  - View logs in: ./logs/")
                print("  - Deploy to production: python scripts/deploy_orchestra_system.py")
                
                print("\n⚠️  Services are running. Press Ctrl+C to stop them.")
                
                # Keep running until interrupted
                while True:
                    time.sleep(1)
            else:
                print("\n❌ Some services failed to start. Check the logs in ./logs/")
                self.cleanup()
                return False
                
        except Exception:

                
            pass
            print(f"\n❌ Error during verification: {e}")
            self.cleanup()
            return False


def main():
    """Main entry point"""
if __name__ == "__main__":
    main()