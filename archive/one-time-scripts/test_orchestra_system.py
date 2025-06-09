# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
    """Test all Cherry AI system components"""
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "environment": {},
            "services": {},
            "api_endpoints": {},
            "search_modes": {},
            "file_processing": {},
            "personas": {},
            "issues": [],
            "recommendations": []
        }
    
    def check_environment(self) -> Dict[str, bool]:
        """Check environment setup"""
            "python_version": sys.version.startswith("3.10") or sys.version.startswith("3.11") or sys.version.startswith("3.12"),
            "venv_active": hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix),
            "env_file": (self.base_dir / ".env").exists(),
            "docker_installed": self._check_command("docker --version"),
            "docker_compose_installed": self._check_command("docker-compose --version") or self._check_command("docker compose version"),
            "node_installed": self._check_command("node --version"),
            "npm_installed": self._check_command("npm --version")
        }
        
        # Check required environment variables
        required_vars = ["POSTGRES_HOST", "POSTGRES_USER", "POSTGRES_DB", "OPENAI_API_KEY"]
        for var in required_vars:
            env_checks[f"env_{var.lower()}"] = os.getenv(var) is not None
        
        self.test_results["environment"] = env_checks
        return env_checks
    
    def _check_command(self, command: str) -> bool:
        """Check if a command is available"""
        """Check if services are running"""
            "postgres": {"port": 5432, "process": "postgres"},
            "redis": {"port": 6379, "process": "redis"},
            "weaviate": {"port": 8080, "process": "weaviate"},
            "api": {"port": 8000, "process": "uvicorn"},
            "ui": {"port": 3000, "process": "nginx"}
        }
        
        service_status = {}
        for service, config in services.items():
            status = {
                "port_open": self._check_port(config["port"]),
                "process_running": self._check_process(config["process"])
            }
            status["healthy"] = status["port_open"] or status["process_running"]
            service_status[service] = status
        
        self.test_results["services"] = service_status
        return service_status
    
    def _check_port(self, port: int) -> bool:
        """Check if a port is open"""
        """Check if a process is running"""
        """Test API endpoints"""
        base_url = "http://localhost:8000"
        endpoints = {
            "health": "/health",
            "docs": "/docs",
            "search": "/api/search?q=test&mode=normal",
            "personas": "/api/personas",
            "agents": "/api/agents",
            "tasks": "/api/tasks"
        }
        
        results = {}
        async with aiohttp.ClientSession() as session:
            for name, endpoint in endpoints.items():
                try:

                    pass
                    async with session.get(f"{base_url}{endpoint}", timeout=5) as response:
                        results[name] = {
                            "status": response.status,
                            "success": 200 <= response.status < 300,
                            "response_time": response.headers.get("X-Response-Time", "N/A")
                        }
                except Exception:

                    pass
                    results[name] = {
                        "status": 0,
                        "success": False,
                        "error": str(e)
                    }
        
        self.test_results["api_endpoints"] = results
        return results
    
    async def test_search_modes(self) -> Dict[str, Dict[str, any]]:
        """Test all search modes"""
        modes = ["normal", "creative", "deep", "super_deep", "uncensored"]
        base_url = "http://localhost:8000/api/search"
        
        results = {}
        async with aiohttp.ClientSession() as session:
            for mode in modes:
                try:

                    pass
                    async with session.get(
                        base_url,
                        params={"q": "test query", "mode": mode},
                        timeout=10
                    ) as response:
                        data = await response.json() if response.status == 200 else None
                        results[mode] = {
                            "status": response.status,
                            "success": response.status == 200,
                            "results_count": len(data.get("results", [])) if data else 0
                        }
                except Exception:

                    pass
                    results[mode] = {
                        "status": 0,
                        "success": False,
                        "error": str(e)
                    }
        
        self.test_results["search_modes"] = results
        return results
    
    async def test_file_processing(self) -> Dict[str, bool]:
        """Test file processing capabilities"""
            "text": ("test.txt", b"Test content"),
            "json": ("test.json", json.dumps({"test": "data"}).encode()),
            "large": ("large.txt", b"x" * (1024 * 1024))  # 1MB file
        }
        
        results = {}
        test_dir = self.base_dir / "test_uploads"
        test_dir.mkdir(exist_ok=True)
        
        for file_type, (filename, content) in test_files.items():
            file_path = test_dir / filename
            file_path.write_bytes(content)
            
            # Test upload
            try:

                pass
                async with aiohttp.ClientSession() as session:
                    with open(file_path, 'rb') as f:
                        data = aiohttp.FormData()
                        data.add_field('file', f, filename=filename)
                        
                        async with session.post(
                            "http://localhost:8000/api/upload",
                            data=data,
                            timeout=30
                        ) as response:
                            results[f"{file_type}_upload"] = response.status == 200
            except Exception:

                pass
                results[f"{file_type}_upload"] = False
                self.test_results["issues"].append(f"File upload failed for {file_type}: {e}")
            
            # Cleanup
            file_path.unlink(missing_ok=True)
        
        test_dir.rmdir()
        self.test_results["file_processing"] = results
        return results
    
    async def test_personas(self) -> Dict[str, Dict[str, any]]:
        """Test persona functionality"""
            "cherry": {"domain": "personal", "color": "#FF69B4"},
            "sophia": {"domain": "payready", "color": "#FFD700"},
            "karen": {"domain": "paragonrx", "color": "#32CD32"}
        }
        
        results = {}
        async with aiohttp.ClientSession() as session:
            for persona, config in personas.items():
                try:

                    pass
                    # Test persona activation
                    async with session.post(
                        f"http://localhost:8000/api/personas/{persona}/activate",
                        timeout=5
                    ) as response:
                        results[persona] = {
                            "activation": response.status == 200,
                            "domain": config["domain"],
                            "configured": True
                        }
                except Exception:

                    pass
                    results[persona] = {
                        "activation": False,
                        "domain": config["domain"],
                        "error": str(e)
                    }
        
        self.test_results["personas"] = results
        return results
    
    def generate_recommendations(self):
        """Generate recommendations based on test results"""
        env = self.test_results["environment"]
        if not env.get("docker_installed"):
            recommendations.append("Install Docker: https://docs.docker.com/get-docker/")
        if not env.get("node_installed"):
            recommendations.append("Install Node.js: https://nodejs.org/")
        
        # Service recommendations
        services = self.test_results["services"]
        for service, status in services.items():
            if not status.get("healthy"):
                recommendations.append(f"Start {service} service: docker-compose up -d {service}")
        
        # API recommendations
        api_endpoints = self.test_results.get("api_endpoints", {})
        if not any(ep.get("success") for ep in api_endpoints.values()):
            recommendations.append("API not responding. Check logs: docker-compose logs api")
        
        self.test_results["recommendations"] = recommendations
    
    def generate_report(self) -> str:
        """Generate comprehensive test report"""
        report = f"""
"""
        for check, passed in self.test_results["environment"].items():
            status = "✅" if passed else "❌"
            report += f"  {status} {check.replace('_', ' ').title()}\n"
        
        report += "\n🚀 SERVICE STATUS:\n"
        for service, status in self.test_results["services"].items():
            health = "✅" if status.get("healthy") else "❌"
            report += f"  {health} {service.upper()}"
            if status.get("port_open"):
                report += " (port open)"
            if status.get("process_running"):
                report += " (process running)"
            report += "\n"
        
        report += "\n🌐 API ENDPOINTS:\n"
        for endpoint, result in self.test_results.get("api_endpoints", {}).items():
            status = "✅" if result.get("success") else "❌"
            report += f"  {status} {endpoint}: "
            if result.get("success"):
                report += f"Status {result.get('status')}"
            else:
                report += f"Failed - {result.get('error', 'Unknown error')}"
            report += "\n"
        
        report += "\n🔍 SEARCH MODES:\n"
        for mode, result in self.test_results.get("search_modes", {}).items():
            status = "✅" if result.get("success") else "❌"
            report += f"  {status} {mode}: "
            if result.get("success"):
                report += f"{result.get('results_count')} results"
            else:
                report += "Failed"
            report += "\n"
        
        report += "\n👥 PERSONAS:\n"
        for persona, result in self.test_results.get("personas", {}).items():
            status = "✅" if result.get("activation") else "❌"
            report += f"  {status} {persona.upper()} ({result.get('domain')})\n"
        
        if self.test_results["issues"]:
            report += "\n⚠️  ISSUES FOUND:\n"
            for issue in self.test_results["issues"]:
                report += f"  • {issue}\n"
        
        if self.test_results["recommendations"]:
            report += "\n💡 RECOMMENDATIONS:\n"
            for rec in self.test_results["recommendations"]:
                report += f"  • {rec}\n"
        
        # Overall status
        all_services_healthy = all(
            s.get("healthy") for s in self.test_results["services"].values()
        )
        api_working = any(
            ep.get("success") for ep in self.test_results.get("api_endpoints", {}).values()
        )
        
        report += f"\n📊 OVERALL STATUS: "
        if all_services_healthy and api_working:
            report += "✅ SYSTEM OPERATIONAL"
        elif api_working:
            report += "⚠️  PARTIALLY OPERATIONAL"
        else:
            report += "❌ SYSTEM DOWN"
        
        report += "\n\n🚀 QUICK START COMMANDS:\n"
        report += "  1. Start all services: ./start_cherry_ai.sh\n"
        report += "  2. Check logs: docker-compose logs -f\n"
        report += "  3. Access UI: http://localhost:3000\n"
        report += "  4. Access API: http://localhost:8000/docs\n"
        
        return report
    
    async def run_all_tests(self):
        """Run all system tests"""
        print("🔍 Running Cherry AI system tests...\n")
        
        # Run tests
        print("Checking environment...")
        self.check_environment()
        
        print("Checking services...")
        self.check_services()
        
        print("Testing API endpoints...")
        await self.test_api_endpoints()
        
        print("Testing search modes...")
        await self.test_search_modes()
        
        print("Testing file processing...")
        await self.test_file_processing()
        
        print("Testing personas...")
        await self.test_personas()
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Generate and display report
        report = self.generate_report()
        print(report)
        
        # Save report
        report_file = self.base_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_file.write_text(report)
        print(f"\n📄 Report saved to: {report_file}")
        
        # Save JSON results
        json_file = self.base_dir / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        print(f"📄 JSON results saved to: {json_file}")

async def main():
    """Main entry point"""
if __name__ == "__main__":
    # Check if psutil is installed
    try:

        pass
        import psutil
    except Exception:

        pass
        print("Installing required dependency: psutil")
        subprocess.run([sys.executable, "-m", "pip", "install", "psutil"], check=True)
        import psutil
    
    # Check if aiohttp is installed
    try:

        pass
        import aiohttp
    except Exception:

        pass
        print("Installing required dependency: aiohttp")
        subprocess.run([sys.executable, "-m", "pip", "install", "aiohttp"], check=True)
        import aiohttp
    
    asyncio.run(main())