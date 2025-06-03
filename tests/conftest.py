"""
"""
    """
    """
        id="test-persona",
        name="Cherry",
        description="A helpful AI assistant.",
        system_prompt="You are a helpful AI assistant",
    )

    # Patch the request state in test environment to include active_persona
    with patch(
        "starlette.requests.Request.state",
        new_callable=lambda: type("MockState", (), {"active_persona": default_persona, "_state": {}})(),
    ):
        yield default_persona

@pytest.fixture
def mock_llm_client():
    """
    """
    mock_client.generate_response.return_value = "This is a mock response from the LLM."

    # Mock generate_chat_completion (legacy method)
    mock_client.generate_chat_completion.return_value = {"choices": [{"message": {"content": "Mock response"}}]}

    return mock_client
