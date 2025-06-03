"""
"""
router = APIRouter(prefix="/llm", tags=["llm"])

class LLMRequest(BaseModel):
    """Request model for LLM completion"""
    """Response model for LLM completion"""
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
    """
@router.post("/generate-code")
async def generate_code(request: CodeGenerationRequest) -> Dict[str, str]:
    """Generate code using the appropriate model"""
        return {"code": response["choices"][0]["message"]["content"], "model": response["model"]}

    except Exception:


        pass
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/design-architecture")
async def design_architecture(request: ArchitectureRequest) -> Dict[str, str]:
    """Design system architecture based on requirements"""
        return {"design": response["choices"][0]["message"]["content"], "model": response["model"]}

    except Exception:


        pass
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/debug-code")
async def debug_code(request: DebugRequest) -> Dict[str, str]:
    """Debug code with error context"""
        prompt = f"Debug this code:\n\n{request.code}\n\nError:\n{request.error}"
        response = await llm_router.complete(prompt, use_case=UseCase.DEBUGGING, tier=ModelTier.PREMIUM)

        return {"solution": response["choices"][0]["message"]["content"], "model": response["model"]}

    except Exception:


        pass
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat(request: ChatRequest) -> Dict[str, str]:
    """Chat conversation with context"""
        messages.append({"role": "user", "content": request.message})

        response = await llm_router.complete(messages, use_case=UseCase.CHAT_CONVERSATION, tier=request.tier)

        return {"response": response["choices"][0]["message"]["content"], "model": response["model"]}

    except Exception:


        pass
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Get LLM router metrics"""
@router.get("/models")
async def get_available_models() -> Dict[str, Any]:
    """Get available models for each use case and tier"""
                        "primary": mapping.primary_model,
                        "fallbacks": mapping.fallback_models,
                        "max_tokens": mapping.max_tokens,
                        "temperature": mapping.temperature,
                    }
                except Exception:

                    pass
                    # Skip if mapping not available
                    pass

        return models

    except Exception:


        pass
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/embed")
async def generate_embeddings(request: EmbeddingRequest) -> Dict[str, Any]:
    """Generate embeddings for text"""
            "embeddings": embeddings,
            "model": request.model,
            "dimension": len(embeddings[0]) if isinstance(embeddings[0], list) else len(embeddings),
        }

    except Exception:


        pass
        raise HTTPException(status_code=500, detail=str(e))
