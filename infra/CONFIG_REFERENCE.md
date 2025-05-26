# Orchestra Configuration & Secret Reference

This document lists all required Pulumi-managed secrets and configuration keys for the AI Orchestra stack.
All sensitive values must be set via Pulumi ESC/config and are injected into Kubernetes as secrets or environment variables.

| Key Name                | Pulumi Config? | Secret? | Consumed By                  | Description / Notes                    |
|-------------------------|:--------------:|:-------:|------------------------------|----------------------------------------|
| OPENAI_API_KEY          |   Yes          |  Yes    | LiteLLM, SuperAGI, MCP       | OpenAI-compatible LLM API key          |
| ANTHROPIC_API_KEY       |   Yes          |  Yes    | LiteLLM, SuperAGI, MCP       | Anthropic Claude API key               |
| GOOGLE_API_KEY          |   Yes          |  Yes    | LiteLLM, SuperAGI, MCP       | Gemini API key                         |
| AZURE_OPENAI_API_KEY    |   Yes          |  Yes    | LiteLLM, SuperAGI, MCP       | Azure OpenAI API key                   |
| AZURE_OPENAI_API_BASE   |   Yes          |  No     | LiteLLM, SuperAGI            | Azure OpenAI API base URL              |
| MONGODB_URI             |   Yes          |  Yes    | SuperAGI, MCP, DB            | MongoDB connection URI                 |
| MONGODB_PASSWORD        |   Yes          |  Yes    | SuperAGI, MCP, DB            | MongoDB password                       |
| WEAVIATE_API_KEY        |   Yes          |  Yes    | SuperAGI, MCP, Vector DB     | Weaviate API key                       |
| DRAGONFLY_URL           |   Yes          |  No     | SuperAGI, MCP, DragonflyDB   | DragonflyDB connection string          |
| GCP_PROJECT_ID          |   Yes          |  No     | All components               | GCP project ID                         |
| GCP_REGION              |   Yes          |  No     | All components               | GCP region                             |
| LITELLM_API_KEY         |   Yes          |  Yes    | LiteLLM                      | LiteLLM admin API key                  |
| ...                     |   ...          |  ...    | ...                          | ...                                    |

**How to update:**
- Add new keys as you add new services or integrations.
- All secrets must be set via Pulumi ESC/config, never in `.env` or source code.

**See also:**
- [`infra/components/secret_helper.py`](infra/components/secret_helper.py) for secret injection logic.
- `.env` for non-sensitive defaults and environment variable documentation.
