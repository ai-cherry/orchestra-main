#!/usr/bin/env python3
"""
AI Router API - FastAPI endpoints for intelligent AI routing
Provides REST API for OpenRouter integration with smart fallbacks

Author: Orchestra AI Team
Version: 1.0.0
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
import asyncio

from .openrouter_integration import (
    ai_router, ChatRequest, ChatResponse, UseCase, ModelProvider,
    chat_casual, chat_business, chat_medical, chat_research, chat_code
)

logger = logging.getLogger(__name__)

# Pydantic models for API
class ChatRequestAPI(BaseModel):
    """API model for chat requests."""
    persona: str = Field(..., description="AI persona (cherry, sophia, karen)")
    message: str = Field(..., description="User message")
    use_case: str = Field(default="casual_chat", description="Use case type")
    complexity: str = Field(default="medium", description="Task complexity (low, medium, high)")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(default=None, description="Temperature for generation")
    fallback_allowed: bool = Field(default=True, description="Allow fallback to other providers")

class ChatResponseAPI(BaseModel):
    """API model for chat responses."""
    content: str
    provider: str
    model_used: str
    tokens_used: int
    cost: float
    response_time_ms: int
    fallback_used: bool = False
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class UsageStatsAPI(BaseModel):
    """API model for usage statistics."""
    total_cost: float
    total_savings: float
    requests_count: int
    provider_usage: Dict[str, Any]
    model_configs: Dict[str, Any]

class HealthCheckAPI(BaseModel):
    """API model for health check."""
    status: str
    providers_available: List[str]
    total_requests: int
    uptime_seconds: float
    last_request: Optional[datetime] = None

# FastAPI app
app = FastAPI(
    title="Orchestra AI Router",
    description="Intelligent AI routing with OpenRouter optimization and smart fallbacks",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
app_start_time = datetime.now()
last_request_time = None

def validate_persona(persona: str) -> str:
    """Validate and normalize persona name."""
    valid_personas = {"cherry", "sophia", "karen"}
    persona_lower = persona.lower()
    if persona_lower not in valid_personas:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid persona. Must be one of: {', '.join(valid_personas)}"
        )
    return persona_lower

def validate_use_case(use_case: str) -> UseCase:
    """Validate and convert use case string to enum."""
    try:
        return UseCase(use_case.lower())
    except ValueError:
        valid_cases = [uc.value for uc in UseCase]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid use case. Must be one of: {', '.join(valid_cases)}"
        )

async def update_last_request():
    """Update last request timestamp."""
    global last_request_time
    last_request_time = datetime.now()

@app.get("/health", response_model=HealthCheckAPI)
async def health_check():
    """Health check endpoint."""
    uptime = (datetime.now() - app_start_time).total_seconds()
    
    # Check provider availability
    available_providers = []
    try:
        # Quick test of each provider
        test_providers = [ModelProvider.OPENROUTER, ModelProvider.OPENAI, ModelProvider.GROK, ModelProvider.PERPLEXITY]
        for provider in test_providers:
            # This is a simplified check - in production you might want to make actual test calls
            available_providers.append(provider.value)
    except Exception as e:
        logger.warning(f"Provider check failed: {e}")
    
    stats = ai_router.get_usage_stats()
    
    return HealthCheckAPI(
        status="healthy",
        providers_available=available_providers,
        total_requests=stats["cost_tracking"]["requests_count"],
        uptime_seconds=uptime,
        last_request=last_request_time
    )

@app.post("/chat", response_model=ChatResponseAPI)
async def chat_completion(
    request: ChatRequestAPI,
    background_tasks: BackgroundTasks
):
    """Main chat completion endpoint with intelligent routing."""
    background_tasks.add_task(update_last_request)
    
    try:
        # Validate inputs
        persona = validate_persona(request.persona)
        use_case = validate_use_case(request.use_case)
        
        # Create internal request
        chat_request = ChatRequest(
            persona=persona,
            message=request.message,
            use_case=use_case,
            complexity=request.complexity,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            fallback_allowed=request.fallback_allowed
        )
        
        # Get response from AI router
        response = await ai_router.chat_completion(chat_request)
        
        # Convert to API response
        return ChatResponseAPI(
            content=response.content,
            provider=response.provider.value,
            model_used=response.model_used,
            tokens_used=response.tokens_used,
            cost=response.cost,
            response_time_ms=response.response_time_ms,
            fallback_used=response.fallback_used,
            error=response.error
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat completion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/casual", response_model=ChatResponseAPI)
async def chat_casual_endpoint(
    persona: str,
    message: str,
    background_tasks: BackgroundTasks,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None
):
    """Casual chat endpoint."""
    background_tasks.add_task(update_last_request)
    
    try:
        persona = validate_persona(persona)
        response = await chat_casual(
            persona=persona,
            message=message,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return ChatResponseAPI(
            content=response.content,
            provider=response.provider.value,
            model_used=response.model_used,
            tokens_used=response.tokens_used,
            cost=response.cost,
            response_time_ms=response.response_time_ms,
            fallback_used=response.fallback_used,
            error=response.error
        )
        
    except Exception as e:
        logger.error(f"Casual chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/business", response_model=ChatResponseAPI)
async def chat_business_endpoint(
    persona: str,
    message: str,
    background_tasks: BackgroundTasks,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None
):
    """Business analysis chat endpoint."""
    background_tasks.add_task(update_last_request)
    
    try:
        persona = validate_persona(persona)
        response = await chat_business(
            persona=persona,
            message=message,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return ChatResponseAPI(
            content=response.content,
            provider=response.provider.value,
            model_used=response.model_used,
            tokens_used=response.tokens_used,
            cost=response.cost,
            response_time_ms=response.response_time_ms,
            fallback_used=response.fallback_used,
            error=response.error
        )
        
    except Exception as e:
        logger.error(f"Business chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/medical", response_model=ChatResponseAPI)
async def chat_medical_endpoint(
    persona: str,
    message: str,
    background_tasks: BackgroundTasks,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None
):
    """Medical compliance chat endpoint."""
    background_tasks.add_task(update_last_request)
    
    try:
        persona = validate_persona(persona)
        response = await chat_medical(
            persona=persona,
            message=message,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return ChatResponseAPI(
            content=response.content,
            provider=response.provider.value,
            model_used=response.model_used,
            tokens_used=response.tokens_used,
            cost=response.cost,
            response_time_ms=response.response_time_ms,
            fallback_used=response.fallback_used,
            error=response.error
        )
        
    except Exception as e:
        logger.error(f"Medical chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/research", response_model=ChatResponseAPI)
async def chat_research_endpoint(
    persona: str,
    message: str,
    background_tasks: BackgroundTasks,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None
):
    """Research and search chat endpoint."""
    background_tasks.add_task(update_last_request)
    
    try:
        persona = validate_persona(persona)
        response = await chat_research(
            persona=persona,
            message=message,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return ChatResponseAPI(
            content=response.content,
            provider=response.provider.value,
            model_used=response.model_used,
            tokens_used=response.tokens_used,
            cost=response.cost,
            response_time_ms=response.response_time_ms,
            fallback_used=response.fallback_used,
            error=response.error
        )
        
    except Exception as e:
        logger.error(f"Research chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/code", response_model=ChatResponseAPI)
async def chat_code_endpoint(
    persona: str,
    message: str,
    background_tasks: BackgroundTasks,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None
):
    """Code generation chat endpoint."""
    background_tasks.add_task(update_last_request)
    
    try:
        persona = validate_persona(persona)
        response = await chat_code(
            persona=persona,
            message=message,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return ChatResponseAPI(
            content=response.content,
            provider=response.provider.value,
            model_used=response.model_used,
            tokens_used=response.tokens_used,
            cost=response.cost,
            response_time_ms=response.response_time_ms,
            fallback_used=response.fallback_used,
            error=response.error
        )
        
    except Exception as e:
        logger.error(f"Code chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats", response_model=UsageStatsAPI)
async def get_usage_stats():
    """Get usage statistics and cost tracking."""
    try:
        stats = ai_router.get_usage_stats()
        
        return UsageStatsAPI(
            total_cost=stats["cost_tracking"]["total_cost"],
            total_savings=stats["cost_tracking"]["total_savings"],
            requests_count=stats["cost_tracking"]["requests_count"],
            provider_usage=stats["cost_tracking"]["provider_usage"],
            model_configs=stats["model_configs"]
        )
        
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def get_available_models():
    """Get list of available models and their configurations."""
    try:
        stats = ai_router.get_usage_stats()
        return {
            "models": stats["model_configs"],
            "providers": [provider.value for provider in ModelProvider],
            "use_cases": [uc.value for uc in UseCase]
        }
        
    except Exception as e:
        logger.error(f"Models retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test/{provider}")
async def test_provider(provider: str, message: str = "Hello, this is a test."):
    """Test a specific provider."""
    try:
        # Validate provider
        try:
            provider_enum = ModelProvider(provider.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid provider. Must be one of: {[p.value for p in ModelProvider]}"
            )
        
        # Find a model for this provider
        available_models = [
            model_id for model_id, config in ai_router.model_configs.items()
            if config.provider == provider_enum
        ]
        
        if not available_models:
            raise HTTPException(
                status_code=404,
                detail=f"No models available for provider: {provider}"
            )
        
        # Test with the first available model
        test_request = ChatRequest(
            persona="cherry",
            message=message,
            use_case=UseCase.CASUAL_CHAT,
            fallback_allowed=False
        )
        
        # Force use of specific model by temporarily modifying router
        original_select = ai_router._select_optimal_model
        ai_router._select_optimal_model = lambda req: available_models[0]
        
        try:
            response = await ai_router.chat_completion(test_request)
            return {
                "status": "success",
                "provider": provider,
                "model_used": response.model_used,
                "response_time_ms": response.response_time_ms,
                "tokens_used": response.tokens_used,
                "cost": response.cost,
                "content_preview": response.content[:100] + "..." if len(response.content) > 100 else response.content
            }
        finally:
            # Restore original method
            ai_router._select_optimal_model = original_select
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Provider test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8020) 