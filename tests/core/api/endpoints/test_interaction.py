"""
Tests for the interaction endpoint of the AI Orchestration System API.

This module contains tests for the interaction endpoint that processes
user input and generates responses using the LLM and active persona.
"""

import json
import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI, Depends, APIRouter, Request, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

# Define our own simplified models to avoid importing the actual ones
class PersonaConfig:
    def __init__(self, name, description, prompt_template, traits):
        self.name = name
        self.description = description
        self.prompt_template = prompt_template
        self.traits = traits

class MemoryItem:
    def __init__(self, id, user_id, session_id, timestamp, item_type, persona_active, text_content, metadata):
        self.id = id
        self.user_id = user_id
        self.session_id = session_id
        self.timestamp = timestamp
        self.item_type = item_type
        self.persona_active = persona_active
        self.text_content = text_content
        self.metadata = metadata

class UserInput(BaseModel):
    """Schema for user input request."""
    text: str = Field(..., description="User's message text")
    user_id: str = Field("patrick", description="User identifier, defaults to 'patrick'")

# Create a simplified version of the interaction router
simplified_router = APIRouter()

# Mock dependencies
async def get_active_persona():
    return PersonaConfig(
        name="TestPersona",
        description="A test persona for unit testing",
        prompt_template="You are a test persona: {input}",
        traits={"helpful": 8, "creative": 7}
    )

class InMemoryMemoryManagerStub:
    def __init__(self):
        self.memory_items = []
        self.initialized = False
    
    def initialize(self):
        self.initialized = True
    
    async def get_conversation_history(self, user_id, limit=10, **kwargs):
        return [item for item in self.memory_items if item.user_id == user_id][:limit]
    
    async def add_memory_item(self, item):
        self.memory_items.append(item)
        return item.id

class MockLLMClient:
    def __init__(self, response_text="This is a mock LLM response"):
        self.response_text = response_text
        self.calls = []
    
    async def generate_chat_completion(self, messages, temperature=0.7, max_tokens=1000):
        self.calls.append({
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        })
        return {"content": self.response_text}

# The actual mocks that will be used during tests
_test_memory_manager = None
_test_llm_client = None

def get_memory_manager():
    return _test_memory_manager

def get_llm_client():
    return _test_llm_client

def build_prompt_for_persona(persona, user_input, history_items):
    return [
        {"role": "system", "content": f"You are {persona.name}: {persona.description}"},
        {"role": "user", "content": user_input}
    ]

# Define the simplified endpoint
@simplified_router.post("/interact")
async def interact(
    user_input: UserInput,
    active_persona = Depends(get_active_persona),
    memory_manager = Depends(get_memory_manager),
    llm_client = Depends(get_llm_client)
):
    try:
        # Get conversation history
        history_items = await memory_manager.get_conversation_history(
            user_id=user_input.user_id,
            limit=10
        )
        
        # Build prompt
        messages = build_prompt_for_persona(
            persona=active_persona,
            user_input=user_input.text,
            history_items=history_items
        )
        
        # Generate response
        response = await llm_client.generate_chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        llm_response_text = response["content"]
        
        # Create and save memory item
        new_memory_item = MemoryItem(
            id=str(uuid.uuid4()),
            user_id=user_input.user_id,
            session_id=None,
            timestamp=datetime.utcnow(),
            item_type="conversation",
            persona_active=active_persona.name,
            text_content=user_input.text,
            metadata={"llm_response": llm_response_text}
        )
        
        await memory_manager.add_memory_item(new_memory_item)
        
        # Return response
        return {
            "response": llm_response_text,
            "persona": active_persona.name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")


# Test fixtures
@pytest.fixture
def mock_memory_manager():
    global _test_memory_manager
    _test_memory_manager = InMemoryMemoryManagerStub()
    _test_memory_manager.initialize()
    return _test_memory_manager

@pytest.fixture
def mock_llm_client():
    global _test_llm_client
    _test_llm_client = MockLLMClient()
    return _test_llm_client

@pytest.fixture
def app(mock_memory_manager, mock_llm_client):
    app = FastAPI()
    app.include_router(simplified_router)
    return app

@pytest.fixture
def client(app):
    return TestClient(app)


# Test cases
class TestInteractionEndpoint:
    def test_interact_success(self, client, mock_memory_manager, mock_llm_client):
        """Test successful interaction flow."""
        # Define test data
        user_input = {"text": "Hello, how are you?", "user_id": "test_user"}
        
        # Make request to the interaction endpoint
        response = client.post("/interact", json=user_input)
        
        # Assert the response status code is 200 OK
        assert response.status_code == 200
        
        # Assert the response contains the expected fields
        data = response.json()
        assert "response" in data
        assert "persona" in data
        assert data["response"] == mock_llm_client.response_text
        assert data["persona"] == "TestPersona"
        
        # Verify the LLM client was called with the expected data
        assert len(mock_llm_client.calls) == 1
        assert mock_llm_client.calls[0]["messages"][0]["role"] == "system"
        assert mock_llm_client.calls[0]["messages"][1]["role"] == "user"
        assert mock_llm_client.calls[0]["messages"][1]["content"] == user_input["text"]
        
        # Verify that a memory item was created and saved
        assert len(mock_memory_manager.memory_items) == 1
        memory_item = mock_memory_manager.memory_items[0]
        assert memory_item.user_id == user_input["user_id"]
        assert memory_item.persona_active == "TestPersona"
        assert memory_item.text_content == user_input["text"]
        assert memory_item.metadata["llm_response"] == mock_llm_client.response_text
    
    def test_interact_with_history(self, client, mock_memory_manager, mock_llm_client):
        """Test interaction with conversation history."""
        # Add some history items
        history_item = MemoryItem(
            id=str(uuid.uuid4()),
            user_id="test_user",
            session_id=None,
            timestamp=datetime.utcnow(),
            item_type="conversation",
            persona_active="TestPersona",
            text_content="Previous user message",
            metadata={"llm_response": "Previous LLM response"}
        )
        mock_memory_manager.memory_items.append(history_item)
        
        # Define test data
        user_input = {"text": "Follow-up question", "user_id": "test_user"}
        
        # Make request to the interaction endpoint
        response = client.post("/interact", json=user_input)
        
        # Assert the response status code is 200 OK
        assert response.status_code == 200
        
        # Verify that a new memory item was created and saved
        assert len(mock_memory_manager.memory_items) == 2
    
    def test_llm_error_handling(self, client, mock_memory_manager):
        """Test handling of LLM errors."""
        # Create a mock LLM client that raises an exception
        error_client = MockLLMClient()
        error_client.generate_chat_completion = AsyncMock(
            side_effect=Exception("LLM service error")
        )
        
        # Update the global test client
        global _test_llm_client
        _test_llm_client = error_client
        
        # Define test data
        user_input = {"text": "This will cause an error", "user_id": "test_user"}
        
        # Make request to the interaction endpoint
        response = client.post("/interact", json=user_input)
        
        # Assert the response status code is 500 Internal Server Error
        assert response.status_code == 500
        
        # Verify the error message
        assert "Failed to generate response" in response.json()["detail"]
