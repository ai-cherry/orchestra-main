#!/usr/bin/env python3
"""
Memory System Deployment Configuration Script

This script configures the memory system for deployment, setting up the
appropriate configuration for different environments (dev, staging, prod)
and ensuring proper separation between development notes and personal information.

Usage:
    python configure_memory_for_deployment.py --env [dev|staging|prod] --tenant [tenant_id]
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from packages.shared.src.memory.dev_notes_manager import DevNotesManager
from packages.shared.src.memory.firestore_adapter import FirestoreMemoryAdapter
from packages.shared.src.memory.privacy_enhanced_memory_manager import (
    PIIDetectionConfig,
    PrivacyEnhancedMemoryManager,
)
from packages.shared.src.models.metadata_schemas import DevNoteType, PrivacyLevel
from packages.shared.src.storage.config import StorageConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("memory_deployment")


class DeploymentConfig:
    """Deployment configuration for memory system"""

    # GCP project IDs
    PROJECT_IDS = {
        "dev": "orchestra-dev-project",
        "staging": "orchestra-staging-project",
        "prod": "orchestra-prod-project",
    }

    # Environment-specific configuration
    ENV_CONFIGS = {
        "dev": {
            "enable_dev_notes": True,
            "pii_redaction": False,
            "default_privacy": "standard",
            "enforce_privacy": False,
            "retention_days": 365,
        },
        "staging": {
            "enable_dev_notes": True,
            "pii_redaction": True,
            "default_privacy": "sensitive",
            "enforce_privacy": True,
            "retention_days": 180,
        },
        "prod": {
            "enable_dev_notes": False,  # Typically disabled in production
            "pii_redaction": True,
            "default_privacy": "sensitive",
            "enforce_privacy": True,
            "retention_days": 90,
        },
    }


def get_credentials_path(env: str) -> str:
    """Get the path to GCP credentials for the specified environment"""
    # In a real implementation, this might fetch from a secret manager
    return os.path.join(
        os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_DIR", "/tmp"),
        f"orchestra-{env}-key.json",
    )


def create_storage_config(env: str, tenant_id: Optional[str] = None) -> StorageConfig:
    """Create a StorageConfig for the specified environment and tenant"""
    env_config = DeploymentConfig.ENV_CONFIGS[env]

    namespace = f"tenant_{tenant_id}" if tenant_id else None

    return StorageConfig(
        namespace=namespace,
        environment=env,
        enable_dev_notes=env_config["enable_dev_notes"],
        default_privacy_level=env_config["default_privacy"],
        enforce_privacy_classification=env_config["enforce_privacy"],
    )


def create_pii_config(env: str) -> PIIDetectionConfig:
    """Create a PIIDetectionConfig for the specified environment"""
    env_config = DeploymentConfig.ENV_CONFIGS[env]

    config = PIIDetectionConfig()
    config.ENABLE_PII_DETECTION = True
    config.ENABLE_PII_REDACTION = env_config["pii_redaction"]
    config.DEFAULT_RETENTION_DAYS = env_config["retention_days"]

    return config


async def setup_memory_managers(env: str, tenant_id: Optional[str] = None):
    """Set up memory managers for the specified environment"""
    project_id = DeploymentConfig.PROJECT_IDS[env]
    credentials_path = get_credentials_path(env)
    storage_config = create_storage_config(env, tenant_id)
    pii_config = create_pii_config(env)

    # Create base Firestore adapter
    firestore_adapter = FirestoreMemoryAdapter(
        project_id=project_id,
        credentials_path=credentials_path,
        namespace=storage_config.namespace or "default",
    )

    # Initialize the adapter
    await firestore_adapter.initialize()

    # Create development notes manager if enabled
    dev_notes_manager = None
    if storage_config.enable_dev_notes:
        dev_notes_manager = DevNotesManager(
            memory_manager=firestore_adapter,
            config=storage_config,
            agent_id=f"deployment_agent_{env}",
        )
        await dev_notes_manager.initialize()
        logger.info(f"Development notes manager initialized for {env} environment")

    # Create privacy-enhanced memory manager
    privacy_manager = PrivacyEnhancedMemoryManager(
        underlying_manager=firestore_adapter,
        config=storage_config,
        pii_config=pii_config,
    )

    await privacy_manager.initialize()
    logger.info(f"Privacy-enhanced memory manager initialized for {env} environment")

    return {
        "base_adapter": firestore_adapter,
        "dev_notes_manager": dev_notes_manager,
        "privacy_manager": privacy_manager,
    }


async def record_deployment_info(
    dev_notes_manager: DevNotesManager,
    deployment_id: str,
    version: str,
    changes: List[str],
    components: List[str],
):
    """Record deployment information as a development note"""
    if not dev_notes_manager:
        logger.warning(
            "Development notes manager not available, skipping deployment record"
        )
        return

    # Format changes list
    changes_formatted = "\n".join([f"- {change}" for change in changes])

    # Create implementation note for each affected component
    for component in components:
        await dev_notes_manager.add_implementation_note(
            component=component,
            overview=f"Deployment {version} - {component}",
            implementation_details=(
                f"Deployment ID: {deployment_id}\n\n" f"Changes:\n{changes_formatted}"
            ),
            affected_files=[],  # Would be populated with actual affected files
            testing_status="verified",
            metadata={
                "deployment_id": deployment_id,
                "version": version,
                "note_type": DevNoteType.DEPLOYMENT.value,
                "priority": "normal",
                "expiration": datetime.utcnow()
                + timedelta(days=365),  # 1 year retention
            },
        )

        logger.info(f"Recorded deployment information for component: {component}")


async def verify_memory_health(managers: Dict):
    """Verify the health of memory managers"""
    results = {}

    # Check base adapter health
    base_health = await managers["base_adapter"].health_check()
    results["base_adapter"] = base_health["status"]

    # Check dev notes manager health if available
    if managers["dev_notes_manager"]:
        dev_notes_health = await managers["dev_notes_manager"].health_check()
        results["dev_notes_manager"] = dev_notes_health["status"]

    # Check privacy manager health
    privacy_health = await managers["privacy_manager"].health_check()
    results["privacy_manager"] = privacy_health["status"]

    # Log health status
    logger.info(f"Memory system health: {json.dumps(results, indent=2)}")

    # Return overall status
    overall_status = all(status == "healthy" for status in results.values())
    return "healthy" if overall_status else "unhealthy"


async def close_managers(managers: Dict):
    """Close all memory managers"""
    if managers["base_adapter"]:
        await managers["base_adapter"].close()

    if managers["dev_notes_manager"]:
        await managers["dev_notes_manager"].close()

    if managers["privacy_manager"]:
        await managers["privacy_manager"].close()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Configure memory system for deployment"
    )
    parser.add_argument(
        "--env",
        choices=["dev", "staging", "prod"],
        default="dev",
        help="Deployment environment",
    )
    parser.add_argument(
        "--tenant",
        help="Tenant ID for multi-tenant deployments",
    )
    parser.add_argument(
        "--deployment-id",
        default=datetime.utcnow().strftime("%Y%m%d%H%M%S"),
        help="Deployment identifier",
    )
    parser.add_argument(
        "--version",
        default="1.0.0",
        help="Version being deployed",
    )

    args = parser.parse_args()

    logger.info(f"Configuring memory system for {args.env} environment")

    try:
        # Setup memory managers
        managers = await setup_memory_managers(args.env, args.tenant)

        # Record deployment information if dev notes are enabled
        if managers["dev_notes_manager"]:
            await record_deployment_info(
                dev_notes_manager=managers["dev_notes_manager"],
                deployment_id=args.deployment_id,
                version=args.version,
                changes=[
                    "Implemented enhanced privacy controls",
                    "Added development notes manager",
                    "Updated collection naming strategy",
                ],
                components=[
                    "memory_system",
                    "storage_layer",
                    "privacy_controls",
                ],
            )

        # Verify memory system health
        health_status = await verify_memory_health(managers)
        logger.info(f"Memory system configuration complete. Status: {health_status}")

        # Close all managers
        await close_managers(managers)

        return 0 if health_status == "healthy" else 1

    except Exception as e:
        logger.error(f"Error configuring memory system: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
