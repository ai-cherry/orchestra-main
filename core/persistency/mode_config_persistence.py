#!/usr/bin/env python3
"""
Mode Configuration Persistence Manager for AI Orchestra

This module provides a persistence system for the enhanced mode configuration,
ensuring settings are maintained across restarts, rebuilds, and deployments.
It supports multiple storage backends:

1. Local filesystem - For development and standalone deployments
2. Environment variables - For configuration override and simple deployments
3. Optional GCP integrations when available:
   - Google Cloud Storage - For cross-environment synchronization
   - Secret Manager - For secure storage of sensitive configurations
   - mongodb - For structured query access to configuration

Usage:
    from core.persistency.mode_config_persistence import get_persistence_manager

    # Save configuration to all available backends
    manager = get_persistence_manager()
    manager.save_mode_definitions()

    # Load configuration from most reliable source
    config = manager.load_mode_definitions()
"""

import hashlib
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CONFIG_DIR = PROJECT_ROOT / "config"
MODE_DEFINITIONS_PATH = CONFIG_DIR / "mode_definitions.yaml"
WORKFLOW_STATE_PATH = CONFIG_DIR / "workflow_state.yaml"
BACKUP_DIR = CONFIG_DIR / "backups"

# Environment variable names
ENV_PROJECT_ID = "MODE_SYSTEM_PROJECT_ID"
ENV_ENVIRONMENT = "MODE_SYSTEM_ENVIRONMENT"
ENV_BUCKET = "MODE_SYSTEM_BUCKET"
ENV_SECRET = "MODE_SYSTEM_SECRET"
ENV_COLLECTION = "MODE_SYSTEM_COLLECTION"

# Default values
DEFAULT_PROJECT_ID = os.environ.get(ENV_PROJECT_ID, "cherry-ai-project")
DEFAULT_ENVIRONMENT = os.environ.get(ENV_ENVIRONMENT, "development")
DEFAULT_BUCKET = os.environ.get(ENV_BUCKET, f"{DEFAULT_PROJECT_ID}-mode-config")
DEFAULT_SECRET = os.environ.get(ENV_SECRET, "mode-system-config")
DEFAULT_COLLECTION = os.environ.get(ENV_COLLECTION, "mode_system_config")

# Optional integrations
try:
    from google.api_core import exceptions as gcp_exceptions
    # Removed GCP import import storage
except ImportError:
    storage = None
    gcp_exceptions = None

            # Check for GCP environment indicators
            # GCP environment indicator check (was unused variable)
            (
                os.environ.get("VULTR_PROJECT_ID") is not None
                or os.environ.get("K_SERVICE") is not None
                or os.path.exists("/var/run/secrets/kubernetes.io")
            )

            return True
        except ImportError:
            logger.info("Google Cloud libraries not available. Operating in local-only mode.")
            return False

    def _initialize_gcp_clients(self):
        """Initialize Google Cloud clients if possible."""
        try:
            # Import GCP libraries

            # Initialize Cloud Storage client
            try:
                self.storage_client = storage.Client(project=self.project_id)
                logger.debug("Initialized Cloud Storage client")
            except Exception as e:
                logger.warning(f"Failed to initialize Cloud Storage client: {str(e)}")

            # Initialize mongodb client
            try:
                self.firestore_client = mongodb.Client(project=self.project_id)
                logger.debug("Initialized mongodb client")
            except Exception as e:
                logger.warning(f"Failed to initialize mongodb client: {str(e)}")

        except ImportError:
            logger.info("Failed to import Google Cloud libraries.")
            self.gcp_enabled = False
        except Exception as e:
            logger.warning(f"Error initializing Google Cloud clients: {str(e)}")
            self.gcp_enabled = False

    def _validate_yaml_config(self, content: str) -> Dict[str, Any]:
        """
        Validate YAML configuration content.

        Args:
            content: YAML content to validate

        Returns:
            Parsed YAML content if valid

        Raises:
            PersistenceError: If validation fails
        """
        try:
            # Parse YAML
            config = yaml.safe_load(content)

            # Check for required sections
            if not isinstance(config, dict):
                raise PersistenceError("Invalid configuration format: root must be a dictionary")

            if "modes" not in config:
                raise PersistenceError("Invalid configuration: 'modes' section is required")

            # Validate modes section
            modes = config["modes"]
            if not isinstance(modes, dict):
                raise PersistenceError("Invalid configuration: 'modes' must be a dictionary")

            # Check each mode has required fields
            for mode_slug, mode_data in modes.items():
                required_fields = ["name", "model", "description"]
                for field in required_fields:
                    if field not in mode_data:
                        raise PersistenceError(f"Invalid mode '{mode_slug}': missing required field '{field}'")

            # Validate workflows section if present
            if "workflows" in config:
                workflows = config["workflows"]
                if not isinstance(workflows, dict):
                    raise PersistenceError("Invalid configuration: 'workflows' must be a dictionary")

                # Check each workflow has required fields
                for workflow_slug, workflow_data in workflows.items():
                    required_fields = ["name", "description", "steps"]
                    for field in required_fields:
                        if field not in workflow_data:
                            raise PersistenceError(
                                f"Invalid workflow '{workflow_slug}': missing required field '{field}'"
                            )

                    # Check steps
                    steps = workflow_data["steps"]
                    if not isinstance(steps, list):
                        raise PersistenceError(f"Invalid workflow '{workflow_slug}': 'steps' must be a list")

                    for i, step in enumerate(steps):
                        if "mode" not in step or "task" not in step:
                            raise PersistenceError(
                                f"Invalid step {i+1} in workflow '{workflow_slug}': "
                                + "missing required field 'mode' or 'task'"
                            )

                        # Check mode exists
                        if step["mode"] not in modes:
                            raise PersistenceError(
                                f"Invalid step {i+1} in workflow '{workflow_slug}': "
                                + f"mode '{step['mode']}' does not exist"
                            )

            return config

        except yaml.YAMLError as e:
            raise PersistenceError(f"Invalid YAML: {str(e)}")
        except PersistenceError:
            raise
        except Exception as e:
            raise PersistenceError(f"Validation error: {str(e)}")

    def _create_backup(self, file_path: Path) -> Optional[Path]:
        """
        Create a backup of a configuration file.

        Args:
            file_path: Path to the file to backup

        Returns:
            Path to the backup file or None if backup failed
        """
        if not file_path.exists():
            logger.warning(f"Cannot backup non-existent file: {file_path}")
            return None

        # Create timestamp for backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = file_path.name
        backup_name = f"{file_name}.{timestamp}.bak"
        backup_path = BACKUP_DIR / backup_name

        # Copy file to backup
        try:
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup of {file_path} at {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup of {file_path}: {str(e)}")
            return None

    def save_mode_definitions(self) -> bool:
        """
        Save mode definitions to persistent storage.

        Returns:
            True if save was successful, False otherwise
        """
        if not MODE_DEFINITIONS_PATH.exists():
            logger.error(f"Mode definitions file does not exist: {MODE_DEFINITIONS_PATH}")
            return False

        # Create backup of mode definitions
        backup_path = self._create_backup(MODE_DEFINITIONS_PATH)

        # Read current mode definitions
        try:
            with open(MODE_DEFINITIONS_PATH, "r") as f:
                content = f.read()

            # Validate configuration
            try:
                self._validate_yaml_config(content)
            except PersistenceError as e:
                logger.error(f"Invalid mode configuration: {str(e)}")
                # Restore backup if available
                if backup_path:
                    shutil.copy2(backup_path, MODE_DEFINITIONS_PATH)
                    logger.info(f"Restored backup from {backup_path}")
                return False

            # Save to each persistence layer
            success = True

            # 1. Local file (already exists)
            logger.info(f"Mode definitions already saved locally at {MODE_DEFINITIONS_PATH}")

            # 2. Save to Cloud Storage
            if self.gcp_enabled and self.storage_client:
                try:
                    from google.api_core.exceptions import NotFound

                    # Check if bucket exists
                    try:
                        bucket = self.storage_client.get_bucket(self.bucket_name)
                    except NotFound:
                        # Create bucket if it doesn't exist
                        bucket = self.storage_client.create_bucket(self.bucket_name, location="us-central1")
                        logger.info(f"Created bucket {self.bucket_name}")

                    # Create blob with path based on environment
                    blob_path = f"{self.environment}/mode_definitions.yaml"
                    blob = bucket.blob(blob_path)
                    blob.upload_from_string(content)
                    logger.info(f"Saved mode definitions to Cloud Storage: gs://{self.bucket_name}/{blob_path}")
                except Exception as e:
                    logger.error(f"Failed to save mode definitions to Cloud Storage: {str(e)}")
                    success = False

            # 4. Save to mongodb
            if self.gcp_enabled and self.firestore_client:
                try:

                    # Save as document with environment as ID
                    doc_ref = self.firestore_client.collection(self.collection_name).document("mode_definitions")
                    doc_ref.set(
                        {
                            "environment": self.environment,
                            "content": content,
                            "updated_at": mongodb.SERVER_TIMESTAMP,
                            "version": hashlib.md5(content.encode()).hexdigest(),
                        }
                    )
                    logger.info(f"Saved mode definitions to mongodb collection: {self.collection_name}")
                except Exception as e:
                    logger.error(f"Failed to save mode definitions to mongodb: {str(e)}")
                    success = False

            return success

        except Exception as e:
            logger.error(f"Failed to save mode definitions: {str(e)}")
            return False

    def save_workflow_state(self, state: Dict[str, Any]) -> bool:
        """
        Save workflow state to persistent storage.

        Args:
            state: Workflow state to save

        Returns:
            True if save was successful, False otherwise
        """
        if not state:
            logger.warning("No workflow state provided")
            return False

        # Convert state to YAML
        try:
            content = yaml.dump(state)
        except Exception as e:
            logger.error(f"Failed to serialize workflow state: {str(e)}")
            return False

        # Create backup if file exists
        if WORKFLOW_STATE_PATH.exists():
            self._create_backup(WORKFLOW_STATE_PATH)

        # Save to local file
        try:
            with open(WORKFLOW_STATE_PATH, "w") as f:
                f.write(content)
            logger.info(f"Saved workflow state locally to {WORKFLOW_STATE_PATH}")
        except Exception as e:
            logger.error(f"Failed to save workflow state locally: {str(e)}")
            return False

        # Save to GCP services if enabled
        if self.gcp_enabled:
            success = True

            # 1. Save to Cloud Storage
            if self.storage_client:
                try:
                    bucket = self.storage_client.bucket(self.bucket_name)
                    blob_path = f"{self.environment}/workflow_state.yaml"
                    blob = bucket.blob(blob_path)
                    blob.upload_from_string(content)
                    logger.info(f"Saved workflow state to Cloud Storage: gs://{self.bucket_name}/{blob_path}")
                except Exception as e:
                    logger.error(f"Failed to save workflow state to Cloud Storage: {str(e)}")
                    success = False

            # 2. Save to mongodb
            if self.firestore_client:
                try:

                    doc_ref = self.firestore_client.collection(self.collection_name).document("workflow_state")
                    doc_ref.set(
                        {
                            "environment": self.environment,
                            "content": content,
                            "updated_at": mongodb.SERVER_TIMESTAMP,
                        }
                    )
                    logger.info("Saved workflow state to mongodb")
                except Exception as e:
                    logger.error(f"Failed to save workflow state to mongodb: {str(e)}")
                    success = False

            return success

        return True

    def load_mode_definitions(self) -> Optional[Dict[str, Any]]:
        """
        Load mode definitions from persistent storage.

        Returns:
            Mode definitions as dictionary if found, None otherwise
        """
        content = None
        source = None

        # Try all possible sources in order of preference

        # 1. Try local file first
        if MODE_DEFINITIONS_PATH.exists():
            try:
                with open(MODE_DEFINITIONS_PATH, "r") as f:
                    content = f.read()
                source = "local file"
                logger.info(f"Loaded mode definitions from local file: {MODE_DEFINITIONS_PATH}")
            except Exception as e:
                logger.error(f"Failed to load mode definitions from local file: {str(e)}")

        # 2. Try GCP Cloud Storage
        if not content and self.gcp_enabled and self.storage_client:
            try:
                from google.api_core.exceptions import NotFound

                bucket = self.storage_client.bucket(self.bucket_name)
                blob_path = f"{self.environment}/mode_definitions.yaml"
                blob = bucket.blob(blob_path)
                content = blob.download_as_text()
                source = "Cloud Storage"
                logger.info(f"Loaded mode definitions from Cloud Storage: gs://{self.bucket_name}/{blob_path}")
            except NotFound:
                logger.warning("Mode definitions not found in Cloud Storage")
            except Exception as e:
                logger.error(f"Failed to load mode definitions from Cloud Storage: {str(e)}")

        # 4. Try mongodb
        if not content and self.gcp_enabled and self.firestore_client:
            try:
                doc_ref = self.firestore_client.collection(self.collection_name).document("mode_definitions")
                doc = doc_ref.get()
                if doc.exists:
                    content = doc.to_dict().get("content")
                    source = "mongodb"
                    logger.info("Loaded mode definitions from mongodb")
                else:
                    logger.warning("Mode definitions not found in mongodb")
            except Exception as e:
                logger.error(f"Failed to load mode definitions from mongodb: {str(e)}")

        # If content was loaded, parse and validate
        if content:
            try:
                config = self._validate_yaml_config(content)
                logger.info(f"Successfully loaded and validated mode definitions from {source}")

                # Save to local file if loaded from remote source
                if source != "local file":
                    try:
                        os.makedirs(os.path.dirname(MODE_DEFINITIONS_PATH), exist_ok=True)
                        with open(MODE_DEFINITIONS_PATH, "w") as f:
                            f.write(content)
                        logger.info(f"Saved remote mode definitions to local file: {MODE_DEFINITIONS_PATH}")
                    except Exception as e:
                        logger.error(f"Failed to save remote mode definitions locally: {str(e)}")

                return config
            except PersistenceError as e:
                logger.error(f"Invalid mode definitions loaded from {source}: {str(e)}")
                return None

        logger.error("Failed to load mode definitions from any source")
        return None

    def load_workflow_state(self) -> Optional[Dict[str, Any]]:
        """
        Load workflow state from persistent storage.

        Returns:
            Workflow state as dictionary if found, None otherwise
        """
        content = None
        source = None

        # 1. Try local file first
        if WORKFLOW_STATE_PATH.exists():
            try:
                with open(WORKFLOW_STATE_PATH, "r") as f:
                    content = f.read()
                source = "local file"
                logger.info(f"Loaded workflow state from local file: {WORKFLOW_STATE_PATH}")
            except Exception as e:
                logger.error(f"Failed to load workflow state from local file: {str(e)}")

        # 2. Try GCP Cloud Storage
        if not content and self.gcp_enabled and self.storage_client:
            try:
                from google.api_core.exceptions import NotFound

                bucket = self.storage_client.bucket(self.bucket_name)
                blob_path = f"{self.environment}/workflow_state.yaml"
                blob = bucket.blob(blob_path)
                content = blob.download_as_text()
                source = "Cloud Storage"
                logger.info(f"Loaded workflow state from Cloud Storage: gs://{self.bucket_name}/{blob_path}")
            except NotFound:
                logger.warning("Workflow state not found in Cloud Storage")
            except Exception as e:
                logger.error(f"Failed to load workflow state from Cloud Storage: {str(e)}")

        # 3. Try mongodb
        if not content and self.gcp_enabled and self.firestore_client:
            try:
                doc_ref = self.firestore_client.collection(self.collection_name).document("workflow_state")
                doc = doc_ref.get()
                if doc.exists:
                    content = doc.to_dict().get("content")
                    source = "mongodb"
                    logger.info("Loaded workflow state from mongodb")
                else:
                    logger.warning("Workflow state not found in mongodb")
            except Exception as e:
                logger.error(f"Failed to load workflow state from mongodb: {str(e)}")

        # If content was loaded, parse
        if content:
            try:
                state = yaml.safe_load(content)
                logger.info(f"Successfully loaded workflow state from {source}")

                # Save to local file if loaded from remote source
                if source != "local file":
                    try:
                        os.makedirs(os.path.dirname(WORKFLOW_STATE_PATH), exist_ok=True)
                        with open(WORKFLOW_STATE_PATH, "w") as f:
                            f.write(content)
                        logger.info(f"Saved remote workflow state to local file: {WORKFLOW_STATE_PATH}")
                    except Exception as e:
                        logger.error(f"Failed to save remote workflow state locally: {str(e)}")

                return state
            except yaml.YAMLError as e:
                logger.error(f"Invalid workflow state loaded from {source}: {str(e)}")
                return None

        logger.warning("No workflow state found")
        return None

    def sync_configurations(self) -> bool:
        """
        Sync configurations across all storage layers.

        This ensures all persistence layers have the same configuration.

        Returns:
            True if sync was successful, False otherwise
        """
        # Load configuration from all sources
        sources = []

        # 1. Local file
        local_config = None
        if MODE_DEFINITIONS_PATH.exists():
            try:
                with open(MODE_DEFINITIONS_PATH, "r") as f:
                    local_content = f.read()
                    local_config = self._validate_yaml_config(local_content)
                    local_hash = hashlib.md5(local_content.encode()).hexdigest()
                    sources.append(("local_file", local_content, local_hash))
            except Exception as e:
                logger.error(f"Failed to load mode definitions from local file: {str(e)}")

        # 2. Secret Manager
        if self.gcp_enabled and self.os.environ_client:
            try:
                from google.api_core.exceptions import NotFound

                secret_name = f"projects/{self.project_id}/secrets/{self.secret_name}/versions/latest"
                response = self.os.environ_client.access_secret_version(request={"name": secret_name})
                secret_content = response.payload.data.decode("UTF-8")
                self._validate_yaml_config(secret_content)
                secret_hash = hashlib.md5(secret_content.encode()).hexdigest()
                sources.append(("os.environ", secret_content, secret_hash))
            except NotFound:
                logger.warning("Mode definitions not found in Secret Manager")
            except Exception as e:
                logger.error(f"Failed to load mode definitions from Secret Manager: {str(e)}")

        # 3. Cloud Storage
        if self.gcp_enabled and self.storage_client:
            try:
                from google.api_core.exceptions import NotFound

                bucket = self.storage_client.bucket(self.bucket_name)
                blob_path = f"{self.environment}/mode_definitions.yaml"
                blob = bucket.blob(blob_path)
                storage_content = blob.download_as_text()
                self._validate_yaml_config(storage_content)
                storage_hash = hashlib.md5(storage_content.encode()).hexdigest()
                sources.append(("cloud_storage", storage_content, storage_hash))
            except NotFound:
                logger.warning("Mode definitions not found in Cloud Storage")
            except Exception as e:
                logger.error(f"Failed to load mode definitions from Cloud Storage: {str(e)}")

        # 4. mongodb
        if self.gcp_enabled and self.firestore_client:
            try:
                doc_ref = self.firestore_client.collection(self.collection_name).document("mode_definitions")
                doc = doc_ref.get()
                if doc.exists:
                    firestore_content = doc.to_dict().get("content")
                    self._validate_yaml_config(firestore_content)
                    firestore_hash = hashlib.md5(firestore_content.encode()).hexdigest()
                    sources.append(("mongodb", firestore_content, firestore_hash))
                else:
                    logger.warning("Mode definitions not found in mongodb")
            except Exception as e:
                logger.error(f"Failed to load mode definitions from mongodb: {str(e)}")

        # If no sources found, return False
        if not sources:
            logger.error("No mode definitions found in any source")
            return False

        # Compare hashes to see if they all match
        hashes = [source[2] for source in sources]
        if len(set(hashes)) == 1:
            logger.info("All configuration sources are in sync")
            return True

        # Find the most recent/authoritative source
        # For now, we'll use the local file if it exists
        # In a production environment, you might want to use timestamp metadata
        source_to_use = None
        for source in sources:
            if source[0] == "local_file" and local_config:
                source_to_use = source
                break

        # If local file doesn't exist, use the first source
        if not source_to_use:
            source_to_use = sources[0]

        logger.info(f"Using {source_to_use[0]} as the authoritative source for syncing")

        # Sync to all destinations
        content_to_sync = source_to_use[1]

        # 1. Sync to local file
        if source_to_use[0] != "local_file":
            try:
                os.makedirs(os.path.dirname(MODE_DEFINITIONS_PATH), exist_ok=True)
                with open(MODE_DEFINITIONS_PATH, "w") as f:
                    f.write(content_to_sync)
                logger.info(f"Synced configuration to local file: {MODE_DEFINITIONS_PATH}")
            except Exception as e:
                logger.error(f"Failed to sync configuration to local file: {str(e)}")
                return False

        # 2. Sync to Secret Manager
        if self.gcp_enabled and self.os.environ_client and source_to_use[0] != "os.environ":
            try:
                from google.api_core.exceptions import NotFound

                secret_name = f"projects/{self.project_id}/secrets/{self.secret_name}"

                try:
                    # Check if secret exists
                    self.os.environ_client.get_secret(request={"name": secret_name})
                except NotFound:
                    # Create secret if it doesn't exist
                    self.os.environ_client.create_secret(
                        request={
                            "parent": f"projects/{self.project_id}",
                            "secret_id": self.secret_name,
                            "secret": {"replication": {"automatic": {}}},
                        }
                    )
                    logger.info(f"Created secret {self.secret_name}")

                # Add new secret version
                self.os.environ_client.add_secret_version(
                    request={
                        "parent": secret_name,
                        "payload": {"data": content_to_sync.encode("UTF-8")},
                    }
                )
                logger.info(f"Synced configuration to Secret Manager: {secret_name}")
            except Exception as e:
                logger.error(f"Failed to sync configuration to Secret Manager: {str(e)}")
                return False

        # 3. Sync to Cloud Storage
        if self.gcp_enabled and self.storage_client and source_to_use[0] != "cloud_storage":
            try:
                from google.api_core.exceptions import NotFound

                bucket = None
                try:
                    bucket = self.storage_client.get_bucket(self.bucket_name)
                except NotFound:
                    # Create bucket if it doesn't exist
                    bucket = self.storage_client.create_bucket(self.bucket_name, location="us-central1")
                    logger.info(f"Created bucket {self.bucket_name}")

                # Create blob with path based on environment
                blob_path = f"{self.environment}/mode_definitions.yaml"
                blob = bucket.blob(blob_path)
                blob.upload_from_string(content_to_sync)
                logger.info(f"Synced configuration to Cloud Storage: gs://{self.bucket_name}/{blob_path}")
            except Exception as e:
                logger.error(f"Failed to sync configuration to Cloud Storage: {str(e)}")
                return False

        # 4. Sync to mongodb
        if self.gcp_enabled and self.firestore_client and source_to_use[0] != "mongodb":
            try:

                doc_ref = self.firestore_client.collection(self.collection_name).document("mode_definitions")
                doc_ref.set(
                    {
                        "environment": self.environment,
                        "content": content_to_sync,
                        "updated_at": mongodb.SERVER_TIMESTAMP,
                        "version": hashlib.md5(content_to_sync.encode()).hexdigest(),
                    }
                )
                logger.info(f"Synced configuration to mongodb collection: {self.collection_name}")
            except Exception as e:
                logger.error(f"Failed to sync configuration to mongodb: {str(e)}")
                return False

        return True

# Singleton instance
_instance = None

def get_persistence_manager() -> PersistenceManager:
    """Get singleton instance of PersistenceManager."""
    global _instance
    if _instance is None:
        _instance = PersistenceManager()
    return _instance

if __name__ == "__main__":
    # Simple CLI for testing the persistence manager
    import argparse

    parser = argparse.ArgumentParser(description="Mode Configuration Persistence Manager")
    parser.add_argument(
        "--action",
        choices=["save", "load", "sync"],
        required=True,
        help="Action to perform",
    )
    parser.add_argument("--project", help="GCP project ID")
    parser.add_argument("--env", help="Deployment environment")

    args = parser.parse_args()

    manager = PersistenceManager(project_id=args.project, environment=args.env)

    if args.action == "save":
        if manager.save_mode_definitions():
            print("Mode definitions saved successfully")
        else:
            print("Failed to save mode definitions")
            sys.exit(1)
    elif args.action == "load":
        config = manager.load_mode_definitions()
        if config:
            print("Mode definitions loaded successfully")
            print(f"Loaded {len(config.get('modes', {}))} modes and {len(config.get('workflows', {}))} workflows")
        else:
            print("Failed to load mode definitions")
            sys.exit(1)
    elif args.action == "sync":
        if manager.sync_configurations():
            print("Configuration synced successfully")
        else:
            print("Failed to sync configuration")
            sys.exit(1)
