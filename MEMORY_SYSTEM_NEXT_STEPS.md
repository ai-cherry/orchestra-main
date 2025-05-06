# Memory System Next Steps

This document outlines the immediate next steps to implement and test the memory system separation between development notes and personal user information.

## Completed Implementations

The following components have been successfully implemented:

1. **Enhanced Storage Configuration System** (`StorageConfig`)
   - Supporting environment, namespace and privacy level parameters
   - Dynamic collection name generation based on configuration

2. **Specialized Memory Managers**
   - `DevNotesManager`: For technical documentation and development context
   - `PrivacyEnhancedMemoryManager`: For user data with PII protection

3. **Documentation**
   - Memory Data Separation Guide: `docs/memory_data_separation_guide.md`
   - Memory System Usage Examples: `docs/memory_system_usage_examples.md`
   - Memory System Deployment Guide: `MEMORY_SYSTEM_DEPLOYMENT_GUIDE.md`

4. **Setup Scripts**
   - Memory configuration script: `scripts/configure_memory_for_deployment.py`
   - Memory system setup: `memory_system_setup.sh`

5. **Security Checklist**
   - Credential security recommendations: `CREDENTIAL_SECURITY_CHECKLIST.md`

## Implementation Checklist

### Immediate Tasks

1. **Security First - Address Exposed Credentials**
   - [ ] Rotate all exposed GCP credentials (API Key, OAuth Client Secret, Service Account Keys)
   - [ ] Rotate exposed Figma PAT
   - [ ] Change SSH passphrase
   - [ ] Implement Secret Manager for credential storage

2. **Configure Memory System For Development**
   - [ ] Run `./memory_system_setup.sh dev`
   - [ ] Verify configuration was applied correctly
   - [ ] Test dev notes functionality
   - [ ] Test privacy enhanced memory functionality with PII detection

3. **Update Existing Backend Code**
   - [ ] Identify where memory operations are performed
   - [ ] Replace direct memory access with the appropriate manager:
     - Use `DevNotesManager` for development context
     - Use `PrivacyEnhancedMemoryManager` for user data

### Figma Setup & Infrastructure Tasks

4. **Complete Figma Setup**
   - [ ] Follow steps in `FIGMA_SETUP_QUICK_GUIDE.md`
   - [ ] Set up Figma pages and variables
   - [ ] Create initial components and draft dashboard

5. **Provision Development Infrastructure**
   - [ ] Run Terraform for dev environment
   - [ ] Verify GCP resources exist
   - [ ] Configure backend environment variables

### Testing & Verification

6. **Test Memory System Configuration**
   - [ ] Run memory verification test: `python test_memory_separation.py`
   - [ ] Verify dev notes are stored in the correct collection
   - [ ] Verify personal info is stored with proper privacy controls
   - [ ] Test PII detection and redaction features

7. **Run Connection Tests**
   - [ ] Execute `./run_connection_tests.sh`
   - [ ] Verify Firestore connectivity
   - [ ] Verify Redis connectivity
   - [ ] Confirm memory system works with the configured connections

## Code Integration Examples

### Using DevNotesManager

```python
from packages.shared.src.memory.dev_notes_manager import DevNotesManager
from packages.shared.src.memory.firestore_adapter import FirestoreMemoryAdapter
from packages.shared.src.storage.config import StorageConfig

# Initialize with environment-aware configuration
config = StorageConfig(
    environment=os.environ.get("MEMORY_ENVIRONMENT", "dev"),
    enable_dev_notes=os.environ.get("MEMORY_ENABLE_DEV_NOTES", "true").lower() == "true"
)

# Create base adapter
adapter = FirestoreMemoryAdapter(
    project_id=os.environ.get("GCP_PROJECT_ID", "agi-baby-cherry")
)

# Initialize manager
dev_notes = DevNotesManager(
    memory_manager=adapter,
    config=config
)

# Store implementation details
await dev_notes.add_implementation_note(
    component="memory_system",
    overview="PII Detection Enhancement",
    implementation_details="Added regex patterns for additional PII types",
    affected_files=["packages/shared/src/memory/pii_detection.py"],
    testing_status="unit_tests_passed"
)
```

### Using PrivacyEnhancedMemoryManager

```python
from packages.shared.src.memory.privacy_enhanced_memory_manager import (
    PrivacyEnhancedMemoryManager,
    PIIDetectionConfig
)
from packages.shared.src.memory.firestore_adapter import FirestoreMemoryAdapter
from packages.shared.src.models.base_models import MemoryItem
from packages.shared.src.storage.config import StorageConfig

# Initialize with environment-aware configuration
config = StorageConfig(
    environment=os.environ.get("MEMORY_ENVIRONMENT", "dev"),
    default_privacy_level=os.environ.get("MEMORY_DEFAULT_PRIVACY_LEVEL", "standard"),
    enforce_privacy_classification=os.environ.get("MEMORY_ENFORCE_PRIVACY", "false").lower() == "true"
)

# Configure PII detection based on environment
pii_config = PIIDetectionConfig()
pii_config.ENABLE_PII_DETECTION = True
pii_config.ENABLE_PII_REDACTION = os.environ.get("MEMORY_ENVIRONMENT", "dev") != "dev"

# Create manager
adapter = FirestoreMemoryAdapter(
    project_id=os.environ.get("GCP_PROJECT_ID", "agi-baby-cherry")
)
privacy_manager = PrivacyEnhancedMemoryManager(
    underlying_manager=adapter,
    config=config,
    pii_config=pii_config
)

# Store user conversation with privacy protection
await privacy_manager.add_memory_item(MemoryItem(
    user_id="user123",
    session_id="session456",
    item_type="conversation",
    text_content="My name is John Smith and I live at 123 Main St.",
    metadata={
        "source": "chat_interface"
    }
))
```

## Environment-Specific Settings

### Development Environment
```bash
MEMORY_ENVIRONMENT=dev
MEMORY_ENABLE_DEV_NOTES=true
MEMORY_DEFAULT_PRIVACY_LEVEL=standard
MEMORY_ENFORCE_PRIVACY=false
```
- Development notes enabled
- PII detection but no redaction
- Privacy classification not enforced
- Longer retention periods (365 days)

### Staging Environment
```bash
MEMORY_ENVIRONMENT=staging
MEMORY_ENABLE_DEV_NOTES=true
MEMORY_DEFAULT_PRIVACY_LEVEL=sensitive
MEMORY_ENFORCE_PRIVACY=true
```
- Development notes still enabled
- PII detection with redaction
- Privacy classification enforced
- Medium retention periods (180 days)

### Production Environment
```bash
MEMORY_ENVIRONMENT=prod
MEMORY_ENABLE_DEV_NOTES=false
MEMORY_DEFAULT_PRIVACY_LEVEL=sensitive
MEMORY_ENFORCE_PRIVACY=true
```
- Development notes disabled
- Strict PII detection with redaction
- Strict privacy classification enforcement
- Shorter retention periods (90 days)

## Known Issues and Considerations

1. **Migration Strategy**
   - No automatic migration of existing data to the new schema
   - Consider writing a migration script if needed

2. **Performance Impact**
   - PII detection adds processing overhead
   - Consider enabling only in production for performance during development

3. **Multi-Tenant Considerations**
   - Set `MEMORY_NAMESPACE=tenant_{id}` for multi-tenant deployments
   - Ensure proper isolation between tenants

## Monitoring and Auditing

1. **Firestore Collection Monitoring**
   - Periodically check collection sizes and growth rates
   - Monitor for unexpected access patterns

2. **PII Detection Logs**
   - Review logs for PII detection rates and false positives
   - Adjust patterns as needed

## Resources

1. **Memory Data Separation Guide**: `docs/memory_data_separation_guide.md`
2. **Memory System Usage Examples**: `docs/memory_system_usage_examples.md`
3. **Memory System Deployment Guide**: `MEMORY_SYSTEM_DEPLOYMENT_GUIDE.md`
4. **Credential Security Checklist**: `CREDENTIAL_SECURITY_CHECKLIST.md`
5. **Orchestra Deployment Steps**: `docs/ORCHESTRA_DEPLOYMENT_STEPS.md`

## Priority Order

1. **URGENT**: Rotate exposed credentials
2. Configure memory system for development
3. Complete Figma setup
4. Provision dev infrastructure
5. Run connection tests
6. Update backend code to use appropriate memory managers
7. Implement continuous testing and monitoring
