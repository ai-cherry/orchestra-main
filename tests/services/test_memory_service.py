from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from core.orchestrator.src.services.memory_service import HashRecord, MemoryService


@pytest.fixture
def mock_memory_manager():
    manager = AsyncMock()
    manager.store = AsyncMock(return_value=True)
    manager.get = AsyncMock(
        return_value={
            "content_type": "file",
            "reference": "test.txt",
            "timestamp": "2023-01-01T00:00:00",
            "ttl": 2592000,  # 30 days in seconds
        }
    )
    return manager


@pytest.fixture
def memory_service(mock_memory_manager):
    return MemoryService(mock_memory_manager)


@pytest.mark.asyncio
async def test_store_hash_success(memory_service, mock_memory_manager):
    # Test successful hash storage
    result = await memory_service.store_hash("file:abc123", {"filename": "test.txt"})
    assert result is True
    mock_memory_manager.store.assert_called_once()


@pytest.mark.asyncio
async def test_store_hash_failure(memory_service, mock_memory_manager):
    # Test storage failure
    mock_memory_manager.store.return_value = False
    result = await memory_service.store_hash("file:abc123", {"filename": "test.txt"})
    assert result is False


@pytest.mark.asyncio
async def test_get_by_hash_success(memory_service, mock_memory_manager):
    # Test successful hash retrieval
    record = await memory_service.get_by_hash("file:abc123")
    assert isinstance(record, HashRecord)
    assert record.content_type == "file"
    assert record.reference == "test.txt"
    mock_memory_manager.get.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_hash_not_found(memory_service, mock_memory_manager):
    # Test hash not found
    mock_memory_manager.get.return_value = None
    record = await memory_service.get_by_hash("file:missing")
    assert record is None


@pytest.mark.asyncio
async def test_get_by_hash_invalid_data(memory_service, mock_memory_manager):
    # Test invalid stored data
    mock_memory_manager.get.return_value = {"invalid": "data"}
    record = await memory_service.get_by_hash("file:bad")
    assert record is None


def test_hash_record_model():
    # Test HashRecord model validation
    record = HashRecord(content_type="file", reference="test.txt", timestamp=datetime.utcnow(), ttl=timedelta(days=30))
    assert isinstance(record.dict(), dict)
    assert "content_type" in record.dict()
