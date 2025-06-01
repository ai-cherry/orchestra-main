# Secrets Configuration Guide

## Overview
This document outlines all secrets and environment variables required for the Orchestra AI project, including Portkey virtual keys and other service integrations.

## GitHub Secrets (Production)

### Core API Keys
| Secret Name | Description | Required | Used By |
|------------|-------------|----------|---------|
| `PORTKEY_API_KEY` | Main Portkey API key for accessing virtual keys | ✅ | Multimodal services, LLM routing |
| `DATABASE_URL` | PostgreSQL connection string | ✅ | All database operations |
| `WEAVIATE_URL` | Weaviate instance URL | ✅ | Vector search, memory storage |
| `WEAVIATE_API_KEY` | Weaviate API key | ✅ | Vector database auth |
| `JWT_SECRET` | JWT token signing secret | ✅ | Authentication |
| `ADMIN_API_KEY` | Admin UI API key (4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd) | ✅ | Admin authentication |

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

### Additional Service Keys
| Secret Name | Description | Required | Used By |
|------------|-------------|----------|---------|
| `PEXELS_API_KEY` | Pexels API for stock media | ❌ | Video synthesis |
| `RESEMBLE_API_KEY` | Resemble AI for voice synthesis | ❌ | Audio generation |
| `SENDGRID_API_KEY` | Email notifications | ❌ | Alert system |
| `SENTRY_DSN` | Error tracking | ❌ | Monitoring |

## Local Development (.env file)

Create a `.env` file in the root directory with the following structure:

```bash
# Core Configuration
NODE_ENV=development
PORT=3000
API_URL=http://localhost:3000

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/orchestra_dev
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=your-weaviate-key

# Authentication
JWT_SECRET=your-jwt-secret-here
ADMIN_API_KEY=4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd

# Portkey Configuration
PORTKEY_API_KEY=your-portkey-api-key
PORTKEY_BASE_URL=https://api.portkey.ai/v1

# Feature Flags
ENABLE_IMAGE_GEN=true
ENABLE_VIDEO_SYNTH=true
ENABLE_ADVANCED_SEARCH=true

# Optional Services
PEXELS_API_KEY=
RESEMBLE_API_KEY=
SENDGRID_API_KEY=
SENTRY_DSN=
```

## Virtual Key Configuration

When using Portkey virtual keys in the application:

```typescript
// Example: Using specific virtual key
import Portkey from '@portkey-ai/portkey-node';

const portkey = new Portkey({
  apiKey: process.env.PORTKEY_API_KEY,
  virtualKey: 'openai-api-key-345cc9' // Use the specific virtual key
});

// For DALL-E 3 image generation
const imageClient = new Portkey({
  apiKey: process.env.PORTKEY_API_KEY,
  virtualKey: 'openai-api-key-345cc9',
  provider: 'openai'
});

// For Claude
const claudeClient = new Portkey({
  apiKey: process.env.PORTKEY_API_KEY,
  virtualKey: 'anthropic-api-k-6feca8',
  provider: 'anthropic'
});
```

## Security Best Practices

1. **Never commit secrets to version control**
   - Use `.gitignore` to exclude `.env` files
   - Use GitHub Secrets for production deployments

2. **Rotate secrets regularly**
   - Set up reminders for quarterly rotation
   - Document rotation procedures

3. **Limit secret access**
   - Use principle of least privilege
   - Separate development and production secrets

4. **Monitor secret usage**
   - Track API usage through Portkey dashboard
   - Set up alerts for unusual activity

## Adding New Secrets

When adding a new secret:

1. Add to this documentation
2. Update `.env.template`
3. Add to GitHub Secrets (for production)
4. Update deployment scripts
5. Notify team members

## Troubleshooting

### Common Issues

1. **"Invalid API Key" errors**
   - Verify the Portkey API key is correctly set
   - Check if the virtual key name matches exactly
   - Ensure the virtual key is active in Portkey dashboard

2. **Rate limiting**
   - Check Portkey dashboard for usage limits
   - Implement caching to reduce API calls
   - Use different virtual keys for load distribution

3. **Missing environment variables**
   - Run `npm run check:env` to validate all required variables
   - Check `.env.template` for the complete list

## Support

For issues with:
- **Portkey virtual keys**: Check https://app.portkey.ai/virtual-keys
- **GitHub Secrets**: Contact repository admin
- **Local development**: See DEVELOPMENT.md 