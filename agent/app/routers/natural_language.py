"""
"""
router = APIRouter(prefix="/api/nl", tags=["natural_language"])

# Initialize NLP components
nlp_processor = NaturalLanguageProcessor()
intent_classifier = IntentClassifier()
voice_transcriber = VoiceTranscriber()
response_generator = ResponseGenerator()

class TextCommand(BaseModel):
    """Text command from user"""
    """Voice command from user"""
    format: str = "webm"
    context: Optional[Dict[str, Any]] = None
    domain: Optional[str] = None  # No default domain

class NLResponse(BaseModel):
    """Natural language response"""
@router.post("/text", response_model=NLResponse)
async def process_text_command(command: TextCommand, api_key: str = Depends(verify_api_key)) -> NLResponse:
    """Process natural language text command"""
    intent = await intent_classifier.classify(command.text, command.domain or "general")

    # Route to appropriate handler
    if intent.category == "agent_control":
        result = await handle_agent_command(intent, command.context)
    elif intent.category == "query":
        result = await handle_query(intent, command.context)
    elif intent.category == "workflow":
        result = await handle_workflow_command(intent, command.context)
    else:
        result = await handle_general_command(intent, command.context)

    # Generate natural response
    response_text = await response_generator.generate(intent=intent, result=result, style="conversational")

    return NLResponse(
        text=response_text,
        actions_taken=result.get("actions", []),
        suggestions=result.get("suggestions", []),
        domain=command.domain or "general",
    )

@router.post("/voice", response_model=NLResponse)
async def process_voice_command(command: VoiceCommand, api_key: str = Depends(verify_api_key)) -> NLResponse:
    """Process natural language voice command"""
@router.websocket("/stream")
async def websocket_nl_interface(websocket: WebSocket, api_key: str = Depends(verify_api_key)):
    """WebSocket interface for real-time natural language interaction"""
            if data.get("type") == "text":
                command = TextCommand(**data.get("payload", {}))
                response = await process_text_command(command, api_key)
            elif data.get("type") == "voice":
                command = VoiceCommand(**data.get("payload", {}))
                response = await process_voice_command(command, api_key)
            else:
                response = {"error": "Unknown command type"}

            # Send response
            await websocket.send_json(
                {"type": "response", "payload": response.dict() if hasattr(response, "dict") else response}
            )

    except Exception:


        pass
        await websocket.send_json({"type": "error", "payload": {"error": str(e)}})
    finally:
        await websocket.close()

# Handler functions
async def handle_agent_command(intent, context):
    """Handle agent control commands"""
    # Example: "Start the data analyzer agent"
    # Example: "Stop all agents"
    # Example: "Show me agent status"
    agents = await get_all_agents()

    if intent.action == "start":
        # Start specific agent
        agent_id = intent.entities.get("agent_id", "sys-001")
        result = await run_agent_task(agent_id, "Start requested via NL interface")
        return {"actions": [{"type": "agent_started", "agent_id": agent_id}], "data": result}
    elif intent.action == "status":
        return {"actions": [{"type": "status_check"}], "data": {"agents": agents}}

    return {"actions": [], "data": {}}

async def handle_query(intent, context):
    """Handle information queries"""
    # Example: "What's the status of X?"
    # Example: "Show me Y"
    # This will integrate with your data sources
    return {
        "actions": [{"type": "query", "query": intent.query}],
        "data": {"placeholder": "Query results will appear here once data sources are connected"},
    }

async def handle_workflow_command(intent, context):
    """Handle workflow commands"""
    # Example: "Process all X"
    # Example: "Generate Y report"
    return {
        "actions": [{"type": "workflow", "name": intent.workflow_name}],
        "data": {"status": "Workflow initiated (placeholder)"},
    }

async def handle_general_command(intent, context):
    """Handle general commands"""
    return {"actions": [], "data": {"message": "Command understood but not yet implemented"}}
