"""
"""
router = APIRouter(prefix="/conversation", tags=["conversation"])

@router.post("/chat", response_model=ConversationResponse)
async def chat(request: ConversationRequest) -> ConversationResponse:
    """
    """
            workflow_name="conversation_workflow",
            inputs={
                "user_id": request.user_id,
                "user_input": request.message,
                "context": request.context or {},
                "persona_id": request.persona_id,
            },
        )

        # Extract results
        response_text = context.outputs.get("response", "I'm sorry, I couldn't generate a response.")
        intent = context.outputs.get("intent")

        return ConversationResponse(
            success=True,
            response=response_text,
            intent=intent,
            persona_used=request.persona_id,
            conversation_id=str(context.workflow_id),
        )

    except Exception:


        pass
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agent-chat", response_model=ConversationResponse)
async def agent_chat(request: ConversationRequest) -> ConversationResponse:
    """
    """
            raise HTTPException(status_code=503, detail="No conversational agents available")

        # Use the first available agent
        agent = conv_agents[0]

        # Send message to agent
        from core.services.agents.base import AgentMessage

        message = AgentMessage(
            sender_id=request.user_id,
            content=request.message,
            metadata={
                "type": "conversation",
                "context": request.context,
                "persona_id": request.persona_id,
            },
        )

        # Process message
        response_message = await agent.process_message(message)

        if not response_message:
            raise HTTPException(status_code=500, detail="Agent did not return a response")

        return ConversationResponse(
            success=True,
            response=response_message.content,
            persona_used=request.persona_id,
            conversation_id=str(message.id),
        )

    except Exception:


        pass
        raise
    except Exception:

        pass
        logger.error(f"Error in agent chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{user_id}")
async def get_conversation_history(user_id: str, limit: int = 10) -> dict:
    """
    """
            query=f"user:{user_id}",
            limit=limit,
            metadata_filter={"type": "interaction"},
        )

        return {
            "success": True,
            "user_id": user_id,
            "conversations": conversations,
            "count": len(conversations),
        }

    except Exception:


        pass
        logger.error(f"Error getting conversation history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
