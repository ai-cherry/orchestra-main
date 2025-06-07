"""
"""
    """User input model for interaction endpoint."""
    text: str = Field(..., min_length=1, description="User's message text")
    user_id: Optional[str] = Field(None, description="User identifier")

# Dependency for getting the interaction service
async def get_interaction_service(
    memory: MemoryManager = Depends(get_memory_manager),
    llm_client: LLMClient = Depends(get_llm_client),
) -> InteractionService:
    """
    """
    model_to_use = getattr(settings, "DEFAULT_LLM_MODEL_PRIMARY", settings.DEFAULT_LLM_MODEL)

    # Create and return the interaction service
    return InteractionService(
        memory_service=memory_service,
        llm_client=llm_client,
        default_model=model_to_use,
    )

@router.post("/interact", response_model=Dict[str, str], tags=["interaction"])
async def interact(
    user_input: UserInput,
    request: Request,
    interaction_service: InteractionService = Depends(get_interaction_service),
) -> Dict[str, str]:
    """
    """
            user_input.user_id = "patrick"  # For backward compatibility
            logger.warning("No user_id provided, using default: 'patrick'")

        # Retrieve active persona from request state
        persona_config = request.state.active_persona

        # Extract session ID and request ID from request state if available
        session_id = str(request.state.session_id) if hasattr(request.state, "session_id") else None
        request_id = getattr(request.state, "request_id", None)

        # Delegate to the interaction service
        response_text, persona_name = await interaction_service.process_interaction(
            user_id=user_input.user_id,
            user_message=user_input.text,
            persona_config=persona_config,
            session_id=session_id,
            request_id=request_id,
        )

        # Return response
        return {"response": response_text, "persona": persona_name}

    except Exception:


        pass
        logger.error(
            "Error processing interaction",
            exc_info=True,
            extra={
                "error_message": str(e),
                "endpoint_path": "interaction_endpoint_placeholder",
            },
        )
        logger.warning("Interaction processing failure may impact user experience or conversation continuity.")
        raise HTTPException(status_code=500, detail=f"Failed to process interaction: {str(e)}")
