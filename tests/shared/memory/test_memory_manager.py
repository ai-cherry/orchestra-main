"""
Unit tests for FirestoreMemoryManager.

This module contains tests for the FirestoreMemoryManager implementation,
using mocks for the Firestore client to avoid actual database operations.
"""

import unittest
import logging
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import MagicMock, patch, PropertyMock, call

# Import the classes we want to test
from future.firestore_memory_manager import (
    FirestoreMemoryManager, 
    MEMORY_RECORDS_COLLECTION,
    AGENT_DATA_COLLECTION
)
from packages.shared.src.models.domain_models import MemoryRecord


class TestFirestoreMemoryManager(unittest.TestCase):
    """Test suite for FirestoreMemoryManager class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create patcher for Firestore client
        self.firestore_patcher = patch(
            'future.firestore_memory_manager.firestore')
        self.mock_firestore = self.firestore_patcher.start()

        # Mock the service_account module
        self.service_account_patcher = patch(
            'future.firestore_memory_manager.service_account')
        self.mock_service_account = self.service_account_patcher.start()

        # Mock the Firestore client
        self.mock_client = MagicMock()
        self.mock_firestore.Client.return_value = self.mock_client
        self.mock_firestore.Client.from_service_account_json.return_value = self.mock_client

        # Create FirestoreMemoryManager instance with mock
        self.memory_manager = FirestoreMemoryManager(project_id="test-project")
        self.memory_manager._client = self.mock_client  # Manually set the client
        self.memory_manager._initialized = True  # Mark as initialized

        # Sample data for testing
        self.test_record = MemoryRecord(
            record_id="test-record-1",
            context="test-context",
            persona="test-persona",
            content="This is a test memory record",
            timestamp=datetime.utcnow(),
            metadata={"key1": "value1", "key2": "value2"}
        )

        # Set up collection reference mock
        self.mock_collection = MagicMock()
        self.mock_client.collection.return_value = self.mock_collection

        # Set up document reference mock
        self.mock_doc_ref = MagicMock()
        self.mock_collection.document.return_value = self.mock_doc_ref

    def tearDown(self):
        """Tear down test fixtures after each test method."""
        self.firestore_patcher.stop()
        self.service_account_patcher.stop()

    def test_initialize_with_default_credentials(self):
        """Test initializing the Firestore memory manager with default credentials."""
        # Mock the Firestore client
        self.memory_manager._client = None  # Reset client for this test
        self.memory_manager._initialized = False

        # Call initialize
        self.memory_manager.initialize()

        # Assert client was created
        self.mock_firestore.Client.assert_called_once_with(
            project="test-project")
        self.assertTrue(self.memory_manager._initialized)

    def test_initialize_with_credentials_path(self):
        """Test initializing with credentials path."""
        # Reset manager for this test
        self.memory_manager._client = None
        self.memory_manager._initialized = False
        self.memory_manager._credentials_path = "/path/to/credentials.json"

        # Mock the service account credentials
        mock_credentials = MagicMock()
        self.mock_service_account.Credentials.from_service_account_file.return_value = mock_credentials

        # Call initialize
        self.memory_manager.initialize()

        # Assert credentials were loaded and client was created
        self.mock_service_account.Credentials.from_service_account_file.assert_called_once_with(
            "/path/to/credentials.json")
        self.mock_firestore.Client.assert_called_with(
            project="test-project", credentials=mock_credentials)
        self.assertTrue(self.memory_manager._initialized)

    def test_initialize_with_credentials_json(self):
        """Test initializing with credentials JSON string."""
        # Reset manager for this test
        self.memory_manager._client = None
        self.memory_manager._initialized = False
        self.memory_manager._credentials_json = '{"type": "service_account", "project_id": "test-project"}'

        # Mock JSON parsing
        with patch('future.firestore_memory_manager.json.loads') as mock_json_loads:
            mock_json_loads.return_value = {"type": "service_account", "project_id": "test-project"}
            
            # Mock the service account credentials
            mock_credentials = MagicMock()
            self.mock_service_account.Credentials.from_service_account_info.return_value = mock_credentials

            # Call initialize
            self.memory_manager.initialize()

            # Assert credentials were loaded from JSON and client was created
            mock_json_loads.assert_called_once_with(self.memory_manager._credentials_json)
            self.mock_service_account.Credentials.from_service_account_info.assert_called_once()
            self.mock_firestore.Client.assert_called_with(
                project="test-project", credentials=mock_credentials)
            self.assertTrue(self.memory_manager._initialized)

    def test_initialize_error_handling(self):
        """Test handling errors during initialization."""
        # Reset manager for this test
        self.memory_manager._client = None
        self.memory_manager._initialized = False

        # Test error handling for GoogleAPIError
        self.mock_firestore.Client.side_effect = self.mock_firestore.GoogleAPIError("Connection failed")
        with self.assertRaises(ConnectionError):
            self.memory_manager.initialize()

        # Test error handling for PermissionError
        self.mock_firestore.Client.side_effect = PermissionError("Permission denied")
        with self.assertRaises(PermissionError):
            self.memory_manager.initialize()

        # Test error handling for other exceptions
        self.mock_firestore.Client.side_effect = Exception("Unknown error")
        with self.assertRaises(ConnectionError):
            self.memory_manager.initialize()

    def test_close(self):
        """Test closing the Firestore connection."""
        # Mock the close method on the client
        self.mock_client.close = MagicMock()

        # Call close
        self.memory_manager.close()

        # Assert close was called on the client
        self.mock_client.close.assert_called_once()

        # Assert client and initialized flag were reset
        self.assertIsNone(self.memory_manager._client)
        self.assertFalse(self.memory_manager._initialized)

        # Test error handling during close
        self.memory_manager._client = self.mock_client
        self.memory_manager._initialized = True
        self.mock_client.close.side_effect = Exception("Close error")

        # Should not propagate the exception
        self.memory_manager.close()
        self.assertIsNone(self.memory_manager._client)
        self.assertFalse(self.memory_manager._initialized)

    def test_save_record(self):
        """Test saving a record to Firestore."""
        # Set up mocks
        collection_name = "test-collection"

        # Call the method with default collection
        result = self.memory_manager.save_record(self.test_record)

        # Assert Firestore methods were called correctly
        self.mock_client.collection.assert_called_once_with(MEMORY_RECORDS_COLLECTION)
        self.mock_collection.document.assert_called_once_with(
            self.test_record.record_id)

        # Verify set was called with record data
        self.mock_doc_ref.set.assert_called_once()

        # Verify result is the record ID
        self.assertEqual(result, self.test_record.record_id)

        # Test with custom collection
        self.mock_client.collection.reset_mock()
        self.mock_collection.document.reset_mock()
        self.mock_doc_ref.set.reset_mock()

        result = self.memory_manager.save_record(self.test_record, collection_name)

        # Assert Firestore methods were called correctly with custom collection
        self.mock_client.collection.assert_called_once_with(collection_name)
        self.mock_collection.document.assert_called_once_with(
            self.test_record.record_id)

        # Assert record_id validation
        invalid_record = MemoryRecord(
            record_id="",  # Empty record_id
            context="test-context",
            persona="test-persona",
            content="This is a test memory record",
            timestamp=datetime.utcnow(),
            metadata={}
        )

        with self.assertRaises(ValueError):
            self.memory_manager.save_record(invalid_record, collection_name)

        # Test GoogleAPIError handling
        self.mock_doc_ref.set.side_effect = self.mock_firestore.GoogleAPIError("Storage failed")

        with self.assertRaises(RuntimeError):
            self.memory_manager.save_record(self.test_record, collection_name)

        # Test general exception handling
        self.mock_doc_ref.set.side_effect = Exception("Unknown error")

        with self.assertRaises(RuntimeError):
            self.memory_manager.save_record(self.test_record, collection_name)

    def test_get_record(self):
        """Test retrieving a record from Firestore."""
        # Set up mocks
        collection_name = "test-collection"
        record_id = "test-record-1"

        # Create a mock document
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "record_id": record_id,
            "context": "test-context",
            "persona": "test-persona",
            "content": "This is a test memory record",
            "timestamp": datetime.utcnow(),
            "metadata": {"key1": "value1", "key2": "value2"}
        }
        self.mock_doc_ref.get.return_value = mock_doc

        # Call the method with default collection
        result = self.memory_manager.get_record(record_id)

        # Assert Firestore methods were called correctly
        self.mock_client.collection.assert_called_with(MEMORY_RECORDS_COLLECTION)
        self.mock_collection.document.assert_called_with(record_id)
        self.mock_doc_ref.get.assert_called_once()

        # Verify result is a MemoryRecord with expected values
        self.assertIsInstance(result, MemoryRecord)
        self.assertEqual(result.record_id, record_id)
        self.assertEqual(result.context, "test-context")

        # Test with custom collection
        self.mock_client.collection.reset_mock()
        self.mock_collection.document.reset_mock()
        self.mock_doc_ref.get.reset_mock()

        result = self.memory_manager.get_record(record_id, collection_name)

        # Assert Firestore methods were called correctly with custom collection
        self.mock_client.collection.assert_called_with(collection_name)
        self.mock_collection.document.assert_called_with(record_id)

        # Test document not found
        mock_doc.exists = False
        with self.assertRaises(ValueError):
            self.memory_manager.get_record(record_id, collection_name)

        # Test GoogleAPIError handling
        mock_doc.exists = True
        self.mock_doc_ref.get.side_effect = self.mock_firestore.GoogleAPIError("Retrieval failed")

        with self.assertRaises(RuntimeError):
            self.memory_manager.get_record(record_id, collection_name)

        # Test general exception handling
        self.mock_doc_ref.get.side_effect = Exception("Unknown error")

        with self.assertRaises(RuntimeError):
            self.memory_manager.get_record(record_id, collection_name)

    def test_query_records(self):
        """Test querying records from Firestore."""
        # Set up mocks
        collection_name = "test-collection"
        filters = {"context": "test-context", "persona": "test-persona"}

        # Create mock query
        mock_query = MagicMock()
        self.mock_collection.where.return_value = mock_query
        mock_query.where.return_value = mock_query

        # Mock documents returned from query
        mock_doc1 = MagicMock()
        mock_doc2 = MagicMock()

        mock_doc1.to_dict.return_value = {
            "record_id": "test-record-1",
            "context": "test-context",
            "persona": "test-persona",
            "content": "This is test record 1",
            "timestamp": datetime.utcnow(),
            "metadata": {"key": "value1"}
        }

        mock_doc2.to_dict.return_value = {
            "record_id": "test-record-2",
            "context": "test-context",
            "persona": "test-persona",
            "content": "This is test record 2",
            "timestamp": datetime.utcnow(),
            "metadata": {"key": "value2"}
        }

        # Mock the stream method to return our documents
        mock_query.stream.return_value = [mock_doc1, mock_doc2]

        # Call the method with default collection
        results = self.memory_manager.query_records(filters)

        # Assert Firestore methods were called correctly
        self.mock_client.collection.assert_called_with(MEMORY_RECORDS_COLLECTION)

        # Verify where calls
        # We expect two where clauses for our filters
        self.assertEqual(self.mock_collection.where.call_count, 1)
        self.assertEqual(mock_query.where.call_count, 1)

        # Verify results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].record_id, "test-record-1")
        self.assertEqual(results[1].record_id, "test-record-2")

        # Test with custom collection
        self.mock_client.collection.reset_mock()
        self.mock_collection.where.reset_mock()
        mock_query.where.reset_mock()
        mock_query.stream.reset_mock()

        results = self.memory_manager.query_records(filters, collection_name)

        # Assert Firestore methods were called correctly with custom collection
        self.mock_client.collection.assert_called_with(collection_name)

        # Test timestamp range filters
        timestamp_filters = {
            "timestamp": {
                "start": datetime(2023, 1, 1),
                "end": datetime(2023, 12, 31)
            },
            "context": "test-context"
        }

        # Reset mocks
        self.mock_collection.reset_mock()
        mock_query.reset_mock()
        self.mock_collection.where.return_value = mock_query
        mock_query.where.return_value = mock_query
        mock_query.stream.return_value = [mock_doc1]

        # Call with timestamp filters
        results = self.memory_manager.query_records(
            timestamp_filters, collection_name)

        # Verify results
        self.assertEqual(len(results), 1)

        # Test error in document parsing
        mock_doc1.to_dict.side_effect = Exception("Parse error")
        mock_query.stream.return_value = [mock_doc1, mock_doc2]

        # Should skip the document with error
        results = self.memory_manager.query_records(filters, collection_name)
        self.assertEqual(len(results), 1)  # Only the second doc should be processed
        self.assertEqual(results[0].record_id, "test-record-2")

        # Test GoogleAPIError handling
        mock_doc1.to_dict.side_effect = None  # Reset side effect
        mock_query.stream.side_effect = self.mock_firestore.GoogleAPIError("Query failed")

        with self.assertRaises(RuntimeError):
            self.memory_manager.query_records(filters, collection_name)

        # Test general exception handling
        mock_query.stream.side_effect = Exception("Unknown error")

        with self.assertRaises(RuntimeError):
            self.memory_manager.query_records(filters, collection_name)

    def test_delete_record(self):
        """Test deleting a record from Firestore."""
        # Set up mocks
        collection_name = "test-collection"
        record_id = "test-record-1"

        # Create a mock document
        mock_doc = MagicMock()
        mock_doc.exists = True
        self.mock_doc_ref.get.return_value = mock_doc

        # Call the method with default collection
        result = self.memory_manager.delete_record(record_id)

        # Assert Firestore methods were called correctly
        self.mock_client.collection.assert_called_with(MEMORY_RECORDS_COLLECTION)
        self.mock_collection.document.assert_called_with(record_id)
        self.mock_doc_ref.get.assert_called_once()
        self.mock_doc_ref.delete.assert_called_once()

        # Verify result is True
        self.assertTrue(result)

        # Test with custom collection
        self.mock_client.collection.reset_mock()
        self.mock_collection.document.reset_mock()
        self.mock_doc_ref.get.reset_mock()
        self.mock_doc_ref.delete.reset_mock()

        result = self.memory_manager.delete_record(record_id, collection_name)

        # Assert Firestore methods were called correctly with custom collection
        self.mock_client.collection.assert_called_with(collection_name)
        self.mock_collection.document.assert_called_with(record_id)

        # Test document not found
        mock_doc.exists = False
        result = self.memory_manager.delete_record(record_id, collection_name)
        self.assertFalse(result)
        self.mock_doc_ref.delete.assert_not_called()  # Delete should not be called

        # Test GoogleAPIError handling
        mock_doc.exists = True
        self.mock_doc_ref.delete.side_effect = self.mock_firestore.GoogleAPIError("Delete failed")

        with self.assertRaises(RuntimeError):
            self.memory_manager.delete_record(record_id, collection_name)

        # Test general exception handling
        self.mock_doc_ref.delete.side_effect = Exception("Unknown error")

        with self.assertRaises(RuntimeError):
            self.memory_manager.delete_record(record_id, collection_name)

    def test_batch_save_records(self):
        """Test saving multiple records in a batch."""
        collection_name = "test-collection"
        
        # Create test records
        records = [
            MemoryRecord(
                record_id=f"test-record-{i}",
                context="test-context",
                persona="test-persona",
                content=f"This is test record {i}",
                timestamp=datetime.utcnow(),
                metadata={"key": f"value{i}"}
            )
            for i in range(1, 6)  # Create 5 records
        ]
        
        # Add one invalid record without ID
        invalid_record = MemoryRecord(
            record_id="",  # Empty record_id
            context="test-context",
            persona="test-persona",
            content="Invalid record",
            timestamp=datetime.utcnow(),
            metadata={}
        )
        records.append(invalid_record)
        
        # Set up batch mock
        mock_batch = MagicMock()
        self.mock_client.batch.return_value = mock_batch
        
        # Call the method with default collection
        result = self.memory_manager.batch_save_records(records)
        
        # Should save 5 valid records
        self.assertEqual(result, 5)
        
        # Verify batch operations
        self.assertEqual(self.mock_client.batch.call_count, 1)
        self.assertEqual(mock_batch.set.call_count, 5)  # 5 valid records
        self.assertEqual(mock_batch.commit.call_count, 1)
        
        # Test with custom collection
        self.mock_client.collection.reset_mock()
        self.mock_client.batch.reset_mock()
        mock_batch.set.reset_mock()
        mock_batch.commit.reset_mock()
        
        result = self.memory_manager.batch_save_records(records, collection_name)
        
        # Verify with custom collection
        self.assertEqual(result, 5)
        self.assertEqual(self.mock_client.collection.call_count, 5)  # One per valid record
        for call_args in self.mock_client.collection.call_args_list:
            self.assertEqual(call_args[0][0], collection_name)
            
        # Test with large batch (over 400 records)
        large_records = [
            MemoryRecord(
                record_id=f"test-record-{i}",
                context="test-context",
                persona="test-persona",
                content=f"This is test record {i}",
                timestamp=datetime.utcnow(),
                metadata={"key": f"value{i}"}
            )
            for i in range(1, 402)  # Create 401 records (enough to trigger batch split)
        ]
        
        self.mock_client.collection.reset_mock()
        self.mock_client.batch.reset_mock()
        mock_batch.set.reset_mock()
        mock_batch.commit.reset_mock()
        
        result = self.memory_manager.batch_save_records(large_records)
        
        # Should save all 401 records
        self.assertEqual(result, 401)
        
        # Should create two batches
        self.assertEqual(self.mock_client.batch.call_count, 2)
        
        # First batch should have 400 records, second batch should have 1
        self.assertEqual(mock_batch.commit.call_count, 2)
        
        # Test empty records list
        self.mock_client.batch.reset_mock()
        result = self.memory_manager.batch_save_records([])
        self.assertEqual(result, 0)
        self.mock_client.batch.assert_not_called()
        
        # Test GoogleAPIError handling
        mock_batch.commit.side_effect = self.mock_firestore.GoogleAPIError("Batch save failed")
        
        with self.assertRaises(RuntimeError):
            self.memory_manager.batch_save_records(records)
            
        # Test general exception handling
        mock_batch.commit.side_effect = Exception("Unknown error")
        
        with self.assertRaises(RuntimeError):
            self.memory_manager.batch_save_records(records)

    def test_health_check(self):
        """Test the health check functionality."""
        # Mock get_record to simulate healthy connection
        with patch.object(self.memory_manager, 'get_record', side_effect=ValueError("Not found")):
            result = self.memory_manager.health_check()
            
            # Check that the health check returns expected values
            self.assertEqual(result["status"], "healthy")
            self.assertTrue(result["firestore"])
            self.assertEqual(result["error_count"], 0)
            self.assertIn("firestore_check", result["details"])
        
        # Test when get_record raises an unexpected error
        with patch.object(self.memory_manager, 'get_record', side_effect=RuntimeError("Connection error")):
            result = self.memory_manager.health_check()
            
            # Check that the health check reports the error
            self.assertEqual(result["status"], "error")
            self.assertFalse(result["firestore"])
            self.assertIn("firestore_error", result["details"])
        
        # Test when connection is not initialized
        self.memory_manager._initialized = False
        
        # Mock initialize to pass
        with patch.object(self.memory_manager, 'initialize'):
            with patch.object(self.memory_manager, 'get_record', side_effect=ValueError("Not found")):
                result = self.memory_manager.health_check()
                
                # Check that initialization happened during health check
                self.assertEqual(result["status"], "healthy")
                self.assertTrue(result["firestore"])
                self.assertIn("initialization", result["details"])
        
        # Test when initialization fails
        with patch.object(self.memory_manager, 'initialize', side_effect=ConnectionError("Init failed")):
            result = self.memory_manager.health_check()
            
            # Check that health check reports initialization error
            self.assertEqual(result["status"], "error")
            self.assertFalse(result["firestore"])
            self.assertIn("initialization_error", result["details"])
        
        # Test when health check itself throws an exception
        with patch.object(self.memory_manager, 'get_record', side_effect=Exception("Unexpected error")):
            result = self.memory_manager.health_check()
            
            # Should handle the exception and return error status
            self.assertEqual(result["status"], "error")
            self.assertFalse(result["firestore"])
            self.assertEqual(result["error_count"], 1)
            self.assertIn("last_error", result)


if __name__ == '__main__':
    unittest.main()
