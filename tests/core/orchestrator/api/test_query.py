"""
"""
    """Create a test client for the FastAPI app."""
@patch("core.orchestrator.src.agents.retriever_agent.RetrieverAgent.retrieve")
def test_api_query_success(mock_retrieve, client):
    """
    """
    mock_retrieve.return_value = "Mocked retriever response"

    # Define test query
    test_query = {"query": "test query", "persona_id": "test_persona"}

    # Make request to the endpoint
    response = client.post("/api/query", json=test_query)

    # Assert response status code
    assert response.status_code == 200

    # Assert mock was called with correct parameters
    mock_retrieve.assert_called_once()

    # Assert response contains expected data
    response_data = response.json()
    assert "result" in response_data
    assert response_data["result"] == "Mocked retriever response"

@patch("core.orchestrator.src.agents.retriever_agent.RetrieverAgent.retrieve")
def test_api_query_with_documents(mock_retrieve, client):
    """
    """
        {"id": "doc1", "content": "This is document 1", "metadata": {"source": "test_source_1", "relevance": 0.95}},
        {"id": "doc2", "content": "This is document 2", "metadata": {"source": "test_source_2", "relevance": 0.85}},
    ]

    mock_response = {"answer": "Mocked answer based on retrieved documents", "documents": mock_documents}

    mock_retrieve.return_value = mock_response

    # Define test query with additional parameters
    test_query = {
        "query": "test query with documents",
        "persona_id": "test_persona",
        "max_documents": 2,
        "threshold": 0.8,
    }

    # Make request to the endpoint
    response = client.post("/api/query", json=test_query)

    # Assert response status code
    assert response.status_code == 200

    # Assert mock was called with correct parameters
    mock_retrieve.assert_called_once()

    # Assert response contains expected data
    response_data = response.json()
    assert "result" in response_data
    assert "documents" in response_data
    assert len(response_data["documents"]) == 2
    assert response_data["documents"][0]["id"] == "doc1"
    assert response_data["documents"][1]["id"] == "doc2"

@patch("core.orchestrator.src.agents.retriever_agent.RetrieverAgent.retrieve")
def test_api_query_error_handling(mock_retrieve, client):
    """
    """
    mock_retrieve.side_effect = Exception("Retrieval error")

    # Define test query
    test_query = {"query": "test query that causes error", "persona_id": "test_persona"}

    # Make request to the endpoint
    response = client.post("/api/query", json=test_query)

    # Assert response status code indicates error
    # (Assuming the API returns 500 for internal errors)
    assert response.status_code == 500

    # Assert response contains error information
    response_data = response.json()
    assert "error" in response_data
    assert "Retrieval error" in response_data["error"]
