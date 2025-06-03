"""
"""
    """Check if the context has query results."""
    return "query_result" in context and context["query_result"] is not None

def has_error(context: Dict[str, Any]) -> bool:
    """Check if the context has an error."""
    return "error" in context and context["error"] is not None

def is_approved(context: Dict[str, Any]) -> bool:
    """Check if the workflow is approved."""
    return context.get("approved", False)

# Example action functions
async def query_knowledge_base(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    """
    query = context.get("query", "")

    # In a real implementation, this would query an actual knowledge base
    # For this example, we'll simulate a result
    result = f"Result for query: {query}"

    return {"query_result": result}

async def generate_response(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    """
    query_result = context.get("query_result", "")

    # In a real implementation, this would use an LLM to generate a response
    # For this example, we'll create a simple response
    response = f"Based on the query result: {query_result}, here is the answer..."

    return {"response": response}

async def format_response(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    """
    response = context.get("response", "")

    # Format the response
    formatted = f"FORMATTED: {response}"

    return {"formatted_response": formatted}

# Define example workflows
def create_query_workflow() -> WorkflowDefinition:
    """
    """
        workflow_id="query_workflow",
        name="Query Processing Workflow",
        description="Process a query through knowledge retrieval and response generation",
        states=[
            WorkflowState.CREATED,
            WorkflowState.RUNNING,
            WorkflowState.WAITING,
            WorkflowState.COMPLETED,
            WorkflowState.FAILED,
        ],
        transitions=[
            # From CREATED to RUNNING
            WorkflowTransition(from_state=WorkflowState.CREATED, to_state=WorkflowState.RUNNING),
            # From RUNNING to WAITING after querying knowledge base
            WorkflowTransition(
                from_state=WorkflowState.RUNNING,
                to_state=WorkflowState.WAITING,
                action_name="query_knowledge_base",
            ),
            # From WAITING to RUNNING when approved
            WorkflowTransition(
                from_state=WorkflowState.WAITING,
                to_state=WorkflowState.RUNNING,
                condition_name="is_approved",
            ),
            # From RUNNING to COMPLETED with response generation and formatting
            WorkflowTransition(
                from_state=WorkflowState.RUNNING,
                to_state=WorkflowState.COMPLETED,
                action_name="generate_and_format_response",
            ),
            # Error handling
            WorkflowTransition(
                from_state=WorkflowState.RUNNING,
                to_state=WorkflowState.FAILED,
                condition_name="has_error",
            ),
            WorkflowTransition(
                from_state=WorkflowState.WAITING,
                to_state=WorkflowState.FAILED,
                condition_name="has_error",
            ),
        ],
        metadata={"category": "query_processing", "version": "1.0"},
    )

def create_multi_agent_workflow() -> WorkflowDefinition:
    """
    """
        workflow_id="multi_agent_workflow",
        name="Multi-Agent Collaboration Workflow",
        description="Coordinate multiple agents to solve a complex task",
        states=[
            WorkflowState.CREATED,
            WorkflowState.RUNNING,
            WorkflowState.WAITING,
            WorkflowState.COMPLETED,
            WorkflowState.FAILED,
        ],
        transitions=[
            # From CREATED to RUNNING
            WorkflowTransition(from_state=WorkflowState.CREATED, to_state=WorkflowState.RUNNING),
            # From RUNNING to WAITING after task assignment
            WorkflowTransition(
                from_state=WorkflowState.RUNNING,
                to_state=WorkflowState.WAITING,
                action_name="assign_tasks_to_agents",
            ),
            # From WAITING to RUNNING when all agents complete
            WorkflowTransition(
                from_state=WorkflowState.WAITING,
                to_state=WorkflowState.RUNNING,
                condition_name="all_agents_complete",
            ),
            # From RUNNING to COMPLETED after aggregating results
            WorkflowTransition(
                from_state=WorkflowState.RUNNING,
                to_state=WorkflowState.COMPLETED,
                action_name="aggregate_agent_results",
            ),
            # Error handling
            WorkflowTransition(
                from_state=WorkflowState.RUNNING,
                to_state=WorkflowState.FAILED,
                condition_name="has_error",
            ),
            WorkflowTransition(
                from_state=WorkflowState.WAITING,
                to_state=WorkflowState.FAILED,
                condition_name="has_error",
            ),
        ],
        metadata={"category": "multi_agent", "version": "1.0"},
    )

async def register_example_workflows():
    """Register example workflows and their actions/conditions."""
    engine.register_condition("has_query_result", has_query_result)
    engine.register_condition("has_error", has_error)
    engine.register_condition("is_approved", is_approved)

    # Register actions
    engine.register_action("query_knowledge_base", query_knowledge_base)
    engine.register_action("generate_response", generate_response)
    engine.register_action("format_response", format_response)

    # Register combined actions
    async def generate_and_format_response(context: Dict[str, Any]) -> Dict[str, Any]:
        """Combined action for response generation and formatting."""
    engine.register_action("generate_and_format_response", generate_and_format_response)

    # Register workflows
    engine.register_workflow(create_query_workflow())
    engine.register_workflow(create_multi_agent_workflow())

    logger.info("Example workflows registered")
