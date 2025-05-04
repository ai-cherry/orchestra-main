# GitHub to GCP Secret Manager Migration

This guide explains how to migrate GitHub organization secrets to Google Cloud Secret Manager.

## Prerequisites

- Google Cloud CLI (`gcloud`) installed and configured
- GitHub CLI (`gh`) installed (the script will attempt to install it if not found)
- Python 3 with `google-cloud-secretmanager` package
- Appropriate permissions:
  - GitHub: Personal access token with `admin:org` scope
  - GCP: Service account with Secret Manager Admin role

## Migration Script

We've created a wrapper script `migrate_github_to_gcp_secrets.sh` that handles:

1. Authentication to both GitHub and GCP
2. Creation of temporary credential files
3. Running the underlying migration tool
4. Secure cleanup after completion

## Usage

1. Make the script executable (already done):
   ```
   chmod +x migrate_github_to_gcp_secrets.sh
   ```

2. Run the script:
   ```
   ./migrate_github_to_gcp_secrets.sh
   ```

3. When prompted, enter your GitHub organization name.

4. For each GitHub secret, you will be prompted to provide the value (since GitHub doesn't allow retrieving the encrypted values).

## Configuration

The script is pre-configured with:

- Project ID: `cherry-ai-project`
- Service account: `secret-management@cherry-ai-project.iam.gserviceaccount.com`
- GitHub token: Provided in the script
- Environment: `prod` (secrets will be created with `-prod` suffix)

## Security Notes

- The service account key is created in a temporary directory and deleted after use
- The GitHub token should be revoked or rotated after migration
- All secrets in GCP Secret Manager should be verified after migration

## Using Secrets in GitHub Actions

After migration, you can access the secrets from GCP Secret Manager in your GitHub Actions workflows:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: "Authenticate to Google Cloud"
        uses: "google-github-actions/auth@v1" 
        with:
          credentials_json: "${{ secrets.GCP_SA_KEY }}"
          
      - name: "Set up Cloud SDK"
        uses: "google-github-actions/setup-gcloud@v1"
        
      - name: "Access secret from Secret Manager" 
        run: |
          SECRET_VALUE=$(gcloud secrets versions access latest --secret=SECRET_NAME-prod)
          echo "SECRET_VALUE=$SECRET_VALUE" >> $GITHUB_ENV
```

Replace `SECRET_NAME` with the name of your secret.
