"""
Phidata Tool Integration Test Script

This script demonstrates how to use the Orchestra tools with Phidata integration.
It provides examples of:
1. Creating and registering tools
2. Converting Orchestra tools to Phidata tools
3. Using the tools with a Phidata agent (if installed)
"""

import logging
import os
import sys
from typing import List

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Import Orchestra tools
from packages.tools.src.base import OrchestraTool, get_registry
from packages.tools.src.web_browser import WebBrowserTool
from packages.tools.src.salesforce import SalesforceTool

# Check if Phidata is available
try:
    import phi
    from phi.assistant import Assistant
    from phi.tools import Tool as PhidataTool
    PHIDATA_AVAILABLE = True
except ImportError:
    logger.warning("Phidata not installed. Some features will be disabled.")
    PHIDATA_AVAILABLE = False

def register_tools():
    """
    Register tool classes with the tool registry.
    """
    registry = get_registry()
    
    # Register built-in tools
    registry.register_tool_class("web_browser", WebBrowserTool)
    registry.register_tool_class("salesforce", SalesforceTool)
    
    logger.info("Registered tools with the registry")
    return registry

def create_tool_instances(registry):
    """
    Create tool instances from the registry.
    
    Args:
        registry: Tool registry instance
        
    Returns:
        List of created tool instances
    """
    tools = []
    
    # Create web browser tool
    web_browser = registry.create_tool(
        tool_id="browser1",
        tool_config={
            "type": "web_browser",
            "params": {
                "timeout": 15,
                "max_content_length": 8000
            }
        }
    )
    if web_browser:
        tools.append(web_browser)
        
    # Create Salesforce tool
    # Note: This would normally use real credentials
    salesforce = registry.create_tool(
        tool_id="salesforce1",
        tool_config={
            "type": "salesforce",
            "params": {
                "username": os.environ.get("SALESFORCE_USERNAME", "demo@example.com"),
                "password": os.environ.get("SALESFORCE_PASSWORD", "demo_password"),
                "security_token": os.environ.get("SALESFORCE_SECURITY_TOKEN", "demo_token")
            }
        }
    )
    if salesforce:
        tools.append(salesforce)
    
    logger.info(f"Created {len(tools)} tool instances")
    return tools

def convert_to_phidata_tools(tools: List[OrchestraTool]):
    """
    Convert Orchestra tools to Phidata-compatible tools.
    
    Args:
        tools: List of Orchestra tool instances
        
    Returns:
        List of Phidata-compatible tools
    """
    if not PHIDATA_AVAILABLE:
        logger.warning("Phidata not available, skipping conversion")
        return []
    
    phidata_tools = []
    for tool in tools:
        phidata_tool = tool.to_phidata_tool()
        if phidata_tool:
            phidata_tools.append(phidata_tool)
    
    logger.info(f"Converted {len(phidata_tools)} tools to Phidata format")
    return phidata_tools

def run_phidata_agent(phidata_tools):
    """
    Run a Phidata agent with the converted tools.
    
    Args:
        phidata_tools: List of Phidata-compatible tools
    """
    if not PHIDATA_AVAILABLE:
        logger.warning("Phidata not available, skipping agent run")
        return
    
    try:
        # Create a Phidata assistant
        agent = Assistant(
            name="OrchestraTest",
            tools=phidata_tools,
            markdown=True,
            show_tool_calls=True
        )
        
        # Run the agent with a test prompt
        logger.info("Running Phidata agent with Orchestra tools...")
        response_gen = agent.run(
            "Search for information about Phidata and Orchestra integration"
        )
        
        # Handle response as a generator or regular object
        if hasattr(response_gen, '__next__') or hasattr(response_gen, '__iter__'):
            # It's a generator, process it
            logger.info("Processing generator response...")
            try:
                # Get the first element (or the complete response if it's not streaming)
                response_content = ""
                for chunk in response_gen:
                    if isinstance(chunk, str):
                        response_content += chunk
                    elif hasattr(chunk, 'content'):
                        response_content += chunk.content
                    elif isinstance(chunk, dict) and 'content' in chunk:
                        response_content += chunk['content']
                
                # Print the response
                print("\n----- AGENT RESPONSE -----")
                print(response_content)
                print("--------------------------\n")
            except Exception as e:
                logger.error(f"Error processing response generator: {e}")
        else:
            # It's a regular object with content attribute
            print("\n----- AGENT RESPONSE -----")
            if hasattr(response_gen, 'content'):
                print(response_gen.content)
            elif isinstance(response_gen, dict) and 'content' in response_gen:
                print(response_gen['content'])
            else:
                print(str(response_gen))
            print("--------------------------\n")
        
    except Exception as e:
        logger.error(f"Error running Phidata agent: {e}")

def test_standalone_tools():
    """
    Test tools directly without Phidata integration.
    """
    logger.info("Testing tools directly...")
    
    # Create a web browser tool
    browser = WebBrowserTool(timeout=10)
    
    # Use the tool to perform a search
    result = browser.run(action="search", query="Phidata and Orchestra integration")
    
    # Print the results
    print("\n----- WEB BROWSER TOOL RESULT -----")
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Search results for '{result.get('title', '')}'")
        for i, item in enumerate(result.get("results", [])[:3]):
            print(f"{i+1}. {item.get('title', 'No title')}: {item.get('url', 'No URL')}")
    print("----------------------------------\n")

def main():
    """
    Main function to demonstrate the tool integration.
    """
    print("\n=== Orchestra Tools with Phidata Integration Demo ===\n")
    
    # Register tools
    registry = register_tools()
    
    # Create tool instances
    tools = create_tool_instances(registry)
    
    # Test tools directly
    test_standalone_tools()
    
    # Convert to Phidata tools
    phidata_tools = convert_to_phidata_tools(tools)
    
    # Run Phidata agent (if available)
    if PHIDATA_AVAILABLE:
        run_phidata_agent(phidata_tools)
    else:
        print("\nTo run with a Phidata agent, install Phidata:")
        print("pip install phidata")
    
    print("\n=== Demo Complete ===\n")

if __name__ == "__main__":
    main()
