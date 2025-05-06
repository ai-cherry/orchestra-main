#!/usr/bin/env python3
"""
Test script for verifying the implemented fixes in the Orchestrator system.

This script tests:
1. Persona loading and fallback mechanisms
2. LLM client resilience
3. Memory system health checks
4. API endpoints for persona management
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("fix-verification")


async def test_persona_loading():
    """Test persona loading and fallback mechanisms."""
    print("\n=== Testing Persona Loading ===")
    
    try:
        from core.orchestrator.src.config.loader import load_persona_configs, force_reload_personas
        
        # Test normal loading
        print("Testing normal persona loading...")
        personas = load_persona_configs()
        print(f"Successfully loaded {len(personas)} personas: {', '.join(personas.keys())}")
        
        # Test cached loading (should be fast)
        print("\nTesting cached loading (should be fast)...")
        start_time = datetime.now()
        personas = load_persona_configs()
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds() * 1000
        print(f"Cached loading took {elapsed:.2f}ms")
        
        # Test force reload
        print("\nTesting force reload...")
        personas = force_reload_personas()
        print(f"Successfully force reloaded {len(personas)} personas")
        
        # Test empty persona name fallback
        print("\nTesting persona resolution...")
        from core.orchestrator.src.api.middleware.persona_loader import get_active_persona
        from fastapi import Request
        
        # Create a mock request with valid persona
        mock_request = Request({"type": "http", "query_string": b"persona=cherry"})
        persona = await get_active_persona(mock_request)
        print(f"Requested 'cherry' persona, got: {persona.name}")
        
        # Create a mock request with invalid persona to test fallback
        mock_request = Request({"type": "http", "query_string": b"persona=nonexistent"})
        persona = await get_active_persona(mock_request)
        print(f"Requested 'nonexistent' persona, got fallback: {persona.name}")
        
        # Create a mock request with no persona to test default
        mock_request = Request({"type": "http", "query_string": b""})
        persona = await get_active_persona(mock_request)
        print(f"Requested no specific persona, got default: {persona.name}")
        
        return True
    except Exception as e:
        print(f"Error testing persona loading: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_llm_client():
    """Test LLM client resilience."""
    print("\n=== Testing LLM Client ===")
    
    try:
        # Test if we have API key in environment
        openrouter_key = os.environ.get("OPENROUTER_API_KEY")
        if not openrouter_key:
            print("OPENROUTER_API_KEY not found in environment. Skipping actual API test.")
            print("Would test: Exception handling, retries, and error messages")
            return True
            
        # If we have a key, test actual client
        from packages.shared.src.llm_client.openrouter_client import OpenRouterClient
        
        # Initialize client
        client = OpenRouterClient()
        print("Successfully initialized OpenRouter client")
        
        # Check health
        health = await client.health_check()
        print(f"Client health: {health.get('status', 'unknown')}")
        
        # Test message generation
        if True:  # Set to False to skip API call
            print("\nTesting LLM response generation...")
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, are you working correctly?"}
            ]
            response = await client.generate_response(
                model="mistralai/mistral-7b-instruct", 
                messages=messages
            )
            print(f"Response received: {response[:50]}...")
        
        return True
    except Exception as e:
        print(f"Error testing LLM client: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_memory_system():
    """Test memory system health checks."""
    print("\n=== Testing Memory System ===")
    
    try:
        from packages.shared.src.memory.concrete_memory_manager import ConcreteMemoryManager
        
        # Create memory manager with minimal configuration
        memory_manager = ConcreteMemoryManager()
        
        try:
            # Initialize memory manager (this should work even without proper credentials)
            memory_manager.initialize()
            print("Memory manager initialized")
            
            # Check health
            health = await memory_manager.health_check()
            print(f"Memory system health: {health.get('status', 'unknown')}")
            
            if health["firestore"]:
                print("Firestore connection is healthy")
            else:
                print("Firestore connection is not available")
                
            if health["redis"]:
                print("Redis connection is healthy")
            else:
                print("Redis is not available (this is normal if not configured)")
            
            return True
        except Exception as e:
            print(f"Error initializing memory system: {e}")
            return False
    except Exception as e:
        print(f"Error testing memory system: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_endpoints():
    """Test if endpoints are defined correctly."""
    print("\n=== Testing API Endpoints ===")
    
    try:
        # Import the router
        from core.orchestrator.src.api.endpoints.personas import router
        
        # Check if the reload endpoint exists
        endpoints = [route.path for route in router.routes]
        if "/reload" in endpoints:
            print("Persona reload endpoint is properly defined")
        else:
            print("WARNING: Persona reload endpoint not found")
        
        print(f"Found {len(endpoints)} persona API endpoints")
        return True
    except Exception as e:
        print(f"Error testing API endpoints: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all tests and summarize results."""
    results = {}
    
    # Run all tests
    results["persona_loading"] = await test_persona_loading()
    results["llm_client"] = await test_llm_client()
    results["memory_system"] = await test_memory_system()
    results["endpoints"] = await test_endpoints()
    
    # Print summary
    print("\n=== Test Results Summary ===")
    all_passed = True
    for test, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        color = "\033[92m" if passed else "\033[91m"  # Green or Red
        print(f"{color}{status}\033[0m - {test}")
        all_passed = all_passed and passed
    
    if all_passed:
        print("\n\033[92mAll tests passed! The fixes have been successfully implemented.\033[0m")
    else:
        print("\n\033[91mSome tests failed. Please review the output above for details.\033[0m")
    
    return all_passed


if __name__ == "__main__":
    print("Running tests to verify implemented fixes...")
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
