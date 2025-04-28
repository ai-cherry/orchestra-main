#!/usr/bin/env python3
"""
DEPRECATED: This diagnostic script is deprecated and will be removed in a future release.

This script has been replaced by the comprehensive unified_diagnostics.py which 
provides complete system diagnostics in one tool.

Please use unified_diagnostics.py instead.
Example: python unified_diagnostics.py

Orchestrator Diagnostic Tool for Patrick's Solo-User Experience

This diagnostic tool specifically focuses on identifying issues in:
1. Persona switching failures
2. Memory retrieval errors
3. LLM integration problems

It performs targeted tests and provides clear, actionable error messages.
"""

import asyncio
import logging
import argparse
import sys
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("patrick-diagnostics")

# Terminal colors for better readability
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

# Status codes for diagnostic results
class Status:
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"

class DiagnosticResult:
    """Container for diagnostic results with user-friendly messaging."""
    
    def __init__(self, component: str, status: str, message: str, 
                details: Optional[Dict[str, Any]] = None, 
                solution: Optional[str] = None,
                user_message: Optional[str] = None):
        self.component = component
        self.status = status
        self.message = message
        self.details = details or {}
        self.solution = solution
        self.user_message = user_message or message  # Default to technical message if no user message
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "component": self.component,
            "status": self.status,
            "message": self.message,
            "user_message": self.user_message,
            "details": self.details,
            "solution": self.solution,
            "timestamp": self.timestamp
        }
    
    def __str__(self) -> str:
        """Format result for display with user-friendly messaging."""
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
        
        if self.user_message and self.user_message != self.message:
            result += f"\n  {Colors.CYAN}User Impact: {Colors.ENDC}{self.user_message}"
            
        if self.solution:
            result += f"\n  {Colors.CYAN}Solution: {Colors.ENDC}{self.solution}"
            
        return result


class PatrickDiagnostic:
    """
    Diagnostic utility specifically focused on Patrick's solo-user experience.
    
    This class provides methods to check issues affecting persona switching,
    memory retrieval, and LLM integration.
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
        """Run all diagnostic checks specifically focused on Patrick's experience."""
        try:
            # Persona diagnostics
            await self.diagnose_persona_switching()
            
            # Memory diagnostics
            await self.diagnose_memory_system()
            
            # LLM integration diagnostics
            await self.diagnose_llm_integration()
            
            # Simulate actual flows
            await self.simulate_user_flows()
            
            return self.results
        except Exception as e:
            import traceback
            logger.error(f"Error running diagnostics: {e}")
            self.results.append(DiagnosticResult(
                "diagnostics", 
                Status.ERROR,
                f"Failed to complete diagnostics: {e}", 
                {"traceback": traceback.format_exc()},
                "Check logs for detailed error information",
                "The diagnostic tool encountered an unexpected error. This might indicate deeper system issues."
            ))
            return self.results
    
    async def diagnose_persona_switching(self) -> None:
        """
        Diagnose issues related to persona switching.
        
        Checks:
        1. Persona configuration loading
        2. Fallback mechanisms
        3. Error reporting quality
        """
        logger.info("Diagnosing persona switching issues...")
        
        try:
            # Check if we can import the necessary modules
            try:
                from core.orchestrator.src.config.loader import load_persona_configs
                from packages.shared.src.models.base_models import PersonaConfig
            except ImportError as e:
                self.results.append(DiagnosticResult(
                    "personas", 
                    Status.ERROR,
                    f"Failed to import persona modules: {e}", 
                    {"error": str(e)},
                    "Ensure core.orchestrator and packages.shared are in the Python path",
                    "System can't access persona configuration files, which will prevent persona switching."
                ))
                return
            
            # Check persona configurations
            try:
                personas = load_persona_configs()
                
                if not personas:
                    self.results.append(DiagnosticResult(
                        "personas", 
                        Status.ERROR,
                        "No persona configurations found", 
                        solution="Ensure personas.yaml exists and is properly formatted",
                        user_message="You won't be able to switch between different AI personalities because no valid personalities were found."
                    ))
                    return
                
                # Check for required personas
                if "cherry" not in personas:
                    self.results.append(DiagnosticResult(
                        "personas", 
                        Status.WARNING,
                        "Default 'cherry' persona not found", 
                        solution="Add a 'cherry' persona configuration for fallback scenarios",
                        user_message="The system might use an unexpected personality if your requested one isn't available."
                    ))
                
                # Check for persona configuration quality
                for name, persona in personas.items():
                    issues = []
                    
                    # Check for minimal required fields with good values
                    if not persona.description or len(persona.description) < 10:
                        issues.append("Short or missing description")
                    
                    if not persona.prompt_template or len(persona.prompt_template) < 20:
                        issues.append("Short or missing prompt template")
                    
                    if issues:
                        self.results.append(DiagnosticResult(
                            "personas", 
                            Status.WARNING,
                            f"Persona '{name}' has configuration issues: {', '.join(issues)}", 
                            {"issues": issues, "persona": name},
                            f"Improve the configuration for persona '{name}'",
                            f"The '{name}' personality might not behave as expected due to incomplete configuration."
                        ))
                
                # Overall status for personas
                if len(personas) > 0:
                    self.results.append(DiagnosticResult(
                        "personas", 
                        Status.OK,
                        f"Found {len(personas)} valid persona configurations",
                        {"personas": list(personas.keys())}
                    ))
                
            except Exception as e:
                import traceback
                self.results.append(DiagnosticResult(
                    "personas", 
                    Status.ERROR,
                    f"Error checking persona configurations: {e}", 
                    {"error": str(e), "traceback": traceback.format_exc()},
                    "Check the personas.yaml file for syntax errors",
                    "The system encountered errors loading AI personalities, which will prevent persona switching."
                ))
                
            # Check persona middleware
            try:
                from core.orchestrator.src.api.middleware.persona_loader import get_active_persona
                
                # Create a mock request to test the middleware
                class MockRequest:
                    def __init__(self, query_params=None):
                        self.query_params = query_params or {}
                        self.state = type('obj', (object,), {})
                
                # Test requesting a valid persona
                mock_request = MockRequest(query_params={"persona": "cherry"})
                try:
                    # This will fail if cherry doesn't exist, which we already check above
                    if "cherry" in personas:
                        active_persona = await get_active_persona(mock_request, personas)
                        if active_persona.name.lower() != "cherry":
                            self.results.append(DiagnosticResult(
                                "personas", 
                                Status.WARNING,
                                f"Middleware returned '{active_persona.name}' when 'cherry' was requested", 
                                solution="Check the persona selection logic in middleware",
                                user_message="The system might use a different personality than the one you requested."
                            ))
                except Exception as e:
                    self.results.append(DiagnosticResult(
                        "personas", 
                        Status.ERROR,
                        f"Persona middleware failed with valid persona: {e}", 
                        {"error": str(e)},
                        "Debug the get_active_persona function in persona_loader.py",
                        "The system is unable to properly select AI personalities even when they exist."
                    ))
                
                # Test requesting an invalid persona to check fallback
                mock_request = MockRequest(query_params={"persona": "nonexistent_persona"})
                try:
                    active_persona = await get_active_persona(mock_request, personas)
                    if not active_persona:
                        self.results.append(DiagnosticResult(
                            "personas", 
                            Status.ERROR,
                            "Persona middleware returned None for invalid persona request", 
                            solution="Fix the fallback logic in get_active_persona",
                            user_message="The system crashes when you request a personality that doesn't exist."
                        ))
                    elif active_persona.name.lower() == "nonexistent_persona":
                        self.results.append(DiagnosticResult(
                            "personas", 
                            Status.ERROR,
                            "Persona middleware didn't properly handle invalid persona", 
                            solution="Fix the fallback logic in get_active_persona",
                            user_message="The system incorrectly accepts invalid personality names without proper fallback."
                        ))
                    else:
                        # Check if it properly stored the requested vs active persona
                        if not hasattr(mock_request.state, 'requested_persona') or not hasattr(mock_request.state, 'active_persona'):
                            self.results.append(DiagnosticResult(
                                "personas", 
                                Status.WARNING,
                                "Persona middleware doesn't store requested and active personas in request state", 
                                solution="Ensure middleware sets request.state.requested_persona and request.state.active_persona",
                                user_message="The system doesn't properly track which personality you requested versus which one was used."
                            ))
                        else:
                            self.results.append(DiagnosticResult(
                                "personas", 
                                Status.OK,
                                "Persona fallback mechanism works correctly"
                            ))
                except Exception as e:
                    self.results.append(DiagnosticResult(
                        "personas", 
                        Status.ERROR,
                        f"Persona middleware failed with invalid persona: {e}", 
                        {"error": str(e)},
                        "Debug the fallback logic in get_active_persona",
                        "The system crashes when you request a personality that doesn't exist."
                    ))
                
            except ImportError as e:
                self.results.append(DiagnosticResult(
                    "personas", 
                    Status.ERROR,
                    f"Could not import persona middleware: {e}", 
                    {"error": str(e)},
                    "Ensure the middleware package is properly installed",
                    "The system component that handles personality switching is missing or inaccessible."
                ))
                
        except Exception as e:
            import traceback
            self.results.append(DiagnosticResult(
                "personas", 
                Status.ERROR,
                f"Failed to diagnose persona system: {e}", 
                {"error": str(e), "traceback": traceback.format_exc()},
                "Check the logs for detailed error information",
                "A critical error occurred when checking the personality switching system."
            ))
    
    async def diagnose_memory_system(self) -> None:
        """
        Diagnose issues related to memory retrieval.
        
        Checks:
        1. Memory manager initialization
        2. Storage backend connectivity
        3. Read/write operations
        4. Error handling quality
        """
        logger.info("Diagnosing memory system...")
        
        try:
            # Import the memory manager
            try:
                from packages.shared.src.memory.memory_manager import MemoryManager, InMemoryMemoryManager
                from packages.shared.src.models.base_models import MemoryItem
            except ImportError as e:
                self.results.append(DiagnosticResult(
                    "memory", 
                    Status.ERROR,
                    f"Failed to import memory modules: {e}", 
                    {"error": str(e)},
                    "Ensure packages.shared is in the Python path",
                    "The system can't access conversation memory components, which will cause chat history loss."
                ))
                return
            
            # Test memory manager initialization
            try:
                memory_manager = InMemoryMemoryManager()
                await memory_manager.initialize()
                
                self.results.append(DiagnosticResult(
                    "memory", 
                    Status.INFO,
                    "Using InMemoryMemoryManager for testing", 
                    {},
                    None,
                    "Your conversation history is stored in memory only and will be lost if the system restarts."
                ))
                
                # Check if Firestore is configured
                if not any(key.startswith("FIRESTORE_") for key in self.environment):
                    self.results.append(DiagnosticResult(
                        "memory", 
                        Status.WARNING,
                        "No Firestore credentials found", 
                        solution="Add Firestore credentials to .env for persistent storage",
                        user_message="Your conversation history will be lost when the system restarts because persistent storage isn't configured."
                    ))
                
                # Test basic memory operations
                test_item = MemoryItem(
                    user_id="patrick_diagnostic",
                    session_id="test_session",
                    item_type="message",
                    persona_active="diagnostic",
                    text_content="This is a test message",
                    timestamp=datetime.utcnow(),
                    metadata={"source": "diagnostic"}
                )
                
                # Test add operation
                await memory_manager.add_memory_item(test_item)
                
                # Test retrieval operation
                history = await memory_manager.get_conversation_history(
                    user_id="patrick_diagnostic",
                    limit=10
                )
                
                # Check if the item was retrieved correctly
                if not history:
                    self.results.append(DiagnosticResult(
                        "memory", 
                        Status.ERROR,
                        "Failed to retrieve conversation history", 
                        solution="Debug the get_conversation_history method",
                        user_message="The system can't retrieve your conversation history, making it forget previous interactions."
                    ))
                else:
                    found = False
                    for item in history:
                        if (item.user_id == "patrick_diagnostic" and
                            item.text_content == "This is a test message"):
                            found = True
                            break
                    
                    if not found:
                        self.results.append(DiagnosticResult(
                            "memory", 
                            Status.ERROR,
                            "Retrieved history does not contain the test item", 
                            solution="Debug the memory storage and retrieval logic",
                            user_message="The system memory isn't working correctly; it can save messages but can't retrieve them properly."
                        ))
                    else:
                        self.results.append(DiagnosticResult(
                            "memory", 
                            Status.OK,
                            "Memory operations (add/retrieve) working correctly"
                        ))
                
                # Test error handling by forcing an error
                try:
                    # Create an invalid memory item without required fields
                    invalid_item = MemoryItem(
                        user_id=None,  # Invalid: user_id is required
                        session_id="test_session",
                        item_type="message",
                        persona_active="diagnostic",
                        text_content="This should fail",
                        timestamp=datetime.utcnow(),
                        metadata={"source": "diagnostic"}
                    )
                    await memory_manager.add_memory_item(invalid_item)
                    
                    # If we get here, it didn't validate properly
                    self.results.append(DiagnosticResult(
                        "memory", 
                        Status.WARNING,
                        "Memory manager accepted an invalid item", 
                        solution="Add validation in add_memory_item method",
                        user_message="The system doesn't properly validate memory entries, which could lead to data corruption."
                    ))
                except Exception:
                    # This is expected - we want to make sure it throws an error for invalid data
                    pass
                
            except Exception as e:
                import traceback
                self.results.append(DiagnosticResult(
                    "memory", 
                    Status.ERROR,
                    f"Memory manager initialization failed: {e}", 
                    {"error": str(e), "traceback": traceback.format_exc()},
                    "Check the memory manager implementation",
                    "The conversation memory system failed to start, which will prevent chat history from working."
                ))
                
            # Test hardcoded user_id in interaction.py
            try:
                from core.orchestrator.src.api.endpoints.interaction import interact
                
                # Use introspection to check if the function has a hardcoded user_id
                import inspect
                source = inspect.getsource(interact)
                
                if "user_id=\"patrick\"" in source or "user_id='patrick'" in source:
                    self.results.append(DiagnosticResult(
                        "memory", 
                        Status.WARNING,
                        "Interaction endpoint has hardcoded user_id 'patrick'", 
                        solution="Modify interaction.py to extract user_id from request authentication or context",
                        user_message="The system is hardcoded for a single user ('patrick'); using it with multiple users will cause chat history confusion."
                    ))
            except Exception:
                # Not critical, just skip this check if it fails
                pass
                
        except Exception as e:
            import traceback
            self.results.append(DiagnosticResult(
                "memory", 
                Status.ERROR,
                f"Failed to diagnose memory system: {e}", 
                {"error": str(e), "traceback": traceback.format_exc()},
                "Check the logs for detailed error information",
                "A critical error occurred when checking the conversation memory system."
            ))
    
    async def diagnose_llm_integration(self) -> None:
        """
        Diagnose issues related to LLM integration.
        
        Checks:
        1. API key validation
        2. Client initialization
        3. Error handling quality
        4. Rate limiting behavior
        """
        logger.info("Diagnosing LLM integration...")
        
        try:
            # Check for API keys
            if not self.environment.get("OPENROUTER_API_KEY") and not self.environment.get("PORTKEY_API_KEY"):
                self.results.append(DiagnosticResult(
                    "llm_integration", 
                    Status.ERROR,
                    "Missing LLM API keys (OPENROUTER_API_KEY or PORTKEY_API_KEY)", 
                    solution="Add required API keys to your .env file",
                    user_message="The system can't connect to any AI models because the required API keys are missing."
                ))
                return
            
            # Import the LLM client
            try:
                from packages.shared.src.llm_client.interface import LLMClient
                # Try to import the regular client first
                try:
                    from packages.shared.src.llm_client.portkey_client import PortkeyClient
                except ImportError:
                    # Fall back to mock client if regular client is not available
                    from packages.shared.src.llm_client.mock_portkey_client import MockPortkeyClient as PortkeyClient
                    logger.info("Using MockPortkeyClient for diagnostics")
            except ImportError as e:
                self.results.append(DiagnosticResult(
                    "llm_integration", 
                    Status.ERROR,
                    f"Failed to import LLM client modules: {e}", 
                    {"error": str(e)},
                    "Ensure packages.shared is in the Python path",
                    "The system can't access the components needed to communicate with AI models."
                ))
                return
            
            # Test LLM client initialization
            try:
                from core.orchestrator.src.config.settings import get_settings
                settings = get_settings()
                llm_client = PortkeyClient(settings)
                
                # Test health check if available
                if hasattr(llm_client, 'health_check'):
                    health_info = await llm_client.health_check()
                    
                    if health_info.get("status") == "healthy":
                        self.results.append(DiagnosticResult(
                            "llm_integration", 
                            Status.OK,
                            "LLM client is healthy", 
                            {"health": health_info}
                        ))
                    else:
                        self.results.append(DiagnosticResult(
                            "llm_integration", 
                            Status.WARNING,
                            f"LLM client reports {health_info.get('status')} status", 
                            {"health": health_info},
                            "Check API key validity and connection to LLM provider",
                            "The connection to AI models is degraded, which may cause slow responses or failures."
                        ))
                else:
                    # If no health check, attempt a simple API call
                    try:
                        # Use a minimal prompt to test connectivity
                        messages = [
                            {"role": "system", "content": "You are a test assistant."},
                            {"role": "user", "content": "Respond with 'OK' if you receive this message."}
                        ]
                        
                        result = await llm_client.generate_response(
                            model="gpt-3.5-turbo",  # Use a cheaper model for testing
                            messages=messages,
                            temperature=0.7,
                            max_tokens=10
                        )
                        
                        if result:
                            self.results.append(DiagnosticResult(
                                "llm_integration", 
                                Status.OK,
                                "Successfully connected to LLM provider", 
                                {"response": result}
                            ))
                        else:
                            self.results.append(DiagnosticResult(
                                "llm_integration", 
                                Status.WARNING,
                                "LLM provider returned empty response", 
                                solution="Check API key and model configuration",
                                user_message="The AI model connection works but returned an empty response, which might indicate configuration issues."
                            ))
                    except Exception as e:
                        self.results.append(DiagnosticResult(
                            "llm_integration", 
                            Status.ERROR,
                            f"Failed to generate test response: {e}", 
                            {"error": str(e)},
                            "Check API key validity and network connectivity",
                            "The system couldn't get a response from the AI models. Check your internet connection and API keys."
                        ))
                        
                # Check for fallback mechanisms
                if not hasattr(llm_client, 'model_fallbacks'):
                    self.results.append(DiagnosticResult(
                        "llm_integration", 
                        Status.WARNING,
                        "LLM client doesn't have model fallback mechanism", 
                        solution="Implement fallback mechanism in the LLM client",
                        user_message="If your preferred AI model is unavailable, the system will fail instead of using an alternative model."
                    ))
                
                # Check for error handling in interaction endpoint
                try:
                    from core.orchestrator.src.api.endpoints.interaction import interact
                    
                    # Use introspection to check if the function has proper error handling
                    import inspect
                    source = inspect.getsource(interact)
                    
                    # Look for common error handling patterns
                    has_llm_try_catch = "try:" in source and "llm_client.generate_response" in source
                    
                    if not has_llm_try_catch:
                        self.results.append(DiagnosticResult(
                            "llm_integration", 
                            Status.WARNING,
                            "Interaction endpoint may lack proper LLM error handling", 
                            solution="Add try/except blocks around LLM calls in interaction.py",
                            user_message="The system doesn't properly handle errors when communicating with AI models, leading to poor error messages."
                        ))
                        
                    # Check for hardcoded model
                    if "model=\"gpt-4\"" in source or "model='gpt-4'" in source:
                        self.results.append(DiagnosticResult(
                            "llm_integration", 
                            Status.WARNING,
                            "Interaction endpoint has hardcoded model (gpt-4)", 
                            solution="Make the model configurable or add fallback logic",
                            user_message="The system is hardcoded to use a specific AI model (GPT-4) and may fail if that model is unavailable."
                        ))
                except Exception:
                    # Not critical, just skip this check if it fails
                    pass
                    
            except Exception as e:
                import traceback
                self.results.append(DiagnosticResult(
                    "llm_integration", 
                    Status.ERROR,
                    f"LLM client initialization failed: {e}", 
                    {"error": str(e), "traceback": traceback.format_exc()},
                    "Check the LLM client implementation and API credentials",
                    "The system failed to initialize the AI model connection, which will prevent any responses."
                ))
                
        except Exception as e:
            import traceback
            self.results.append(DiagnosticResult(
                "llm_integration", 
                Status.ERROR,
                f"Failed to diagnose LLM integration: {e}", 
                {"error": str(e), "traceback": traceback.format_exc()},
                "Check the logs for detailed error information",
                "A critical error occurred when checking the AI model integration."
            ))
    
    async def simulate_user_flows(self) -> None:
        """
        Simulate actual user flows to detect integration issues.
        
        This tests the full interaction path from request to response,
        checking for issues that might only appear during actual usage.
        """
        logger.info("Simulating user flows...")
        
        # In a real system, we'd test the actual API endpoints here
        # For now, we'll just add a placeholder result
        self.results.append(DiagnosticResult(
            "user_flows", 
            Status.INFO,
            "User flow simulation not implemented in diagnostic script", 
            solution="For complete testing, manually test the full interaction flow",
            user_message="For a thorough check, try having a few conversations with different personalities to verify everything works."
        ))


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Patrick's Orchestrator Diagnostic Tool")
    parser.add_argument("--env", default=".env", help="Path to .env file")
    parser.add_argument("--output", help="Path to save results as JSON file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print(f"{Colors.BOLD}Patrick's Orchestrator Diagnostic Tool{Colors.ENDC}")
    print(f"{Colors.CYAN}Running diagnostics...{Colors.ENDC}")
    
    # Run diagnostics
    diagnostic = PatrickDiagnostic(env_file=args.env)
    results = await diagnostic.run_all_checks()
    
    # Print results
    print(f"\n{Colors.BOLD}Diagnostic Results:{Colors.ENDC}")
    
    # Group by component and status
    components = {}
    for result in results:
        if result.component not in components:
            components[result.component] = []
        components[result.component].append(result)
    
    for component, component_results in components.items():
        print(f"\n{Colors.BOLD}[{component.upper()}]{Colors.ENDC}")
        for result in component_results:
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
    # Make script executable
    import os
    if os.name != "nt":  # Not Windows
        import stat
        script_path = Path(__file__)
        st = os.stat(script_path)
        os.chmod(script_path, st.st_mode | stat.S_IEXEC)
    
    sys.exit(asyncio.run(main()))
