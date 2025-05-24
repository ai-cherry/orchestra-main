"""
Manages the Firestore client instance, including initialization,
emulator configuration, and providing a shared client.
"""

import asyncio  # Retained for asyncio.Lock
import logging
import os
from typing import Optional

# google.cloud.firestore is not directly used, only FirestoreAsyncClient from the specific path
from google.cloud.firestore_v1.async_client import AsyncClient as FirestoreAsyncClient

# TODO: Replace with actual import from your project's config module
# from ai_orchestra.core.config import settings


# Placeholder for settings if the actual import isn't readily available
class PlaceholderSettings:
    def __init__(self):
        self.gcp_project_id: Optional[str] = os.environ.get("GCP_PROJECT_ID", "your-gcp-project-id")  # Fallback
        self.database_use_firestore_emulator: bool = os.environ.get("USE_FIRESTORE_EMULATOR", "false").lower() == "true"
        self.database_firestore_emulator_host: Optional[str] = os.environ.get("FIRESTORE_EMULATOR_HOST")
        # Add other relevant settings attributes if needed by client initialization
        # self.firestore_api_endpoint: Optional[str] = None # Example


logger = logging.getLogger(__name__)


class FirestoreClientManager:
    """
    Manages the lifecycle and configuration of the Firestore AsyncClient.
    This can be implemented as a singleton or simply ensure that components
    requiring a client get a consistently configured one.
    """

    _client_instance: Optional[FirestoreAsyncClient] = None
    _lock = asyncio.Lock()  # For thread-safe/async-safe singleton initialization

    def __init__(
        self, app_settings: PlaceholderSettings
    ):  # TODO: Replace PlaceholderSettings with actual settings type
        """
        Initialize the FirestoreClientManager.

        Args:
            app_settings: The application settings object containing GCP project ID,
                         emulator host, etc.
        """
        self.settings = app_settings
        logger.info("FirestoreClientManager configured.")

    async def get_client(self) -> FirestoreAsyncClient:
        """
        Provides an initialized and configured Firestore AsyncClient.
        Implements async-safe singleton pattern for the client instance.

        Returns:
            An instance of FirestoreAsyncClient.

        Raises:
            RuntimeError: If client initialization fails.
            ValueError: If GCP Project ID is not configured.
        """
        if FirestoreClientManager._client_instance is None:
            async with FirestoreClientManager._lock:
                if FirestoreClientManager._client_instance is None:
                    logger.info("Initializing Firestore AsyncClient...")
                    try:
                        project_id_to_use = self.settings.gcp_project_id

                        if not project_id_to_use:
                            logger.error("GCP Project ID is not configured. Cannot initialize Firestore client.")
                            raise ValueError("GCP Project ID is not configured for Firestore client.")

                        client_options = {}
                        # Example: if hasattr(self.settings, 'firestore_api_endpoint') and self.settings.firestore_api_endpoint:
                        #     client_options["api_endpoint"] = self.settings.firestore_api_endpoint

                        if (
                            self.settings.database_use_firestore_emulator
                            and self.settings.database_firestore_emulator_host
                        ):
                            current_emulator_host_env = os.environ.get("FIRESTORE_EMULATOR_HOST")
                            if current_emulator_host_env != self.settings.database_firestore_emulator_host:
                                logger.warning(
                                    f"FIRESTORE_EMULATOR_HOST env var ('{current_emulator_host_env}') "
                                    f"differs from settings ('{self.settings.database_firestore_emulator_host}'). "
                                    "Ensure it is set correctly if emulator is intended, or align your settings."
                                )
                            # The Firestore client library primarily uses the FIRESTORE_EMULATOR_HOST environment variable.
                            # If it's set, the client will automatically connect to the emulator.
                            # No direct `emulator_host` parameter for `AsyncClient` constructor.
                            logger.info(
                                f"""Firestore client will attempt to use emulator if FIRESTORE_EMULATOR_HOST is set to '{os.environ.get("FIRESTORE_EMULATOR_HOST")}'."""
                            )

                        FirestoreClientManager._client_instance = FirestoreAsyncClient(
                            project=project_id_to_use, client_options=client_options if client_options else None
                        )
                        logger.info(f"Firestore AsyncClient initialized for project: {project_id_to_use}.")
                    except Exception as e:
                        logger.error(f"Failed to initialize Firestore AsyncClient: {e}", exc_info=True)
                        raise RuntimeError(f"Could not initialize Firestore client: {e}") from e

        return FirestoreClientManager._client_instance

    async def close_client(self) -> None:
        """
        Closes the shared Firestore client instance if it exists.
        Important for graceful shutdown.
        """
        async with FirestoreClientManager._lock:
            if FirestoreClientManager._client_instance is not None:
                client_to_close = FirestoreClientManager._client_instance
                FirestoreClientManager._client_instance = (
                    None  # Set to None before close to prevent re-use during close
                )
                try:
                    if hasattr(client_to_close, "close") and callable(client_to_close.close):
                        await client_to_close.close()
                        logger.info("Firestore AsyncClient closed.")
                    else:
                        # For google-cloud-firestore >= 2.2.0, AsyncClient uses aiohttp.ClientSession internally
                        # which should be closed. If no explicit close, rely on __aexit__ if used in context manager.
                        # If not, the underlying connections might not be released properly without an explicit close.
                        # This part of the google-cloud-python library can be a bit opaque.
                        logger.info(
                            "Firestore AsyncClient does not have an explicit close() method or it's managed by other means (e.g. context manager)."
                        )
                except Exception as e:
                    logger.error(f"Error closing Firestore AsyncClient: {e}", exc_info=True)
                    # Instance is already set to None, so further calls to get_client will re-initialize.


# Example of how it might be used by other components or a central facade:
# async def main_example():
#     settings = PlaceholderSettings() # TODO: Load your actual settings
#     client_manager = FirestoreClientManager(app_settings=settings)
#
#     try:
#         firestore_client_instance = await client_manager.get_client()
#         # Now pass firestore_client_instance to FirestoreCrudOperations, FirestoreQueryEngine, etc.
#         # from .firestore_crud_operations import FirestoreCrudOperations # Example
#         # crud_ops = FirestoreCrudOperations(firestore_client_instance, "my_collection")
#         # item = await crud_ops.get_item("some_id")
#         # print(item)
#     finally:
#         await client_manager.close_client()

# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO)
#     # To run the example:
#     # Ensure FIRESTORE_EMULATOR_HOST is set if using emulator, e.g.:
#     # os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
#     # os.environ["GCP_PROJECT_ID"] = "test-project" # For emulator, project_id can be arbitrary but must be set
#     # asyncio.run(main_example())
#     pass
