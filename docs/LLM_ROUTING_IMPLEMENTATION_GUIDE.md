# LLM Routing Implementation Guide

This guide provides practical implementation steps for the Orchestra LLM routing strategy.

## Quick Start

### 1. Install Dependencies

```bash
# Python dependencies
pip install portkey-ai openai litellm pydantic prometheus-client

# TypeScript dependencies (for admin-ui)
npm install portkey-ai openai
```

### 2. Basic Configuration

Create `config/llm_router_config.py`:

```python
import os
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class ModelSpec(BaseModel):
    """Specification for a model configuration"""
    provider: str
    model_id: str
    max_tokens: int = 4096
    temperature: float = 0.7
    cost_per_1k_tokens: float = 0.002
    context_window: int = 4096
    supports_functions: bool = True
    supports_vision: bool = False

class UseCase(BaseModel):
    """Configuration for a specific use case"""
    name: str
    description: str
    primary_model: ModelSpec
    fallback_models: List[ModelSpec] = []
    max_latency_ms: Optional[int] = None
    max_cost_per_request: Optional[float] = None

# Model catalog
MODELS = {
    # OpenAI Models
    "gpt-4o": ModelSpec(
        provider="openai",
        model_id="gpt-4o",
        max_tokens=128000,
        temperature=0.7,
        cost_per_1k_tokens=0.015,
        context_window=128000,
        supports_vision=True
    ),
    "gpt-4o-mini": ModelSpec(
        provider="openai",
        model_id="gpt-4o-mini",
        max_tokens=128000,
        temperature=0.7,
        cost_per_1k_tokens=0.00015,
        context_window=128000
    ),
    "gpt-3.5-turbo": ModelSpec(
        provider="openai",
        model_id="gpt-3.5-turbo",
        max_tokens=16384,
        temperature=0.7,
        cost_per_1k_tokens=0.0005,
        context_window=16384
    ),
    
    # Anthropic Models
    "claude-3-opus": ModelSpec(
        provider="anthropic",
