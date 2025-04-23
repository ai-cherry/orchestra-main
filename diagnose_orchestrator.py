#!/usr/bin/env python3
"""
Orchestrator System Diagnostic Utility

This script performs comprehensive diagnostics on the Orchestrator system,
checking for common issues and providing actionable solutions.
"""

import asyncio
import argparse
import logging
import os
import sys
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("orchestrator-diagnostics")

# Color constants for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Diagnostic result categories
class Status:
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"


class DiagnosticResult:
    """Container for diagnostic results."""
    
    def __init__(self, component: str, status: str, message: str, 
                details: Optional[Dict[str, Any]] = None, 
                solution: Optional[str] = None):
        self.component = component
        self.status = status
        self.message = message
        self.details = details or {}
        self.solution = solution
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "component": self.component,
            "status": self.status,
            "message": self.message,
            "details": self.details,
            "solution": self.solution,
            "timestamp": self.timestamp
        }
    
    def __str__(self) -> str:
        """Format result for display."""
        if self.status == Status.OK:
            status_color = Colors.GREEN
            status_text = "OK"
        elif self.status == Status.WARNING:
            status_color = Colors.YELLOW
            status_text = "WARNING"
        elif self.status == Status.ERROR:
            status_color = Colors.RED
            status_text = "ERROR"
        else:
            status_color = Colors.BLUE
            status_text = "INFO"
            
        result = (f"{Colors.BOLD}{self.component}{Colors.ENDC}: "
                 f"{status_color}{status_text}{Colors.ENDC} - {self.message}")
        
        if self.solution:
            result += f"\n  {Colors.CYAN}Solution: {Colors.ENDC}{self.solution}"
            
        return result


class OrchestratorDiagnostic:
    """
    Diagnostic utility for Orchestrator system.
    
    This class provides methods to check various components of the
    Orchestrator system and identify issues.
    """
    
    def __init__(self, env_file: str = ".env"):
        """
        Initialize the diagnostic utility.
        
        Args:
            env_file: Path to .env file (default: ".env")
        """
        self.env_file = env_file
        self.results = []
        self.environment = {}
        self._load_environment()
    
    def _load_environment(self) -> None:
        """Load environment variables from .env file."""
        if not os.path.exists(self.env_file):
            logger.warning(f".env file not found at {self.env_file}")
            return
            
        try:
            with open(self.env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    key, value = line.split("=", 1)
                    self.environment[key.strip()] = value.strip()
            logger.debug(f"Loaded {len(self.environment)} variables from {self.env_file}")
        except Exception as e:
            logger.error(f"Error reading .env file: {e}")
    
    async def run_all_checks(self) -> List[DiagnosticResult]:
        """Run all diagnostic checks."""
        try:
            # Basic system checks
            self.check_environment()
            self.check_python_dependencies()
            
            # Component checks
            await self.check_personas()
            await self.check_llm_client()
            await self.check_memory_system()
            
            # API checks
            await self.check_api_health()
            
            return self.results
        except Exception as e:
            logger.error(f"Error running diagnostics: {e}")
            self.results.append(DiagnosticResult(
                "diagnostics", 
                Status.ERROR,
                f"Failed to complete diagnostics: {e}", 
                {"traceback": traceback.format_exc()},
                "Check logs for detailed error information"
            ))
            return self.results
    
    def check_environment(self) -> None:
        """Check environment variables and configuration."""
        logger.info("Checking environment...")
        
        # Check for required API keys
        if not self.environment.get("OPENROUTER_API_KEY"):
            self.results.append(DiagnosticResult(
                "environment", 
                Status.ERROR,
                "Missing OPENROUTER_API_KEY in environment", 
                solution="Add OPENROUTER_API_KEY to your .env file. Get a key from https://openrouter.ai"
            ))
        else:
            self.results.append(DiagnosticResult(
                "environment", 
                Status.OK,
                "OPENROUTER_API_KEY found in environment"
            ))
        
        # Check for database credentials
        if not any(key.startswith("FIRESTORE_") for key in self.environment):
            self.results.append(DiagnosticResult(
                "environment", 
                Status.WARNING,
                "No Firestore credentials found in environment", 
                solution="Add Firestore credentials to your .env file if using cloud deployment"
            ))
        
        # Check for Redis configuration
        if not any(key.startswith("REDIS_") for key in self.environment):
            self.results.append(DiagnosticResult(
                "environment", 
                Status.INFO,
                "No Redis configuration found", 
                solution="Add Redis configuration to your .env file for improved performance"
            ))
    
    def check_python_dependencies(self) -> None:
        """Check Python dependencies."""
        logger.info("Checking Python dependencies...")
        
        dependencies = {
            "fastapi": "Required for API server",
            "pydantic": "Required for data validation",
            "yaml": "Required for configuration loading",
            "openai": "Required for LLM client",
            "firebase_admin": "Required for Firestore storage",
            "redis": "Optional for Redis caching"
        }
        
        missing = []
        for package, description in dependencies.items():
            try:
                __import__(package)
            except ImportError:
                missing.append((package, description))
        
        if not missing:
            self.results.append(DiagnosticResult(
                "dependencies", 
                Status.OK,
                "All required dependencies installed"
            ))
        else:
            # Distinguish between required and optional
            required = [(p, d) for p, d in missing if "Optional" not in d]
            optional = [(p, d) for p, d in missing if "Optional" in d]
            
            if required:
                missing_packages = ", ".join([p for p, _ in required])
                self.results.append(DiagnosticResult(
                    "dependencies", 
                    Status.ERROR,
                    f"Missing required dependencies: {missing_packages}", 
                    {"missing": [{"package": p, "description": d} for p, d in required]},
                    f"Run: pip install {' '.join([p for p, _ in required])}"
                ))
            
            if optional:
                missing_packages = ", ".join([p for p, _ in optional])
                self.results.append(DiagnosticResult(
                    "dependencies", 
                    Status.INFO,
                    f"Missing optional dependencies: {missing_packages}", 
                    {"missing": [{"package": p, "description": d} for p, d in optional]},
                    f"For full functionality: pip install {' '.join([p for p, _ in optional])}"
                ))
    
    async def check_personas(self) -> None:
        """Check persona configurations."""
        logger.info("Checking persona configurations...")
        
        try:
            # Import here to avoid module-level dependency issues
            from core.orchestrator.src.config.loader import load_persona_configs
            
            personas = load_persona_configs()
            
            if not personas:
                self.results.append(DiagnosticResult(
                    "personas", 
                    Status.ERROR,
                    "No persona configurations found", 
                    solution="Ensure personas.yaml exists and is properly formatted"
                ))
                return
            
            # Check for default persona
            if "cherry" not in personas:
                self.results.append(DiagnosticResult(
                    "personas", 
                    Status.WARNING,
                    "Default 'cherry' persona not found", 
                    solution="Add a 'cherry' persona configuration for fallback scenarios"
                ))
            
            # Check personas for minimum required fields
            invalid_personas = []
            for name, persona in personas.items():
                missing_fields = []
                for field in ["name", "description", "prompt_template"]:
                    if not hasattr(persona, field) or not getattr(persona, field):
                        missing_fields.append(field)
                
                if missing_fields:
                    invalid_personas.append((name, missing_fields))
            
            if invalid_personas:
                self.results.append(DiagnosticResult(
                    "personas", 
                    Status.WARNING,
                    f"{len(invalid_personas)} persona(s) have missing required fields", 
                    {"invalid": [{"name": name, "missing": fields} for name, fields in invalid_personas]},
                    "Update personas.yaml to include all required fields"
                ))
            
            self.results.append(DiagnosticResult(
                "personas", 
                Status.OK,
                f"Found {len(personas)} valid persona configurations",
                {"personas": list(personas.keys())}
            ))
            
        except Exception as e:
            self.results.append(DiagnosticResult(
                "personas", 
                Status.ERROR,
                f"Error checking persona configurations: {e}", 
                {"error": str(e), "traceback": traceback.format_exc()},
                "Check the personas.yaml file for syntax errors"
            ))
    
    async def check_llm_client(self) -> None:
        """Check LLM client configuration."""
        logger.info("Checking LLM client...")
        
        if not self.environment.get("OPENROUTER_API_KEY"):
            self.results.append(DiagnosticResult(
                "llm_client", 
                Status.WARNING,
                "Skipping LLM client check due to missing API key",
                solution="Add OPENROUTER_API_KEY to your .env file to run this check"
            ))
            return
        
        try:
            # Import here to avoid module-level dependency issues
            from packages.shared.src.llm_client.openrouter_client import OpenRouterClient
            
            client = OpenRouterClient()
            health_info = await client.health_check()
            
            if health_info.get("status") == "healthy":
                self.results.append(DiagnosticResult(
                    "llm_client", 
                    Status.OK,
                    "LLM client is healthy", 
                    {"health": health_info}
                ))
            else:
                self.results.append(DiagnosticResult(
                    "llm_client", 
                    Status.WARNING,
                    f"LLM client reports {health_info.get('status')} status", 
                    {"health": health_info},
                    "Check API key validity and connection to OpenRouter"
                ))
        except Exception as e:
            self.results.append(DiagnosticResult(
                "llm_client", 
                Status.ERROR,
                f"Error checking LLM client: {e}", 
                {"error": str(e), "traceback": traceback.format_exc()},
                "Verify your OpenRouter API key and check network connectivity"
            ))
    
    async def check_memory_system(self) -> None:
        """Check memory system configuration."""
        logger.info("Checking memory system...")
        
        try:
            # Import here to avoid module-level dependency issues
            from packages.shared.src.memory.concrete_memory_manager import ConcreteMemoryManager
            
            # Create memory manager with minimal configuration
            memory_manager = ConcreteMemoryManager()
            
            try:
                # Initialize memory manager
                memory_manager.initialize()
                
                # Check health
                health_info = await memory_manager.health_check()
                
                if health_info.get("status") == "healthy":
                    self.results.append(DiagnosticResult(
                        "memory_system", 
                        Status.OK,
                        "Memory system is healthy", 
                        {"health": health_info}
                    ))
                elif health_info.get("status") == "degraded":
                    solutions = []
                    if not health_info.get("redis", False):
                        solutions.append("Configure Redis for improved performance")
                    
                    self.results.append(DiagnosticResult(
                        "memory_system", 
                        Status.WARNING,
                        "Memory system is in degraded state", 
                        {"health": health_info},
                        ". ".join(solutions) if solutions else "Check Firestore and Redis connections"
                    ))
                else:
                    self.results.append(DiagnosticResult(
                        "memory_system", 
                        Status.ERROR,
                        "Memory system reports unhealthy status", 
                        {"health": health_info},
                        "Check Firestore credentials and connectivity"
                    ))
            except Exception as e:
                self.results.append(DiagnosticResult(
                    "memory_system", 
                    Status.ERROR,
                    f"Failed to initialize memory system: {e}", 
                    {"error": str(e), "traceback": traceback.format_exc()},
                    "Verify Firestore credentials in environment"
                ))
                
        except Exception as e:
            self.results.append(DiagnosticResult(
                "memory_system", 
                Status.ERROR,
                f"Error setting up memory system diagnostic: {e}", 
                {"error": str(e), "traceback": traceback.format_exc()},
                "Check import dependencies and installed packages"
            ))
    
    async def check_api_health(self) -> None:
        """Check API health."""
        logger.info("Checking API health endpoints...")
        
        try:
            import requests
            
            # Try to connect to the API health endpoint
            try:
                response = requests.get("http://localhost:8000/api/health", timeout=5)
                if response.status_code == 200:
                    health_data = response.json()
                    self.results.append(DiagnosticResult(
                        "api_health", 
                        Status.OK,
                        "API health endpoint is responding", 
                        {"health": health_data}
                    ))
                else:
                    self.results.append(DiagnosticResult(
                        "api_health", 
                        Status.ERROR,
                        f"API health endpoint returned status code {response.status_code}", 
                        {"status_code": response.status_code, "response": response.text},
                        "Check API server logs for errors"
                    ))
            except requests.exceptions.ConnectionError:
                self.results.append(DiagnosticResult(
                    "api_health", 
                    Status.WARNING,
                    "Could not connect to API health endpoint", 
                    solution="Ensure the API server is running: python -m core.orchestrator.src.main"
                ))
            except Exception as e:
                self.results.append(DiagnosticResult(
                    "api_health", 
                    Status.ERROR,
                    f"Error connecting to API health endpoint: {e}", 
                    {"error": str(e), "traceback": traceback.format_exc()},
                    "Check if the API server is running and configured correctly"
                ))
        except ImportError:
            self.results.append(DiagnosticResult(
                "api_health", 
                Status.WARNING,
                "Skipping API health check - requests module not installed", 
                solution="Install requests module: pip install requests"
            ))


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Orchestrator System Diagnostic Utility")
    parser.add_argument("--env", default=".env", help="Path to .env file")
    parser.add_argument("--output", help="Path to save results as JSON file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print(f"{Colors.BOLD}Orchestrator System Diagnostic{Colors.ENDC}")
    print(f"{Colors.CYAN}Running diagnostics...{Colors.ENDC}")
    
    # Run diagnostics
    diagnostic = OrchestratorDiagnostic(env_file=args.env)
    results = await diagnostic.run_all_checks()
    
    # Print results
    print(f"\n{Colors.BOLD}Diagnostic Results:{Colors.ENDC}")
    
    # Group by component and status
    components = {}
    for result in results:
        if result.component not in components:
            components[result.component] = []
        components[result.component].append(result)
    
    for component, results in components.items():
        print(f"\n{Colors.BOLD}[{component.upper()}]{Colors.ENDC}")
        for result in results:
            print(f"  {result}")
    
    # Count issues by severity
    errors = sum(1 for r in results if r.status == Status.ERROR)
    warnings = sum(1 for r in results if r.status == Status.WARNING)
    
    print(f"\n{Colors.BOLD}Summary:{Colors.ENDC}")
    print(f"  Total checks: {len(results)}")
    print(f"  {Colors.RED}Errors: {errors}{Colors.ENDC}")
    print(f"  {Colors.YELLOW}Warnings: {warnings}{Colors.ENDC}")
    print(f"  {Colors.GREEN}Passed: {len(results) - errors - warnings}{Colors.ENDC}")
    
    # Save results to file if requested
    if args.output:
        try:
            with open(args.output, "w") as f:
                json.dump({
                    "timestamp": datetime.utcnow().isoformat(),
                    "results": [r.to_dict() for r in results]
                }, f, indent=2)
            print(f"\nResults saved to {args.output}")
        except Exception as e:
            print(f"\n{Colors.RED}Error saving results: {e}{Colors.ENDC}")
    
    # Return exit code based on results
    if errors > 0:
        return 2
    elif warnings > 0:
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
