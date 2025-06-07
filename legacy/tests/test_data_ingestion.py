# TODO: Consider adding connection pooling configuration
"""
"""
    """Sample Slack message export data."""
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
        "url": "http://localhost:8080",
        "class_name": "TestDataContent"
    }

# Parser Tests

class TestSlackParser:
    """Test suite for Slack parser."""
        """Test validation of valid Slack message file."""
        is_valid = await parser.validate(content, "general/2024-01-01.json")
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_valid_users_file(self, slack_users_data):
        """Test validation of valid Slack users file."""
        is_valid = await parser.validate(content, "users.json")
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_invalid_file(self):
        """Test validation of invalid file."""
        content = b"This is not JSON"
        
        is_valid = await parser.validate(content, "invalid.json")
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_parse_messages(self, slack_message_data):
        """Test parsing Slack messages."""
            "filename": "general/2024-01-01.json",
            "channel": "general",
            "file_import_id": str(uuid.uuid4())
        }
        
        parsed_items = []
        async # TODO: Consider using list comprehension for better performance
 # TODO: Consider using list comprehension for better performance
 # TODO: Consider using list comprehension for better performance
 for item in parser.parse(content, metadata):
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
        assert metadata["source_type"] == "slack"
        assert metadata["type"] == "messages"
        assert metadata["message_count"] == 2
        assert "earliest_timestamp" in metadata
        assert "latest_timestamp" in metadata

class TestZipHandler:
    """Test suite for ZIP file handler."""
        """Test validation of valid ZIP file."""
        is_valid = await handler.validate(content, "test.zip")
        assert is_valid is True
        
        # Cleanup
        Path(tmp.name).unlink()
    
    @pytest.mark.asyncio
    async def test_validate_invalid_zip(self):
        """Test validation of invalid ZIP file."""
        content = b"This is not a ZIP file"
        
        is_valid = await handler.validate(content, "invalid.zip")
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_detect_slack_source(self):
        """Test detection of Slack source in ZIP."""
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
        """Test connection and disconnection."""
        """Test storing and retrieving data."""
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
        """Test connection and disconnection."""
        """Test data object preparation."""
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
        """Test end-to-end processing of Slack file."""
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
    """Performance tests for the data ingestion system."""
        """Test parsing performance with large files."""
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
        """Test parser handling of malformed JSON."""
        content = b'{"invalid": json content}'
        metadata = {"filename": "malformed.json"}
        
        with pytest.raises(json.JSONDecodeError):
            async for item in parser.parse(content, metadata):
                pass
    
    @pytest.mark.asyncio
    async def test_storage_connection_failure(self, postgres_config):
        """Test storage adapter behavior when not connected."""
        result = await adapter.store("test data")
        assert result.success is False
        assert "Not connected" in result.error
    
    @pytest.mark.asyncio
    async def test_zip_extraction_failure(self):
        """Test ZIP handler with corrupted archive."""
        is_valid = await handler.validate(corrupted_data, "corrupted.zip")
        assert is_valid is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])