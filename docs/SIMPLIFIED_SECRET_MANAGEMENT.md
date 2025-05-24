# Simplified Secret Management for Single-Developer Projects

## Overview

This document outlines a streamlined approach to secret management for single-developer, single-user projects in the AI Orchestra framework. It focuses on maintaining essential security protections while eliminating excessive overhead that creates unnecessary complexity.

## Simplified Approach

### 1. Local Development

For local development in a single-developer environment:

```bash
# Store secrets in a local .env file (added to .gitignore)
echo "API_KEY=your_api_key_here" >> .env
echo "OPENAI_API_KEY=your_openai_key_here" >> .env
```

Load environment variables in your application:

```python
import os
from dotenv import load_dotenv

# Simple environment loading
load_dotenv()
api_key = os.getenv("API_KEY")
```

### 2. Cloud Deployment

For cloud deployment, use GCP Secret Manager with simplified access:

```terraform
# Simple secret definition
resource "google_secret_manager_secret" "api_key" {
  secret_id = "api-key"
  replication {
    automatic = true
  }
}

# Simple access for the service account
resource "google_secret_manager_secret_iam_binding" "binding" {
  secret_id = google_secret_manager_secret.api_key.id
  role      = "roles/secretmanager.secretAccessor"
  members   = ["serviceAccount:${var.service_account}"]
}
```

### 3. CI/CD Integration

Simplified GitHub Actions workflow:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Auth to GCP
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Deploy to Cloud Run
        uses: google-github-actions/deploy-cloudrun@v1
        with:
          service: my-service
          region: us-central1
          env_vars: |
            ENVIRONMENT=production
```

## Security Essentials Maintained

1. **Gitignore Protection**: Sensitive files are still added to .gitignore
2. **Secret Manager**: Secrets are still stored in GCP Secret Manager
3. **Service Account Access**: Proper IAM roles are maintained

## Eliminated Complexity

1. **Automated Rotation**: Weekly rotation schedules removed
2. **Multi-environment Secrets**: Simplified naming conventions
3. **Complex Audit Logging**: Removed excessive logging
4. **Tiered Access Controls**: Simplified access model

## Best Practices for Single-Developer Projects

1. **Use .env files** for local development
2. **Keep secrets out of code** using environment variables
3. **Use Secret Manager** for cloud deployments
4. **Maintain a simple .gitignore** to prevent accidental commits

This simplified approach maintains essential security while eliminating unnecessary overhead for single-developer projects.
