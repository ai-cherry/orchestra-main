# Orchestra AI Secrets Configuration Guide

## Overview
This document provides a complete reference for all secrets and environment variables required to run the Orchestra AI system. All secrets should be stored in GitHub Secrets for production use.

## Required GitHub Secrets

### 🌐 Frontend Deployment (Vercel)
- **VERCEL_TOKEN**: Your Vercel API token
  - Get from: https://vercel.com/account/tokens
  - Required for: Automated deployments
  - Current value starts with: `NAoa1I5OLy...`

- **VERCEL_ORG_ID**: Your Vercel organization ID
  - Get from: Vercel dashboard → Settings → General
  - Current value: `61RiUIeLRc3vudbi9g3v8B3C`

- **VERCEL_ADMIN_PROJECT_ID**: Admin interface project ID
  - Get from: Vercel project settings
  - Required for: Admin interface deployments

- **VERCEL_DASHBOARD_PROJECT_ID**: Dashboard project ID
  - Get from: Vercel project settings
  - Required for: Dashboard deployments

### 🖥️ Infrastructure (Lambda Labs)
- **LAMBDA_LABS_API_KEY**: Lambda Labs API authentication key
  - Get from: https://cloud.lambdalabs.com/api-keys
  - Required for: Instance provisioning
  - Used in: Pulumi infrastructure deployments

- **LAMBDA_LABS_SSH_KEY_NAME**: Name of SSH key in Lambda Labs
  - Register at: https://cloud.lambdalabs.com/ssh-keys
  - Default: `cherry-ai-collaboration-20250604`

### 🔧 Infrastructure as Code (Pulumi)
- **PULUMI_ACCESS_TOKEN**: Pulumi service authentication
  - Get from: https://app.pulumi.com/account/tokens
  - Required for: State management

- **PULUMI_CONFIG_PASSPHRASE**: Encryption passphrase for stack configs
  - Generate: Strong random string
  - Required for: Secure configuration storage

### 🗄️ Databases
- **POSTGRES_HOST**: PostgreSQL server address
  - Default: `localhost` (update for production)
  - Used by: Main application database

- **POSTGRES_DB**: Database name
  - Default: `cherry_ai`
  
- **POSTGRES_USER**: Database username
  - Default: `orchestra`

- **POSTGRES_PASSWORD**: Database password
  - Default: `orchestra_prod_2024` (change in production!)

- **REDIS_URL**: Redis connection string
  - Format: `redis://[user:password@]host:port/db`
  - Default: `redis://localhost:6379`

### 🔍 Vector Databases
- **PINECONE_API_KEY**: Pinecone authentication key
  - Get from: https://app.pinecone.io
  - Required for: Vector search operations

- **PINECONE_ENVIRONMENT**: Pinecone deployment region
  - Example: `us-west1-gcp`
  - Must match your Pinecone index location

- **WEAVIATE_URL**: Weaviate instance URL
  - Format: `https://your-instance.weaviate.network`
  - Or self-hosted: `http://localhost:8080`

### 🤖 AI/LLM Providers
- **OPENAI_API_KEY**: OpenAI API authentication
  - Get from: https://platform.openai.com/api-keys
  - Required for: GPT model access

- **ANTHROPIC_API_KEY**: Anthropic Claude API key
  - Get from: https://console.anthropic.com
  - Required for: Claude model access

- **DEEPSEEK_API_KEY**: DeepSeek API key
  - Get from: DeepSeek platform
  - Optional: Alternative LLM provider

- **PERPLEXITY_API_KEY**: Perplexity AI API key
  - Get from: Perplexity platform
  - Optional: Search-enhanced responses

- **GROK_API_KEY**: xAI Grok API key
  - Get from: xAI platform
  - Optional: Alternative LLM provider

### 📱 Integrations
- **NOTION_API_KEY**: Notion integration token
  - Get from: https://www.notion.so/my-integrations
  - Required for: Notion database operations

- **SLACK_BOT_TOKEN**: Slack bot user OAuth token
  - Get from: https://api.slack.com/apps
  - Format: `xoxb-...`
  - Required for: Slack notifications

- **SLACK_WEBHOOK_URL**: Slack incoming webhook
  - Get from: Slack app settings
  - Used for: Simple notifications

- **PORTKEY_API_KEY**: Portkey AI gateway key
  - Get from: https://app.portkey.ai
  - Required for: LLM routing and observability

- **PORTKEY_CONFIG_ID**: Portkey configuration ID
  - Get from: Portkey dashboard
  - Defines: Routing rules and fallbacks

### 📊 Monitoring
- **GRAFANA_API_KEY**: Grafana API authentication
  - Get from: Grafana → Configuration → API Keys
  - Required for: Metrics and annotations

- **GRAFANA_URL**: Grafana instance URL
  - Format: `https://your-grafana.com`
  - Required for: Dashboard integration

### 🔐 Additional Services
- **ELEVEN_LABS_API_KEY**: Eleven Labs voice synthesis
  - Get from: https://elevenlabs.io
  - Optional: Voice generation features

- **SERP_API_KEY**: Search engine results API
  - Get from: SERP provider
  - Optional: Web search integration

- **STABILITY_API_KEY**: Stability AI image generation
  - Get from: https://platform.stability.ai
  - Optional: Image generation features

- **PHANTOM_BUSTER_API_KEY**: PhantomBuster automation
  - Get from: https://phantombuster.com
  - Optional: Web automation tasks

- **APIFY_API_KEY**: Apify web scraping platform
  - Get from: https://apify.com
  - Optional: Web scraping tasks

- **ZENROWS_API_KEY**: ZenRows web scraping
  - Get from: https://zenrows.com
  - Optional: Anti-bot scraping

- **HUBSPOT_API_KEY**: HubSpot CRM integration
  - Get from: HubSpot settings
  - Optional: CRM operations

## Environment-Specific Variables

### Development
```bash
NODE_ENV=development
LOG_LEVEL=debug
API_BASE_URL=http://localhost:8000
```

### Production  
```bash
NODE_ENV=production
LOG_LEVEL=info
API_BASE_URL=https://api.cherry-ai.me
```

## Setting Up Secrets

### GitHub Repository
1. Go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add each secret with its name and value

### Local Development
```bash
# Copy from .env.example and fill in your values
cp .env.example .env
```

### Vercel Environment Variables
Already configured via API:
- VITE_API_BASE_URL
- All database credentials
- Node version settings

## Security Best Practices

1. **Never commit secrets** to version control
2. **Rotate keys regularly** (every 90 days recommended)
3. **Use least privilege** - create keys with minimal required permissions
4. **Monitor usage** - set up alerts for unusual API usage
5. **Use different keys** for development and production

## Validation

Run this command to check if all required secrets are set:
```bash
python scripts/validate_secrets.py
```

## Last Updated
- Date: December 2024
- Updated by: Orchestra AI Configuration System
- Status: ✅ All critical secrets documented 