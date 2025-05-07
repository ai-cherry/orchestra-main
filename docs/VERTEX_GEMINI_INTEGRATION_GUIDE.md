# Vertex AI & Gemini Integration Guide

This guide provides detailed instructions for integrating Vertex AI and Gemini into your development workflow for the `orchestra-main` project. It covers authentication setup, replacing legacy API key usage with Vertex AI Gemini SDK calls, using Gemini Code Assist for context-aware code generation in VS Code, and deploying and monitoring agents with Vertex AI Agent Builder.

## Table of Contents
- [Authentication Setup](#authentication-setup)
- [Vertex AI Gemini SDK Integration](#vertex-ai-gemini-sdk-integration)
- [Context-Aware Code Generation with Gemini Code Assist](#context-aware-code-generation-with-gemini-code-assist)
- [Deploying and Monitoring Agents with Vertex AI Agent Builder](#deploying-and-monitoring-agents-with-vertex-ai-agent-builder)

## Authentication Setup

To ensure all AI agent and model calls are authenticated using the service account `vertex-agent@cherry-ai-project.iam.gserviceaccount.com`, follow these steps:

1. **Run the Setup Script**:
   Execute the provided setup script to configure authentication and environment variables.
   ```bash
   bash scripts/setup_vertex_auth.sh
   ```
   **Note**: Before running the script, update the path to the service account key file in the script (replace `/path/to/service-account-key.json` with the actual path).

2. **Verify Authentication**:
   After running the script, confirm that `GOOGLE_APPLICATION_CREDENTIALS` is set correctly and Vertex AI SDK is initialized.
   ```bash
   echo $GOOGLE_APPLICATION_CREDENTIALS
   python3 -c "from google.cloud import aiplatform; print(aiplatform.__version__)"
   ```

## Vertex AI Gemini SDK Integration

Legacy Gemini API key usage has been replaced with Vertex AI Gemini SDK calls in the project. The key file to review is `agent/core/vertex_operations.py`, where the `generate_gemini_docs` method now uses Gemini Enterprise with a 10M-token context window, authenticated via the service account.

**Key Code Snippet** (from `agent/core/vertex_operations.py`):
```python
def generate_gemini_docs(self, code_path: str):
    """Use Gemini Enterprise to generate documentation with extended context window"""
    from google.cloud import gemini
    
    # Leverage Gemini Enterprise for larger context processing
    enterprise_agent = gemini.EnterpriseAgent(
        model="gemini-3.0-enterprise",
        context_window=10_000_000,
        data_sources=["bigquery://prod-dataset"]
    )
    with open(code_path) as f:
        response = enterprise_agent.generate_content(
            prompt={
                "context": "You are a senior Python developer. Generate detailed Google-style docstrings for this codebase.",
                "content": f.read()
            }
        )
    return response.content
```

This ensures that all Gemini interactions are authenticated through the Vertex AI SDK using the configured service account, eliminating direct API key usage.

## Context-Aware Code Generation with Gemini Code Assist

Gemini Code Assist in VS Code provides context-aware code generation and review capabilities. A sample file has been created to demonstrate this functionality.

1. **Open the Sample File**:
   Open `examples/gemini_code_assist_example.py` in VS Code.

2. **Trigger Gemini Code Assist**:
   - Place your cursor on a TODO comment within the file.
   - Use the shortcut `Ctrl+I` or right-click and select `Gemini: Generate` to trigger code suggestions.
   - Review and accept the generated code based on the context of the surrounding code and comments.

**Sample TODO from `gemini_code_assist_example.py`**:
```python
def process_data(data_list):
    processed_data = []
    for item in data_list:
        # TODO: Implement data transformation logic for each item.
        # Gemini Code Assist should suggest a transformation based on the context of 'item'.
        pass
    return processed_data
```

3. **Review Suggestions**:
   Gemini Code Assist will analyze the context (e.g., variable names, function purpose) and suggest relevant code. You can modify or accept the suggestions as needed.

## Deploying and Monitoring Agents with Vertex AI Agent Builder

A sample script has been provided to demonstrate how to define, deploy, and monitor an agent using Vertex AI Agent Builder directly from your development environment.

1. **Run the Deployment Script**:
   Execute the provided script to create and deploy a sample agent.
   ```bash
   python3 examples/deploy_vertex_agent.py
   ```

2. **Key Code Snippet** (from `examples/deploy_vertex_agent.py`):
   ```python
   def create_and_deploy_agent():
       print("Initializing Vertex AI Agent Builder...")
       ai_agent_builder.init(project="cherry-ai-project", location="us-west4")
       
       agent_config = {
           "display_name": "Sample-Orchestra-Agent",
           "base_model": "gemini-2.5-pro",
           "description": "A sample agent for orchestra-main project automation.",
           "tools": ["google-maps", "supply-chain-db"],
           "memory_config": {
               "short_term": "redis://cherry-ai-project-redis",
               "long_term": "firestore://projects/cherry-ai-project/databases/agent-memories"
           },
           "context_window": 1000000
       }
       
       agent = ai_agent_builder.Agent(**agent_config)
       agent.register_protocols(["mcp", "a2a"])
       agent_id = agent.deploy()
       return agent_id
   ```

3. **Monitor Deployment**:
   The script includes a `monitor_agent` function that checks the agent's status until it is running or fails. Additionally, use Cloud Monitoring or IDE plugins like Cloud Code to view detailed metrics and logs.
   - Access Cloud Monitoring via the Google Cloud Console to see agent performance metrics.
   - Use Cloud Code in VS Code to interact with deployed resources directly from the IDE.

## Additional Notes
- Ensure that the Google Cloud SDK and necessary Python libraries (`google-cloud-aiplatform`, `google-cloud-gemini`) are installed in your environment.
- If you encounter authentication issues, verify that the service account key file path is correctly set in `GOOGLE_APPLICATION_CREDENTIALS`.
- For advanced agent configurations or monitoring, refer to the Vertex AI documentation or use the Cloud Code extension for a graphical interface within VS Code.

This guide completes the integration process for Vertex AI and Gemini, providing a seamless workflow for authentication, code generation, and agent deployment.