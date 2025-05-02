"""
Example script demonstrating how to deploy and monitor a Vertex AI Agent using Vertex AI Agent Builder.

This script assumes:
1. The Google Cloud SDK is configured with the correct project (agi-baby-cherry).
2. Authentication is set up with the service account vertex-agent@agi-baby-cherry.iam.gserviceaccount.com.
3. Necessary permissions are granted for agent creation and deployment.

Instructions:
1. Run the setup script `scripts/setup_vertex_auth.sh` to ensure proper authentication.
2. Execute this script to define, deploy, and monitor a sample agent.
3. Use Cloud Monitoring or IDE plugins like Cloud Code to check deployment status.
"""

from google.cloud import ai_agent_builder
import time

def create_and_deploy_agent():
    """
    Create and deploy a sample agent using Vertex AI Agent Builder.
    
    Returns:
        str: Agent ID of the deployed agent.
    """
    print("Initializing Vertex AI Agent Builder...")
    # Initialize with project and location
    ai_agent_builder.init(project="agi-baby-cherry", location="us-central1")
    
    # Define a sample agent
    agent_config = {
        "display_name": "Sample-Orchestra-Agent",
        "base_model": "gemini-2.5-pro",
        "description": "A sample agent for orchestra-main project automation.",
        "tools": ["google-maps", "supply-chain-db"],
        "memory_config": {
            "short_term": "redis://agi-baby-cherry-redis",
            "long_term": "firestore://projects/agi-baby-cherry/databases/agent-memories"
        },
        "context_window": 1000000  # 1M token context window
    }
    
    print("Creating agent with configuration:", agent_config)
    agent = ai_agent_builder.Agent(**agent_config)
    
    # Register protocols for inter-agent communication
    agent.register_protocols(["mcp", "a2a"])
    
    # Deploy the agent
    print("Deploying agent to Vertex AI...")
    agent_id = agent.deploy()
    print(f"Agent deployed successfully with ID: {agent_id}")
    
    return agent_id

def monitor_agent(agent_id):
    """
    Monitor the status and performance of a deployed agent.
    
    Args:
        agent_id (str): ID of the deployed agent to monitor.
    """
    print(f"Monitoring agent {agent_id}...")
    while True:
        status = ai_agent_builder.get_agent_status(agent_id)
        print(f"Agent Status: {status['state']}, Health: {status['health']}, Uptime: {status['uptime']}")
        if status['state'] == "RUNNING":
            print("Agent is fully operational.")
            break
        elif status['state'] in ["FAILED", "STOPPED"]:
            print("Agent deployment failed or stopped. Check logs for details.")
            break
        time.sleep(10)  # Check every 10 seconds

if __name__ == "__main__":
    try:
        agent_id = create_and_deploy_agent()
        monitor_agent(agent_id)
        print("Deployment and monitoring process completed. Use Cloud Monitoring for detailed metrics.")
    except Exception as e:
        print(f"Error during agent deployment or monitoring: {e}")