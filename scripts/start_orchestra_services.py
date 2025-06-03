# TODO: Consider adding connection pooling configuration
import asyncio
#!/usr/bin/env python3
"""
"""
    """Manages Orchestra AI services"""
        self.venv_path = self.project_root / "venv"
        self.services_status = {}
        
    def check_docker(self) -> bool:
        """Check if Docker is available"""
                ["docker", "--version"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:

            pass
            return False
    
    def check_docker_compose(self) -> bool:
        """Check if docker-compose is available"""
                ["docker-compose", "--version"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:

            pass
            return False
    
    def start_postgresql(self) -> Tuple[bool, str]:
        """Start PostgreSQL if not running"""
        logger.info("Checking PostgreSQL...")
        
        # Check if PostgreSQL is running
        try:

            pass
            result = subprocess.run(
                ["pg_isready", "-h", "localhost", "-p", "5432"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return True, "PostgreSQL already running"
            
            # Try to start PostgreSQL
            logger.info("Starting PostgreSQL...")
            subprocess.run(["sudo", "systemctl", "start", "postgresql"], check=True)
            await asyncio.sleep(2)
            
            # Create orchestra database if it doesn't exist
            subprocess.run([
                "sudo", "-u", "postgres", "createdb", "orchestra"
            ], capture_output=True)
            
            return True, "PostgreSQL started"
            
        except Exception:

            
            pass
            return False, f"Failed to start PostgreSQL: {str(e)}"
    
    def start_redis(self) -> Tuple[bool, str]:
        """Start Redis if not running"""
        logger.info("Checking Redis...")
        
        try:

        
            pass
            # Check if Redis is running
            result = subprocess.run(
                ["redis-cli", "ping"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and "PONG" in result.stdout:
                return True, "Redis already running"
            
            # Try to start Redis
            logger.info("Starting Redis...")
            subprocess.run(["sudo", "systemctl", "start", "redis"], check=True)
            await asyncio.sleep(1)
            
            return True, "Redis started"
            
        except Exception:

            
            pass
            return False, f"Failed to start Redis: {str(e)}"
    
    def ensure_weaviate_running(self) -> Tuple[bool, str]:
        """Ensure Weaviate is running via Docker"""
        logger.info("Checking Weaviate...")
        
        if not self.check_docker():
            return False, "Docker not available"
        
        try:

        
            pass
            # Check if Weaviate container is running
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=weaviate", "--format", "{{.Names}}"],
                capture_output=True,
                text=True
            )
            
            if "weaviate" in result.stdout:
                return True, "Weaviate container already running"
            
            # Check for docker-compose file
            compose_files = [
                self.project_root / "docker-compose.yml",
                self.project_root / "docker-compose.yaml",
                self.project_root / "deploy" / "docker-compose.yml"
            ]
            
            compose_file = None
            for f in compose_files:
                if f.exists():
                    compose_file = f
                    break
            
            if compose_file:
                logger.info(f"Starting Weaviate using {compose_file}")
                subprocess.run(
                    ["docker-compose", "-f", str(compose_file), "up", "-d", "weaviate"],
                    check=True
                )
                await asyncio.sleep(5)  # Wait for Weaviate to start
                return True, "Weaviate started via docker-compose"
            else:
                # Start Weaviate standalone
                logger.info("Starting Weaviate standalone container...")
                subprocess.run([
                    "docker", "run", "-d",
                    "--name", "weaviate",
                    "-p", "8080:8080",
                    "-p", "50051:50051",
                    "--env", "AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true",
                    "--env", "PERSISTENCE_DATA_PATH=/var/lib/weaviate",
                    "--env", "DEFAULT_VECTORIZER_MODULE=none",
                    "--env", "CLUSTER_HOSTNAME=node1",
                    "semitechnologies/weaviate:latest"
                ], check=True)
                await asyncio.sleep(10)  # Wait for Weaviate to start
                return True, "Weaviate started as standalone container"
                
        except Exception:

                
            pass
            return False, f"Failed to start Weaviate: {str(e)}"
    
    def start_mcp_server(self, server_name: str, script_path: str, port: int) -> Tuple[bool, str]:
        """Start an MCP server"""
        logger.info(f"Starting MCP {server_name} server on port {port}...")
        
        try:

        
            pass
            # Check if already running
            result = subprocess.run(
                ["lsof", "-i", f":{port}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return True, f"Port {port} already in use (server may be running)"
            
            # Start the server
            log_file = self.project_root / "logs" / f"mcp_{server_name}.log"
            log_file.parent.mkdir(exist_ok=True)
            
            with open(log_file, 'a') as log:
                process = subprocess.Popen(
                    [str(self.venv_path / "bin" / "python"), script_path],
                    stdout=log,
                    stderr=log,
                    cwd=str(self.project_root)
                )
                
                # Save PID
                pid_file = self.project_root / "logs" / f"mcp_{server_name}.pid"
                pid_file.write_text(str(process.pid))
                
                await asyncio.sleep(2)  # Wait for server to start
                
                # Check if process is still running
                if process.poll() is None:
                    return True, f"Started with PID {process.pid}"
                else:
                    return False, "Process exited immediately"
                    
        except Exception:

                    
            pass
            return False, f"Failed to start: {str(e)}"
    
    def create_mcp_health_endpoint(self):
        """Create a simple health endpoint wrapper for MCP servers"""
"""MCP Server Health Endpoint Wrapper"""
@app.get("/health")
async def health():
    return {"status": "healthy", "server": "{server_name}"}

@app.post("/tools/list")
async def list_tools():
    return await server.list_tools()

@app.post("/tools/call")
async def call_tool(request: dict):
    return await server.call_tool(request)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port={port})
'''
        # Start MCP servers (skip weaviate_direct as it's already running)
        mcp_servers = {
            "orchestrator": ("mcp_server/wrappers/orchestrator_wrapper.py", 8000),
            "memory": ("mcp_server/wrappers/memory_wrapper.py", 8002),
            "tools": ("mcp_server/wrappers/tools_wrapper.py", 8003),
            "deployment": ("mcp_server/wrappers/deployment_wrapper.py", 8004)
        }
        
        for server_name, (script_path, port) in mcp_servers.items():
            if (self.project_root / script_path).exists():
                status = self.start_mcp_server(server_name, script_path, port)
                self.services_status[f"mcp_{server_name}"] = status
            else:
                self.services_status[f"mcp_{server_name}"] = (False, "Script not found")
        
        return self.services_status
    
    def generate_report(self) -> str:
        """Generate service status report"""
        report = """
"""
            status = "✅" if success else "❌"
            report += f"{status} {service}: {message}\n"
            if not success:
                all_success = False
        
        if all_success:
            report += """
"""
            report += """
"""
    """Main function"""
if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)