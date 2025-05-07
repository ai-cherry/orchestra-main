#!/bin/bash
# Memory System Configuration Script
#
# This script configures the memory system for proper data separation between
# development notes and personal information. It's designed to be run as part
# of the deployment process or independently for memory system configuration.

set -e  # Exit on any error

# Text styling
BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m"  # No Color

# Print section header
section() {
    echo ""
    echo -e "${BOLD}${BLUE}==== $1 ====${NC}"
    echo ""
}

# Print success message
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Print warning message
warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Print error message
error() {
    echo -e "${RED}❌ $1${NC}"
}

# Ask for confirmation
confirm() {
    read -p "$1 (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return 1
    fi
    return 0
}

# Default values
ENV=${1:-"dev"}  # Default to dev environment if not specified
PROJECT_ID=${GCP_PROJECT_ID:-"agi-baby-cherry"}
TENANT_ID=""

section "Memory System Configuration"
echo "This script will configure the memory system to properly separate:"
echo "  - Development context notes (technical documentation, implementation details)"
echo "  - Personal user information (user conversations, potentially containing PII)"
echo ""
echo "Current settings:"
echo "  - Environment: $ENV"
echo "  - Project ID: $PROJECT_ID"
echo ""

# Confirm environment choice
echo "Available environments:"
echo "  1. dev (Development) - Dev notes enabled, no PII redaction"
echo "  2. staging (Staging) - Dev notes enabled, PII redaction active" 
echo "  3. prod (Production) - Dev notes disabled, strict PII redaction"
read -p "Select environment [1-3] (default: 1): " env_choice
case $env_choice in
    2) ENV="staging" ;;
    3) ENV="prod" ;;
    *) ENV="dev" ;;
esac

# Ask for multi-tenant configuration
if confirm "Do you want to configure for a specific tenant? (multi-tenant setup)"; then
    read -p "Enter tenant ID: " TENANT_ID
fi

# Update .env file with memory configuration
section "Updating Environment Configuration"

# Create backup of .env file
if [ -f ".env" ]; then
    cp .env .env.bak
    success "Created backup of .env file at .env.bak"
fi

# Check if memory configuration already exists in .env
if grep -q "MEMORY_ENVIRONMENT" .env; then
    echo "Memory configuration already exists in .env file."
    if confirm "Do you want to update it?"; then
        # Remove existing memory configuration
        sed -i '/^# Memory Configuration/d' .env
        sed -i '/^MEMORY_ENVIRONMENT/d' .env
        sed -i '/^MEMORY_ENABLE_DEV_NOTES/d' .env
        sed -i '/^MEMORY_DEFAULT_PRIVACY_LEVEL/d' .env
        sed -i '/^MEMORY_ENFORCE_PRIVACY/d' .env
        sed -i '/^MEMORY_NAMESPACE/d' .env
    else
        warning "Skipping .env update"
    fi
fi

# Add memory configuration to .env
echo "" >> .env
echo "# Memory Configuration" >> .env
echo "MEMORY_ENVIRONMENT=$ENV" >> .env

# Set environment-specific values
case $ENV in
    "dev")
        echo "MEMORY_ENABLE_DEV_NOTES=true" >> .env
        echo "MEMORY_DEFAULT_PRIVACY_LEVEL=standard" >> .env
        echo "MEMORY_ENFORCE_PRIVACY=false" >> .env
        ;;
    "staging")
        echo "MEMORY_ENABLE_DEV_NOTES=true" >> .env
        echo "MEMORY_DEFAULT_PRIVACY_LEVEL=sensitive" >> .env
        echo "MEMORY_ENFORCE_PRIVACY=true" >> .env
        ;;
    "prod")
        echo "MEMORY_ENABLE_DEV_NOTES=false" >> .env
        echo "MEMORY_DEFAULT_PRIVACY_LEVEL=sensitive" >> .env
        echo "MEMORY_ENFORCE_PRIVACY=true" >> .env
        ;;
esac

# Add tenant namespace if specified
if [ ! -z "$TENANT_ID" ]; then
    echo "MEMORY_NAMESPACE=tenant_$TENANT_ID" >> .env
fi

success "Updated .env with memory configuration for $ENV environment"

# Make memory configuration script executable
section "Setting Up Memory Configuration Script"
if [ -f "scripts/configure_memory_for_deployment.py" ]; then
    chmod +x scripts/configure_memory_for_deployment.py
    success "Made memory configuration script executable"
else
    error "Memory configuration script not found at scripts/configure_memory_for_deployment.py"
    exit 1
fi

# Run memory configuration script
section "Configuring Memory System"
echo "Running memory system configuration for $ENV environment..."

TENANT_PARAM=""
if [ ! -z "$TENANT_ID" ]; then
    TENANT_PARAM="--tenant $TENANT_ID"
fi

VERSION="1.0.0"
DEPLOYMENT_ID=$(date +%Y%m%d%H%M%S)

python scripts/configure_memory_for_deployment.py --env $ENV $TENANT_PARAM --version $VERSION --deployment-id $DEPLOYMENT_ID

if [ $? -eq 0 ]; then
    success "Memory system configured successfully"
else
    error "Failed to configure memory system"
    exit 1
fi

# Create a simple memory test script if it doesn't exist
section "Setting Up Memory Verification Test"
if [ ! -f "test_memory_separation.py" ]; then
    echo "Creating memory verification test script..."
    cat > test_memory_separation.py << 'EOF'
#!/usr/bin/env python3
"""
Memory System Separation Verification Test

This script tests if the memory system separation is configured correctly by:
1. Attempting to store a development note
2. Attempting to store a personal information item
3. Verifying the items are stored in the correct collections
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("memory_verification")

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


async def verify_memory_separation():
    """Verify that memory system separation is configured correctly"""
    # Import here to ensure paths are set up
    from packages.shared.src.memory.dev_notes_manager import DevNotesManager
    from packages.shared.src.memory.firestore_adapter import FirestoreMemoryAdapter
    from packages.shared.src.memory.privacy_enhanced_memory_manager import (
        PIIDetectionConfig,
        PrivacyEnhancedMemoryManager,
    )
    from packages.shared.src.models.base_models import MemoryItem
    from packages.shared.src.storage.config import StorageConfig

    # Get environment settings from .env
    env = os.environ.get("MEMORY_ENVIRONMENT", "dev")
    enable_dev_notes = os.environ.get("MEMORY_ENABLE_DEV_NOTES", "true").lower() == "true"
    default_privacy = os.environ.get("MEMORY_DEFAULT_PRIVACY_LEVEL", "standard")
    enforce_privacy = os.environ.get("MEMORY_ENFORCE_PRIVACY", "false").lower() == "true"
    namespace = os.environ.get("MEMORY_NAMESPACE", None)

    logger.info(f"Testing memory separation for environment: {env}")
    logger.info(f"Development notes enabled: {enable_dev_notes}")
    logger.info(f"Default privacy level: {default_privacy}")
    logger.info(f"Enforce privacy classification: {enforce_privacy}")
    logger.info(f"Namespace: {namespace}")

    # Create storage config
    config = StorageConfig(
        namespace=namespace,
        environment=env,
        enable_dev_notes=enable_dev_notes,
        default_privacy_level=default_privacy,
        enforce_privacy_classification=enforce_privacy,
    )

    # Create firestore adapter
    firestore_adapter = FirestoreMemoryAdapter(
        project_id=os.environ.get("GCP_PROJECT_ID", "agi-baby-cherry"),
        namespace=namespace or "default",
    )

    # Initialize the adapter
    await firestore_adapter.initialize()
    logger.info("Firestore adapter initialized")

    results = {"success": True, "tests": []}

    # Test dev notes manager if enabled
    dev_notes_id = None
    if enable_dev_notes:
        try:
            logger.info("Testing DevNotesManager...")
            dev_notes_manager = DevNotesManager(
                memory_manager=firestore_adapter,
                config=config,
                agent_id="verification_test",
            )
            await dev_notes_manager.initialize()

            # Add a test note
            dev_notes_id = await dev_notes_manager.add_implementation_note(
                component="memory_verification",
                overview="Memory System Verification Test",
                implementation_details="This is a test note to verify the memory system separation works correctly.",
                affected_files=["test_memory_separation.py"],
                testing_status="testing",
                metadata={
                    "test_id": f"verification_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    "environment": env,
                },
            )

            # Try to retrieve the note
            note = await dev_notes_manager.get_note_by_id(dev_notes_id)

            if note:
                logger.info(f"Successfully created and retrieved development note with ID: {dev_notes_id}")
                results["tests"].append({
                    "name": "DevNotesManager Test",
                    "success": True,
                    "note_id": dev_notes_id,
                    "collection": dev_notes_manager.get_collection_name(),
                })
            else:
                logger.error(f"Failed to retrieve development note with ID: {dev_notes_id}")
                results["success"] = False
                results["tests"].append({
                    "name": "DevNotesManager Test",
                    "success": False,
                    "error": f"Failed to retrieve note with ID: {dev_notes_id}",
                })

            await dev_notes_manager.close()
        except Exception as e:
            logger.error(f"Error testing DevNotesManager: {e}")
            results["success"] = False
            results["tests"].append({
                "name": "DevNotesManager Test",
                "success": False,
                "error": str(e),
            })
    else:
        logger.info("DevNotesManager testing skipped (not enabled in this environment)")
        results["tests"].append({
            "name": "DevNotesManager Test",
            "success": None,
            "message": "Skipped - dev notes not enabled in this environment",
        })

    # Test privacy enhanced memory manager
    try:
        logger.info("Testing PrivacyEnhancedMemoryManager...")
        
        # Create PII config based on environment
        pii_config = PIIDetectionConfig()
        pii_config.ENABLE_PII_DETECTION = True
        pii_config.ENABLE_PII_REDACTION = env != "dev"  # Enable in staging/prod, disable in dev
        
        # Retention days by environment
        if env == "prod":
            pii_config.DEFAULT_RETENTION_DAYS = 90
        elif env == "staging":
            pii_config.DEFAULT_RETENTION_DAYS = 180
        else:
            pii_config.DEFAULT_RETENTION_DAYS = 365  # Longer retention in dev

        privacy_manager = PrivacyEnhancedMemoryManager(
            underlying_manager=firestore_adapter,
            config=config,
            pii_config=pii_config,
        )

        await privacy_manager.initialize()

        # Create a memory item with some mock PII
        memory_item = MemoryItem(
            user_id="test_user_123",
            session_id="test_session_456",
            item_type="conversation",
            text_content="This is a test message from John Doe (john.doe@example.com)",
            metadata={
                "test_id": f"verification_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "source": "memory_verification_test",
            },
        )

        # Store the item
        memory_item_id = await privacy_manager.add_memory_item(memory_item)

        # Retrieve the item
        stored_item = await privacy_manager.get_memory_item(memory_item_id)

        if stored_item:
            logger.info(f"Successfully created and retrieved memory item with ID: {memory_item_id}")
            results["tests"].append({
                "name": "PrivacyEnhancedMemoryManager Test",
                "success": True,
                "item_id": memory_item_id,
                "collection": privacy_manager.get_collection_name(),
                "pii_detected": stored_item.metadata.get("pii_detected", False),
                "privacy_level": stored_item.metadata.get("privacy_level", default_privacy),
                "text_content": stored_item.text_content,
            })
        else:
            logger.error(f"Failed to retrieve memory item with ID: {memory_item_id}")
            results["success"] = False
            results["tests"].append({
                "name": "PrivacyEnhancedMemoryManager Test",
                "success": False,
                "error": f"Failed to retrieve item with ID: {memory_item_id}",
            })

        await privacy_manager.close()
    except Exception as e:
        logger.error(f"Error testing PrivacyEnhancedMemoryManager: {e}")
        results["success"] = False
        results["tests"].append({
            "name": "PrivacyEnhancedMemoryManager Test",
            "success": False,
            "error": str(e),
        })

    # Close the adapter
    await firestore_adapter.close()

    # Print summary
    logger.info("\nTest Results Summary:")
    logger.info(f"Overall success: {results['success']}")
    
    for test in results["tests"]:
        test_name = test["name"]
        if test["success"] is True:
            logger.info(f"✅ {test_name}: PASSED")
        elif test["success"] is False:
            logger.info(f"❌ {test_name}: FAILED - {test.get('error', 'Unknown error')}")
        else:
            logger.info(f"⏭️ {test_name}: SKIPPED - {test.get('message', 'No message')}")

    # If dev notes were created, show how to access them
    if dev_notes_id:
        logger.info(f"\nCreated development note with ID: {dev_notes_id}")
        logger.info("You can retrieve this note with DevNotesManager.get_note_by_id()")

    # Return results dictionary
    return results


if __name__ == "__main__":
    asyncio.run(verify_memory_separation())
EOF
    chmod +x test_memory_separation.py
    success "Created memory verification test script"
else
    success "Memory verification test script already exists"
fi

section "Memory System Configuration Complete"
echo ""
echo -e "${GREEN}The memory system has been configured successfully for the $ENV environment!${NC}"
echo ""
echo "Memory configuration summary:"
echo "  - Environment: $ENV"
echo "  - Dev notes enabled: $([ "$ENV" == "prod" ] && echo "No" || echo "Yes")"
echo "  - Privacy level: $([ "$ENV" == "dev" ] && echo "standard" || echo "sensitive")"
echo "  - PII redaction: $([ "$ENV" == "dev" ] && echo "Disabled" || echo "Enabled")"
echo "  - Privacy enforcement: $([ "$ENV" == "dev" ] && echo "Disabled" || echo "Enabled")"
if [ ! -z "$TENANT_ID" ]; then
    echo "  - Tenant namespace: tenant_$TENANT_ID"
fi
echo ""
echo "To verify the memory system configuration, run:"
echo "  python test_memory_separation.py"
echo ""
echo "For additional guidance, see:"
echo "  - docs/memory_data_separation_guide.md"
echo "  - docs/memory_system_usage_examples.md"
echo "  - MEMORY_SYSTEM_DEPLOYMENT_GUIDE.md"
