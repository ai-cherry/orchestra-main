# Security Policy

## Reporting Security Issues

If you believe you have found a security vulnerability in the AI cherry_ai project, please report it to us through coordinated disclosure.

**Please do not report security vulnerabilities through public GitHub issues, discussions, or pull requests.**

Instead, please send an email to security@ai-cherry.com.

## Secret Management

This project follows secure practices for credential management:

1. **No Credentials in Code**: We never store actual credentials or secrets in the codebase.

2. **Secret Manager**: All credentials are stored in Google Cloud Secret Manager and accessed securely at runtime.

3. **False Positives**: Some files contain code that interacts with Secret Manager but do not contain actual secrets. These include:

   - `track_migration_progress.sh` - Contains functions to retrieve secrets from Secret Manager
   - Other utility scripts that check for the existence of secrets

4. **Secret Scanning Configuration**: We use `.github/secret_scanning.yml` to configure GitHub's secret scanning to ignore known false positives.

## Secure Development Practices

1. **Least Privilege**: Service accounts are configured with the minimum permissions needed.

2. **Workload Identity Federation**: We use Workload Identity Federation for GitHub Actions instead of service account keys.

3. **Regular Audits**: We regularly audit our security configurations and dependencies.

4. **Dependency Management**: We use Poetry to manage dependencies and regularly update them to address security vulnerabilities.
