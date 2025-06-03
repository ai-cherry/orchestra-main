"""
"""
router = APIRouter(prefix="/llm", tags=["llm"])

class LLMRequestModel(BaseModel):
    """Request model for LLM interaction API."""
    message: str = Field(..., description="The user's message")
    user_id: str = Field(..., description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier for conversation continuity")
    persona_id: Optional[str] = Field(None, description="Persona identifier to use for this interaction")
    model: Optional[str] = Field(None, description="LLM model to use")
    temperature: Optional[float] = Field(0.7, description="Temperature for generation", ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate", gt=0)
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the interaction")

class LLMResponseModel(BaseModel):
    """Response model for LLM interaction API."""
    message: str = Field(..., description="The response message")
    persona_id: str = Field(..., description="The persona identifier used")
    persona_name: str = Field(..., description="The persona name used")
    model: str = Field(..., description="The model used")
    provider: str = Field(..., description="The provider used")
    usage: Optional[Dict[str, int]] = Field(None, description="Token usage information")
    session_id: str = Field(..., description="The session identifier")
    interaction_id: str = Field(..., description="The interaction identifier")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")

class ErrorResponse(BaseModel):
    """Standard error response model."""
    detail: str = Field(..., description="Error detail message")
    error_type: Optional[str] = Field(None, description="Type of error")
    status_code: int = Field(..., description="HTTP status code")

@router.post(
    "/interact",
    response_model=LLMResponseModel,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Authentication failed",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Invalid request parameters",
        },
        status.HTTP_408_REQUEST_TIMEOUT: {
            "model": ErrorResponse,
            "description": "Request timeout",
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "model": ErrorResponse,
            "description": "Rate limit exceeded",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Server error",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "Service unavailable",
        },
    },
)
async def llm_interact(request: LLMRequestModel, persona_manager=Depends(get_persona_manager)):
    """
    """
        if not hasattr(settings, "OPENROUTER_API_KEY") or not settings.OPENROUTER_API_KEY:
            raise LLMProviderAuthenticationError(
                "OpenRouter API key not configured. Please set OPENROUTER_API_KEY in your environment."
            )

        # Add LLM-specific context
        context = request.context or {}
        if request.model:
            context["llm_model"] = request.model
        if request.temperature is not None:
            context["llm_temperature"] = request.temperature
        if request.max_tokens is not None:
            context["llm_max_tokens"] = request.max_tokens

        # Use the enhanced orchestrator for better persona support
        orchestrator = get_enhanced_agent_orchestrator()

        # Process the interaction
        result = await orchestrator.process_interaction(
            user_input=request.message,
            user_id=request.user_id,
            session_id=request.session_id,
            persona_id=request.persona_id,
            context=context,
        )

        # Get conversation context metadata
        conversation_context = result.get("conversation_context", {})

        # Extract model and provider info from metadata
        model = conversation_context.get("model", settings.DEFAULT_LLM_MODEL)
        provider = conversation_context.get("provider", "openrouter")
        usage = conversation_context.get("usage")
        response_time = conversation_context.get("response_time_ms")

        # If there was an error in the LLM call, it would be captured in the metadata
        if "error" in conversation_context:
            # Log the error but still return a successful response with the fallback message
            error_type = conversation_context.get("error")
            error_message = conversation_context.get("error_message", "Unknown error")
            logger.warning(f"LLM error handled by agent: {error_type} - {error_message}")

        # Return formatted response
        return LLMResponseModel(
            message=result["message"],
            persona_id=result["persona_id"],
            persona_name=result["persona_name"],
            model=model,
            provider=provider,
            usage=usage,
            session_id=result["session_id"],
            interaction_id=result["interaction_id"],
            response_time_ms=response_time,
        )

    except Exception:


        pass
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    except Exception:


        pass
        logger.error(f"Invalid request: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception:


        pass
        logger.error(f"Request timeout: {e}")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=f"Request timed out: {str(e)}",
        )

    except Exception:


        pass
        logger.warning(f"Rate limit exceeded: {e}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {str(e)}",
            headers={"Retry-After": "30"},  # Suggest retry after 30 seconds
        )

    except Exception:


        pass
        logger.error(f"Connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {str(e)}",
            headers={"Retry-After": "10"},  # Suggest retry after 10 seconds
        )

    except Exception:


        pass
        logger.error(f"Model error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Model error: {str(e)}")

    except Exception:


        pass
        logger.error(f"Service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service error: {str(e)}",
            headers={"Retry-After": "60"},  # Suggest retry after 60 seconds
        )

    except Exception:


        pass
        logger.error(f"LLM provider error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM provider error: {str(e)}",
        )

    except Exception:


        pass
        logger.error(f"Error processing LLM interaction: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process interaction: {str(e)}",
        )

@router.post(
    "/direct",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Authentication failed",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Invalid request parameters",
        },
        status.HTTP_408_REQUEST_TIMEOUT: {
            "model": ErrorResponse,
            "description": "Request timeout",
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "model": ErrorResponse,
            "description": "Rate limit exceeded",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Server error",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "Service unavailable",
        },
    },
)
async def direct_llm_completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: Optional[float] = 0.7,
    max_tokens: Optional[int] = None,
):
    """
    """
            raise LLMProviderInvalidRequestError("Messages must be a non-empty list")

        for msg in messages:
            if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                raise LLMProviderInvalidRequestError("Each message must be a dict with 'role' and 'content' keys")

        # Get LLM provider
        llm_provider = get_llm_provider("openrouter")

        # Generate completion
        result = await llm_provider.generate_chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Return result directly
        return result

    except Exception:


        pass
        logger.error(f"Authentication error: {e}", exc_info=True)
        logger.warning("Authentication failure may prevent direct LLM completion.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    except Exception:


        pass
        logger.error(f"Invalid request: {e}", exc_info=True)
        logger.warning("Invalid request may indicate input or configuration issues in direct completion.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception:


        pass
        logger.error(f"Request timeout: {e}", exc_info=True)
        logger.warning("Timeout may impact direct completion; consider retrying or adjusting timeout settings.")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=f"Request timed out: {str(e)}",
        )

    except Exception:


        pass
        logger.warning(f"Rate limit exceeded: {e}", exc_info=True)
        logger.warning("Rate limit exceeded; direct completion may be delayed.")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {str(e)}",
            headers={"Retry-After": "30"},  # Suggest retry after 30 seconds
        )

    except Exception:


        pass
        logger.error(f"Connection error: {e}", exc_info=True)
        logger.warning("Connection issues may prevent direct LLM completion; check network or provider status.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {str(e)}",
            headers={"Retry-After": "10"},  # Suggest retry after 10 seconds
        )

    except Exception:


        pass
        logger.error(f"Model error: {e}", exc_info=True)
        logger.warning("Model error may require configuration or model selection adjustments for direct completion.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Model error: {str(e)}")

    except Exception:


        pass
        logger.error(f"Service error: {e}", exc_info=True)
        logger.warning("Service error may indicate provider issues; consider fallback options for direct completion.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service error: {str(e)}",
            headers={"Retry-After": "60"},  # Suggest retry after 60 seconds
        )

    except Exception:


        pass
        logger.error(f"LLM provider error: {e}", exc_info=True)
        logger.warning("Provider error may disrupt direct LLM completion.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM provider error: {str(e)}",
        )

    except Exception:


        pass
        logger.error(f"Error in direct LLM completion: {e}", exc_info=True)
        logger.warning("Unexpected error may impact direct completion processing; review logs for details.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM completion failed: {str(e)}",
        )
