# LLM Configuration Guide

## Overview

The Orchestra AI project now includes a comprehensive LLM configuration system that allows dynamic model selection and routing through Portkey and OpenRouter without requiring code changes. This guide explains how to set up and use the system.

## Key Features

- **Dynamic Model Selection**: Change models for different use cases through the admin UI
- **Automatic Fallback**: If primary model fails, automatically tries fallback models
- **Cost Optimization**: Choose between Premium, Standard, and Economy tiers
- **Performance Monitoring**: Track usage, costs, and performance metrics
- **Real-time Updates**: Configuration changes take effect immediately
- **Multi-Provider Support**: Use Portkey as primary and OpenRouter as fallback

## Architecture

```
┌─────────────────────┐
│   Admin Dashboard   │
│  (React/TypeScript) │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   FastAPI Routes    │
│  (/admin/llm/*)     │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Dynamic LLM Router │
│  (Python/AsyncIO)   │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │             │
┌───▼───┐    ┌───▼────┐
│Portkey│    │OpenRouter│
└───────┘    └─────────┘
```

## Setup Instructions

### 1. Database Setup

Run the setup script to create tables and migrate existing configurations:

```bash
python scripts/setup_llm_configuration.py
```

This will:
- Create all necessary database tables
- Migrate hardcoded model mappings to the database
- Update env.example with required variables

### 2. Environment Variables

Add the following to your `.env` file:

```bash
# Portkey Configuration
PORTKEY_API_KEY=your_portkey_api_key_here
PORTKEY_CONFIG=your_portkey_config_id_here

# OpenRouter Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here
OR_SITE_URL=https://your-site.com
OR_APP_NAME=Orchestra AI
```

### 3. Access Admin Dashboard

Navigate to `/admin/llm` in your browser to access the LLM configuration interface.

## Admin Dashboard Components

### 1. Model Selection (`/admin/llm`)
- Configure which models to use for each use case
- Set up fallback models for high availability
- Customize temperature and token limits per use case/tier

### 2. Provider Settings
- Configure API keys for Portkey and OpenRouter
- Enable/disable providers
- Set priority order for fallback routing

### 3. Metrics Dashboard
- View usage statistics by model and use case
- Monitor costs and performance
- Track success rates and latency

### 4. Test Interface
- Test model configurations before applying
- Compare response quality across models
- Measure latency and token usage

## Use Cases and Tiers

### Use Cases
- **Code Generation**: Writing code with proper syntax and logic
- **Architecture Design**: System design and architectural decisions
- **Debugging**: Analyzing and fixing code issues
- **Documentation**: Creating technical documentation
- **Chat Conversation**: General conversational interactions
- **Memory Processing**: Extracting and structuring information
- **Workflow Orchestration**: Breaking down complex tasks

### Model Tiers
- **Premium**: Most capable models (e.g., GPT-4, Claude Opus)
- **Standard**: Balanced performance/cost (e.g., GPT-3.5, Claude Sonnet)
- **Economy**: Fast, low-cost models (e.g., Claude Haiku, Mixtral)

## API Usage

### Python (Using Dynamic Router)

```python
from core.llm_router_dynamic import get_dynamic_llm_router, UseCase, ModelTier

# Get router instance
router = get_dynamic_llm_router()

# Make a completion request
response = await router.complete(
    messages="Write a Python function to calculate fibonacci",
    use_case=UseCase.CODE_GENERATION,
    tier=ModelTier.STANDARD
)

print(response["choices"][0]["message"]["content"])
```

### TypeScript (Frontend)

```typescript
import { llmClient, UseCase, ModelTier } from '@/types/llm';

// Make a completion request
const response = await llmClient.complete({
  messages: "Explain microservices architecture",
  useCase: UseCase.ARCHITECTURE_DESIGN,
  tier: ModelTier.PREMIUM
});

console.log(response.choices[0].message.content);
```

### REST API

```bash
# Complete request
curl -X POST http://localhost:8000/api/llm/complete \
  -H "Content-Type: application/json" \
  -d '{
    "messages": "Hello, how are you?",
    "use_case": "chat_conversation",
    "tier": "standard"
  }'

# Get metrics
curl http://localhost:8000/api/admin/llm/metrics

# Test a model
curl -X POST http://localhost:8000/api/admin/llm/test \
  -H "Content-Type: application/json" \
  -d '{
    "model_identifier": "anthropic/claude-3-sonnet",
    "provider": "portkey",
    "test_prompt": "Hello, please confirm you can read this."
  }'
```

## Configuration Examples

### Setting Up Code Generation

1. Go to Model Selection tab
2. Select "Code Generation" use case
3. For each tier:
   - **Premium**: Claude 3 Opus (primary), GPT-4 Turbo (fallback)
   - **Standard**: Claude 3 Sonnet (primary), GPT-4 (fallback)
   - **Economy**: Claude 3 Haiku (primary), Mixtral 8x7B (fallback)
4. Set temperature to 0.2 for focused output
5. Save configuration

### Optimizing for Cost

1. Use Economy tier for simple tasks
2. Set up aggressive caching (enabled by default)
3. Monitor metrics dashboard for cost per use case
4. Adjust model assignments based on performance/cost ratio

### High Availability Setup

1. Enable both Portkey and OpenRouter
2. Set Portkey priority to 0 (highest)
3. Configure multiple fallback models per tier
4. Test failover scenarios using the test interface

## Monitoring and Optimization

### Key Metrics to Track

- **Success Rate**: Should be >95% for production
- **Average Latency**: Target <2s for most use cases
- **Cost per Request**: Monitor for budget compliance
- **Token Usage**: Optimize prompts to reduce tokens

### Performance Tips

1. **Use Appropriate Tiers**: Don't use Premium for simple tasks
2. **Enable Caching**: Reduces latency and cost for repeated queries
3. **Optimize Prompts**: Shorter, clearer prompts use fewer tokens
4. **Monitor Failures**: Check logs for specific model failures

## Troubleshooting

### Common Issues

1. **"No API key configured"**
   - Ensure environment variables are set
   - Restart the application after setting keys

2. **"All models failed"**
   - Check provider status on their dashboards
   - Verify API keys are valid
   - Check rate limits

3. **High latency**
   - Consider using closer geographic endpoints
   - Enable caching for repeated queries
   - Use Economy tier for faster responses

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger("core.llm_router_dynamic").setLevel(logging.DEBUG)
```

## Best Practices

1. **Test Before Production**: Always test new configurations
2. **Set Reasonable Fallbacks**: Ensure fallback models are reliable
3. **Monitor Costs**: Set up alerts for unusual spending
4. **Document Changes**: Keep track of configuration changes
5. **Regular Reviews**: Review metrics weekly to optimize

## Migration from Static Configuration

If you're migrating from the old hardcoded system:

1. Run `scripts/setup_llm_configuration.py`
2. Update code to use `DynamicLLMRouter` instead of `UnifiedLLMRouter`
3. Remove hardcoded model references
4. Test all use cases thoroughly

## Security Considerations

- API keys are stored as environment variables
- Database stores only references to env vars, not actual keys
- Admin routes should be protected in production
- Use HTTPS for all API communications

## Future Enhancements

- Automatic model discovery and updates
- A/B testing for model selection
- Custom use case definitions
- Budget alerts and limits
- Model performance benchmarking