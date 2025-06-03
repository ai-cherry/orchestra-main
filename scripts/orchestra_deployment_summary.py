# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
    """Generates a comprehensive summary of Orchestra AI deployment"""
            "orchestrator_api": {
                "port": 8000,
                "process_name": "gunicorn",
                "description": "Main Orchestrator API"
            },
            "weaviate": {
                "port": 8080,
                "endpoint": "http://localhost:8080/v1",
                "description": "Vector Database"
            },
            "mcp_weaviate": {
                "port": 8001,
                "process_name": "weaviate_direct_mcp_server",
                "description": "MCP Weaviate Direct Server"
            },
            "postgresql": {
                "port": 5432,
                "description": "PostgreSQL Database"
            },
            "redis": {
                "port": 6379,
                "description": "Redis Cache"
            }
        }
        
    def check_process(self, process_name: str) -> Tuple[bool, Optional[str]]:
        """Check if a process is running"""
                ["pgrep", "-f", process_name],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                return True, f"PIDs: {', '.join(pids)}"
            return False, None
        except Exception:

            pass
            return False, f"Error: {e}"
    
    def check_port(self, port: int) -> bool:
        """Check if a port is listening"""
                ["ss", "-tlnp"],
                capture_output=True,
                text=True
            )
            return f":{port}" in result.stdout
        except Exception:

            pass
            return False
    
    def check_http_endpoint(self, url: str) -> Tuple[bool, Optional[str]]:
        """Check if an HTTP endpoint is responding"""
            return True, f"Status: {response.status_code}"
        except Exception:

            pass
            return False, "Connection refused"
        except Exception:

            pass
            return False, "Timeout"
        except Exception:

            pass
            return False, str(e)
    
    def get_docker_containers(self) -> List[Dict]:
        """Get running Docker containers"""
                ["docker", "ps", "--format", "json"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                containers = []
                # TODO: Consider using list comprehension for better performance

                for line in result.stdout.strip().split('\n'):
                    if line:
                        containers.append(json.loads(line))
                return containers
            return []
        except Exception:

            pass
            return []
    
    def generate_summary(self) -> str:
        """Generate deployment summary"""
        summary = f"""
"""
        orchestrator_running, orchestrator_info = self.check_process("gunicorn")
        orchestrator_port = self.check_port(8000)
        summary += f"\n✅ Orchestrator API (Port 8000):\n"
        summary += f"   Process: {'Running' if orchestrator_running else 'Not Running'}\n"
        if orchestrator_info:
            summary += f"   {orchestrator_info}\n"
        summary += f"   Port: {'Open' if orchestrator_port else 'Closed'}\n"
        
        # Check Weaviate
        weaviate_ok, weaviate_status = self.check_http_endpoint("http://localhost:8080/v1")
        summary += f"\n{'✅' if weaviate_ok else '❌'} Weaviate (Port 8080):\n"
        summary += f"   Status: {weaviate_status}\n"
        summary += f"   Endpoint: http://localhost:8080/v1\n"
        
        # Check MCP Weaviate Server
        mcp_running, mcp_info = self.check_process("weaviate_direct_mcp_server")
        mcp_port = self.check_port(8001)
        summary += f"\n{'✅' if mcp_running else '❌'} MCP Weaviate Server (Port 8001):\n"
        summary += f"   Process: {'Running' if mcp_running else 'Not Running'}\n"
        if mcp_info:
            summary += f"   {mcp_info}\n"
        summary += f"   Port: {'Open' if mcp_port else 'Closed'}\n"
        
        # Check PostgreSQL
        pg_port = self.check_port(5432)
        summary += f"\n{'✅' if pg_port else '❌'} PostgreSQL (Port 5432):\n"
        summary += f"   Port: {'Open' if pg_port else 'Closed'}\n"
        
        # Check Redis
        redis_port = self.check_port(6379)
        summary += f"\n{'✅' if redis_port else '❌'} Redis (Port 6379):\n"
        summary += f"   Port: {'Open' if redis_port else 'Closed'}\n"
        
        # Docker containers
        containers = self.get_docker_containers()
        if containers:
            summary += f"\n\n🐳 DOCKER CONTAINERS\n"
            summary += "-" * 20 + "\n"
            for container in containers:
                summary += f"• {container.get('Names', 'Unknown')} - {container.get('Image', 'Unknown')}\n"
                summary += f"  Status: {container.get('Status', 'Unknown')}\n"
                summary += f"  Ports: {container.get('Ports', 'None')}\n"
        
        # Access URLs
        summary += f"""
"""
    """Main function"""
    logger.info("Generating Orchestra AI deployment summary...")
    
    summary_generator = OrchestraDeploymentSummary()
    summary = summary_generator.generate_summary()
    
    print(summary)
    
    # Save to file
    summary_file = f"deployment_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    Path(summary_file).write_text(summary)
    logger.info(f"Summary saved to: {summary_file}")


if __name__ == "__main__":
    main()