# Memory System Deployment Guide

This guide outlines how to properly configure and implement the memory system separation during deployment, ensuring development notes and personal information are correctly segregated across environments.

## Overview of Memory Separation Implementation

The memory system now supports separation of two distinct data types:

1. **Development Context Notes**: Technical documentation, implementation details, and agent data
2. **Personal User Information**: User conversations, preferences, potentially containing PII

This separation is managed through:
- Enhanced `StorageConfig` with environment, namespace, and privacy settings
- Specialized managers (`DevNotesManager` and `PrivacyEnhancedMemoryManager`)
- Collection namespacing for proper isolation
- Privacy controls including PII detection and redaction

## Pre-Deployment Configuration Steps

### 1. Review Current Memory Documentation

Ensure you've reviewed these documents:
- `docs/memory_data_separation_guide.md`
- `docs/memory_system_usage_examples.md`

### 2. Configure Memory for Development Environment

```bash
# Make script executable
chmod +x scripts/configure_memory_for_deployment.py

# Configure memory system for dev environment
python scripts/configure_memory_for_deployment.py --env dev
```

This configures the memory system with dev-appropriate settings:
- Development notes enabled
- Standard privacy level
- No PII redaction in development
- Longer retention periods

### 3. Update Environment Variables

Ensure these variables are configured appropriately:

```bash
# Add to .env file
MEMORY_ENVIRONMENT=dev  # or staging, prod
MEMORY_ENABLE_DEV_NOTES=true  # typically false in prod
MEMORY_DEFAULT_PRIVACY_LEVEL=standard  # typically sensitive in prod
MEMORY_ENFORCE_PRIVACY=false  # typically true in prod
```

## Integration with Deployment Process

### 1. Modify Deployment Scripts

Update your deployment scripts to configure the memory system during deployment:

```bash
# Add to deploy_to_cloud_run.sh or similar deployment script
echo "Configuring memory system for $ENVIRONMENT environment..."
python scripts/configure_memory_for_deployment.py --env $ENVIRONMENT
```

### 2. Add Memory Configuration to CI/CD Pipeline

If using GitHub Actions or similar CI/CD:

```yaml
# Add to your GitHub workflow file
- name: Configure Memory System
  run: |
    python scripts/configure_memory_for_deployment.py --env ${{ env.DEPLOY_ENV }}
```

## Environment-Specific Configurations

### Development Environment

```python
dev_config = StorageConfig(
    environment="dev",
    enable_dev_notes=True,
    default_privacy_level="standard",
    enforce_privacy_classification=False
)

# For development, typically use:
dev_notes_manager = DevNotesManager(memory_manager=adapter, config=dev_config)
```

### Staging Environment

```python
staging_config = StorageConfig(
    environment="staging",
    enable_dev_notes=True,  # Still useful to have dev notes in staging
    default_privacy_level="sensitive",
    enforce_privacy_classification=True
)

# In staging, start enforcing privacy controls:
privacy_manager = PrivacyEnhancedMemoryManager(
    underlying_manager=adapter,
    config=staging_config,
    pii_config=PIIDetectionConfig(enable_pii_redaction=True)
)
```

### Production Environment

```python
prod_config = StorageConfig(
    environment="prod",
    enable_dev_notes=False,  # Typically disable dev notes in production
    default_privacy_level="sensitive",
    enforce_privacy_classification=True
)

# In production, enforce strict privacy:
privacy_manager = PrivacyEnhancedMemoryManager(
    underlying_manager=adapter,
    config=prod_config,
    pii_config=PIIDetectionConfig(
        enable_pii_detection=True,
        enable_pii_redaction=True,
        default_retention_days=90
    )
)
```

## Verification Steps

### 1. Verify Collection Separation

After configuring each environment, run these checks:

```python
# Add to your verification scripts
async def verify_memory_collections():
    firestore_client = firestore.Client()
    
    # List collections
    collections = list(firestore_client.collections())
    collection_names = [c.id for c in collections]
    
    # Check for proper environment prefixes/suffixes
    dev_collections = [c for c in collection_names if "_dev" in c]
    prod_collections = [c for c in collection_names if "_prod" in c]
    
    print(f"Dev collections: {dev_collections}")
    print(f"Prod collections: {prod_collections}")
```

### 2. Test Memory Manager Health

After deployment, verify memory manager health:

```bash
# Run the health check included in configure_memory_for_deployment.py
python scripts/configure_memory_for_deployment.py --env prod --verify-only
```

### 3. Verify Data Separation

Test storing and retrieving both types of data:

```python
# Test dev notes (should work in dev/staging, fail in prod)
await dev_notes_manager.add_implementation_note(
    component="test_component",
    overview="Test note",
    implementation_details="Details here",
    affected_files=[],
    testing_status="testing"
)

# Test personal information (should work in all environments)
await privacy_manager.add_memory_item(MemoryItem(
    user_id="test_user",
    session_id="test_session",
    item_type="conversation",
    text_content="Test message"
))
```

## Connection Testing with Memory System

Extend the existing connection tests to verify memory system configuration:

```bash
# Add memory system tests to run_connection_tests.sh
echo "Testing memory system configuration..."
python tests/test_memory_config.py --env $ENVIRONMENT
```

## Handling Different Deployment Types

### For Local Development

```bash
# Configure for local development
python scripts/configure_memory_for_deployment.py --env dev --local
```

### For Kubernetes Deployment

```bash
# Add to your Kubernetes deployment scripts
kubectl create configmap memory-config \
  --from-literal=MEMORY_ENVIRONMENT=prod \
  --from-literal=MEMORY_ENABLE_DEV_NOTES=false
```

## Troubleshooting

### Collection Permission Issues

If you encounter permission issues with collections:

```bash
# Check Firestore permissions
gcloud projects get-iam-policy cherry-ai-project

# Grant appropriate permissions if needed
gcloud projects add-iam-policy-binding cherry-ai-project \
  --member="serviceAccount:vertex-agent@cherry-ai-project.iam.gserviceaccount.com" \
  --role="roles/datastore.user"
```

### Incorrect Collection Names

If data is stored in the wrong collections:

1. Check environment configuration in StorageConfig
2. Verify environment variables are correctly set
3. Ensure the correct manager is being used for each data type

### Data Not Found in Expected Collection

If you can't find data where expected:

```python
# List all documents in a collection
async def list_collection_documents(collection_name):
    base_adapter = FirestoreMemoryAdapter()
    await base_adapter.initialize()
    
    docs = await base_adapter.list_documents(collection_name)
    for doc in docs:
        print(f"Document ID: {doc.id}, Data: {doc.to_dict()}")
```

## Security Considerations

Refer to the [Credential Security Checklist](CREDENTIAL_SECURITY_CHECKLIST.md) for handling sensitive API keys and credentials.

Additionally:

1. Ensure appropriate Firestore security rules for each collection
2. Apply the principle of least privilege when accessing memory collections
3. Enable audit logging for sensitive data access

## Next Steps in Your Deployment Pipeline

With the memory system configured properly, continue with:

1. Completing the Figma setup per FIGMA_SETUP_QUICK_GUIDE.md
2. Provisioning dev infrastructure via Terraform
3. Running connection tests to verify backend connectivity
4. Configuring and testing memory separation
5. Setting up webhook and CI/CD

## Conclusion

The memory system separation implementation enhances both developer productivity and data privacy:

- Development context is preserved where needed but isolated from production
- Personal information is properly protected with appropriate privacy controls
- Data is organized by environment, privacy level, and namespace
- Deployment process supports proper configuration across environments

By following this guide, you'll ensure the memory system is properly configured throughout your deployment process.
