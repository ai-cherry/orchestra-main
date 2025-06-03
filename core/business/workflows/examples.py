"""
"""
    """Fetch user context from memory."""
    user_id = context.inputs.get("user_id")
    if not user_id:
        raise ValueError("user_id is required")

    memory_service = get_memory_service()

    # Fetch recent interactions
    recent_interactions = await memory_service.search(
        query=f"user:{user_id}", limit=10, metadata_filter={"type": "interaction"}
    )

    # Fetch user preferences
    preferences = await memory_service.get(f"preferences:{user_id}")

    return {"recent_interactions": recent_interactions, "preferences": preferences}

async def analyze_intent(context: WorkflowContext) -> str:
    """Analyze user intent from input."""
    user_input = context.inputs.get("user_input")
    if not user_input:
        raise ValueError("user_input is required")

    llm_service = get_llm_service()

    # Create intent analysis prompt
    prompt = f"""
Return only the intent category."""
    context.set_output("intent", intent)

    return intent

async def generate_response(context: WorkflowContext) -> str:
    """Generate response based on intent and context."""
    user_input = context.inputs.get("user_input")
    intent = context.get_task_output("analyze_intent")
    user_context = context.get_task_output("fetch_context")

    llm_service = get_llm_service()
    persona_manager = get_persona_manager()

    # Get persona based on intent
    persona_id = None
    if intent == "question":
        persona_id = "helpful_assistant"
    elif intent == "command":
        persona_id = "task_executor"
    else:
        persona_id = "conversationalist"

    # Build context-aware prompt
    prompt = f"""
Please provide an appropriate response."""
    """Store the interaction in memory."""
    user_id = context.inputs.get("user_id")
    user_input = context.inputs.get("user_input")
    response = context.get_task_output("generate_response")
    intent = context.get_task_output("analyze_intent")

    memory_service = get_memory_service()

    # Store interaction
    await memory_service.store(
        key=f"interaction:{user_id}:{context.workflow_id}",
        value={
            "user_id": user_id,
            "input": user_input,
            "response": response,
            "intent": intent,
            "workflow_id": str(context.workflow_id),
        },
        metadata={"type": "interaction", "user_id": user_id, "intent": intent},
    )

    logger.info(f"Stored interaction for user {user_id}")

async def summarize_document(context: WorkflowContext) -> str:
    """Summarize a document."""
    document = context.inputs.get("document")
    if not document:
        raise ValueError("document is required")

    llm_service = get_llm_service()

    request = LLMRequest(
        prompt=f"Please provide a concise summary of the following document:\n\n{document}",
        max_tokens=500,
        temperature=0.5,
    )

    response = await llm_service.complete(request)
    return response.text

async def extract_entities(context: WorkflowContext) -> List[Dict[str, str]]:
    """Extract entities from document."""
    document = context.inputs.get("document")
    if not document:
        raise ValueError("document is required")

    llm_service = get_llm_service()

    request = LLMRequest(
        prompt=f"""
Return as a JSON list with format: [{{"type": "PERSON|ORG|LOCATION", "name": "entity name"}}]"""
        logger.error(f"Failed to parse entities: {response.text}")
        return []

async def generate_keywords(context: WorkflowContext) -> List[str]:
    """Generate keywords from document."""
    document = context.inputs.get("document")
    summary = context.get_task_output("summarize")

    llm_service = get_llm_service()

    request = LLMRequest(
        prompt=f"""
Return keywords as a comma-separated list."""
    keywords = [k.strip() for k in response.text.split(",")]

    return keywords

async def store_analysis(context: WorkflowContext) -> None:
    """Store document analysis results."""
    document_id = context.inputs.get("document_id")
    summary = context.get_task_output("summarize")
    entities = context.get_task_output("extract_entities")
    keywords = context.get_task_output("generate_keywords")

    memory_service = get_memory_service()

    # Store analysis
    await memory_service.store(
        key=f"analysis:{document_id}",
        value={
            "document_id": document_id,
            "summary": summary,
            "entities": entities,
            "keywords": keywords,
            "workflow_id": str(context.workflow_id),
        },
        metadata={"type": "document_analysis", "document_id": document_id},
    )

    # Set outputs
    context.set_output("summary", summary)
    context.set_output("entities", entities)
    context.set_output("keywords", keywords)

def create_conversation_workflow() -> Workflow:
    """Create a conversation handling workflow."""
        name="conversation_workflow",
        description="Handle user conversations with context awareness",
    )

    # Add tasks
    workflow.add_task(
        task_id="fetch_context",
        name="Fetch User Context",
        handler=fetch_user_context,
        priority=TaskPriority.HIGH,
    )

    workflow.add_task(
        task_id="analyze_intent",
        name="Analyze User Intent",
        handler=analyze_intent,
        priority=TaskPriority.HIGH,
    )

    workflow.add_task(
        task_id="generate_response",
        name="Generate Response",
        handler=generate_response,
        dependencies=["fetch_context", "analyze_intent"],
        priority=TaskPriority.NORMAL,
        timeout_seconds=30,
        retry_count=2,
    )

    workflow.add_task(
        task_id="store_interaction",
        name="Store Interaction",
        handler=store_interaction,
        dependencies=["generate_response"],
        priority=TaskPriority.LOW,
    )

    return workflow

def create_document_analysis_workflow() -> Workflow:
    """Create a document analysis workflow."""
        name="document_analysis",
        description="Analyze documents to extract summary, entities, and keywords",
    )

    # Add tasks
    workflow.add_task(
        task_id="summarize",
        name="Summarize Document",
        handler=summarize_document,
        priority=TaskPriority.HIGH,
        timeout_seconds=60,
    )

    workflow.add_task(
        task_id="extract_entities",
        name="Extract Entities",
        handler=extract_entities,
        priority=TaskPriority.NORMAL,
        timeout_seconds=45,
    )

    workflow.add_task(
        task_id="generate_keywords",
        name="Generate Keywords",
        handler=generate_keywords,
        dependencies=["summarize"],
        priority=TaskPriority.NORMAL,
        timeout_seconds=30,
    )

    workflow.add_task(
        task_id="store_analysis",
        name="Store Analysis Results",
        handler=store_analysis,
        dependencies=["summarize", "extract_entities", "generate_keywords"],
        priority=TaskPriority.LOW,
    )

    return workflow

def register_example_workflows() -> None:
    """Register all example workflows with the engine."""
    logger.info("Registered example workflows")
