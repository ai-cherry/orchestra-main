import os
# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
CONFIG_DIR = PROJECT_T / "config"
MODE_DEFINITIONS_PATH = CONFIG_DIR / "mode_definitions.yaml"
WORKFLOW_STATE_PATH = CONFIG_DIR / "workflow_state.yaml"
BACKUP_DIR = CONFIG_DIR / "backups"

# Environment variable names
ENV_PROJECT_ID = "MODE_SYSTEM_PROJECT_ID"
ENV_ENVIRONMENT = "MODE_SYSTEM_ENVIRONMENT"
ENV_BUCKET = "MODE_SYSTEM_BUCKET"
ENV_SECRET = os.getenv('SECRET')
ENV_COLLECTION = "MODE_SYSTEM_COLLECTION"

# Default values
DEFAULT_PROJECT_ID = os.environ.get(ENV_PROJECT_ID, "cherry-ai-project")
DEFAULT_ENVIRONMENT = os.environ.get(ENV_ENVIRONMENT, "development")
DEFAULT_BUCKET = os.environ.get(ENV_BUCKET, f"{DEFAULT_PROJECT_ID}-mode-config")
DEFAULT_SECRET = os.environ.get(ENV_SECRET, "mode-system-config")
DEFAULT_COLLECTION = os.environ.get(ENV_COLLECTION, "mode_system_config")

# Optional integrations
try:

    pass
    from google.api_core import except Exception:
     pass
    storage = None
    gcp_exceptions = None

            # Check for GCP environment indicators
            # GCP environment indicator check (was unused variable)
            (
                os.environ.get("LAMBDA_PROJECT_ID") is not None
                or os.environ.get("K_SERVICE") is not None
                or os.path.exists("/var/run/secrets/kubernetes.io")
            )

            return True
        except Exception:

            pass
            logger.info("Google Cloud libraries not available. Operating in local-only mode.")
            return False

    def _initialize_gcp_clients(self):
        """Initialize Google Cloud clients if possible."""
            except Exception:

                pass
                logger.warning(f"Failed to initialize Cloud Storage client: {str(e)}")

            try:

                pass
            except Exception:

                pass

        except Exception:


            pass
            logger.info("Failed to import Google Cloud libraries.")
            self.gcp_enabled = False
        except Exception:

            pass
            logger.warning(f"Error initializing Google Cloud clients: {str(e)}")
            self.gcp_enabled = False

    def _validate_yaml_config(self, content: str) -> Dict[str, Any]:
        """
        """

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

        except Exception:


            pass
            raise PersistenceError(f"Invalid YAML: {str(e)}")
        except Exception:

            pass
            raise
        except Exception:

            pass
            raise PersistenceError(f"Validation error: {str(e)}")

    def _create_backup(self, file_path: Path) -> Optional[Path]:
        """
        """
            logger.warning(f"Cannot backup non-existent file: {file_path}")
            return None

        # Create timestamp for backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = file_path.name
        backup_name = f"{file_name}.{timestamp}.bak"
        backup_path = BACKUP_DIR / backup_name

        # Copy file to backup
        try:

            pass
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup of {file_path} at {backup_path}")
            return backup_path
        except Exception:

            pass
            logger.error(f"Failed to create backup of {file_path}: {str(e)}")
            return None

    def save_mode_definitions(self) -> bool:
        """
        """
            logger.error(f"Mode definitions file does not exist: {MODE_DEFINITIONS_PATH}")
            return False

        # Create backup of mode definitions
        backup_path = self._create_backup(MODE_DEFINITIONS_PATH)

        # Read current mode definitions
        try:

            pass
            with open(MODE_DEFINITIONS_PATH, "r") as f:
                content = f.read()

            # Validate configuration
            try:

                pass
                self._validate_yaml_config(content)
            except Exception:

                pass
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

                    pass
                    from google.api_core.exceptions import NotFound

                    # Check if bucket exists
                    try:

                        pass
                        bucket = self.storage_client.get_bucket(self.bucket_name)
                    except Exception:

                        pass
                        # Create bucket if it doesn't exist
                        bucket = self.storage_client.create_bucket(self.bucket_name, location="us-central1")
                        logger.info(f"Created bucket {self.bucket_name}")

                    # Create blob with path based on environment
                    blob_path = f"{self.environment}/mode_definitions.yaml"
                    blob = bucket.blob(blob_path)
                    blob.upload_from_string(content)
                    logger.info(f"Saved mode definitions to Cloud Storage: gs://{self.bucket_name}/{blob_path}")
                except Exception:

                    pass
                    logger.error(f"Failed to save mode definitions to Cloud Storage: {str(e)}")
                    success = False

            if self.gcp_enabled and self.firestore_client:
                try:

                    pass
                    # Save as document with environment as ID
                    doc_ref = self.firestore_client.collection(self.collection_name).document("mode_definitions")
                    doc_ref.set(
                        {
                            "environment": self.environment,
                            "content": content,
                            "version": hashlib.md5(content.encode()).hexdigest(),
                        }
                    )
                except Exception:

                    pass
                    success = False

            return success

        except Exception:


            pass
            logger.error(f"Failed to save mode definitions: {str(e)}")
            return False

    def save_workflow_state(self, state: Dict[str, Any]) -> bool:
        """
        """
            logger.warning("No workflow state provided")
            return False

        # Convert state to YAML
        try:

            pass
            content = yaml.dump(state)
        except Exception:

            pass
            logger.error(f"Failed to serialize workflow state: {str(e)}")
            return False

        # Create backup if file exists
        if WORKFLOW_STATE_PATH.exists():
            self._create_backup(WORKFLOW_STATE_PATH)

        # Save to local file
        try:

            pass
            with open(WORKFLOW_STATE_PATH, "w") as f:
                f.write(content)
            logger.info(f"Saved workflow state locally to {WORKFLOW_STATE_PATH}")
        except Exception:

            pass
            logger.error(f"Failed to save workflow state locally: {str(e)}")
            return False

        # Save to GCP services if enabled
        if self.gcp_enabled:
            success = True

            # 1. Save to Cloud Storage
            if self.storage_client:
                try:

                    pass
                    bucket = self.storage_client.bucket(self.bucket_name)
                    blob_path = f"{self.environment}/workflow_state.yaml"
                    blob = bucket.blob(blob_path)
                    blob.upload_from_string(content)
                    logger.info(f"Saved workflow state to Cloud Storage: gs://{self.bucket_name}/{blob_path}")
                except Exception:

                    pass
                    logger.error(f"Failed to save workflow state to Cloud Storage: {str(e)}")
                    success = False

            if self.firestore_client:
                try:

                    pass
                    doc_ref = self.firestore_client.collection(self.collection_name).document("workflow_state")
                    doc_ref.set(
                        {
                            "environment": self.environment,
                            "content": content,
                        }
                    )
                except Exception:

                    pass
                    success = False

            return success

        return True

    def load_mode_definitions(self) -> Optional[Dict[str, Any]]:
        """
        """
                with open(MODE_DEFINITIONS_PATH, "r") as f:
                    content = f.read()
                source = "local file"
                logger.info(f"Loaded mode definitions from local file: {MODE_DEFINITIONS_PATH}")
            except Exception:

                pass
                logger.error(f"Failed to load mode definitions from local file: {str(e)}")

        # 2. Try GCP Cloud Storage
        if not content and self.gcp_enabled and self.storage_client:
            try:

                pass
                from google.api_core.exceptions import NotFound

                bucket = self.storage_client.bucket(self.bucket_name)
                blob_path = f"{self.environment}/mode_definitions.yaml"
                blob = bucket.blob(blob_path)
                content = blob.download_as_text()
                source = "Cloud Storage"
                logger.info(f"Loaded mode definitions from Cloud Storage: gs://{self.bucket_name}/{blob_path}")
            except Exception:

                pass
                logger.warning("Mode definitions not found in Cloud Storage")
            except Exception:

                pass
                logger.error(f"Failed to load mode definitions from Cloud Storage: {str(e)}")

        if not content and self.gcp_enabled and self.firestore_client:
            try:

                pass
                doc_ref = self.firestore_client.collection(self.collection_name).document("mode_definitions")
                doc = doc_ref.get()
                if doc.exists:
                    content = doc.to_dict().get("content")
                else:
            except Exception:

                pass

        # If content was loaded, parse and validate
        if content:
            try:

                pass
                config = self._validate_yaml_config(content)
                logger.info(f"Successfully loaded and validated mode definitions from {source}")

                # Save to local file if loaded from remote source
                if source != "local file":
                    try:

                        pass
                        os.makedirs(os.path.dirname(MODE_DEFINITIONS_PATH), exist_ok=True)
                        with open(MODE_DEFINITIONS_PATH, "w") as f:
                            f.write(content)
                        logger.info(f"Saved remote mode definitions to local file: {MODE_DEFINITIONS_PATH}")
                    except Exception:

                        pass
                        logger.error(f"Failed to save remote mode definitions locally: {str(e)}")

                return config
            except Exception:

                pass
                logger.error(f"Invalid mode definitions loaded from {source}: {str(e)}")
                return None

        logger.error("Failed to load mode definitions from any source")
        return None

    def load_workflow_state(self) -> Optional[Dict[str, Any]]:
        """
        """
                with open(WORKFLOW_STATE_PATH, "r") as f:
                    content = f.read()
                source = "local file"
                logger.info(f"Loaded workflow state from local file: {WORKFLOW_STATE_PATH}")
            except Exception:

                pass
                logger.error(f"Failed to load workflow state from local file: {str(e)}")

        # 2. Try GCP Cloud Storage
        if not content and self.gcp_enabled and self.storage_client:
            try:

                pass
                from google.api_core.exceptions import NotFound

                bucket = self.storage_client.bucket(self.bucket_name)
                blob_path = f"{self.environment}/workflow_state.yaml"
                blob = bucket.blob(blob_path)
                content = blob.download_as_text()
                source = "Cloud Storage"
                logger.info(f"Loaded workflow state from Cloud Storage: gs://{self.bucket_name}/{blob_path}")
            except Exception:

                pass
                logger.warning("Workflow state not found in Cloud Storage")
            except Exception:

                pass
                logger.error(f"Failed to load workflow state from Cloud Storage: {str(e)}")

        if not content and self.gcp_enabled and self.firestore_client:
            try:

                pass
                doc_ref = self.firestore_client.collection(self.collection_name).document("workflow_state")
                doc = doc_ref.get()
                if doc.exists:
                    content = doc.to_dict().get("content")
                else:
            except Exception:

                pass

        # If content was loaded, parse
        if content:
            try:

                pass
                state = yaml.safe_load(content)
                logger.info(f"Successfully loaded workflow state from {source}")

                # Save to local file if loaded from remote source
                if source != "local file":
                    try:

                        pass
                        os.makedirs(os.path.dirname(WORKFLOW_STATE_PATH), exist_ok=True)
                        with open(WORKFLOW_STATE_PATH, "w") as f:
                            f.write(content)
                        logger.info(f"Saved remote workflow state to local file: {WORKFLOW_STATE_PATH}")
                    except Exception:

                        pass
                        logger.error(f"Failed to save remote workflow state locally: {str(e)}")

                return state
            except Exception:

                pass
                logger.error(f"Invalid workflow state loaded from {source}: {str(e)}")
                return None

        logger.warning("No workflow state found")
        return None

    def sync_configurations(self) -> bool:
        """
        """
                with open(MODE_DEFINITIONS_PATH, "r") as f:
                    local_content = f.read()
                    local_config = self._validate_yaml_config(local_content)
                    local_hash = hashlib.md5(local_content.encode()).hexdigest()
                    sources.append(("local_file", local_content, local_hash))
            except Exception:

                pass
                logger.error(f"Failed to load mode definitions from local file: {str(e)}")

        # 2. Secret Manager
        if self.gcp_enabled and self.os.environ_client:
            try:

                pass
                from google.api_core.exceptions import NotFound

                secret_name = f"projects/{self.project_id}/secrets/{self.secret_name}/versions/latest"
                response = self.os.environ_client.access_secret_version(request={"name": secret_name})
                secret_content = response.payload.data.decode("UTF-8")
                self._validate_yaml_config(secret_content)
                secret_hash = hashlib.md5(secret_content.encode()).hexdigest()
                sources.append(("os.environ", secret_content, secret_hash))
            except Exception:

                pass
                logger.warning("Mode definitions not found in Secret Manager")
            except Exception:

                pass
                logger.error(f"Failed to load mode definitions from Secret Manager: {str(e)}")

        # 3. Cloud Storage
        if self.gcp_enabled and self.storage_client:
            try:

                pass
                from google.api_core.exceptions import NotFound

                bucket = self.storage_client.bucket(self.bucket_name)
                blob_path = f"{self.environment}/mode_definitions.yaml"
                blob = bucket.blob(blob_path)
                storage_content = blob.download_as_text()
                self._validate_yaml_config(storage_content)
                storage_hash = hashlib.md5(storage_content.encode()).hexdigest()
                sources.append(("cloud_storage", storage_content, storage_hash))
            except Exception:

                pass
                logger.warning("Mode definitions not found in Cloud Storage")
            except Exception:

                pass
                logger.error(f"Failed to load mode definitions from Cloud Storage: {str(e)}")

        if self.gcp_enabled and self.firestore_client:
            try:

                pass
                doc_ref = self.firestore_client.collection(self.collection_name).document("mode_definitions")
                doc = doc_ref.get()
                if doc.exists:
                    firestore_content = doc.to_dict().get("content")
                    self._validate_yaml_config(firestore_content)
                    firestore_hash = hashlib.md5(firestore_content.encode()).hexdigest()
                else:
            except Exception:

                pass

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

                pass
                os.makedirs(os.path.dirname(MODE_DEFINITIONS_PATH), exist_ok=True)
                with open(MODE_DEFINITIONS_PATH, "w") as f:
                    f.write(content_to_sync)
                logger.info(f"Synced configuration to local file: {MODE_DEFINITIONS_PATH}")
            except Exception:

                pass
                logger.error(f"Failed to sync configuration to local file: {str(e)}")
                return False

        # 2. Sync to Secret Manager
        if self.gcp_enabled and self.os.environ_client and source_to_use[0] != "os.environ":
            try:

                pass
                from google.api_core.exceptions import NotFound

                secret_name = f"projects/{self.project_id}/secrets/{self.secret_name}"

                try:


                    pass
                    # Check if secret exists
                    self.os.environ_client.get_secret(request={"name": secret_name})
                except Exception:

                    pass
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
            except Exception:

                pass
                logger.error(f"Failed to sync configuration to Secret Manager: {str(e)}")
                return False

        # 3. Sync to Cloud Storage
        if self.gcp_enabled and self.storage_client and source_to_use[0] != "cloud_storage":
            try:

                pass
                from google.api_core.exceptions import NotFound

                bucket = None
                try:

                    pass
                    bucket = self.storage_client.get_bucket(self.bucket_name)
                except Exception:

                    pass
                    # Create bucket if it doesn't exist
                    bucket = self.storage_client.create_bucket(self.bucket_name, location="us-central1")
                    logger.info(f"Created bucket {self.bucket_name}")

                # Create blob with path based on environment
                blob_path = f"{self.environment}/mode_definitions.yaml"
                blob = bucket.blob(blob_path)
                blob.upload_from_string(content_to_sync)
                logger.info(f"Synced configuration to Cloud Storage: gs://{self.bucket_name}/{blob_path}")
            except Exception:

                pass
                logger.error(f"Failed to sync configuration to Cloud Storage: {str(e)}")
                return False

            try:

                pass
                doc_ref = self.firestore_client.collection(self.collection_name).document("mode_definitions")
                doc_ref.set(
                    {
                        "environment": self.environment,
                        "content": content_to_sync,
                        "version": hashlib.md5(content_to_sync.encode()).hexdigest(),
                    }
                )
            except Exception:

                pass
                return False

        return True

# Singleton instance
_instance = None

def get_persistence_manager() -> PersistenceManager:
    """Get singleton instance of PersistenceManager."""
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
