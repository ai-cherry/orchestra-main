#!/usr/bin/env python
"""
Test script for verifying Phidata Agent UI integration.

This script tests the enhanced Phidata Agent UI integration by:
1. Making requests to the /phidata/chat endpoint
2. Verifying markdown formatting
3. Testing structured output formatting
4. Checking session persistence

Usage:
  python tools/test_phidata_ui_integration.py --api-url http://localhost:8000
"""

import argparse
import json
import logging
import os
import requests
import sys
import uuid
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_regular_markdown_response(api_url: str, agent_id: Optional[str] = None) -> bool:
    """
    Test a regular response with markdown formatting.
    
    Args:
        api_url: URL of the API endpoint
        agent_id: Optional agent ID to use
        
    Returns:
        True if test passed, False otherwise
    """
    logger.info("Testing regular markdown response...")
    
    # Generate a unique session ID for this test
    session_id = str(uuid.uuid4())
    user_id = "test_user"
    
    # Create request payload
    payload = {
        "message": "Please format your response with markdown. Include a code block, list, and table.",
        "session_id": session_id,
        "user_id": user_id
    }
    
    if agent_id:
        payload["agent_id"] = agent_id
    
    # Send request
    try:
        response = requests.post(f"{api_url}/phidata/chat", json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        # Check response structure
        if "response_content" not in data:
            logger.error("Missing response_content in API response")
            return False
        
        content = data["response_content"]
        
        # Check for markdown elements
        markdown_elements = [
            "```", # Code block
            "-", # List item
            "|", # Table
            "#" # Heading
        ]
        
        missing_elements = [elem for elem in markdown_elements if elem not in content]
        
        if missing_elements:
            logger.warning(f"Response is missing markdown elements: {missing_elements}")
            logger.info(f"Response content: {content[:200]}...")
            return False
        
        logger.info("Markdown response test passed!")
        return True
        
    except Exception as e:
        logger.error(f"Error testing markdown response: {e}")
        return False


def test_structured_output_formatting(api_url: str, agent_id: Optional[str] = None) -> bool:
    """
    Test structured output formatting as markdown.
    
    Args:
        api_url: URL of the API endpoint
        agent_id: Optional agent ID to use (should be a structured output agent)
        
    Returns:
        True if test passed, False otherwise
    """
    logger.info("Testing structured output formatting...")
    
    # Generate a unique session ID for this test
    session_id = str(uuid.uuid4())
    user_id = "test_user"
    
    # Create request payload - this should trigger a structured response
    payload = {
        "message": "Create a movie script about a detective solving a mystery",
        "session_id": session_id,
        "user_id": user_id
    }
    
    if agent_id:
        payload["agent_id"] = agent_id
    else:
        logger.warning("No agent_id provided for structured output test, using default agent")
    
    # Send request
    try:
        response = requests.post(f"{api_url}/phidata/chat", json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        # Check response structure
        if "response_content" not in data:
            logger.error("Missing response_content in API response")
            return False
        
        content = data["response_content"]
        
        # Check if it contains structured content formatted as markdown
        # For a movie script, we'd expect headings for scenes
        if "# " not in content and "## Scene" not in content:
            logger.warning("Response does not appear to be a formatted structured output")
            logger.info(f"Response content: {content[:200]}...")
            return False
        
        logger.info("Structured output formatting test passed!")
        return True
        
    except Exception as e:
        logger.error(f"Error testing structured output formatting: {e}")
        return False


def test_session_persistence(api_url: str, agent_id: Optional[str] = None) -> bool:
    """
    Test session persistence across multiple requests.
    
    Args:
        api_url: URL of the API endpoint
        agent_id: Optional agent ID to use
        
    Returns:
        True if test passed, False otherwise
    """
    logger.info("Testing session persistence...")
    
    # Generate a unique session ID for this test
    session_id = str(uuid.uuid4())
    user_id = "test_user"
    
    # First message
    payload1 = {
        "message": "My name is Alice",
        "session_id": session_id,
        "user_id": user_id
    }
    
    if agent_id:
        payload1["agent_id"] = agent_id
    
    # Second message that references the first
    payload2 = {
        "message": "What's my name?",
        "session_id": session_id,
        "user_id": user_id
    }
    
    if agent_id:
        payload2["agent_id"] = agent_id
    
    try:
        # Send first message
        response1 = requests.post(f"{api_url}/phidata/chat", json=payload1)
        response1.raise_for_status()
        
        # Send second message
        response2 = requests.post(f"{api_url}/phidata/chat", json=payload2)
        response2.raise_for_status()
        
        data = response2.json()
        
        # Check if the response contains the name from the first message
        if "Alice" not in data["response_content"]:
            logger.warning("Session persistence test failed - agent doesn't remember previous message")
            logger.info(f"Response content: {data['response_content'][:200]}...")
            return False
        
        logger.info("Session persistence test passed!")
        return True
        
    except Exception as e:
        logger.error(f"Error testing session persistence: {e}")
        return False


def test_tool_call_visibility(api_url: str, dev_agent_id: str, prod_agent_id: str) -> bool:
    """
    Test tool call visibility settings for dev and prod agents.
    
    Args:
        api_url: URL of the API endpoint
        dev_agent_id: ID of a development agent (with visible tool calls)
        prod_agent_id: ID of a production agent (with hidden tool calls)
        
    Returns:
        True if test passed, False otherwise
    """
    logger.info("Testing tool call visibility settings...")
    
    # Generate unique session IDs
    dev_session_id = str(uuid.uuid4())
    prod_session_id = str(uuid.uuid4())
    user_id = "test_user"
    
    # Create payloads that should trigger tool use
    dev_payload = {
        "message": "Search the web for recent news about AI",
        "session_id": dev_session_id,
        "user_id": user_id,
        "agent_id": dev_agent_id
    }
    
    prod_payload = {
        "message": "Search the web for recent news about AI",
        "session_id": prod_session_id,
        "user_id": user_id,
        "agent_id": prod_agent_id
    }
    
    try:
        # Test dev agent (should have tool_calls in response)
        dev_response = requests.post(f"{api_url}/phidata/chat", json=dev_payload)
        dev_response.raise_for_status()
        dev_data = dev_response.json()
        
        # Test prod agent (should NOT have tool_calls in response)
        prod_response = requests.post(f"{api_url}/phidata/chat", json=prod_payload)
        prod_response.raise_for_status()
        prod_data = prod_response.json()
        
        # Check if dev agent has tool_calls
        if "tool_calls" not in dev_data or not dev_data["tool_calls"]:
            logger.warning("Dev agent doesn't have tool_calls in response")
            return False
        
        # Check if prod agent has no tool_calls
        if "tool_calls" in prod_data and prod_data["tool_calls"]:
            logger.warning("Prod agent has tool_calls in response (should be hidden)")
            return False
        
        logger.info("Tool call visibility test passed!")
        return True
        
    except Exception as e:
        logger.error(f"Error testing tool call visibility: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Test Phidata Agent UI integration"
    )
    parser.add_argument(
        "--api-url", 
        required=True,
        help="URL of the API endpoint (e.g., http://localhost:8000)"
    )
    parser.add_argument(
        "--dev-agent-id",
        help="ID of a development agent with visible tool calls"
    )
    parser.add_argument(
        "--prod-agent-id",
        help="ID of a production agent with hidden tool calls"
    )
    parser.add_argument(
        "--structured-agent-id",
        help="ID of an agent that returns structured output"
    )
    
    args = parser.parse_args()
    
    # Run tests
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Regular markdown response
    if test_regular_markdown_response(args.api_url, args.dev_agent_id):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 2: Structured output formatting
    if test_structured_output_formatting(args.api_url, args.structured_agent_id):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 3: Session persistence
    if test_session_persistence(args.api_url, args.dev_agent_id):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 4: Tool call visibility (if both agent IDs provided)
    if args.dev_agent_id and args.prod_agent_id:
        if test_tool_call_visibility(args.api_url, args.dev_agent_id, args.prod_agent_id):
            tests_passed += 1
        else:
            tests_failed += 1
    else:
        logger.warning("Skipping tool call visibility test (requires both dev and prod agent IDs)")
    
    # Print summary
    logger.info(f"Tests completed: {tests_passed} passed, {tests_failed} failed")
    
    if tests_failed > 0:
        logger.error("Some tests failed!")
        sys.exit(1)
    else:
        logger.info("All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
