# Business Intelligence Agents Integration Tests

This directory contains integration tests for the Orchestra Business Intelligence Agents and Team implementation using Phidata/Agno.

## Overview

The implementation includes:

1. **Business Intelligence Tools**: Located in `packages/tools/src/`

   - `gong.py`: Interface with Gong API for call transcripts and insights
   - `hubspot.py`: Manage HubSpot CRM contacts and deals
   - `netsuite.py`: Access inventory data from NetSuite
   - `slack.py`: Send messages and reports to Slack channels
   - `salesforce.py`: Query and update data in Salesforce CRM
   - `looker.py`: Run analytics queries and access Looker dashboards

2. **Agent Configurations**: Located in `config/agents.yaml`

   - Individual agent definitions for each tool
   - Team configuration that references individual agents as members

3. **Enhanced Team Support**:
   - `packages/agents/src/phidata/team_wrapper.py`: Handles agent references in team member configuration
   - `packages/agents/src/registry.py`: Updated to use the enhanced team wrapper

## Testing

### Unit Tests

The individual tools have unit tests that verify their functionality with mocked external services:

- `tests/packages/tools/test_gong_tool.py`
- `tests/packages/tools/test_hubspot_tool.py`
- etc.

### Integration Tests

Integration tests focus on the interaction between components:

- `test_phidata_team_agents.py`: Tests the orchestration of agents as team members
  - Verifies individual agent creation
  - Tests team member resolution from references
  - Checks execution flow with mocked responses

## Running the Tests

### Prerequisites

- Python 3.9+
- Poetry or pip for dependency management
- Access to required environment variables (or mocks)

### Setup

1. Install dependencies:

```bash
poetry install
# or
pip install -r requirements-dev.txt
```

2. Set up environment variables (or run with mocks):

```bash
source .env  # Or add to your environment
```

### Execute Tests

Run specific business intelligence agent integration tests:

```bash
pytest tests/integration/test_phidata_team_agents.py -v
```

Run all integration tests:

```bash
pytest tests/integration/ -v
```

## Development Notes

### Adding New Tools

1. Create a new tool module in `packages/tools/src/`
2. Implement both function-based (`@tool` decorator) and class-based (`OrchestraTool`) interfaces
3. Add appropriate agent configuration to `config/agents.yaml`
4. Update the team configuration to include the new agent

### Environment Variables

Required environment variables for tools:

- Gong: `GONG_API_KEY`, `GONG_API_BASE_URL`
- HubSpot: `HUBSPOT_API_KEY`
- NetSuite: `NETSUITE_ACCOUNT_ID`, `NETSUITE_CONSUMER_KEY`, etc.
- Salesforce: `SALESFORCE_USERNAME`, `SALESFORCE_PASSWORD`, etc.
- Looker: `LOOKER_API_URL`, `LOOKER_CLIENT_ID`, `LOOKER_CLIENT_SECRET`
- Slack: `SLACK_BOT_TOKEN`

For local development, these can be configured in a `.env` file, which will be loaded from the environment.

### Team Configuration

The team configuration in `config/agents.yaml` references individual agents by name. The system resolves these references using `PhidataTeamAgentWrapper` which handles instantiating the underlying agents.
