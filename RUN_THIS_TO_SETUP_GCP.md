it # Run This Command to Set Up GCP Now

To set up your GCP infrastructure with badass Vertex AI and Gemini service accounts, run the following command in your terminal:

```bash
chmod +x setup_gcp_now.sh && ./setup_gcp_now.sh
```

This will:

1. Make the script executable
2. Run the script to set up your GCP infrastructure

## What This Will Do

The script will:

1. Create service account key files
2. Authenticate with GCP
3. Enable required APIs
4. Create Vertex AI and Gemini service accounts with extensive permissions
5. Create service account keys
6. Store keys in Secret Manager
7. Set up Workload Identity Federation for GitHub Actions
8. Store secrets in GitHub (if GitHub CLI is installed)
9. Create GitHub Actions workflow
10. Verify the setup

## Prerequisites

- Google Cloud SDK (`gcloud`) installed and configured
- Terraform installed (optional, not required for this script)
- GitHub CLI (`gh`) installed (optional, for storing secrets in GitHub)

## Troubleshooting

If you encounter any issues:

1. Make sure you have the necessary permissions to create service accounts and grant IAM roles
2. Check that the Google Cloud SDK is properly installed and configured
3. Verify that the service account keys are valid

For more detailed instructions, refer to the `GCP_SETUP_GUIDE.md` file.
