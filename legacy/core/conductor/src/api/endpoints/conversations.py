"""
"""
router = APIRouter(prefix="/conversations", tags=["conversations"])

class MessageInput(BaseModel):
    """Input model for adding a message to a conversation."""
    content: str = Field(..., min_length=1, description="Message content")
    is_user: bool = Field(
        True,
        description="Whether this is a user message (True) or system message (False)",
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata for the message")

class ConversationStartInput(BaseModel):
    """Input model for starting a conversation."""
    user_id: str = Field(..., description="User identifier")
    persona_name: Optional[str] = Field(None, description="Optional persona name to activate")

class ConversationEndInput(BaseModel):
    """Input model for ending a conversation."""
    user_id: str = Field(..., description="User identifier")

@router.post("/start", response_model=Dict[str, str])
async def start_conversation(
    input_data: ConversationStartInput,
) -> Dict[str, str]:
    """
    """
        return {"session_id": session_id, "status": "created"}
    except Exception:

        pass
        logger.error(f"Failed to start conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start conversation: {str(e)}")

@router.post("/{session_id}/end", response_model=Dict[str, str])
async def end_conversation(
    session_id: str,
    input_data: ConversationEndInput,
) -> Dict[str, str]:
    """
    """
                detail=f"Conversation not found for user {input_data.user_id}",
            )

        return {"session_id": session_id, "status": "ended"}
    except Exception:

        pass
        raise
    except Exception:

        pass
        logger.error(f"Failed to end conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to end conversation: {str(e)}")

@router.post("/{session_id}/messages", response_model=Dict[str, str])
async def add_message(
    session_id: str,
    input_data: MessageInput,
    user_id: str = Query(..., description="User identifier"),
) -> Dict[str, str]:
    """
    """
        return {"message_id": message_id, "status": "added"}
    except Exception:

        pass
        logger.error(f"Failed to add message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to add message: {str(e)}")

@router.get("/{session_id}/history", response_model=List[Dict[str, Any]])
async def get_conversation_history(
    session_id: str,
    user_id: str = Query(..., description="User identifier"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of messages to retrieve"),
    persona_name: Optional[str] = Query(None, description="Filter by persona name"),
) -> List[Dict[str, Any]]:
    """
    """
        logger.error(f"Failed to retrieve conversation history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve conversation history: {str(e)}")

@router.get("/active", response_model=Dict[str, Any])
async def get_active_conversation(
    user_id: str = Query(..., description="User identifier"),
) -> Dict[str, Any]:
    """
    """
                "user_id": conversation.user_id,
                "session_id": conversation.session_id,
                "persona_active": conversation.persona_active,
                "start_time": conversation.start_time.isoformat(),
                "last_activity": conversation.last_activity.isoformat(),
                "turn_count": conversation.turn_count,
                "status": "active",
            }
        else:
            return {"status": "no_active_conversation"}
    except Exception:

        pass
        logger.error(f"Failed to get active conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get active conversation: {str(e)}")
