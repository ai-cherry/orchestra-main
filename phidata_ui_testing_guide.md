# Phidata Agent UI Testing Guide

This guide provides instructions for testing the Phidata Agent UI after deployment to verify proper functionality and end-to-end interactions with the backend API.

## Deployment

Before testing, ensure the Phidata Agent UI has been deployed using the `deploy_phidata_ui.sh` script:

```bash
./deploy_phidata_ui.sh
```

This script will:
1. Create a Docker container with Terraform
2. Initialize Terraform
3. Apply the configuration for the Phidata Agent UI service
4. Output the service URL for testing

## Accessing the UI

Once deployed, access the Phidata Agent UI using the URL provided by the deployment script. This URL should be in the format:

```
https://phidata-agent-ui-dev-[hash].a.run.app
```

## Test Scenarios

### 1. Basic Connectivity Test

**Objective**: Verify the UI loads and connects to the backend API.

**Steps**:
- Access the UI URL in a browser
- Confirm the UI loads without errors
- Check browser console for any connection errors
- Verify the app title and description match the configured values

### 2. Agent Selection Test

**Objective**: Verify that multiple agents can be selected and switched between.

**Steps**:
- Look for an agent selection dropdown
- Select different agents from the dropdown
- Verify the agent information updates to reflect the selected agent
- Confirm any agent-specific instructions or capabilities are displayed

### 3. Basic Chat Interaction Test

**Objective**: Test basic message submission and response.

**Steps**:
- Send a simple greeting message (e.g., "Hello")
- Verify the message appears in the chat interface
- Confirm a response is received within a reasonable timeframe
- Check that the response is relevant to the message sent

### 4. Web Search Tool Test

**Objective**: Verify the DuckDuckGo search integration.

**Steps**:
- Send a message that requires web search (e.g., "What is the latest news about AI regulation?")
- Verify the agent uses the DuckDuckGo tool to search for information
- Check that search results are incorporated into the response
- Confirm sources are properly attributed in the response

### 5. Calculator Tool Test

**Objective**: Test the calculator functionality.

**Steps**:
- Send a message with a mathematical calculation (e.g., "Calculate 15% of 2350")
- Verify the agent uses the calculator tool
- Check that the calculation result is correct
- Confirm the steps are shown in the response

### 6. Wikipedia Tool Test (if configured)

**Objective**: Verify the Wikipedia integration.

**Steps**:
- Send a message requesting encyclopedia information (e.g., "Tell me about quantum computing")
- Verify the agent uses the Wikipedia tool to fetch information
- Check that the information is relevant and properly summarized
- Confirm sources are properly attributed in the response

### 7. Multiple Tool Interaction Test

**Objective**: Test scenarios requiring multiple tools.

**Steps**:
- Send a message that would require multiple tools (e.g., "Compare the population of New York and Tokyo, and calculate the percentage difference")
- Verify the agent correctly identifies and uses multiple tools
- Check that the response integrates information from all tools used
- Confirm the final response provides a coherent answer

### 8. Session Persistence Test

**Objective**: Verify conversation history persistence.

**Steps**:
- Have a multi-message conversation with the agent
- Refresh the browser
- Verify the conversation history is preserved
- Confirm the agent maintains context from previous messages

## Troubleshooting Common Issues

### UI Connection Issues

If the UI fails to load or connect to the backend API:
- Verify the `PHIDATA_API_URL` environment variable is correctly set in the Cloud Run configuration
- Check that the API service is running and accessible
- Confirm the correct authentication settings are configured

### Tool Integration Issues

If specific tools are not working:
- Verify the tool is properly registered with the agent
- Check that any required API keys are correctly configured
- Review logs for any authentication or connection errors

### Agent Response Issues

If agent responses are slow or unexpected:
- Check the backend API logs for any errors
- Verify that the LLM API keys are valid and have sufficient quota
- Confirm the agent configuration with the correct tools and instructions

## Reporting Issues

Document any issues encountered during testing, including:
- Screenshot of the issue
- Steps to reproduce
- Expected vs. actual behavior
- Browser console logs (if applicable)
- Network request details (if visible)

## Next Steps

After successful testing, consider:
1. Adding additional agents with specialized capabilities
2. Configuring authentication for production use
3. Optimizing the UI for specific use cases
4. Setting up monitoring and alerting for the services
