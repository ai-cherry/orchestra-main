"""
FastAPI router for unified LLM operations
"""

from typing import Dict, Any, List, Optional, Union
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from core.llm_router_dynamic import (
    get_dynamic_llm_router,
    UseCase,
    ModelTier,
    RouterConfig
)

router = APIRouter(prefix="/llm", tags=["llm"])


class LLMRequest(BaseModel):
    """Request model for LLM completion"""
    messages: Union[str, List[Dict[str, str]]]
    use_case: UseCase = UseCase.GENERAL_PURPOSE
    tier: ModelTier = ModelTier.STANDARD
    model_override: Optional[str] = None
    temperature_override: Optional[float] = None
    max_tokens_override: Optional[int] = None
    system_prompt_override: Optional[str] = None
    stream: bool = False
    cache: bool = True


class LLMResponse(BaseModel):
    """Response model for LLM completion"""
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Optional[Dict[str, int]] = None


class CodeGenerationRequest(BaseModel):
    """Request model for code generation"""
    prompt: str = Field(..., description="Code generation prompt")
    tier: ModelTier = ModelTier.STANDARD


class ArchitectureRequest(BaseModel):
    """Request model for architecture design"""
    requirements: str = Field(..., description="Architecture requirements")
    tier: ModelTier = ModelTier.PREMIUM


class DebugRequest(BaseModel):
    """Request model for debugging"""
    code: str = Field(..., description="Code to debug")
    error: str = Field(..., description="Error message or description")


class ChatRequest(BaseModel):
    """Request model for chat"""
    message: str = Field(..., description="Chat message")
    history: Optional[List[Dict[str, str]]] = Field(None, description="Conversation history")
    tier: ModelTier = ModelTier.STANDARD


class EmbeddingRequest(BaseModel):
    """Request model for embeddings"""
    text: Union[str, List[str]] = Field(..., description="Text to embed")
    model: str = Field("openai/text-embedding-3-small", description="Embedding model")


@router.post("/complete", response_model=LLMResponse)
async def complete(request: LLMRequest) -> LLMResponse:
    """
    Complete an LLM request with automatic model routing
    
    This endpoint automatically selects the best model based on the use case
    and tier, handles fallbacks, and provides caching.
    """
    try:
        llm_router = get_dynamic_llm_router()
        
        response = await llm_router.complete(
            messages=request.messages,
            use_case=request.use_case,
            tier=request.tier,
            model_override=request.model_override,
            temperature_override=request.temperature_override,
            max_tokens_override=request.max_tokens_override,
            system_prompt_override=request.system_prompt_override,
            stream=request.stream,
            cache=request.cache
        )
        
        return LLMResponse(**response)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-code")
async def generate_code(request: CodeGenerationRequest) -> Dict[str, str]:
    """Generate code using the appropriate model"""
    try:
        llm_router = get_dynamic_llm_router()
        
        response = await llm_router.complete(
            request.prompt,
            use_case=UseCase.CODE_GENERATION,
            tier=request.tier
        )
        
        return {
            "code": response["choices"][0]["message"]["content"],
            "model": response["model"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/design-architecture")
async def design_architecture(request: ArchitectureRequest) -> Dict[str, str]:
    """Design system architecture based on requirements"""
    try:
        llm_router = get_dynamic_llm_router()
        
        response = await llm_router.complete(
            request.requirements,
            use_case=UseCase.ARCHITECTURE_DESIGN,
            tier=request.tier
        )
        
        return {
            "design": response["choices"][0]["message"]["content"],
            "model": response["model"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/debug-code")
async def debug_code(request: DebugRequest) -> Dict[str, str]:
    """Debug code with error context"""
    try:
        llm_router = get_dynamic_llm_router()
        
        prompt = f"Debug this code:\n\n{request.code}\n\nError:\n{request.error}"
        response = await llm_router.complete(
            prompt,
            use_case=UseCase.DEBUGGING,
            tier=ModelTier.PREMIUM
        )
        
        return {
            "solution": response["choices"][0]["message"]["content"],
            "model": response["model"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def chat(request: ChatRequest) -> Dict[str, str]:
    """Chat conversation with context"""
    try:
        llm_router = get_dynamic_llm_router()
        
        messages = request.history or []
        messages.append({"role": "user", "content": request.message})
        
        response = await llm_router.complete(
            messages,
            use_case=UseCase.CHAT_CONVERSATION,
            tier=request.tier
        )
        
        return {
            "response": response["choices"][0]["message"]["content"],
            "model": response["model"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Get LLM router metrics"""
    try:
        llm_router = get_dynamic_llm_router()
        return llm_router.get_metrics()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def get_available_models() -> Dict[str, Any]:
    """Get available models for each use case and tier"""
    try:
        llm_router = get_dynamic_llm_router()
        
        models = {}
        for use_case in UseCase:
            models[use_case.value] = {}
            for tier in ModelTier:
                try:
                    mapping = llm_router.get_model_mapping(use_case, tier)
                    models[use_case.value][tier.value] = {
                        "primary": mapping.primary_model,
                        "fallbacks": mapping.fallback_models,
                        "max_tokens": mapping.max_tokens,
                        "temperature": mapping.temperature
                    }
                except:
                    # Skip if mapping not available
                    pass
        
        return models
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/embed")
async def generate_embeddings(request: EmbeddingRequest) -> Dict[str, Any]:
    """Generate embeddings for text"""
    try:
        llm_router = get_dynamic_llm_router()
        embeddings = await llm_router.embed(request.text, request.model)
        
        return {
            "embeddings": embeddings,
            "model": request.model,
            "dimension": len(embeddings[0]) if isinstance(embeddings[0], list) else len(embeddings)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))