"""
Error handling demonstration for Orchestra.

This script demonstrates how to use the error handling utilities in real-world scenarios
with GCP services and LLM providers. It provides practical examples of implementing
robust error handling patterns across different components of the system.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional

from . import error_handling as eh
from ..memory.exceptions import MemoryError

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger(__name__)


#########################################
# Firestore Example
#########################################

# Create circuit breakers for different services
firestore_circuit = eh.CircuitBreaker(
    name="firestore", failure_threshold=3, recovery_timeout=60
)

portkey_circuit = eh.CircuitBreaker(
    name="portkey",
    failure_threshold=5,
    recovery_timeout=300,  # Longer recovery time for external API
)

vertex_circuit = eh.CircuitBreaker(
    name="vertex", failure_threshold=3, recovery_timeout=120
)


class FirestoreClient:
    """Example class for Firestore operations with robust error handling."""

    def __init__(self, project_id: str, credentials_path: Optional[str] = None):
        self.project_id = project_id
        self.credentials_path = credentials_path
        self._client = None
        self.logger = logging.getLogger(__name__)

    async def initialize(self) -> None:
        """Initialize the Firestore client with error handling."""
        try:
            # Import Firestore
            from google.cloud import firestore

            # Initialize client
            if self.credentials_path:
                from google.oauth2 import service_account

                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path
                )
                self._client = firestore.Client(
                    project=self.project_id, credentials=credentials
                )
            else:
                self._client = firestore.Client(project=self.project_id)

            self.logger.info(
                f"Firestore client initialized for project {self.project_id}"
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize Firestore client: {e}")
            raise eh.ConnectionError(f"Failed to connect to Firestore: {e}", e)

    @eh.with_retry(
        max_retries=3, retryable_exceptions=(eh.TemporaryError, eh.TimeoutError)
    )
    @eh.with_circuit_breaker(firestore_circuit)
    @eh.handle_gcp_error
    async def get_document(self, collection: str, doc_id: str) -> Dict[str, Any]:
        """
        Retrieve a document from Firestore with comprehensive error handling.

        This method demonstrates:
        1. GCP error handling
        2. Circuit breaker pattern
        3. Automatic retries for temporary failures

        Args:
            collection: Firestore collection name
            doc_id: Document ID to retrieve

        Returns:
            The document data

        Raises:
            NotFoundError: If the document doesn't exist
            ConnectionError: If connection to Firestore fails
            TimeoutError: If the operation times out
            ServiceError: If Firestore returns an API error
        """
        if not self._client:
            await self.initialize()

        # Get document reference
        doc_ref = self._client.collection(collection).document(doc_id)

        # Get document
        doc = doc_ref.get()

        # Check if document exists
        if not doc.exists:
            raise eh.NotFoundError(
                f"Document {doc_id} not found in collection {collection}"
            )

        # Return document data
        return doc.to_dict()

    @eh.with_retry(max_retries=2)
    @eh.with_circuit_breaker(firestore_circuit)
    @eh.handle_gcp_error
    async def save_document(
        self, collection: str, doc_id: str, data: Dict[str, Any]
    ) -> str:
        """
        Save a document to Firestore with comprehensive error handling.

        Args:
            collection: Firestore collection name
            doc_id: Document ID to save
            data: Document data to save

        Returns:
            The document ID

        Raises:
            ConnectionError: If connection to Firestore fails
            ServiceError: If Firestore returns an API error
        """
        if not self._client:
            await self.initialize()

        # Get document reference
        doc_ref = self._client.collection(collection).document(doc_id)

        # Save document
        doc_ref.set(data)

        self.logger.info(f"Saved document {doc_id} to collection {collection}")
        return doc_id

    async def close(self) -> None:
        """Close the Firestore client and release resources."""
        if hasattr(self._client, "close") and callable(getattr(self._client, "close")):
            try:
                self._client.close()
                self.logger.info("Firestore client closed")
            except Exception as e:
                self.logger.warning(f"Error closing Firestore client: {e}")


#########################################
# LLM Client Example
#########################################


class LLMClient:
    """Example class for LLM operations with robust error handling."""

    def __init__(self, api_key: str, provider: str = "openai"):
        self.api_key = api_key
        self.provider = provider
        self._client = None
        self.logger = logging.getLogger(__name__)

    async def initialize(self) -> None:
        """Initialize the LLM client with error handling."""
        # This would typically initialize the appropriate client based on provider
        self.logger.info(f"LLM client initialized for provider: {self.provider}")

    @eh.with_retry(
        max_retries=2,
        retryable_exceptions=(eh.TemporaryError, eh.TimeoutError, eh.RateLimitError),
    )
    @eh.with_circuit_breaker(portkey_circuit)
    @eh.handle_llm_error
    async def generate_text(
        self,
        prompt: str,
        model: str = "gpt-4",
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate text using an LLM with comprehensive error handling.

        This method demonstrates:
        1. LLM-specific error handling
        2. Circuit breaker pattern
        3. Automatic retries for temporary failures

        Args:
            prompt: The prompt to generate text from
            model: The model to use
            max_tokens: Maximum number of tokens in the response
            temperature: Randomness parameter (0.0-1.0)

        Returns:
            The generated text

        Raises:
            ConnectionError: If connection to LLM provider fails
            TimeoutError: If the operation times out
            RateLimitError: If the provider's rate limit is exceeded
            ServiceError: If the provider returns an API error
        """
        # In a real implementation, this would call the appropriate LLM API
        # For illustration, we're simulating the API call with error cases

        # Simulate different error scenarios
        if "timeout" in prompt.lower():
            raise eh.TimeoutError("LLM request timed out")
        elif "rate_limit" in prompt.lower():
            raise eh.RateLimitError("Rate limit exceeded")
        elif "error" in prompt.lower():
            raise eh.ServiceError("LLM service error")

        # Simulate successful response
        return f"Generated text for prompt: {prompt[:50]}... using model {model}"

    async def close(self) -> None:
        """Close the LLM client and release resources."""
        self.logger.info("LLM client closed")


#########################################
# Usage Example
#########################################


async def run_firestore_example() -> None:
    """Example of using the FirestoreClient class."""
    client = None
    try:
        # Initialize client
        client = FirestoreClient(project_id="example-project")

        # Use ResourceManager for proper cleanup
        async with eh.ResourceManager(client, "firestore_client"):
            # Save a document
            data = {
                "name": "Example Document",
                "timestamp": "2025-05-01T08:00:00Z",
                "attributes": {"key1": "value1", "key2": "value2"},
            }
            doc_id = await client.save_document("examples", "doc1", data)

            # Get the document back
            retrieved_data = await client.get_document("examples", doc_id)
            print(f"Retrieved document: {retrieved_data}")

            # Try to get a non-existent document
            try:
                await client.get_document("examples", "nonexistent_doc")
            except eh.NotFoundError as e:
                print(f"Got expected not found error: {e}")
    except eh.OrchestraError as e:
        # Handle Orchestra's custom exceptions
        error_logger = eh.ErrorLogger(__name__)
        error_id = error_logger.log_error(
            "run_firestore_example",
            e,
            include_traceback=True,
            context={"error_type": type(e).__name__},
        )
        print(f"Operation failed with error ID: {error_id}")
    finally:
        # ResourceManager should handle cleanup automatically,
        # but this is a fallback
        if client:
            await client.close()


async def run_llm_example() -> None:
    """Example of using the LLMClient class."""
    client = None
    try:
        # Initialize client
        client = LLMClient(api_key="sk-example-api-key", provider="openai")

        # Use ResourceManager for proper cleanup
        async with eh.ResourceManager(client, "llm_client"):
            # Generate text
            text = await client.generate_text(
                prompt="Explain the benefits of error handling patterns in distributed systems",
                model="gpt-4",
                max_tokens=500,
            )
            print(f"Generated text: {text}")

            # Try a prompt that will trigger a rate limit error
            try:
                await client.generate_text(prompt="This will cause a rate_limit error")
            except eh.RateLimitError as e:
                print(f"Got expected rate limit error: {e}")

    except eh.OrchestraError as e:
        # Handle Orchestra's custom exceptions
        error_logger = eh.ErrorLogger(__name__)
        error_id = error_logger.log_error(
            "run_llm_example",
            e,
            include_traceback=True,
            context={"error_type": type(e).__name__},
        )
        print(f"Operation failed with error ID: {error_id}")
    finally:
        # ResourceManager should handle cleanup automatically,
        # but this is a fallback
        if client:
            await client.close()


async def main() -> None:
    """Run the demonstration."""
    print("Running Firestore Example...")
    await run_firestore_example()

    print("\nRunning LLM Example...")
    await run_llm_example()


if __name__ == "__main__":
    print("Error Handling Demonstration")
    print("===========================")
    asyncio.run(main())
