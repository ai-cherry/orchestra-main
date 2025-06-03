from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Models for mocking return types if necessary
from core.orchestrator.src.llm.litellm_client import LLMEmbeddingResponse, LLMUsage

# Import the FastAPI app instance
from core.orchestrator.src.main import app

# Test client for the FastAPI app
client = TestClient(app)

# --- Fixtures for common mocks ---

@pytest.fixture
def mock_memory_service():
    service = MagicMock()
    service.add_memory_item_async = AsyncMock()
    service.add_memory_items_async = AsyncMock()
    return service

@pytest.fixture
def mock_litellm_client_instance():
    client_instance = MagicMock()
    client_instance.get_embedding = AsyncMock(
        return_value=LLMEmbeddingResponse(
            model="test-embedding-model",
            embedding=[0.1] * 1536,
            usage=LLMUsage(prompt_tokens=10, total_tokens=10),
        )
    )
    return client_instance

@pytest.fixture
def mock_weaviate_adapter_instance():
    adapter_instance = MagicMock()
    adapter_instance.connect = AsyncMock()
    adapter_instance.batch_upsert = AsyncMock()
    return adapter_instance

# --- Test Cases ---

@patch("core.orchestrator.src.api.endpoints.resources.get_memory_service")
@patch("core.orchestrator.src.api.endpoints.resources.LiteLLMClient")
@patch("core.orchestrator.src.api.endpoints.resources.WeaviateAdapter")
def test_upload_csv_success(
    mock_weaviate_adapter_constructor,
    mock_litellm_client_constructor,
    mock_get_memory_service_dep,
    mock_memory_service,
    mock_litellm_client_instance,
    mock_weaviate_adapter_instance,
):
    """
    """
    csv_content = "header1,header2\nvalue1,value2\nvalue3,value4"
    file_bytes = BytesIO(csv_content.encode("utf-8"))

    response = client.post(
        "/api/resources/upload",
        files={"uploaded_file": ("test.csv", file_bytes, "text/csv")},
    )

    assert response.status_code == 200
    json_response = response.json()
    assert json_response["message"] == "File processed and ingested successfully to Firestore and Weaviate"
    assert json_response["filename"] == "test.csv"

    mock_litellm_client_instance.get_embedding.assert_called()
    assert mock_litellm_client_instance.get_embedding.call_count == 2

    if hasattr(mock_memory_service, "add_memory_items_async") and mock_memory_service.add_memory_items_async.called:
        mock_memory_service.add_memory_items_async.assert_called_once()
    else:
        assert mock_memory_service.add_memory_item_async.call_count == 2

    mock_weaviate_adapter_instance.connect.assert_called_once()
    mock_weaviate_adapter_instance.batch_upsert.assert_called_once()

@patch("core.orchestrator.src.api.endpoints.resources.get_memory_service")
@patch("core.orchestrator.src.api.endpoints.resources.LiteLLMClient")
@patch("core.orchestrator.src.api.endpoints.resources.WeaviateAdapter")
def test_upload_jsonl_success(
    mock_weaviate_adapter_constructor,
    mock_litellm_client_constructor,
    mock_get_memory_service_dep,
    mock_memory_service,
    mock_litellm_client_instance,
    mock_weaviate_adapter_instance,
):
    """
    """
    jsonl_content = '{"key": "value1", "num": 1}\n{"key": "value2", "num": 2}'
    file_bytes = BytesIO(jsonl_content.encode("utf-8"))

    response = client.post(
        "/api/resources/upload",
        files={"uploaded_file": ("test.jsonl", file_bytes, "application/json-lines")},
    )

    assert response.status_code == 200
    json_response = response.json()
    assert json_response["message"] == "File processed and ingested successfully to Firestore and Weaviate"
    assert json_response["filename"] == "test.jsonl"

    assert mock_litellm_client_instance.get_embedding.call_count == 2
    if hasattr(mock_memory_service, "add_memory_items_async") and mock_memory_service.add_memory_items_async.called:
        mock_memory_service.add_memory_items_async.assert_called_once()
    else:
        assert mock_memory_service.add_memory_item_async.call_count == 2
    mock_weaviate_adapter_instance.batch_upsert.assert_called_once()

@patch("core.orchestrator.src.api.endpoints.resources.get_memory_service")
@patch("core.orchestrator.src.api.endpoints.resources.LiteLLMClient")
@patch("core.orchestrator.src.api.endpoints.resources.WeaviateAdapter")
def test_upload_json_success(
    mock_weaviate_adapter_constructor,
    mock_litellm_client_constructor,
    mock_get_memory_service_dep,
    mock_memory_service,
    mock_litellm_client_instance,
    mock_weaviate_adapter_instance,
):
    """
    """
    json_content = '[{"key": "value1", "num": 1},{"key": "value2", "num": 2}]'
    file_bytes = BytesIO(json_content.encode("utf-8"))

    response = client.post(
        "/api/resources/upload",
        files={"uploaded_file": ("test.json", file_bytes, "application/json")},
    )

    assert response.status_code == 200
    json_response = response.json()
    assert json_response["message"] == "File processed and ingested successfully to Firestore and Weaviate"
    assert json_response["filename"] == "test.json"

    assert mock_litellm_client_instance.get_embedding.call_count == 2
    if hasattr(mock_memory_service, "add_memory_items_async") and mock_memory_service.add_memory_items_async.called:
        mock_memory_service.add_memory_items_async.assert_called_once()
    else:
        assert mock_memory_service.add_memory_item_async.call_count == 2
    mock_weaviate_adapter_instance.batch_upsert.assert_called_once()

@patch("core.orchestrator.src.api.endpoints.resources.get_memory_service")
@patch("core.orchestrator.src.api.endpoints.resources.LiteLLMClient")
@patch("core.orchestrator.src.api.endpoints.resources.WeaviateAdapter")
def test_upload_unsupported_file_type(
    mock_weaviate_adapter_constructor,
    mock_litellm_client_constructor,
    mock_get_memory_service_dep,
    mock_memory_service,
    mock_litellm_client_instance,
    mock_weaviate_adapter_instance,
):
    """
    """
    txt_content = "This is a text file."
    file_bytes = BytesIO(txt_content.encode("utf-8"))

    response = client.post(
        "/api/resources/upload",
        files={"uploaded_file": ("test.txt", file_bytes, "text/plain")},
    )

    assert response.status_code == 400
    json_response = response.json()
    assert "Unsupported file type: .txt" in json_response["detail"]

    mock_memory_service.add_memory_item_async.assert_not_called()
    mock_memory_service.add_memory_items_async.assert_not_called()
    mock_weaviate_adapter_instance.batch_upsert.assert_not_called()

@patch("core.orchestrator.src.api.endpoints.resources.get_memory_service")
@patch("core.orchestrator.src.api.endpoints.resources.LiteLLMClient")
@patch("core.orchestrator.src.api.endpoints.resources.WeaviateAdapter")
def test_upload_embedding_error(
    mock_weaviate_adapter_constructor,
    mock_litellm_client_constructor,
    mock_get_memory_service_dep,
    mock_memory_service,
    mock_litellm_client_instance,
    mock_weaviate_adapter_instance,
):
    """
    """
    mock_litellm_client_instance.get_embedding.side_effect = Exception("Embedding API Error")

    csv_content = "header1,header2\nvalue1,value2"
    file_bytes = BytesIO(csv_content.encode("utf-8"))

    response = client.post(
        "/api/resources/upload",
        files={"uploaded_file": ("test.csv", file_bytes, "text/csv")},
    )

    assert response.status_code == 500
    json_response = response.json()
    assert (
        "An unexpected error occurred" in json_response["detail"]
        or "Error processing record" in json_response["detail"]
    )

    mock_memory_service.add_memory_item_async.assert_not_called()
    mock_memory_service.add_memory_items_async.assert_not_called()
    mock_weaviate_adapter_instance.batch_upsert.assert_not_called()

@patch("core.orchestrator.src.api.endpoints.resources.get_memory_service")
@patch("core.orchestrator.src.api.endpoints.resources.LiteLLMClient")
@patch("core.orchestrator.src.api.endpoints.resources.WeaviateAdapter")
def test_upload_memory_service_store_error(
    mock_weaviate_adapter_constructor,
    mock_litellm_client_constructor,
    mock_get_memory_service_dep,
    mock_memory_service,
    mock_litellm_client_instance,
    mock_weaviate_adapter_instance,
):
    """
    """
    if hasattr(mock_memory_service, "add_memory_items_async"):
        mock_memory_service.add_memory_items_async.side_effect = Exception("Firestore Error")
    else:
        mock_memory_service.add_memory_item_async.side_effect = Exception("Firestore Error")

    csv_content = "header1,header2\nvalue1,value2"
    file_bytes = BytesIO(csv_content.encode("utf-8"))

    response = client.post(
        "/api/resources/upload",
        files={"uploaded_file": ("test.csv", file_bytes, "text/csv")},
    )

    assert response.status_code == 500
    json_response = response.json()
    assert "Could not store processed data to Firestore: Firestore Error" in json_response["detail"]

    mock_weaviate_adapter_instance.batch_upsert.assert_not_called()

@patch("core.orchestrator.src.api.endpoints.resources.get_memory_service")
@patch("core.orchestrator.src.api.endpoints.resources.LiteLLMClient")
@patch("core.orchestrator.src.api.endpoints.resources.WeaviateAdapter")
def test_upload_weaviate_store_error(
    mock_weaviate_adapter_constructor,
    mock_litellm_client_constructor,
    mock_get_memory_service_dep,
    mock_memory_service,
    mock_litellm_client_instance,
    mock_weaviate_adapter_instance,
):
    """
    """
    mock_weaviate_adapter_instance.batch_upsert.side_effect = Exception("Weaviate Error")

    csv_content = "header1,header2\nvalue1,value2"
    file_bytes = BytesIO(csv_content.encode("utf-8"))

    with patch("core.orchestrator.src.api.endpoints.resources.logger") as mock_logger:
        response = client.post(
            "/api/resources/upload",
            files={"uploaded_file": ("test.csv", file_bytes, "text/csv")},
        )

        assert response.status_code == 200
        json_response = response.json()
        assert json_response["message"] == "File processed and ingested successfully to Firestore and Weaviate"

        if hasattr(mock_memory_service, "add_memory_items_async") and mock_memory_service.add_memory_items_async.called:
            mock_memory_service.add_memory_items_async.assert_called_once()
        else:
            mock_memory_service.add_memory_item_async.assert_called()

        mock_weaviate_adapter_instance.batch_upsert.assert_called_once()
        mock_logger.error.assert_any_call("Error adding batch to Weaviate for test.csv: Weaviate Error", exc_info=True)

@patch("core.orchestrator.src.api.endpoints.resources.shutil.copyfileobj")
@patch("core.orchestrator.src.api.endpoints.resources.get_memory_service")
@patch("core.orchestrator.src.api.endpoints.resources.LiteLLMClient")
@patch("core.orchestrator.src.api.endpoints.resources.WeaviateAdapter")
def test_upload_file_save_error(
    mock_weaviate_adapter_constructor,
    mock_litellm_client_constructor,
    mock_get_memory_service_dep,
    mock_shutil_copy,
    mock_memory_service,
    mock_litellm_client_instance,
    mock_weaviate_adapter_instance,
):
    """
    """
    mock_shutil_copy.side_effect = Exception("Disk full error")

    csv_content = "header1,header2\nvalue1,value2"
    file_bytes = BytesIO(csv_content.encode("utf-8"))

    response = client.post(
        "/api/resources/upload",
        files={"uploaded_file": ("test.csv", file_bytes, "text/csv")},
    )

    assert response.status_code == 500
    json_response = response.json()
    assert "An unexpected error occurred: Disk full error" in json_response["detail"]

    mock_memory_service.add_memory_item_async.assert_not_called()
    mock_memory_service.add_memory_items_async.assert_not_called()
    mock_weaviate_adapter_instance.batch_upsert.assert_not_called()

@patch("core.orchestrator.src.api.endpoints.resources.get_memory_service")
@patch("core.orchestrator.src.api.endpoints.resources.LiteLLMClient")
@patch("core.orchestrator.src.api.endpoints.resources.WeaviateAdapter")
def test_upload_no_filename(
    mock_weaviate_adapter_constructor,
    mock_litellm_client_constructor,
    mock_get_memory_service_dep,
    mock_memory_service,
    mock_litellm_client_instance,
    mock_weaviate_adapter_instance,
):
    """
    """
    file_bytes = BytesIO(b"content")

    response = client.post("/api/resources/upload", files={"uploaded_file": ("", file_bytes, "text/csv")})
    assert response.status_code == 400
    assert response.json()["detail"] == "No filename provided."

    response = client.post("/api/resources/upload", files={"uploaded_file": (None, file_bytes, "text/csv")})
    assert response.status_code == 400
    assert response.json()["detail"] == "No filename provided."
