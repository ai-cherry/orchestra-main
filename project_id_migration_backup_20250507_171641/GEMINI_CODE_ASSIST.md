ex# Gemini Code Assist Integration

This document describes how the Gemini Code Assist has been integrated into the project using the Generative Language API.

## Overview

The Gemini Code Assist integration provides AI-powered code analysis directly in the CI/CD pipeline and during local development. It helps identify potential security issues, performance bottlenecks, and code quality concerns before they make it into production.

## Components

The integration consists of three main components:

1. **Secret Management**: Secure storage of the Gemini API key in Google Cloud Secret Manager
2. **Analysis Script**: A bash script that handles code analysis requests
3. **CI/CD Integration**: GitHub Actions workflow steps that automatically analyze code changes
4. **Local Development Hook**: A pre-commit hook for local code analysis

## Secret Management

The Gemini API key is securely stored in Google Cloud Secret Manager:

```bash
# The key is stored with automatic replication
gcloud secrets create GEMINI_API_KEY --data-file="gemini.key" \
  --project=agi-baby-cherry \
  --replication-policy=automatic

# The vertex-agent service account has access to the key
gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
  --member=serviceAccount:vertex-agent@agi-baby-cherry.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

The GitHub Actions workflow will ensure this secret exists and is configured correctly whenever code is pushed to the main branch.

## Analysis Script

The `analyze_code.sh` script handles code analysis requests:

```bash
./analyze_code.sh orchestrator/main.py,core/utils.py
```

Options:
- `--project=ID`: GCP Project ID (default: agi-baby-cherry)
- `--secret=NAME`: API key secret name (default: GEMINI_API_KEY)
- `--type=TYPE`: Analysis type: security|performance|style (default: security)
- `--output=PATH`: Path to output file (default: analysis-results.json)
- `--use-key=KEY`: Directly use API key instead of fetching from Secret Manager
- `--help`: Display help message

## CI/CD Integration

The GitHub Actions workflow has been updated to:

1. Automatically identify changed files in pull requests or pushes
2. Run code analysis on those files
3. Upload analysis results as artifacts
4. Block the deployment if critical issues are detected

This functionality runs in a dedicated job that happens before deployment.

## Local Development

A pre-commit hook has been set up to run code analysis before each commit:

```bash
# The hook analyzes staged files that match the patterns
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.py$|\.js$|\.ts$|\.go$')
```

To bypass the hook when needed:

```bash
git commit --no-verify
```

## Endpoint Information

The code analysis uses a Cloud Function endpoint:

- URL: `https://us-central1-agi-baby-cherry.cloudfunctions.net/code-analysis`
- API Key: Located in `gemini.key` file or in Secret Manager
- Method: `POST`
- Payload Structure:
  ```json
  {
    "files": ["path/to/file1.py", "path/to/file2.js"],
    "analysis_type": "security"
  }
  ```

## Available Analysis Types

- `security`: Identifies security vulnerabilities, potential exploits, and unsafe practices
- `performance`: Analyzes code for performance bottlenecks and inefficient patterns
- `style`: Reviews code against style guidelines and best practices

## Troubleshooting

If you encounter issues with the code analysis:

1. Ensure the API key is correct and accessible
2. Check the GCP permissions for the service account
3. Verify the files specified for analysis exist
4. Examine the analysis output for error messages

For local development issues:
```bash
# To test the hook manually
.git/hooks/pre-commit
```

## Maintenance

To update the API key:

```bash
# Update the key file
echo "NEW_API_KEY" > gemini.key

# Update the secret in Secret Manager (automatic in CI/CD)
./secrets_setup.sh --secret=GEMINI_API_KEY --file=gemini.key
