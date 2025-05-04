# Google Cloud Platform Migration Toolkit

This toolkit provides sanitized scripts and templates for migrating a GCP project between organizations and setting up a hybrid IDE environment with Vertex AI. All sensitive information has been replaced with placeholders.

## Security Notice

⚠️ **IMPORTANT**: These scripts handle sensitive GCP credentials and permissions. Before using:

1. Replace all placeholders with your actual values
2. Store credential files securely with `chmod 600` permissions
3. Never commit credential files to version control
4. Use the principle of least privilege when assigning service account roles
5. Consider setting up key rotation practices

## Toolkit Components

### 1. Migration Script
`sanitized_migration_script.sh` - Main script for migrating a GCP project to a different organization

```bash
# Make executable
chmod +x sanitized_migration_script.sh

# Review and replace placeholders
nano sanitized_migration_script.sh

# Run
./sanitized_migration_script.sh
```

### 2. Service Account Key Management
`sanitized_manage_keys.sh` - Script for managing service account keys

```bash
# Make executable
chmod +x sanitized_manage_keys.sh

# Get help
./sanitized_manage_keys.sh help

# Create a key template
./sanitized_manage_keys.sh template
```

### 3. Service Account Key Template
`sanitized-service-account-key-template.json` - Template for service account credentials

### 4. Validation Script
`sanitized_validate_migration.sh` - Validates the migration was successful

```bash
# Make executable
chmod +x sanitized_validate_migration.sh

# Run after migration
./sanitized_validate_migration.sh
```

### 5. Workstation Configuration
`sanitized_workstation_config.tf` - Terraform configuration for cloud workstations

```bash
# Initialize Terraform
terraform init

# Apply configuration
terraform apply -var="project_id=YOUR_PROJECT_ID" -var="org_id=YOUR_ORGANIZATION_ID"
```

## Migration Process

1. **Service Account Setup**
   - Replace placeholders in the key template
   - Set secure permissions: `chmod 600 service-account-key.json`

2. **IAM Preparation**
   - Grant required roles to the service account
   - Wait 5 minutes for IAM propagation (critical step)

3. **Project Migration**
   - Run the migration script
   - Verify organization membership immediately

4. **Enable Required Services**
   - Enable Vertex AI, Workstations, Redis, and AlloyDB APIs

5. **Infrastructure Deployment**
   - Apply Terraform configuration for workstations
   - Provision with required GPU and disk resources

6. **Validation**
   - Verify project organization membership
   - Check service account roles
   - Test resource access

## Critical Success Factors

1. **IAM Propagation**: Always wait 5 minutes after granting roles
2. **Key Security**: Maintain strict 600 permissions on key files
3. **Validation**: Always verify project organization membership immediately
4. **Roles**: Ensure service account has project mover and creator roles at organization level

## Troubleshooting

1. **Permission Denied**: Ensure IAM roles have propagated (wait 5 minutes)
2. **Organization Not Found**: Verify organization ID format
3. **Service Account Issues**: Verify key is valid and has required permissions
4. **Terraform Errors**: Ensure Google provider is properly configured

## Customization

Modify these scripts based on your requirements:
- GPU type and count in the workstation configuration
- Disk sizes for persistent storage
- Number of workstation instances
- Additional services to enable
