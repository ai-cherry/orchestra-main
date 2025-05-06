# Secret Manager Validation

This directory contains tools for validating your Secret Manager configuration for Orchestra. These tools help ensure that:

1. All required secrets are properly configured in Secret Manager
2. Cloud Run services have proper permissions to access secrets
3. Environment separation is properly enforced
4. Secret configuration follows best practices

## Prerequisites

Before you start, make sure you have the following:
- Python 3.7+
- Google Cloud SDK (gcloud)
- Authentication to your GCP project with Secret Manager access
- The following Python packages:
  - google-cloud-secretmanager

## Quick Start

To run the validation script:
Run the validation script to check your Secret Manager configuration:

```bash
# Make script executable (if not already)
chmod +x run_validation.sh

# Run validation on default environment (dev)
./run_validation.sh [your-project-id]

# To validate production environment
./run_validation.sh [your-project-id] prod 

# To validate a specific service in staging
./run_validation.sh [your-project-id] staging my-service-name
```

## Understanding the Results

The validation script checks the following aspects of your Secret Manager configuration:
The validation script checks several aspects of your Secret Manager configuration:

### Required Secrets

The script verifies that all required secrets for Orchestra are present and accessible in your Secret Manager:

- LLM API keys (OpenAI, Anthropic, etc.)
- Tool API keys (Portkey, Tavily, etc.)
- Infrastructure secrets (Redis, database credentials)
- GCP configuration secrets

### Environment Separation

The script checks that:
- Dev secrets are only present in dev environment
- Prod secrets are only present in prod environment
- Required production-only secrets exist in prod
- Non-production secrets are not present in prod

### Cloud Run Service Access

The script validates that your Cloud Run services:
- Have properly configured service accounts
- Those service accounts have secretAccessor role
- Can access the secrets they need

## Automated Integration

To integrate this validation into your CI/CD pipeline:
You can integrate this validation into your CI/CD pipeline:

```yaml
# Example GitHub Actions step
- name: Validate Secret Manager Configuration
  run: |
    cd infra/modules/secret-manager/validation
    ./run_validation.sh ${{ secrets.GCP_PROJECT_ID }} prod orchestra-api
  env:
    GOOGLE_APPLICATION_CREDENTIALS: ${{ secrets.GCP_SA_KEY }}
```

## Customizing Validation Rules

To customize which secrets are required or environment-specific:
To customize which secrets are required or environment-specific, edit the `validate_secrets.py` file and modify the following constants:

- `REQUIRED_SECRETS`: Dictionary of required secrets by category
- `PROD_ONLY_SECRETS`: Set of secrets that should only exist in prod
- `NON_PROD_SECRETS`: Set of secrets that should not exist in prod

## Troubleshooting

This section provides solutions to common issues you might encounter.
### Authentication Issues

If you see authentication errors:

```
Error: Not authenticated with gcloud
```

Run `gcloud auth login` and try again.

### Missing Secrets

If the validation fails due to missing secrets:

```
Required secret openai-api-key-prod not found
```

Check that you have created all necessary secrets in Secret Manager.

### Permission Issues

If you see access errors:

```
Cannot access required secret redis-auth-prod
```

Check that your account and the service being validated both have proper IAM permissions to access secrets.