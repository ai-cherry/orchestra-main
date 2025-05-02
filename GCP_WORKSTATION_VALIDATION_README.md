# GCP Environment Validation System

This system provides comprehensive validation and verification for GCP workstations, Vertex AI Workbench instances, and general GCP environments. It helps ensure that all required components are properly configured and accessible after migration or setup.

## Overview

The validation system consists of:

1. **Comprehensive Checklist**: A detailed checklist covering all aspects that need verification
2. **Master Validation Script**: A script that coordinates all validation activities
3. **Specialized Validation Scripts**: Individual scripts for validating specific components
4. **Setup Helper**: A script to configure Gemini Code Assist in the IDE

## Components

### 1. Validation Checklist

The file `GCP_MIGRATION_VALIDATION_CHECKLIST.md` provides a detailed checklist of all aspects that need verification:

- Source code and repository verification
- Secret Manager and credential verification
- Build and deployment pipeline verification
- Vertex AI and Gemini integration
- Development environment setup
- GCP best practices implementation

This checklist serves as both a guide for manual verification and a reference for what the automated scripts will check.

### 2. Master Validation Script

The `gcp_migration_validator.sh` script coordinates all validation activities:

```bash
# Run with default project and location
./gcp_migration_validator.sh

# Or specify custom project and location
./gcp_migration_validator.sh --project your-project-id --location your-location
```

This script will:
- Check prerequisites (Python, gcloud CLI, authentication)
- Run each specialized validation script
- Generate a comprehensive validation report

### 3. Specialized Validation Scripts

Located in the `scripts/validation/` directory, these scripts perform targeted validation of specific components:

- `validate_source.py`: Verifies source code accessibility
- `validate_secrets.py`: Verifies Secret Manager access
- `validate_build_deploy.py`: Verifies Cloud Build and deployment pipeline
- `validate_vertex.py`: Verifies Vertex AI integration
- `validate_gemini.py`: Verifies Gemini Code Assist in the IDE
- `validate_best_practices.py`: Assesses adherence to GCP best practices

Each script can be run individually if needed, but they're designed to be run by the master script.

### 4. Gemini IDE Integration Setup

The `setup_gemini_ide_integration.sh` script helps set up Gemini Code Assist in your IDE:

```bash
# Run with default project and location
./setup_gemini_ide_integration.sh

# Or specify custom project and location
./setup_gemini_ide_integration.sh --project your-project-id --location your-location
```

This script:
- Sets up required environment variables
- Installs the Google Cloud Code extension in VS Code
- Configures application default credentials
- Enables required GCP APIs
- Creates a test file and configuration for Gemini Code Assist

## Usage Instructions

### Complete Validation Process

To perform a complete validation of your GCP environment:

1. Run the master validation script:
   ```bash
   ./gcp_migration_validator.sh
   ```

2. Review the generated report (`gcp_validation_report.md`)

3. Address any issues identified in the report

4. Re-run the validation script to confirm all issues are resolved

### Setting up Gemini Code Assist

To set up Gemini Code Assist in your IDE:

1. Run the setup script:
   ```bash
   ./setup_gemini_ide_integration.sh
   ```

2. Follow the instructions displayed at the end of the script to test Gemini Code Assist

3. Validate the setup using the validation script:
   ```bash
   ./gcp_migration_validator.sh
   ```

## Addressing Common Issues

### Source Code Access Issues

If you encounter source code access issues:
- Ensure your git repository is properly cloned
- Verify all required directories exist
- Check that Python and poetry are properly installed

### Secret Manager Issues

If you encounter Secret Manager issues:
- Verify you have the correct permissions
- Ensure the secrets exist in the specified project
- Check that the Secret Manager API is enabled

### Cloud Build Issues

If you encounter Cloud Build issues:
- Verify the Cloud Build API is enabled
- Check that your service account has the necessary permissions
- Ensure your cloudbuild.yaml file is valid

### Vertex AI Issues

If you encounter Vertex AI issues:
- Verify the Vertex AI API is enabled
- Ensure required environment variables are set
- Check that your service account has the necessary permissions

### Gemini Code Assist Issues

If you encounter Gemini Code Assist issues:
- Ensure the Google Cloud Code extension is installed
- Verify application default credentials are set up
- Check that the Vertex AI API is enabled

## GCP Best Practices

The validation system checks for adherence to GCP best practices, including:

- **IAM & Security**: Least privilege principles, proper service account usage
- **Containerization**: Docker best practices, multi-stage builds, non-root users
- **Monitoring**: Custom metrics, alerting policies
- **Infrastructure-as-Code**: Terraform usage
- **Secret Management**: Using Secret Manager, avoiding hardcoded secrets
- **General Best Practices**: Workload identity, budget alerts, CI/CD pipelines

## References

- [GCP Migration Guide](GCP_MIGRATION_GUIDE.md)
- [Cloud Build Trigger Guide](GCP_CLOUDBUILD_TRIGGER_GUIDE.md)
- [Google Cloud Documentation](https://cloud.google.com/docs)
