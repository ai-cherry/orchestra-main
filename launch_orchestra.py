#!/usr/bin/env python3
"""
AI Orchestra Agent Orchestration System Launcher

This script launches the AI Orchestra agent orchestration system, including the API server.
It handles initialization of the gateway adapter, agent orchestration, and all dependencies.
"""

import os
import sys
import asyncio
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("orchestra-launcher")

# Ensure the shared package is in the Python path
sys.path.insert(0, str(Path(__file__).parent))


async def launch_api_server(port: int = 8000, reload: bool = False):
    """Launch the FastAPI server."""
    try:
        import uvicorn
        from api import app
        
        logger.info(f"Starting AI Orchestra API server on port {port}")
        
        config = uvicorn.Config(
            "api:app",
            host="0.0.0.0",
            port=port,
            reload=reload,
            log_level="info",
        )
        server = uvicorn.Server(config)
        await server.serve()
    except ImportError as e:
        logger.error(f"Required package not found: {e}")
        logger.info("Please install required packages: pip install fastapi uvicorn")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start API server: {e}")
        sys.exit(1)


async def validate_environment():
    """Validate that the environment is properly configured."""
    # Check for required environment variables
    required_vars = ["PORTKEY_API_KEY"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.warning(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.info("For optimal performance, set the following environment variables:")
        
        for var in missing_vars:
            logger.info(f"  - {var}")
        
        # Continue with default configurations, don't exit
    
    # Check for optional but recommended environment variables
    recommended_vars = [
        "PORTKEY_VIRTUAL_KEY_OPENAI",
        "PORTKEY_VIRTUAL_KEY_ANTHROPIC",
        "PORTKEY_VIRTUAL_KEY_GEMINI",
    ]
    missing_recommended = [var for var in recommended_vars if not os.environ.get(var)]
    
    if missing_recommended:
        logger.warning(f"Missing recommended environment variables: {', '.join(missing_recommended)}")
    
    # Check for gateway config
    config_path = os.environ.get(
        "LLM_GATEWAY_CONFIG_PATH", 
        str(Path(__file__).parent / "config" / "llm_gateway_config.yaml")
    )
    
    if not Path(config_path).exists():
        logger.warning(f"Gateway configuration file not found at {config_path}")
        logger.info("Will use default configuration")
    
    return True


async def init_orchestrator():
    """Initialize the agent orchestrator directly for testing."""
    try:
        from packages.shared.src.agent_orchestration import AgentOrchestrator
        
        logger.info("Initializing agent orchestrator for testing")
        
        orchestrator = AgentOrchestrator()
        success = await orchestrator.initialize()
        
        if not success:
            logger.error("Failed to initialize orchestrator")
            sys.exit(1)
        
        return orchestrator
    except ImportError as e:
        logger.error(f"Required package not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
        sys.exit(1)


async def test_message(orchestrator, message: str):
    """Test the orchestrator with a message."""
    logger.info(f"Testing orchestrator with message: {message}")
    
    response = await orchestrator.process_user_message(
        user_id="test_user",
        message=message,
    )
    
    logger.info(f"Domain: {response.get('domain', 'unknown')}")
    logger.info(f"Response: {response.get('message', '')}")
    
    return response


async def main():
    """Main function to launch the system."""
    parser = argparse.ArgumentParser(description="AI Orchestra Agent Orchestration System Launcher")
    
    # Add command-line arguments
    parser.add_argument(
        "--port", type=int, default=8000, 
        help="Port to run the API server on"
    )
    parser.add_argument(
        "--reload", action="store_true", 
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--test", action="store_true", 
        help="Run in test mode with a simple message"
    )
    parser.add_argument(
        "--test-message", type=str, 
        default="What are the latest sales trends in our CRM data?",
        help="Test message to send (if --test is used)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Validate environment
    if not await validate_environment():
        sys.exit(1)
    
    # Run in test mode if requested
    if args.test:
        orchestrator = await init_orchestrator()
        await test_message(orchestrator, args.test_message)
        return
    
    # Launch API server
    await launch_api_server(args.port, args.reload)


if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())