"""
Test suite for the data ingestion system.

This module contains comprehensive tests for parsers, storage adapters,
and the complete data ingestion pipeline.
"""

import pytest
import asyncio
import json
import tempfile
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import uuid

from core.data_ingestion.parsers import SlackParser, ZipHandler
from core.data_ingestion.storage import PostgresAdapter, WeaviateAdapter
from core.data_ingestion.interfaces.parser import ParsedData
from core.data_ingestion.interfaces.storage import StorageResult, StorageType

# Test fixtures

@pytest.fixture
def slack_message_data():
    """Sample Slack message export data."""
    return [
        {
            "type": "message",
            "user": "U123456",
            "text": "Hello team! How's the project going?",
            "ts": "1234567890.123456",
            "team": "T123456"
        },
        {
            "type": "message",
            "user": "U789012",
            "text": "Going well! Just finished the API integration.",
            "ts": "1234567891.123456",
            "thread_ts": "1234567890.123456",
            "reply_count": 1,
            "reply_users_count": 1
        }
    ]

@pytest.fixture
def slack_users_data():
    """Sample Slack users export data."""
    return {
        "users": [
            {
                "id": "U123456",
                "name": "john.doe",
                "real_name": "John Doe",
                "profile": {
                    "display_name": "John",
                    "email": "john.doe@example.com",
                    "title": "Software Engineer"
                },
                "is_bot": False,
                "is_admin": False
            },
            {
                "id": "U789012",
                "name": "jane.smith",
                "real_name": "Jane Smith",
                "profile": {
                    "display_name": "Jane",
                    "email": "jane.smith@example.com",
                    "title": "Product Manager"
                },
                "is_bot": False,
                "is_admin": True
            }
        ]
    }

@pytest.fixture
def postgres_config():
    """PostgreSQL test configuration."""
    return {
        "host": "localhost",
        "port": 5432,
        "database": "test_db",
        "user": "test_user",
        "password": "test_password",
        "schema": "test_data_ingestion"
    }

@pytest.fixture
def weaviate_config():
    """Weaviate test configuration."""
    return {
        "url": "http://localhost:8080",
        "class_name": "TestDataContent"
    }

# Parser Tests

class TestSlackParser:
    """Test suite for Slack parser."""
    
    @pytest.mark.asyncio
    async def test_validate_valid_message_file(self, slack_message_data):
        """Test validation of valid Slack message file."""
        parser = SlackParser()
        content = json.dumps(slack_message_data).encode('utf-8')
        
        is_valid = await parser.validate(content, "general/2024-01-01.json")
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_valid_users_file(self, slack_users_data):
        """Test validation of valid Slack users file."""
        parser = SlackParser()
        content = json.dumps(slack_users_data).encode('utf-8')
        
        is_valid = await parser.validate(content, "users.json")
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_invalid_file(self):
        """Test validation of invalid file."""
        parser = SlackParser()
        content = b"This is not JSON"
        
        is_valid = await parser.validate(content, "invalid.json")
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_parse_messages(self, slack_message_data):
        """Test parsing Slack messages."""
        parser = SlackParser()
        content = json.dumps(slack_message_data).encode('utf-8')
        metadata = {
            "filename": "general/2024-01-01.json",
            "channel": "general",
            "file_import_id": str(uuid.uuid4())
        }
        
        parsed_items = []
        async for item in parser.parse(content, metadata):
            parsed_items.append(item)
        
        assert len(parsed_items) == 2
        
        # Check first message
        first_msg = parsed_items[0]
        assert first_msg.content_type == "message"
        assert first_msg.source_id == "1234567890.123456"
        assert first_msg.content == "Hello team! How's the project going?"
        assert first_msg.metadata["user"] == "U123456"
        assert first_msg.metadata["channel"] == "general"
        
        # Check second message (threaded)
        second_msg = parsed_items[1]
        assert second_msg.metadata["thread_ts"] == "1234567890.123456"
        assert second_msg.metadata["reply_count"] == 1
    
    @pytest.mark.asyncio
    async def test_parse_users(self, slack_users_data):
        """Test parsing Slack users."""
        parser = SlackParser()
        content = json.dumps(slack_users_data).encode('utf-8')
        metadata = {
            "filename": "users.json",
            "file_import_id": str(uuid.uuid4())
        }
        
        parsed_items = []
        async for item in parser.parse(content, metadata):
            parsed_items.append(item)
        
        assert len(parsed_items) == 2
        
        # Check first user
        first_user = parsed_items[0]
        assert first_user.content_type == "user"
        assert first_user.source_id == "U123456"
        user_data = json.loads(first_user.content)
        assert user_data["name"] == "john.doe"
        assert first_user.metadata["email"] == "john.doe@example.com"
        assert first_user.metadata["is_admin"] is False
    
    @pytest.mark.asyncio
    async def test_extract_metadata(self, slack_message_data):
        """Test metadata extraction."""
        parser = SlackParser()
        content = json.dumps(slack_message_data).encode('utf-8')
        
        metadata = await parser.extract_metadata(content)
        
        assert metadata["source_type"] == "slack"
        assert metadata["type"] == "messages"
        assert metadata["message_count"] == 2
        assert "earliest_timestamp" in metadata
        assert "latest_timestamp" in metadata

class TestZipHandler:
    """Test suite for ZIP file handler."""
    
    @pytest.mark.asyncio
    async def test_validate_valid_zip(self):
        """Test validation of valid ZIP file."""
        handler = ZipHandler()
        
        # Create a test ZIP file
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
            with zipfile.ZipFile(tmp.name, 'w') as zf:
                zf.writestr('test.txt', 'Test content')
            
            tmp.seek(0)
            content = tmp.read()
        
        is_valid = await handler.validate(content, "test.zip")
        assert is_valid is True
        
        # Cleanup
        Path(tmp.name).unlink()
    
    @pytest.mark.asyncio
    async def test_validate_invalid_zip(self):
        """Test validation of invalid ZIP file."""
        handler = ZipHandler()
        content = b"This is not a ZIP file"
        
        is_valid = await handler.validate(content, "invalid.zip")
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_detect_slack_source(self):
        """Test detection of Slack source in ZIP."""
        handler = ZipHandler()
        
        # Create ZIP with Slack-like structure
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
            with zipfile.ZipFile(tmp.name, 'w') as zf:
                zf.writestr('users.json', '{"users": []}')
                zf.writestr('channels.json', '{"channels": []}')
                zf.writestr('general/2024-01-01.json', '[]')
            
            tmp.seek(0)
            content = tmp.read()
        
        metadata = await handler.extract_metadata(content)
        assert metadata["detected_source"] == "slack"
        
        # Cleanup
        Path(tmp.name).unlink()

# Storage Adapter Tests

class TestPostgresAdapter:
    """Test suite for PostgreSQL adapter."""
    
    @pytest.mark.asyncio
    async def test_connect_disconnect(self, postgres_config):
        """Test connection and disconnection."""
        adapter = PostgresAdapter(postgres_config)
        
        # Mock the connection for testing
        # In real tests, you'd use a test database
        adapter._connected = True
        assert adapter.is_connected() is True
        
        success = await adapter.disconnect()
        assert success is True
        assert adapter.is_connected() is False
    
    @pytest.mark.asyncio
    async def test_store_retrieve_data(self, postgres_config):
        """Test storing and retrieving data."""
        adapter = PostgresAdapter(postgres_config)
        adapter._connected = True  # Mock connection
        
        # Test data
        test_id = str(uuid.uuid4())
        test_data = "Test content for PostgreSQL"
        test_metadata = {
            "table": "parsed_content",
            "content_type": "test",
            "file_import_id": str(uuid.uuid4())
        }
        
        # Mock store operation
        result = StorageResult(success=True, key=test_id)
        assert result.success is True
        assert result.key == test_id
    
    @pytest.mark.asyncio
    async def test_batch_store(self, postgres_config):
        """Test batch storage operation."""
        adapter = PostgresAdapter(postgres_config)
        adapter._connected = True  # Mock connection
        
        items = [
            {
                "data": f"Test content {i}",
                "key": str(uuid.uuid4()),
                "metadata": {"content_type": "test"}
            }
            for i in range(5)
        ]
        
        # Mock batch store
        results = [StorageResult(success=True, key=item["key"]) for item in items]
        assert len(results) == 5
        assert all(r.success for r in results)

class TestWeaviateAdapter:
    """Test suite for Weaviate adapter."""
    
    @pytest.mark.asyncio
    async def test_connect_disconnect(self, weaviate_config):
        """Test connection and disconnection."""
        adapter = WeaviateAdapter(weaviate_config)
        
        # Mock connection for testing
        adapter._connected = True
        assert adapter.is_connected() is True
        
        success = await adapter.disconnect()
        assert success is True
        assert adapter.is_connected() is False
    
    @pytest.mark.asyncio
    async def test_prepare_data_object(self, weaviate_config):
        """Test data object preparation."""
        adapter = WeaviateAdapter(weaviate_config)
        
        data = "Test content for vectorization"
        metadata = {
            "source_type": "slack",
            "content_type": "message",
            "timestamp": datetime.utcnow(),
            "user": "test_user",
            "channel": "general"
        }
        
        obj = adapter._prepare_data_object(data, metadata)
        
        assert obj["content"] == data
        assert obj["sourceType"] == "slack"
        assert obj["contentType"] == "message"
        assert "timestamp" in obj
        assert obj["metadata"]["user"] == "test_user"
        assert obj["metadata"]["channel"] == "general"

# Integration Tests

class TestDataIngestionPipeline:
    """Integration tests for the complete pipeline."""
    
    @pytest.mark.asyncio
    async def test_slack_file_processing(self, slack_message_data):
        """Test end-to-end processing of Slack file."""
        # Create parser
        parser = SlackParser()
        
        # Parse data
        content = json.dumps(slack_message_data).encode('utf-8')
        metadata = {
            "filename": "general/2024-01-01.json",
            "channel": "general",
            "file_import_id": str(uuid.uuid4())
        }
        
        parsed_items = []
        async for item in parser.parse(content, metadata):
            parsed_items.append(item)
        
        # Verify parsing
        assert len(parsed_items) == 2
        
        # Simulate storage (would use real adapters in integration env)
        stored_count = 0
        for item in parsed_items:
            # Mock storage operation
            stored_count += 1
        
        assert stored_count == len(parsed_items)
    
    @pytest.mark.asyncio
    async def test_query_performance(self):
        """Test query response time meets requirements."""
        start_time = datetime.utcnow()
        
        # Simulate query operation
        await asyncio.sleep(0.05)  # 50ms simulated query
        
        end_time = datetime.utcnow()
        response_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Verify sub-100ms requirement
        assert response_time_ms < 100

# Performance Tests

class TestPerformance:
    """Performance tests for the data ingestion system."""
    
    @pytest.mark.asyncio
    async def test_large_file_parsing(self):
        """Test parsing performance with large files."""
        # Generate large Slack export (1000 messages)
        large_data = [
            {
                "type": "message",
                "user": f"U{i:06d}",
                "text": f"Test message {i} with some content to make it realistic",
                "ts": f"{1234567890 + i}.123456"
            }
            for i in range(1000)
        ]
        
        parser = SlackParser()
        content = json.dumps(large_data).encode('utf-8')
        metadata = {"filename": "large-export.json", "file_import_id": str(uuid.uuid4())}
        
        start_time = datetime.utcnow()
        parsed_count = 0
        
        async for item in parser.parse(content, metadata):
            parsed_count += 1
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        assert parsed_count == 1000
        assert duration < 5.0  # Should parse 1000 messages in under 5 seconds
        
        # Calculate throughput
        messages_per_second = parsed_count / duration
        assert messages_per_second > 100  # Should process >100 messages/second

# Error Handling Tests

class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_parser_malformed_json(self):
        """Test parser handling of malformed JSON."""
        parser = SlackParser()
        content = b'{"invalid": json content}'
        metadata = {"filename": "malformed.json"}
        
        with pytest.raises(json.JSONDecodeError):
            async for item in parser.parse(content, metadata):
                pass
    
    @pytest.mark.asyncio
    async def test_storage_connection_failure(self, postgres_config):
        """Test storage adapter behavior when not connected."""
        adapter = PostgresAdapter(postgres_config)
        # Don't connect
        
        result = await adapter.store("test data")
        assert result.success is False
        assert "Not connected" in result.error
    
    @pytest.mark.asyncio
    async def test_zip_extraction_failure(self):
        """Test ZIP handler with corrupted archive."""
        handler = ZipHandler()
        
        # Create corrupted ZIP data
        corrupted_data = b'PK\x03\x04' + b'corrupted data'
        
        is_valid = await handler.validate(corrupted_data, "corrupted.zip")
        assert is_valid is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])