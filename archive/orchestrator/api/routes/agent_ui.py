"""
Agent UI API routes for AI Orchestra.

This module provides FastAPI routes for managing agents in the AI Orchestra system,
including creating, configuring, and monitoring agents.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from core.orchestrator.src.agents.agent_registry import (
    delete_agent,
    get_agent_by_id,
    get_all_agents,
    register_agent,
    update_agent,
)
from packages.shared.src.memory.factory import MemoryManagerFactory
from packages.shared.src.memory.memory_interface import MemoryInterface

# Set up logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/agents", tags=["agents"])


# Models
class ToolConfig(BaseModel):
    """Configuration for an agent tool."""

    name: str
    path: str
    config: Optional[Dict[str, Any]] = None


class MemoryConfig(BaseModel):
    """Memory configuration for an agent."""

    memory_type: str = "pgvector"
    ttl: Optional[int] = None
    namespace: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class AgentConfig(BaseModel):
    """Configuration for creating or updating an agent."""

    name: str
    description: str
    tools: List[Union[str, ToolConfig]]
    model: str
    temperature: float = Field(0.7, ge=0, le=1.0)
    system_prompt: Optional[str] = None
    memory_config: Optional[MemoryConfig] = None
    wrapper_type: str = "phidata"
    phidata_agent_class: str = "agno.agent.Agent"
    role: Optional[str] = None
    instructions: Optional[List[str]] = None


class AgentResponse(BaseModel):
    """Response model for agent operations."""

    id: str
    name: str
    description: str
    status: str = "active"


class AgentListResponse(BaseModel):
    """Response model for listing agents."""

    agents: List[AgentResponse]
    total: int


class ConversationMessage(BaseModel):
    """A message in a conversation."""

    role: str
    content: str
    timestamp: str


class Conversation(BaseModel):
    """A conversation with an agent."""

    id: str
    agent_id: str
    messages: List[ConversationMessage]
    created_at: str
    updated_at: str


class ConversationListResponse(BaseModel):
    """Response model for listing conversations."""

    conversations: List[Conversation]
    total: int


# Dependency for memory manager
async def get_memory_manager() -> MemoryInterface:
    """Get a memory manager instance."""
    memory_manager = await MemoryManagerFactory.create_memory_manager()
    try:
        yield memory_manager
    finally:
        await memory_manager.close()


# Routes
@router.get("/", response_model=AgentListResponse)
async def list_agents(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100)):
    """
    List all available agents.

    Args:
        skip: Number of agents to skip
        limit: Maximum number of agents to return

    Returns:
        List of agents
    """
    try:
        agents = await get_all_agents()
        total = len(agents)

        # Apply pagination
        paginated_agents = agents[skip : skip + limit]

        # Convert to response model
        agent_responses = [
            AgentResponse(
                id=agent.id,
                name=agent.name,
                description=agent.description,
                status="active",
            )
            for agent in paginated_agents
        ]

        return AgentListResponse(agents=agent_responses, total=total)
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list agents: {str(e)}",
        )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """
    Get an agent by ID.

    Args:
        agent_id: The ID of the agent to retrieve

    Returns:
        The agent details

    Raises:
        HTTPException: If the agent is not found
    """
    agent = await get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )

    return AgentResponse(
        id=agent.id, name=agent.name, description=agent.description, status="active"
    )


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(config: AgentConfig):
    """
    Create a new agent with the given configuration.

    Args:
        config: The agent configuration

    Returns:
        The created agent details

    Raises:
        HTTPException: If the agent creation fails
    """
    try:
        # Generate a unique ID for the agent
        agent_id = str(uuid4())

        # Convert tools to the expected format
        tools = []
        for tool in config.tools:
            if isinstance(tool, str):
                tools.append({"name": tool})
            else:
                tools.append(
                    {
                        "name": tool.name,
                        "path": tool.path,
                        **({"config": tool.config} if tool.config else {}),
                    }
                )

        # Create memory config
        memory_config = None
        if config.memory_config:
            memory_config = {
                "memory_type": config.memory_config.memory_type,
                **(
                    {"ttl": config.memory_config.ttl}
                    if config.memory_config.ttl
                    else {}
                ),
                **(
                    {"namespace": config.memory_config.namespace}
                    if config.memory_config.namespace
                    else {}
                ),
                **(
                    {"config": config.memory_config.config}
                    if config.memory_config.config
                    else {}
                ),
            }

        # Register the agent
        await register_agent(
            agent_id=agent_id,
            name=config.name,
            description=config.description,
            tools=tools,
            model=config.model,
            temperature=config.temperature,
            system_prompt=config.system_prompt,
            memory_config=memory_config,
            wrapper_type=config.wrapper_type,
            phidata_agent_class=config.phidata_agent_class,
            role=config.role,
            instructions=config.instructions,
        )

        return AgentResponse(
            id=agent_id,
            name=config.name,
            description=config.description,
            status="active",
        )
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create agent: {str(e)}",
        )


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent_config(agent_id: str, config: AgentConfig):
    """
    Update an existing agent's configuration.

    Args:
        agent_id: The ID of the agent to update
        config: The new agent configuration

    Returns:
        The updated agent details

    Raises:
        HTTPException: If the agent is not found or the update fails
    """
    # Check if agent exists
    agent = await get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )

    try:
        # Convert tools to the expected format
        tools = []
        for tool in config.tools:
            if isinstance(tool, str):
                tools.append({"name": tool})
            else:
                tools.append(
                    {
                        "name": tool.name,
                        "path": tool.path,
                        **({"config": tool.config} if tool.config else {}),
                    }
                )

        # Create memory config
        memory_config = None
        if config.memory_config:
            memory_config = {
                "memory_type": config.memory_config.memory_type,
                **(
                    {"ttl": config.memory_config.ttl}
                    if config.memory_config.ttl
                    else {}
                ),
                **(
                    {"namespace": config.memory_config.namespace}
                    if config.memory_config.namespace
                    else {}
                ),
                **(
                    {"config": config.memory_config.config}
                    if config.memory_config.config
                    else {}
                ),
            }

        # Update the agent
        await update_agent(
            agent_id=agent_id,
            name=config.name,
            description=config.description,
            tools=tools,
            model=config.model,
            temperature=config.temperature,
            system_prompt=config.system_prompt,
            memory_config=memory_config,
            wrapper_type=config.wrapper_type,
            phidata_agent_class=config.phidata_agent_class,
            role=config.role,
            instructions=config.instructions,
        )

        return AgentResponse(
            id=agent_id,
            name=config.name,
            description=config.description,
            status="active",
        )
    except Exception as e:
        logger.error(f"Failed to update agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update agent: {str(e)}",
        )


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent_by_id(agent_id: str):
    """
    Delete an agent by ID.

    Args:
        agent_id: The ID of the agent to delete

    Raises:
        HTTPException: If the agent is not found or the deletion fails
    """
    # Check if agent exists
    agent = await get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )

    try:
        # Delete the agent
        await delete_agent(agent_id)
    except Exception as e:
        logger.error(f"Failed to delete agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete agent: {str(e)}",
        )


@router.get("/{agent_id}/conversations", response_model=ConversationListResponse)
async def get_agent_conversations(
    agent_id: str,
    memory_manager: MemoryInterface = Depends(get_memory_manager),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    """
    Get recent conversations for an agent.

    Args:
        agent_id: The ID of the agent
        memory_manager: Memory manager instance
        skip: Number of conversations to skip
        limit: Maximum number of conversations to return

    Returns:
        List of conversations

    Raises:
        HTTPException: If the agent is not found or the retrieval fails
    """
    # Check if agent exists
    agent = await get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )

    try:
        # Get conversation history
        memory_items = await memory_manager.get_conversation_history(
            user_id="system", limit=limit + skip, filters={"agent_id": agent_id}
        )

        # Apply pagination
        paginated_items = memory_items[skip : skip + limit]

        # Group by conversation ID
        conversations_map = {}
        for item in paginated_items:
            conversation_id = item.metadata.get("conversation_id", "default")
            if conversation_id not in conversations_map:
                conversations_map[conversation_id] = {
                    "id": conversation_id,
                    "agent_id": agent_id,
                    "messages": [],
                    "created_at": item.created_at.isoformat(),
                    "updated_at": item.created_at.isoformat(),
                }

            # Add message
            conversations_map[conversation_id]["messages"].append(
                {
                    "role": item.metadata.get("role", "system"),
                    "content": item.content,
                    "timestamp": item.created_at.isoformat(),
                }
            )

            # Update conversation timestamp
            if (
                item.created_at.isoformat()
                > conversations_map[conversation_id]["updated_at"]
            ):
                conversations_map[conversation_id][
                    "updated_at"
                ] = item.created_at.isoformat()

        # Convert to list
        conversations = list(conversations_map.values())

        return ConversationListResponse(
            conversations=conversations, total=len(memory_items)
        )
    except Exception as e:
        logger.error(f"Failed to get agent conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent conversations: {str(e)}",
        )


@router.post("/{agent_id}/test", response_model=Dict[str, Any])
async def test_agent(agent_id: str, input_data: Dict[str, Any]):
    """
    Test an agent with a sample input.

    Args:
        agent_id: The ID of the agent to test
        input_data: The input data for testing

    Returns:
        The agent's response

    Raises:
        HTTPException: If the agent is not found or the test fails
    """
    # Check if agent exists
    agent = await get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found",
        )

    try:
        # Get input text
        input_text = input_data.get("text", "")
        if not input_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Input text is required"
            )

        # Process input
        response = await agent.process(input_text)

        return {
            "agent_id": agent_id,
            "input": input_text,
            "response": response,
            "status": "success",
        }
    except Exception as e:
        logger.error(f"Failed to test agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test agent: {str(e)}",
        )
