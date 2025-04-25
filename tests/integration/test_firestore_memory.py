"""
Integration tests for the FirestoreMemoryManager implementation.

These tests interact with a real Firestore instance and will be skipped
if the necessary GCP credentials or project ID are not available.
"""

import os
import pytest
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from future.firestore_memory_manager import (
    FirestoreMemoryManager,
    MEMORY_RECORDS_COLLECTION,
    AGENT_DATA_COLLECTION
)
from packages.shared.src.models.domain_models import MemoryRecord

# Configure logging
logger = logging.getLogger(__name__)

# Check if integration tests should be run
SKIP_INTEGRATION_TESTS = os.environ.get("RUN_INTEGRATION_TESTS", "").lower() != "true"
SKIP_FIRESTORE_TESTS = os.environ.get("RUN_FIRESTORE_TESTS", "").lower() != "true"
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
GCP_SA_KEY_PATH = os.environ.get("GCP_SA_KEY_PATH")
GCP_SA_KEY_JSON = os.environ.get("GCP_SA_KEY_JSON")

# Skip markers
skip_reason = "Integration tests are disabled. Set RUN_INTEGRATION_TESTS=true and RUN_FIRESTORE_TESTS=true to enable."
skip_firestore = pytest.mark.skipif(
    SKIP_INTEGRATION_TESTS or SKIP_FIRESTORE_TESTS or not GCP_PROJECT_ID, 
    reason=skip_reason + " Also requires GCP_PROJECT_ID to be set."
)


def generate_unique_key() -> str:
    """Generate a unique key for test data."""
    return f"test_{uuid.uuid4().hex[:8]}_{int(datetime.utcnow().timestamp())}"


@pytest.fixture
def test_record() -> MemoryRecord:
    """Create a test memory record with a unique key."""
    return MemoryRecord(
        record_id=generate_unique_key(),
        context="test-integration",
        persona="test-persona",
        content=f"Test content {generate_unique_key()}",
        timestamp=datetime.utcnow(),
        metadata={"test_key": "test_value", "integration": True}
    )


@pytest.fixture
def test_records(request) -> List[MemoryRecord]:
    """Create a batch of test records with the specified count."""
    count = getattr(request, "param", 5)  # Default to 5 records if not specified
    
    return [
        MemoryRecord(
            record_id=generate_unique_key(),
            context="test-integration-batch",
            persona="test-persona",
            content=f"Test content {i} - {generate_unique_key()}",
            timestamp=datetime.utcnow() - timedelta(minutes=i),
            metadata={"test_key": f"test_value_{i}", "integration": True, "index": i}
        )
        for i in range(count)
    ]


@skip_firestore
class TestFirestoreMemoryManagerIntegration:
    """Integration tests for the FirestoreMemoryManager implementation."""

    @pytest.fixture(autouse=True)
    def setup_firestore(self):
        """Set up Firestore client before tests and clean up after."""
        # Create a unique collection name for this test run to avoid conflicts
        self.test_collection = f"test_memory_{generate_unique_key()}"
        self.test_ids = []  # Track created records for cleanup
        
        # Create FirestoreMemoryManager instance
        self.memory_manager = FirestoreMemoryManager(
            project_id=GCP_PROJECT_ID,
            credentials_json=GCP_SA_KEY_JSON,
            credentials_path=GCP_SA_KEY_PATH
        )
        
        # Initialize
        self.memory_manager.initialize()
        logger.info(f"Initialized FirestoreMemoryManager with collection {self.test_collection}")
        
        # Yield for test execution
        yield
        
        # Clean up created records
        for record_id in self.test_ids:
            try:
                self.memory_manager.delete_record(record_id, self.test_collection)
                logger.debug(f"Deleted test record {record_id}")
            except Exception as e:
                logger.warning(f"Error cleaning up record {record_id}: {e}")
        
        # Close the connection
        self.memory_manager.close()
        logger.info("Closed FirestoreMemoryManager")

    def test_save_and_get_record(self, test_record):
        """Test saving and retrieving a record."""
        # Save the record
        record_id = self.memory_manager.save_record(test_record, self.test_collection)
        self.test_ids.append(record_id)
        
        # Verify record ID
        assert record_id == test_record.record_id
        
        # Retrieve the record
        retrieved = self.memory_manager.get_record(record_id, self.test_collection)
        
        # Verify record contents
        assert retrieved is not None
        assert retrieved.record_id == test_record.record_id
        assert retrieved.context == test_record.context
        assert retrieved.persona == test_record.persona
        assert retrieved.content == test_record.content
        assert retrieved.metadata == test_record.metadata

    def test_query_records(self, test_records):
        """Test querying records with filters."""
        # Save multiple records
        for record in test_records:
            record_id = self.memory_manager.save_record(record, self.test_collection)
            self.test_ids.append(record_id)
        
        # Query by context
        results = self.memory_manager.query_records(
            {"context": "test-integration-batch"}, 
            self.test_collection
        )
        
        # Verify results
        assert len(results) == len(test_records)
        
        # Query by persona
        results = self.memory_manager.query_records(
            {"persona": "test-persona"}, 
            self.test_collection
        )
        
        # Verify results (should include all our test records)
        assert len(results) >= len(test_records)
        
        # Query with multiple filters
        results = self.memory_manager.query_records(
            {
                "context": "test-integration-batch",
                "persona": "test-persona"
            }, 
            self.test_collection
        )
        
        # Verify results
        assert len(results) == len(test_records)
        
        # Query with metadata filter
        results = self.memory_manager.query_records(
            {"metadata.integration": True}, 
            self.test_collection
        )
        
        # Verify results (should include all our test records)
        assert len(results) >= len(test_records)

    def test_delete_record(self, test_record):
        """Test deleting a record."""
        # Save the record
        record_id = self.memory_manager.save_record(test_record, self.test_collection)
        
        # Verify it exists
        retrieved = self.memory_manager.get_record(record_id, self.test_collection)
        assert retrieved is not None
        assert retrieved.record_id == record_id
        
        # Delete the record
        result = self.memory_manager.delete_record(record_id, self.test_collection)
        assert result is True
        
        # Verify it's gone
        with pytest.raises(ValueError):
            self.memory_manager.get_record(record_id, self.test_collection)
        
        # Remove from cleanup list since we deleted it
        if record_id in self.test_ids:
            self.test_ids.remove(record_id)

    def test_batch_save_records(self, test_records):
        """Test batch saving multiple records."""
        # Use batch operation to save records
        count = self.memory_manager.batch_save_records(test_records, self.test_collection)
        
        # Add to cleanup list
        for record in test_records:
            self.test_ids.append(record.record_id)
        
        # Verify count
        assert count == len(test_records)
        
        # Verify records exist
        for record in test_records:
            retrieved = self.memory_manager.get_record(record.record_id, self.test_collection)
            assert retrieved is not None
            assert retrieved.record_id == record.record_id
            assert retrieved.content == record.content

    @pytest.mark.parametrize("test_records", [401], indirect=True)
    def test_large_batch_save(self, test_records):
        """Test batch saving a large number of records that exceeds Firestore batch limits."""
        # This tests the batch splitting functionality (Firestore has a 500 op limit per batch)
        count = self.memory_manager.batch_save_records(test_records, self.test_collection)
        
        # Add to cleanup list (just a sample for verification)
        sample_ids = [record.record_id for record in test_records[:5]]
        self.test_ids.extend(sample_ids)
        
        # Verify count
        assert count == len(test_records)
        
        # Verify a sample of records exist
        for record_id in sample_ids:
            retrieved = self.memory_manager.get_record(record_id, self.test_collection)
            assert retrieved is not None
            assert retrieved.record_id == record_id

    def test_health_check(self):
        """Test the health check functionality with a live Firestore instance."""
        # Run health check
        health = self.memory_manager.health_check()
        
        # Verify health status
        assert health["status"] == "healthy"
        assert health["firestore"] is True
        assert health["error_count"] == 0
        assert "details" in health
