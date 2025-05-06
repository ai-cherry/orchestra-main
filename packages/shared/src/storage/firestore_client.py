"""
Firestore client implementation for the AI Orchestration System.

This module provides a client for interacting with Google Cloud Firestore.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union, Tuple

# Import Firestore
try:
    from google.cloud import firestore
    from google.cloud.firestore_v1.base_query import FieldFilter
    from google.api_core.exceptions import GoogleAPIError
except ImportError:
    firestore = None

    class FieldFilter:
        pass

    class GoogleAPIError(Exception):
        pass

# Import GCP authentication utilities
try:
    from ..gcp.auth import get_gcp_credentials, get_project_id
except ImportError:
    # Fallback for older code structure
    try:
        from packages.shared.src.gcp.auth import get_gcp_credentials, get_project_id
    except ImportError:
        get_gcp_credentials = None
        get_project_id = None

# Configure logger
logger = logging.getLogger(__name__)


class FirestoreClient:
    """
    Client for interacting with Google Cloud Firestore.

    This class provides methods for storing, retrieving, and querying documents
    in Firestore collections.
    """

    def __init__(
        self, 
        project_id: Optional[str] = None, 
        credentials_path: Optional[str] = None,
        service_account_json: Optional[str] = None
    ):
        """
        Initialize a new FirestoreClient.

        Args:
            project_id: Optional Google Cloud project ID. If not provided,
                        it will be retrieved from environment variables.
            credentials_path: Optional path to service account credentials file.
            service_account_json: Optional service account key JSON string.
                                  Takes precedence over credentials_path if provided.
        """
        self._client = None
        self._project_id = project_id  # Will be set during initialization
        self._credentials_path = credentials_path or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        self._service_account_json = service_account_json or os.environ.get("GCP_SA_KEY_JSON")

        if firestore is None:
            logger.error("Google Cloud Firestore library not available. Install with: pip install google-cloud-firestore")
            raise ImportError("Google Cloud Firestore library not available")

        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize the Firestore client."""
        try:
            # Use the GCP auth module if available, otherwise fall back to direct initialization
            if get_gcp_credentials is not None:
                logger.debug("Using GCP auth module for Firestore authentication")
                
                # Get credentials and project_id from our auth utility
                credentials, project_id = get_gcp_credentials(
                    service_account_json=self._service_account_json,
                    service_account_file=self._credentials_path,
                    project_id=self._project_id
                )
                
                # Set the project_id from what was returned or passed in
                self._project_id = project_id or self._project_id
                
                # Create client with credentials
                self._client = firestore.Client(
                    project=self._project_id,
                    credentials=credentials
                )
            else:
                # Fall back to the original initialization logic
                logger.debug("Falling back to direct Firestore authentication")
                
                if self._service_account_json:
                    # Write service account JSON to a temporary file and use it
                    import tempfile
                    import json
                    
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
                    temp_file_path = temp_file.name
                    temp_file.write(self._service_account_json.encode('utf-8'))
                    temp_file.flush()
                    temp_file.close()
                    
                    self._client = firestore.Client.from_service_account_json(temp_file_path)
                    
                    # Clean up the temporary file
                    import os
                    os.unlink(temp_file_path)
                    
                    # Extract project_id from the service account JSON if not already set
                    if not self._project_id:
                        try:
                            sa_info = json.loads(self._service_account_json)
                            self._project_id = sa_info.get('project_id')
                        except (json.JSONDecodeError, KeyError):
                            logger.warning("Could not extract project_id from service account JSON")
                elif self._credentials_path:
                    self._client = firestore.Client.from_service_account_json(self._credentials_path)
                    
                    # Extract project_id from credentials file if not already set
                    if not self._project_id:
                        try:
                            import json
                            with open(self._credentials_path, 'r') as f:
                                sa_info = json.load(f)
                                self._project_id = sa_info.get('project_id')
                        except Exception:
                            pass
                else:
                    # Use Application Default Credentials
                    # If project_id is not explicitly set, try to get it from environment
                    if not self._project_id:
                        self._project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or \
                                           os.environ.get("GCP_PROJECT_ID")
                    
                    self._client = firestore.Client(project=self._project_id)
            
            logger.info(f"Firestore client initialized for project {self._project_id}")
        except GoogleAPIError as e:
            logger.error(f"Failed to initialize Firestore client: {e}")
            raise ConnectionError(f"Failed to initialize Firestore connection: {e}")
        except Exception as e:
            logger.error(f"Unexpected error initializing Firestore client: {e}")
            raise

    async def save_document(
        self, collection: str, doc_id: str, data: Dict[str, Any]
    ) -> None:
        """
        Save a document to a Firestore collection.

        Args:
            collection: The name of the collection to save to
            doc_id: The document ID
            data: The document data to save
        """
        if not self._client:
            raise RuntimeError("Firestore client not initialized")
        
        try:
            # Convert datetime objects to Firestore timestamps
            processed_data = self._process_data_for_firestore(data)
            
            # Add the document to Firestore
            self._client.collection(collection).document(doc_id).set(processed_data)
            logger.debug(f"Saved document {doc_id} to collection {collection}")
        except Exception as e:
            logger.error(f"Error saving document to Firestore: {e}")
            raise

    async def get_document(
        self, collection: str, doc_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document from a Firestore collection.

        Args:
            collection: The name of the collection to retrieve from
            doc_id: The document ID to retrieve

        Returns:
            The document data or None if not found
        """
        if not self._client:
            raise RuntimeError("Firestore client not initialized")
        
        try:
            doc_ref = self._client.collection(collection).document(doc_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                logger.debug(f"Document {doc_id} not found in collection {collection}")
                return None
                
            return doc.to_dict()
        except Exception as e:
            logger.error(f"Error retrieving document from Firestore: {e}")
            raise

    async def query_collection(
        self, 
        collection: str, 
        filters: List[Union[Tuple[str, str, Any], Dict[str, Any]]] = None,
        order_by: Optional[List[Tuple[str, str]]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Query documents from a Firestore collection.

        Args:
            collection: The name of the collection to query
            filters: A list of filter conditions as tuples (field, operator, value) 
                    or a list of dictionaries for simple equality filters
            order_by: Optional list of fields to order by with direction ('asc' or 'desc')
            limit: Optional maximum number of documents to return

        Returns:
            A list of documents matching the query
        """
        if not self._client:
            raise RuntimeError("Firestore client not initialized")
        
        try:
            query = self._client.collection(collection)
            
            # Apply filters if provided
            if filters:
                for filter_item in filters:
                    if isinstance(filter_item, tuple) and len(filter_item) == 3:
                        field, op, value = filter_item
                        query = query.where(field, op, value)
                    elif isinstance(filter_item, dict):
                        for field, value in filter_item.items():
                            query = query.where(field, "==", value)
            
            # Apply ordering
            if order_by:
                for field, direction in order_by:
                    if direction.lower() == 'desc':
                        query = query.order_by(field, direction=firestore.Query.DESCENDING)
                    else:
                        query = query.order_by(field, direction=firestore.Query.ASCENDING)
            
            # Apply limit
            if limit:
                query = query.limit(limit)
                
            # Execute query and get results
            docs = query.stream()
            results = [doc.to_dict() for doc in docs]
            
            logger.debug(f"Query returned {len(results)} documents from collection {collection}")
            return results
        except Exception as e:
            logger.error(f"Error querying collection in Firestore: {e}")
            raise

    async def delete_document(self, collection: str, doc_id: str) -> None:
        """
        Delete a document from a Firestore collection.

        Args:
            collection: The name of the collection
            doc_id: The document ID to delete
        """
        if not self._client:
            raise RuntimeError("Firestore client not initialized")
        
        try:
            self._client.collection(collection).document(doc_id).delete()
            logger.debug(f"Deleted document {doc_id} from collection {collection}")
        except Exception as e:
            logger.error(f"Error deleting document from Firestore: {e}")
            raise
            
    def _process_data_for_firestore(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data before saving to Firestore to handle special types.
        
        Args:
            data: The data to process
            
        Returns:
            Processed data suitable for Firestore
        """
        processed = {}
        
        for key, value in data.items():
            # Handle datetime objects
            if hasattr(value, 'isoformat') and callable(getattr(value, 'isoformat')):
                processed[key] = firestore.SERVER_TIMESTAMP if value is None else value
            # Handle nested dictionaries
            elif isinstance(value, dict):
                processed[key] = self._process_data_for_firestore(value)
            # Handle lists with possible nested objects
            elif isinstance(value, list):
                processed[key] = [
                    self._process_data_for_firestore(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                processed[key] = value
                
        return processed
