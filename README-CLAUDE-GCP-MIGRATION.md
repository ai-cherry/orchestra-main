# GCP Migration & Claude Code Integration Suite

This suite provides a comprehensive solution for migrating the `cherry-ai-project` GCP project to organization `873291114285` and setting up a hybrid IDE environment, with full Claude Code integration for AI-assisted management.

## Components

### 1. Migration Script

The `execute_gcp_migration.sh` script provides an end-to-end migration solution:

- Secure service account authentication with zero-disk footprint
- Critical IAM role assignment with proper propagation waiting
- Project migration to the target organization with immediate verification
- Billing account validation and linking
- Service enablement for Vertex AI, Workstations, Redis, and AlloyDB
- Hybrid IDE deployment via Terraform (n2d-standard-32 with 2x T4 GPUs)
- Comprehensive validation and reporting

### 2. Claude Code Setup

The `setup_claude_code.sh` script prepares Claude Code for GCP project management:

- Node.js and Claude Code installation
- Project memory creation via CLAUDE.md
- Configuration setup for optimal GCP integration
- Tool permissions configuration

### 3. Claude Code Examples

The `use_claude_code_examples.sh` script demonstrates how Claude Code can enhance migration:

- Pre-migration analysis and readiness assessment
- IAM troubleshooting and permission diagnosis
- Terraform optimization suggestions
- Post-migration verification
- Extended thinking for complex architecture questions

## Quick Start

```bash
# 1. Execute the migration
./execute_gcp_migration.sh

# 2. Set up Claude Code
./setup_claude_code.sh

# 3. Explore Claude Code examples
./use_claude_code_examples.sh
```

## Migration Validation

After running the migration script, verify success with:

```bash
# Check organization membership
gcloud projects describe cherry-ai-project --format="value(parent.id)"
# Expected: 873291114285

# Check workstation deployment
gcloud workstations list --project=cherry-ai-project

# Verify GPU configuration
gcloud workstations configs describe ai-dev-config \
  --cluster=ai-development \
  --region=us-west4 \
  --format="json" | jq '.host.gceInstance.accelerators'
```

## Using Claude Code for Migration Tasks

Claude Code enhances your GCP management workflow in several ways:

### Pre-Migration Analysis

```bash
cd /workspaces/orchestra-main
claude "analyze if our project is ready for migration"
```

### Troubleshooting

```bash
claude "diagnose why I'm getting PERMISSION_DENIED during project move"
```

### Terraform Optimization

```bash
claude "analyze and optimize our hybrid workstation configuration"
```

### Post-Migration Verification

```bash
claude "create a comprehensive verification script for our GCP migration"
```

## Benefits of This Solution

1. **Robust Migration**: The migration script handles all critical aspects with proper waiting periods, verification steps, and error handling.

2. **Zero-Disk Authentication**: Service account credentials are never written to disk permanently, enhancing security.

3. **AI Integration**: Claude Code provides intelligent assistance for migration planning, troubleshooting, and optimization.

4. **High-Performance Hybrid IDE**: The deployed workstation uses n2d-standard-32 with 2x NVIDIA T4 GPUs for optimal AI development.

5. **Automated Verification**: Built-in validation ensures the migration completed successfully.

## Rate Limits & Considerations

With Claude Code's Max plan:

- Standard Max Plan ($100): ~225 messages or 10-20 coding tasks per 5 hours
- Enhanced Max Plan ($200): ~900 messages or 40-80 coding tasks per 5 hours

Optimize usage by:
- Using `/compact` to reduce context usage
- Initializing projects with `/init` for better memory management
- Monitoring usage with `/cost`

## Troubleshooting

Common migration issues and solutions:

1. **PERMISSION_DENIED**: Ensure you've waited the full 5 minutes for IAM propagation.

2. **Organization Not Found**: Verify you're using the exact numeric ID: 873291114285.

3. **Billing Not Linked**: After migration, you may need to manually link a billing account.

4. **Terraform Failures**: If Terraform deployment fails, examine the error and run:
   ```bash
   claude "help me fix this Terraform error: [error message]"
   ```

For Claude Code issues, run:
```bash
claude /doctor
```

## Security Notes

- The migration script uses temporary files for service account credentials.
- All key files are created with 600 permissions and promptly deleted.
- Cloud workstations use shielded VM configuration with secure boot.
- The Terraform configuration is designed with security best practices.

## Additional Resources

For detailed documentation on Claude Code, visit:
https://console.anthropic.com/docs/claude-code

For GCP organization migration best practices:
https://cloud.google.com/resource-manager/docs/moving-projects-between-organizations
