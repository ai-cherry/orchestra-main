# Secrets Configuration Guide

## Overview
This document outlines all secrets and environment variables required for the Orchestra AI project, including Portkey virtual keys and other service integrations.

## GitHub Secrets (Production) - Complete List

### AI/LLM Services
| Secret Name | Description | Last Updated | Status |
|------------|-------------|--------------|---------|
| `PORTKEY_API_KEY` | Main Portkey API key for virtual keys | 3 days ago | ✅ Documented |
| `ANTHROPIC_API_KEY` | Direct Anthropic API key | 3 days ago | Alternative to Portkey |
| `OPENAI_API_KEY` | Direct OpenAI API key | last month | Alternative to Portkey |
| `DEEPSEEK_API_KEY` | Direct DeepSeek API key | last month | Alternative to Portkey |
| `PERPLEXITY_API_KEY` | Direct Perplexity API key | 2 months ago | Alternative to Portkey |
| `MISTRAL_API_KEY` | Mistral AI API key | last month | New provider |
| `OPENROUTER_API_KEY` | OpenRouter API key | last month | Alternative to Portkey |
| `CODESTRAL_API_KEY` | Codestral API key | last month | Code generation |
| `CLAUDE_API_KEY` | Claude API (see ANTHROPIC_API_KEY) | - | Use ANTHROPIC_API_KEY |
| `LANGCHAIN_API_KEY` | LangChain API key | 3 days ago | LLM orchestration |
| `LANGSMITH_API_KEY` | LangSmith API key | 2 months ago | LLM monitoring |
| `HUGGINGFACE_API_TOKEN` | HuggingFace API token | 3 days ago | Open source models |

### Media & Voice Services
| Secret Name | Description | Last Updated | Status |
|------------|-------------|--------------|---------|
| `ELEVENLABS_API_KEY` | ElevenLabs voice synthesis | 2 hours ago | ✅ Primary voice |
| `RECRAFT_API_KEY` | Recraft API for image generation | 3 days ago | Alternative to DALL-E |
| `PEXELS_API_KEY` | Pexels image search | 2 months ago | Optional media |

### Database & Storage
| Secret Name | Description | Last Updated | Status |
|------------|-------------|--------------|---------|
| `DRAGONFLYDB_API_KEY` | DragonflyDB API key | 3 days ago | Redis alternative |
| `REDIS_API_ACCOUNTKEY` | Redis account key | 2 months ago | Cache layer |
| `REDIS_API_USERKEY` | Redis user key | 2 months ago | Cache auth |
| `REDIS_DATABASE_NAME` | Redis database name | last month | Database config |
| `REDIT_DATABASE_ENDPOINT` | Redis endpoint (typo?) | last month | Connection string |
| `PINECONE_API_KEY` | Pinecone vector DB | last month | Alternative to Weaviate |
| `PINECONE_HOST_URL` | Pinecone host URL | last month | Vector DB endpoint |

### Cloud Infrastructure
| Secret Name | Description | Last Updated | Status |
|------------|-------------|--------------|---------|
| `GCP_PROJECT_ID` | Google Cloud project ID | 2 weeks ago | Main cloud provider |
| `GCP_MASTER_SERVICE_JSON` | GCP service account JSON | 3 weeks ago | Authentication |
| `GCP_VERTEX_JSON` | Vertex AI credentials | 2 weeks ago | AI/ML services |
| `AWS_ACCESS_KEY_ID` | AWS access key | 2 months ago | Alternative cloud |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | 2 months ago | AWS auth |
| `AZURE_STORAGE_ACCOUNT` | Azure storage account | 2 months ago | Blob storage |
| `DIGITALOCEAN_TOKEN` | DigitalOcean API token | 2 days ago | Alternative hosting |

### DevOps & CI/CD
| Secret Name | Description | Last Updated | Status |
|------------|-------------|--------------|---------|
| `PULUMI_ACCESS_TOKEN` | Pulumi IaC token | 3 days ago | Infrastructure |
| `PULUMI_CONFIGURE_PASSPHRASE` | Pulumi passphrase | 3 days ago | Encryption |
| `PULUMI_CLOUD_TOKEN` | Pulumi Cloud token | - | Infrastructure as Code |
| `DOCKERHUB_USERNAME` | DockerHub username | 3 days ago | Container registry |
| `DOCKER_PERSONAL_ACCESS_TOKEN` | Docker PAT | 3 days ago | Registry auth |
| `GITHUB_TOKEN` | GitHub Actions token | - | Built-in |
| `GH_API_TOKEN` | GitHub API token | 2 months ago | API access |
| `GH_CLASSIC_PAT_TOKEN` | GitHub classic PAT | 3 weeks ago | Legacy access |
| `GH_FINE_GRAINED_TOKEN` | GitHub fine-grained PAT | 3 weeks ago | Scoped access |

### Integration Services
| Secret Name | Description | Last Updated | Status |
|------------|-------------|--------------|---------|
| `SLACK_BOT_TOKEN` | Slack bot token | 11 hours ago | Notifications |
| `SLACK_APP_TOKEN` | Slack app token | 11 hours ago | App management |
| `SLACK_CLIENT_ID` | Slack OAuth client ID | 12 hours ago | OAuth flow |
| `NOTION_API_KEY` | Notion integration | 3 days ago | Documentation |
| `PIPEDREAM_API_KEY` | Pipedream workflows | 3 weeks ago | Automation |
| `N8N_API_KEY` | n8n workflow automation | 3 weeks ago | Alternative automation |

### Search & Data Services
| Secret Name | Description | Last Updated | Status |
|------------|-------------|--------------|---------|
| `BRAVE_API_KEY` | Brave Search API | 2 months ago | Web search |
| `SERP_API_KEY` | SERP API for search results | 2 months ago | Search scraping |
| `TAVILY_API_KEY` | Tavily search API | 2 months ago | AI-powered search |
| `EXA_API_KEY` | Exa (formerly Metaphor) | 2 months ago | Semantic search |
| `APIFY_API_TOKEN` | Apify web scraping | 2 months ago | Data extraction |
| `PHANTOMBUSTER_API_KEY` | PhantomBuster automation | 3 days ago | Web automation |

### Business Tools
| Secret Name | Description | Last Updated | Status |
|------------|-------------|--------------|---------|
| `HUBSPOT_ACCESS_TOKEN` | HubSpot CRM | last month | Customer data |
| `SALESFORCE_ACCESS_TOKEN` | Salesforce CRM | last month | Enterprise CRM |
| `APOLLO_API_KEY` | Apollo.io API | last month | Sales intelligence |
| `GONG_ACCESS_KEY` | Gong.io access | 12 hours ago | Conversation insights |
| `LATTICE_API_KEY` | Lattice HR platform | last month | HR management |

### Portkey Virtual Keys Available
Based on your Portkey account setup, these virtual keys are available:

| Virtual Key Name | Provider | Key ID | Usage |
|-----------------|----------|---------|--------|
| `gemini-api-key-1ea5a2` | Google Gemini | AI*****gps | Gemini Pro models |
| `perplexity-api-015025` | Perplexity | pp*****6HS | Search-enhanced responses |
| `deepseek-api-ke-e7859b` | DeepSeek | sk*****bd0 | Code generation |
| `xai-api-key-a760a5` | X.AI (Grok) | xa*****0JL | Grok models |
| `openai-api-key-345cc9` | OpenAI | sk*****aoA | GPT-4, DALL-E 3 |
| `anthropic-api-k-6feca8` | Anthropic | sk*****AAA | Claude models |
| `together-ai-670469` | Together AI | tg*****WWo | Open source models |
| `openrouter-api-15df95` | OpenRouter | sk*****081 | Model routing |

## Recommended Configuration Strategy

### 1. Primary AI Services (via Portkey)
Use Portkey virtual keys for unified billing, monitoring, and fallback handling:
- OpenAI models → `openai-api-key-345cc9`
- Anthropic models → `anthropic-api-k-6feca8`
- Google models → `gemini-api-key-1ea5a2`
- Perplexity search → `perplexity-api-015025`

### 2. Direct API Keys (When Needed)
Use direct API keys for:
- Services not available through Portkey (ElevenLabs, specialized APIs, etc.)
- When you need provider-specific features
- Development/testing with specific providers

### 3. Environment-Specific Usage
```bash
# Production (use Portkey for cost control)
PORTKEY_API_KEY=${PORTKEY_API_KEY}
USE_PORTKEY=true

# Development (can use direct keys)
OPENAI_API_KEY=${OPENAI_API_KEY}
USE_PORTKEY=false
```

## Core Required Secrets for Orchestra AI

### Minimum Required (Production)
1. `PORTKEY_API_KEY` - For AI/LLM services
2. `DATABASE_URL` - PostgreSQL connection (construct from GCP credentials)
3. `WEAVIATE_URL` & `WEAVIATE_API_KEY` - Vector database
4. `JWT_SECRET` - Authentication
5. `ADMIN_API_KEY` - Admin UI access
6. `GCP_PROJECT_ID` & related - Cloud infrastructure

### Recommended Additions
1. `RESEMBLE_API_KEY` - Voice synthesis
2. `SLACK_BOT_TOKEN` - Notifications
3. `SENTRY_DSN` - Error tracking
4. `REDIS_API_*` - Caching layer

## Security Best Practices

1. **API Key Rotation Schedule**
   - High-risk keys (payment, auth): Monthly
   - AI service keys: Quarterly
   - Read-only keys: Bi-annually

2. **Access Control**
   - Use GitHub environment protection rules
   - Limit secret access by environment
   - Regular audit of secret usage

3. **Monitoring**
   - Set up alerts for unusual API usage
   - Monitor costs through Portkey dashboard
   - Track rate limits across services

## Adding New Secrets

When adding a new secret:
1. Add to GitHub Secrets
2. Update this documentation
3. Update `env.example`
4. Update deployment scripts
5. Test in staging environment
6. Document in team wiki

## Troubleshooting

### Common Issues

1. **Multiple API Keys for Same Service**
   - Prefer Portkey virtual keys over direct keys
   - Document which key is primary
   - Set up fallback logic

2. **Secret Not Found in Production**
   - Check GitHub Actions environment
   - Verify secret name matches exactly
   - Check deployment workflow permissions

3. **Rate Limiting**
   - Use Portkey for automatic rate limit handling
   - Implement exponential backoff
   - Monitor usage dashboards

## Support

For issues with:
- **Portkey virtual keys**: https://app.portkey.ai/virtual-keys
- **GitHub Secrets**: Contact repository admin
- **GCP secrets**: Use Secret Manager
- **Local development**: See DEVELOPMENT.md 

## Non-Portkey Services

Some services aren't available through Portkey and require direct API keys:

- Voice synthesis (ElevenLabs)
- Media services (Pexels)
- Services not available through Portkey (ElevenLabs, specialized APIs, etc.)

### Voice & Media Services

1. `ELEVENLABS_API_KEY` - Voice synthesis
2. `PEXELS_API_KEY` - Stock images (optional)

### Sentry

| Secret Name | Description | Last Updated | Status |
|------------|-------------|--------------|---------|
| `SENTRY_DSN` | Error tracking | 3 months ago | ⚠️ Optional | 

## Core Secrets Configuration

| Environment Variable         | Description                                       | Last Changed | Purpose                 |
|------------------------------|---------------------------------------------------|--------------|-------------------------|
| `DATABASE_URL`               | PostgreSQL connection string                      | 1 week ago   | Primary data storage    |
| `WEAVIATE_URL`               | Weaviate Cloud instance URL                       | 1 week ago   | Vector database         |
| `WEAVIATE_API_KEY`           | Weaviate Cloud API key                            | 1 week ago   | Vector database auth    |
| `VULTR_API_KEY`              | Vultr API Key for cloud infrastructure management | New          | Cloud provider          |
| `OPENAI_API_KEY`             | OpenAI API key for GPT models                     | 2 weeks ago  | LLM access              |
| `ANTHROPIC_API_KEY`          | Anthropic API key for Claude models               | 2 weeks ago  | LLM access              |
| `RECRAFT_API_KEY`            | Recraft API key for design generation             | New          | Design AI               |
| `OPENROUTER_API_KEY`         | OpenRouter API key for model routing              | New          | LLM routing             |
| `JWT_SECRET_KEY`             | Secret key for signing JWT tokens                 | 3 weeks ago  | Authentication          |
| `REDIS_URL`                  | Redis connection string (if used for caching)     | 4 weeks ago  | Caching (optional)      |
| `ROOT_API_KEY`               | Master API key for administrative tasks           | 1 month ago  | System administration   |

---

## Setup and Management

### Environment Variables
- **Local Development**: Use a `.env` file in the project root. See `.env.example`.
- **Vultr Deployment**: Set environment variables directly on the Vultr instance or through your deployment automation (e.g., cloud-init, Ansible, Pulumi).
- **CI/CD (GitHub Actions)**: Store secrets in GitHub repository secrets (`Settings > Secrets and variables > Actions`).

### Secret Management Best Practices
- **Principle of Least Privilege**: Ensure API keys and service accounts have only the necessary permissions.
- **Rotation**: Regularly rotate API keys and sensitive credentials.
- **Storage**: Avoid hardcoding secrets. Use environment variables or a dedicated secret manager (e.g., HashiCorp Vault if self-hosted, or Vultr's metadata service if applicable for instance-specific secrets).
- **Audit**: Regularly audit access to secrets and their usage.

### Vultr Specifics
- **VULTR_API_KEY**: This is the primary key for interacting with the Vultr API to manage instances, storage, networks, etc. Secure it carefully.
- **Instance Metadata**: For services running on Vultr instances, consider if any configuration can be passed via user-data or instance metadata if appropriate and secure for your use case.

### Deprecated Secrets (To Be Removed)
- Any secrets related to GCP (e.g., `GCP_PROJECT_ID`, `GCP_MASTER_SERVICE_JSON`) should be identified and removed from all configurations and documentation after ensuring they are no longer in use.

---

## Notes
- The `ROOT_API_KEY` should be a strong, randomly generated key and managed with extreme care.
- For PostgreSQL, ensure the `DATABASE_URL` includes credentials with appropriate, limited permissions for the application.
- Weaviate Cloud API keys are managed through the Weaviate Cloud console. 