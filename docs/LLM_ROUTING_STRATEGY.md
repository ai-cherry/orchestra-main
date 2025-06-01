# Orchestra LLM Routing Strategy

## Executive Summary

This document outlines a comprehensive strategy for implementing a unified LLM routing solution across the Orchestra project. After analyzing the current implementation, I recommend **Portkey** as the primary routing solution with **OpenRouter** as a secondary option for specific use cases.

## Current State Analysis

### 1. Model Usage Across the Project

The Orchestra project currently uses multiple LLM models across different components:

#### Backend Services (Python)
- **Phidata/Agno Agents**: Using Portkey-configured models
- **Analyze Code Wrapper**: Direct Gemini 1.5 Pro integration
- **Enhanced Natural Language Interface**: Mixed Gemini + Portkey usage
- **LLM Test Server**: Multiple provider testing (OpenAI, Anthropic, OpenRouter, Portkey, DeepSeek)
- **Web Scraping Agents**: Direct OpenAI integration

#### Frontend Services (TypeScript)
- **Admin UI**: Portkey integration with virtual keys for multiple providers
- **Dashboard**: Model references but no direct implementation yet

#### Configuration Files
- **litellm_config.yaml**: Defines model routing for Azure, Portkey, OpenRouter, and Vertex AI
- **llm_gateway_config.yaml**: Comprehensive gateway configuration with Portkey as primary

### 2. Different Use Cases and Model Requirements

| Use Case | Current Model | Token Requirements | Latency Sensitivity | Cost Sensitivity |
|----------|---------------|-------------------|-------------------|------------------|
| Code Generation | GPT-4o | Medium (4-8k) | Medium | Low |
| Business Analytics | Claude 3 Sonnet | High (32k+) | Low | Medium |
| Creative Content | Claude 3 Opus | High (100k+) | Low | Low |
| Quick Responses | GPT-4o-mini | Low (2-4k) | High | High |
| Code Analysis | Gemini 1.5 Pro | Very High (2M) | Low | Medium |
| Research Tasks | GPT-4o/Claude Opus | High (32k+) | Low | Low |
| Real-time Chat | GPT-3.5/Claude Haiku | Low (2-4k) | Very High | High |

## Portkey vs OpenRouter Comparison

### Portkey Advantages ✅
1. **Enterprise Features**
   - Built-in PII redaction and guardrails
   - Comprehensive observability and tracing
   - Cost tracking and budget management
   - Circuit breaker and failover mechanisms

2. **Integration Quality**
   - Already deeply integrated in the project
   - Virtual key system for provider abstraction
   - Native support in Phidata/Agno agents
   - Existing TypeScript SDK in admin-ui

3. **Performance**
   - Intelligent caching mechanisms
   - Load balancing across providers
   - Automatic retry with exponential backoff
   - Regional routing for lower latency

### OpenRouter Advantages ✅
1. **Model Variety**
   - Access to 300+ models from 50+ providers
   - Unique models not available elsewhere
   - Community and open-source models
   - Rapid addition of new models

2. **Pricing Flexibility**
   - Pay-per-use with no minimums
   - Transparent pricing across all models
   - Often cheaper for specific models
   - No virtual key management overhead

3. **Simplicity**
   - Single API key for all models
   - Straightforward model naming convention
   - Less configuration complexity
   - Direct model access without abstraction

### Recommendation: Hybrid Approach

**Primary: Portkey** for production workloads requiring:
- Enterprise features (security, compliance)
- Multi-provider failover
- Cost management and observability
- Consistent performance

**Secondary: OpenRouter** for:
- Experimental model testing
- Access to niche/specialized models
- Cost optimization for specific use cases
- Development and prototyping

## Migration Strategy

### Phase 1: Standardization (Week 1-2)

1. **Create Unified Configuration**
```python
# config/llm_config.py
from pydantic import BaseModel
from typing import Dict, Optional, List

class ModelConfig(BaseModel):
    """Configuration for a specific model"""
    provider: str  # portkey, openrouter, direct
    model_id: str
    max_tokens: int
    temperature: float
    fallback_models: List[str] = []
    
class LLMRoutingConfig(BaseModel):
    """Master LLM routing configuration"""
    primary_gateway: str = "portkey"
    fallback_gateway: str = "openrouter"
    
    # Model selection by use case
    use_case_models: Dict[str, ModelConfig] = {
        "code_generation": ModelConfig(
            provider="portkey",
            model_id="openai/gpt-4o",
            max_tokens=8000,
            temperature=0.2,
            fallback_models=["anthropic/claude-3-sonnet"]
        ),
        "analysis": ModelConfig(
            provider="portkey",
            model_id="google/gemini-1.5-pro",
            max_tokens=200000,
            temperature=0.3,
            fallback_models=["anthropic/claude-3-opus"]
        ),
        "chat": ModelConfig(
            provider="portkey",
            model_id="openai/gpt-4o-mini",
            max_tokens=4000,
            temperature=0.7,
            fallback_models=["anthropic/claude-3-haiku"]
        )
    }
    
    # Provider configurations
    portkey_config: Dict = {}
    openrouter_config: Dict = {}
```

2. **Implement Unified Router**
```python
# services/llm_router.py
from typing import Optional, Dict, Any, List
import asyncio
from portkey_ai import Portkey
import openai
import logging

class LLMRouter:
    """Unified LLM routing with automatic failover"""
    
    def __init__(self, config: LLMRoutingConfig):
        self.config = config
        self.portkey_client = None
        self.openrouter_client = None
        self._initialize_clients()
        
    def _initialize_clients(self):
        """Initialize gateway clients"""
        if self.config.primary_gateway == "portkey":
            self.portkey_client = Portkey(
                api_key=os.getenv("PORTKEY_API_KEY"),
                virtual_keys=self._get_virtual_keys()
            )
            
        if self.config.fallback_gateway == "openrouter":
            self.openrouter_client = openai.AsyncOpenAI(
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1"
            )
    
    async def complete(
        self,
        messages: List[Dict[str, str]],
        use_case: str = "chat",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Route completion request to appropriate model/provider
        
        Args:
            messages: Chat messages
            use_case: Use case identifier for model selection
            **kwargs: Additional parameters
            
        Returns:
            Completion response with metadata
        """
        model_config = self.config.use_case_models.get(
            use_case, 
            self.config.use_case_models["chat"]
        )
        
        # Try primary provider
        try:
            response = await self._complete_with_provider(
                model_config.provider,
                model_config.model_id,
                messages,
                model_config,
                **kwargs
            )
            return response
            
        except Exception as e:
            logging.warning(f"Primary provider failed: {e}")
            
            # Try fallback models
            for fallback_model in model_config.fallback_models:
                try:
                    response = await self._complete_with_provider(
                        self.config.fallback_gateway,
                        fallback_model,
                        messages,
                        model_config,
                        **kwargs
                    )
                    return response
                except Exception as fallback_error:
                    logging.warning(f"Fallback {fallback_model} failed: {fallback_error}")
                    
        raise Exception("All providers failed")
    
    async def _complete_with_provider(
        self,
        provider: str,
        model_id: str,
        messages: List[Dict[str, str]],
        config: ModelConfig,
        **kwargs
    ) -> Dict[str, Any]:
        """Complete with specific provider"""
        
        start_time = asyncio.get_event_loop().time()
        
        if provider == "portkey" and self.portkey_client:
            response = await self.portkey_client.chat.completions.create(
                model=model_id,
                messages=messages,
                max_tokens=kwargs.get("max_tokens", config.max_tokens),
                temperature=kwargs.get("temperature", config.temperature),
                **kwargs
            )
        elif provider == "openrouter" and self.openrouter_client:
            response = await self.openrouter_client.chat.completions.create(
                model=model_id,
                messages=messages,
                max_tokens=kwargs.get("max_tokens", config.max_tokens),
                temperature=kwargs.get("temperature", config.temperature),
                **kwargs
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")
            
        # Add metadata
        return {
            "content": response.choices[0].message.content,
            "model": response.model,
            "usage": response.usage.dict() if response.usage else {},
            "latency_ms": (asyncio.get_event_loop().time() - start_time) * 1000,
            "provider": provider
        }
```

### Phase 2: Agent Migration (Week 3-4)

1. **Update Phidata/Agno Agents**
```python
# packages/agents/src/base_agent.py
class OrchestraAgent:
    def __init__(self, config: Dict[str, Any]):
        self.llm_router = LLMRouter(load_llm_config())
        self.use_case = config.get("use_case", "chat")
        
    async def generate(self, prompt: str) -> str:
        """Generate response using unified router"""
        messages = [{"role": "user", "content": prompt}]
        response = await self.llm_router.complete(
            messages=messages,
            use_case=self.use_case
        )
        return response["content"]
```

2. **Migrate Direct Integrations**
- Replace direct OpenAI calls with router
- Update Gemini-specific code to use router
- Consolidate all LLM calls through unified interface

### Phase 3: Frontend Integration (Week 5)

1. **Update TypeScript Client**
```typescript
// services/llm-router.ts
export class LLMRouter {
  private portkeyClient: Portkey;
  private openrouterClient: OpenAI;
  
  constructor(private config: LLMConfig) {
    this.initializeClients();
  }
  
  async complete(params: CompletionParams): Promise<CompletionResponse> {
    const modelConfig = this.config.useCaseModels[params.useCase || 'chat'];
    
    try {
      // Try primary provider
      return await this.completeWithProvider(
        modelConfig.provider,
        modelConfig.modelId,
        params
      );
    } catch (error) {
      // Fallback logic
      for (const fallbackModel of modelConfig.fallbackModels) {
        try {
          return await this.completeWithProvider(
            this.config.fallbackGateway,
            fallbackModel,
            params
          );
        } catch (fallbackError) {
          console.warn(`Fallback ${fallbackModel} failed:`, fallbackError);
        }
      }
      throw new Error('All providers failed');
    }
  }
}
```

### Phase 4: Monitoring & Optimization (Week 6)

1. **Implement Comprehensive Monitoring**
```python
# services/llm_monitor.py
class LLMMonitor:
    """Monitor LLM usage and performance"""
    
    def __init__(self):
        self.metrics = {
            "requests_total": Counter("llm_requests_total", "Total LLM requests", ["provider", "model", "use_case"]),
            "request_duration": Histogram("llm_request_duration_seconds", "LLM request duration", ["provider", "model"]),
            "tokens_used": Counter("llm_tokens_used_total", "Total tokens used", ["provider", "model", "type"]),
            "errors_total": Counter("llm_errors_total", "Total LLM errors", ["provider", "model", "error_type"]),
            "cost_usd": Counter("llm_cost_usd_total", "Total cost in USD", ["provider", "model"])
        }
    
    async def track_request(self, request_data: Dict[str, Any]):
        """Track LLM request metrics"""
        # Implementation details...
```

2. **Cost Optimization Engine**
```python
# services/llm_cost_optimizer.py
class LLMCostOptimizer:
    """Optimize model selection based on cost/performance"""
    
    def __init__(self, config: LLMRoutingConfig):
        self.config = config
        self.performance_history = {}
        
    def select_optimal_model(
        self,
        use_case: str,
        context_length: int,
        required_quality: float = 0.8
    ) -> ModelConfig:
        """
        Select optimal model based on:
        - Cost per token
        - Historical performance
        - Context requirements
        - Quality requirements
        """
        candidates = self._get_candidate_models(use_case)
        
        scored_models = []
        for model in candidates:
            score = self._calculate_model_score(
                model,
                context_length,
                required_quality
            )
            scored_models.append((score, model))
            
        # Return best model
        return max(scored_models, key=lambda x: x[0])[1]
```

## Configuration Architecture

### 1. Environment Variables
```bash
# Primary Gateway
PORTKEY_API_KEY=your-portkey-key
PORTKEY_BASE_URL=https://api.portkey.ai/v1

# Virtual Keys (Portkey)
PORTKEY_OPENAI_VIRTUAL_KEY=openai-key-xxx
PORTKEY_ANTHROPIC_VIRTUAL_KEY=anthropic-key-xxx
PORTKEY_GEMINI_VIRTUAL_KEY=gemini-key-xxx

# Fallback Gateway
OPENROUTER_API_KEY=your-openrouter-key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Feature Flags
LLM_ROUTING_ENABLED=true
LLM_FALLBACK_ENABLED=true
LLM_COST_OPTIMIZATION=true
LLM_MONITORING_ENABLED=true
```

### 2. Dynamic Configuration
```yaml
# config/llm_routing.yaml
routing:
  # Model selection rules
  rules:
    - name: "large-context"
      condition: "context_tokens > 32000"
      model: "google/gemini-1.5-pro"
      provider: "portkey"
      
    - name: "code-generation"
      condition: "use_case == 'code'"
      model: "openai/gpt-4o"
      provider: "portkey"
      
    - name: "cost-sensitive"
      condition: "cost_tier == 'economy'"
      model: "anthropic/claude-3-haiku"
      provider: "openrouter"
      
  # Provider health checks
  health_checks:
    interval_seconds: 60
    timeout_seconds: 5
    failure_threshold: 3
    
  # Cost limits
  cost_limits:
    hourly_usd: 10
    daily_usd: 100
    monthly_usd: 1000
```

## Best Practices

### 1. Error Handling
- Implement exponential backoff for retries
- Log all failures with context
- Graceful degradation to simpler models
- User notification for degraded service

### 2. Performance Optimization
- Cache common responses (with TTL)
- Batch similar requests when possible
- Use streaming for long responses
- Implement request deduplication

### 3. Security
- Never log full prompts/responses
- Implement PII detection and redaction
- Use environment variables for all keys
- Regular key rotation schedule

### 4. Monitoring
- Track latency percentiles (p50, p95, p99)
- Monitor token usage by use case
- Alert on cost anomalies
- Dashboard for real-time metrics

## Implementation Timeline

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1-2 | Standardization | Unified config, base router implementation |
| 3-4 | Agent Migration | Updated agents, deprecated direct calls |
| 5 | Frontend Integration | TypeScript client, UI updates |
| 6 | Monitoring & Optimization | Metrics, dashboards, cost optimization |

## Success Metrics

1. **Performance**
   - 99.9% availability across all LLM calls
   - < 500ms additional latency from routing
   - < 1% error rate with automatic recovery

2. **Cost**
   - 20% reduction in LLM costs through optimization
   - Stay within monthly budget limits
   - Accurate cost attribution by use case

3. **Developer Experience**
   - Single interface for all LLM interactions
   - Clear documentation and examples
   - Easy model experimentation

## Conclusion

The recommended approach leverages Portkey's enterprise features while maintaining flexibility through OpenRouter integration. This hybrid strategy provides the best balance of reliability, performance, and cost-effectiveness for the Orchestra project's AI orchestration needs.            "model": response.model,
            "usage": response.usage.dict() if response.usage else {},
            "latency_ms": (asyncio.get_event_loop().time() - start_time) * 1000,
            "provider": provider
        }
```

### Phase 2: Agent Migration (Week 3-4)

1. **Update Phidata/Agno Agents**
```python
# packages/agents/src/base_agent.py
class OrchestraAgent:
    def __init__(self, config: Dict[str, Any]):
        self.llm_router = LLMRouter(load_llm_config())
        self.use_case = config.get("use_case", "chat")
        
    async def generate(self, prompt: str) -> str:
        """Generate response using unified router"""
        messages = [{"role": "user", "content": prompt}]
        response = await self.llm_router.complete(
            messages=messages,
            use_case=self.use_case
        )
        return response["content"]
```

2. **Migrate Direct Integrations**
- Replace direct OpenAI calls with router
- Update Gemini-specific code to use router
- Consolidate all LLM calls through unified interface

### Phase 3: Frontend Integration (Week 5)

1. **Update TypeScript Client**
```typescript
// services/llm-router.ts
export class LLMRouter {
  private portkeyClient: Portkey;
  private openrouterClient: OpenAI;
  
  constructor(private config: LLMConfig) {
    this.initializeClients();
  }
  
  async complete(params: CompletionParams): Promise<CompletionResponse> {
    const modelConfig = this.config.useCaseModels[params.useCase || 'chat'];
    
    try {
      // Try primary provider
      return await this.completeWithProvider(
        modelConfig.provider,
        modelConfig.modelId,
        params
      );
    } catch (error) {
      // Fallback logic
      for (const fallbackModel of modelConfig.fallbackModels) {
        try {
          return await this.completeWithProvider(
            this.config.fallbackGateway,
            fallbackModel,
            params
          );
        } catch (fallbackError) {
          console.warn(`Fallback ${fallbackModel} failed:`, fallbackError);
        }
      }
      throw new Error('All providers failed');
    }
  }
}
```

### Phase 4: Monitoring & Optimization (Week 6)

1. **Implement Comprehensive Monitoring**
```python
# services/llm_monitor.py
class LLMMonitor:
    """Monitor LLM usage and performance"""
    
    def __init__(self):
        self.metrics = {
            "requests_total": Counter("llm_requests_total", "Total LLM requests", ["provider", "model", "use_case"]),
            "request_duration": Histogram("llm_request_duration_seconds", "LLM request duration", ["provider", "model"]),
            "tokens_used": Counter("llm_tokens_used_total", "Total tokens used", ["provider", "model", "type"]),
            "errors_total": Counter("llm_errors_total", "Total LLM errors", ["provider", "model", "error_type"]),
            "cost_usd": Counter("llm_cost_usd_total", "Total cost in USD", ["provider", "model"])
        }
    
    async def track_request(self, request_data: Dict[str, Any]):
        """Track LLM request metrics"""
        # Implementation details...
```

2. **Cost Optimization Engine**
```python
# services/llm_cost_optimizer.py
class LLMCostOptimizer:
    """Optimize model selection based on cost/performance"""
    
    def __init__(self, config: LLMRoutingConfig):
        self.config = config
        self.performance_history = {}
        
    def select_optimal_model(
        self,
        use_case: str,
        context_length: int,
        required_quality: float = 0.8
    ) -> ModelConfig:
        """
        Select optimal model based on:
        - Cost per token
        - Historical performance
        - Context requirements
        - Quality requirements
        """
        candidates = self._get_candidate_models(use_case)
        
        scored_models = []
        for model in candidates:
            score = self._calculate_model_score(
                model,
                context_length,
                required_quality
            )
            scored_models.append((score, model))
            
        # Return best model
        return max(scored_models, key=lambda x: x[0])[1]
```

## Configuration Architecture

### 1. Environment Variables
```bash
# Primary Gateway
PORTKEY_API_KEY=your-portkey-key
PORTKEY_BASE_URL=https://api.portkey.ai/v1

# Virtual Keys (Portkey)
PORTKEY_OPENAI_VIRTUAL_KEY=openai-key-xxx
PORTKEY_ANTHROPIC_VIRTUAL_KEY=anthropic-key-xxx
PORTKEY_GEMINI_VIRTUAL_KEY=gemini-key-xxx

# Fallback Gateway
OPENROUTER_API_KEY=your-openrouter-key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Feature Flags
LLM_ROUTING_ENABLED=true
LLM_FALLBACK_ENABLED=true
LLM_COST_OPTIMIZATION=true
LLM_MONITORING_ENABLED=true
```

### 2. Dynamic Configuration
```yaml
# config/llm_routing.yaml
routing:
  # Model selection rules
  rules:
    - name: "large-context"
      condition: "context_tokens > 32000"
      model: "google/gemini-1.5-pro"
      provider: "portkey"
      
    - name: "code-generation"
      condition: "use_case == 'code'"
      model: "openai/gpt-4o"
      provider: "portkey"
      
    - name: "cost-sensitive"
      condition: "cost_tier == 'economy'"
      model: "anthropic/claude-3-haiku"
      provider: "openrouter"
      
  # Provider health checks
  health_checks:
    interval_seconds: 60
    timeout_seconds: 5
    failure_threshold: 3
    
  # Cost limits
  cost_limits:
    hourly_usd: 10
    daily_usd: 100
    monthly_usd: 1000
```

## Best Practices

### 1. Error Handling
- Implement exponential backoff for retries
- Log all failures with context
- Graceful degradation to simpler models
- User notification for degraded service

### 2. Performance Optimization
- Cache common responses (with TTL)
- Batch similar requests when possible
- Use streaming for long responses
- Implement request deduplication

### 3. Security
- Never log full prompts/responses
- Implement PII detection and redaction
- Use environment variables for all keys
- Regular key rotation schedule

### 4. Monitoring
- Track latency percentiles (p50, p95, p99)
- Monitor token usage by use case
- Alert on cost anomalies
- Dashboard for real-time metrics

## Implementation Timeline

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1-2 | Standardization | Unified config, base router implementation |
| 3-4 | Agent Migration | Updated agents, deprecated direct calls |
| 5 | Frontend Integration | TypeScript client, UI updates |
| 6 | Monitoring & Optimization | Metrics, dashboards, cost optimization |

## Success Metrics

1. **Performance**
   - 99.9% availability across all LLM calls
   - < 500ms additional latency from routing
   - < 1% error rate with automatic recovery

2. **Cost**
   - 20% reduction in LLM costs through optimization
   - Stay within monthly budget limits
   - Accurate cost attribution by use case

3. **Developer Experience**
   - Single interface for all LLM interactions
   - Clear documentation and examples
   - Easy model experimentation

## Conclusion

The recommended approach leverages Portkey's enterprise features while maintaining flexibility through OpenRouter integration. This hybrid strategy provides the best balance of reliability, performance, and cost-effectiveness for the Orchestra project's AI orchestration needs.
