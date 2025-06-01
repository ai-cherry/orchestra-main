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
| `RESEMBLE_API_KEY` | Resemble AI voice synthesis | 5 hours ago | ✅ Documented |
| `RESEMBLE_SYNTHESIS_ENDPOINT` | Resemble synthesis endpoint | 5 hours ago | Voice generation |
| `RESEMBLE_STREAMING_ENDPOINT` | Resemble streaming endpoint | 5 hours ago | Real-time voice |
| `ELEVENLABS_API_KEY` | ElevenLabs voice API | 2 months ago | Alternative voice |
| `RECRAFT_API_KEY` | Recraft API for image generation | 3 days ago | Alternative to DALL-E |

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
| `TERRAFORM_API_TOKEN` | Terraform Cloud token | - | Alternative IaC |
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
- Services not available through Portkey (Resemble, ElevenLabs, etc.)
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