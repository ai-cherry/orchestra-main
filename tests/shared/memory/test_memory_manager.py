"""
Unit tests for FirestoreMemoryManager.

This module contains tests for the FirestoreMemoryManager implementation,
using mocks for the Firestore client to avoid actual database operations.
"""

import unittest
import logging
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import MagicMock, patch, PropertyMock

# Import the classes we want to test
from future.firestore_memory_manager import FirestoreMemoryManager
from packages.shared.src.models.domain_models import MemoryRecord


class TestFirestoreMemoryManager(unittest.TestCase):
    """Test suite for FirestoreMemoryManager class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create patcher for Firestore client
        self.firestore_patcher = patch(
            'future.firestore_memory_manager.firestore')
        self.mock_firestore = self.firestore_patcher.start()

        # Mock the Firestore client
        self.mock_client = MagicMock()
        self.mock_firestore.Client.return_value = self.mock_client
        self.mock_firestore.Client.from_service_account_json.return_value = self.mock_client

        # Mock SERVER_TIMESTAMP
        self.mock_firestore.SERVER_TIMESTAMP = 'server_timestamp'

        # Create FirestoreMemoryManager instance with mock
        self.memory_manager = FirestoreMemoryManager(project_id="test-project")
        self.memory_manager._client = self.mock_client  # Manually set the client

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

    def test_initialize(self):
        """Test initializing the Firestore memory manager."""
        # Mock the Firestore client
        self.memory_manager._client = None  # Reset client for this test

        # Call initialize
        self.memory_manager.initialize()

        # Assert client was created
        self.mock_firestore.Client.assert_called_once_with(
            project="test-project")

        # Test error handling
        self.mock_firestore.Client.side_effect = Exception("Connection failed")

        # Verify that exceptions are caught and re-raised appropriately
        with self.assertRaises(ConnectionError):
            self.memory_manager.initialize()

    def test_save_record(self):
        """Test saving a record to Firestore."""
        # Set up mocks
        collection_name = "test-collection"

        # Call the method
        self.memory_manager.save_record(self.test_record, collection_name)

        # Assert Firestore methods were called correctly
        self.mock_client.collection.assert_called_once_with(collection_name)
        self.mock_collection.document.assert_called_once_with(
            self.test_record.record_id)

        # Verify set was called with record data
        self.mock_doc_ref.set.assert_called_once()

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

        # Test error handling
        self.mock_doc_ref.set.side_effect = Exception("Storage failed")

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

        # Call the method
        result = self.memory_manager.get_record(record_id, collection_name)

        # Assert Firestore methods were called correctly
        self.mock_client.collection.assert_called_with(collection_name)
        self.mock_collection.document.assert_called_with(record_id)
        self.mock_doc_ref.get.assert_called_once()

        # Verify result is a MemoryRecord with expected values
        self.assertIsInstance(result, MemoryRecord)
        self.assertEqual(result.record_id, record_id)
        self.assertEqual(result.context, "test-context")

        # Test document not found
        mock_doc.exists = False
        with self.assertRaises(ValueError):
            self.memory_manager.get_record(record_id, collection_name)

        # Test error handling
        mock_doc.exists = True
        self.mock_doc_ref.get.side_effect = Exception("Retrieval failed")

        with self.assertRaises(RuntimeError):
            self.memory_manager.get_record(record_id, collection_name)

    def test_query_records(self):
        """Test querying records from Firestore."""
        # Set up mocks
        collection_name = "test-collection"
        filters = {"context": "test-context", "persona": "test-persona"}

        # Create mock query and results
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

        # Call the method
        results = self.memory_manager.query_records(filters, collection_name)

        # Assert Firestore methods were called correctly
        self.mock_client.collection.assert_called_with(collection_name)

        # Verify where calls
        # We expect two where clauses for our filters
        self.assertEqual(self.mock_collection.where.call_count, 1)
        self.assertEqual(mock_query.where.call_count, 1)

        # Verify results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].record_id, "test-record-1")
        self.assertEqual(results[1].record_id, "test-record-2")

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

        # Test error handling
        mock_query.stream.side_effect = Exception("Query failed")

        with self.assertRaises(RuntimeError):
            self.memory_manager.query_records(filters, collection_name)


if __name__ == '__main__':
    unittest.main()
