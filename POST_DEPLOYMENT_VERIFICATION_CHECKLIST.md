# Post-Deployment Verification Checklist

Use this checklist to verify that your Badass GCP & GitHub Integration has been properly deployed and is functioning correctly.

## Service Account Verification

- [ ] **Vertex AI Service Account**

  - [ ] Verified `vertex-ai-badass-access` service account exists in GCP
  - [ ] Confirmed service account has all required IAM roles
  - [ ] Validated that the service account key exists in GitHub organization secrets as `VERTEX_AI_BADASS_KEY`

- [ ] **Gemini API Service Account**

  - [ ] Verified `gemini-api-badass-access` service account exists in GCP
  - [ ] Confirmed service account has all required IAM roles
  - [ ] Validated that the service account key exists in GitHub organization secrets as `GEMINI_API_BADASS_KEY`

- [ ] **Gemini Code Assist Service Account**

  - [ ] Verified `gemini-code-assist-badass-access` service account exists in GCP
  - [ ] Confirmed service account has all required IAM roles
  - [ ] Validated that the service account key exists in GitHub organization secrets as `GEMINI_CODE_ASSIST_BADASS_KEY`

- [ ] **Gemini Cloud Assist Service Account**

  - [ ] Verified `gemini-cloud-assist-badass-access` service account exists in GCP
  - [ ] Confirmed service account has all required IAM roles
  - [ ] Validated that the service account key exists in GitHub organization secrets as `GEMINI_CLOUD_ASSIST_BADASS_KEY`

- [ ] **Secret Sync Service Account**
  - [ ] Verified `github-secret-sync-sa` service account exists in GCP
  - [ ] Confirmed service account has required Secret Manager IAM roles
  - [ ] Validated that the service account key exists in GitHub organization secrets as `GCP_SECRET_SYNC_KEY`

## GitHub Verification

- [ ] **GitHub Organization Secrets**

  - [ ] Verified all service account keys exist as secrets in GitHub organization
  - [ ] Confirmed GitHub PAT is stored securely or revoked if no longer needed

- [ ] **GitHub Organization Variables**

  - [ ] Verified `GCP_PROJECT_ID` is set correctly
  - [ ] Verified `GCP_PROJECT_NAME` is set correctly
  - [ ] Verified `GCP_REGION` is set correctly
  - [ ] Verified `GCP_ZONE` is set correctly
  - [ ] Verified `DEPLOYMENT_ENVIRONMENT` is set correctly

- [ ] **GitHub Actions Workflow**
  - [ ] Verified secret sync workflow exists in repository
  - [ ] Confirmed workflow permissions are properly configured

## GCP Secret Manager Verification

- [ ] **GitHub Secrets in GCP**

  - [ ] Verified all GitHub organization secrets are mirrored in GCP Secret Manager
  - [ ] Confirmed secrets have proper naming convention (`github-*`)
  - [ ] Validated that secret values have been properly updated (not placeholders)

- [ ] **GitHub PAT in GCP**
  - [ ] Verified GitHub PAT is stored in GCP Secret Manager as `github-pat`
  - [ ] Confirmed Secret Sync service account has access to the PAT secret

## Cloud Function and Scheduler Verification

- [ ] **Cloud Function**

  - [ ] Verified `github-gcp-secret-sync` function exists in GCP
  - [ ] Confirmed function has proper service account and permissions
  - [ ] Validated function can be manually triggered successfully

- [ ] **Cloud Scheduler**
  - [ ] Verified `github-gcp-secret-sync-daily` scheduler job exists
  - [ ] Confirmed scheduler is set to run at the expected frequency
  - [ ] Validated scheduler is using the correct service account

## End-to-End Testing

- [ ] **GitHub to GCP Sync Test**

  - [ ] Created a test secret in GitHub organization
  - [ ] Manually triggered the sync function
  - [ ] Verified the test secret was created in GCP Secret Manager
  - [ ] Deleted the test secret from both GitHub and GCP

- [ ] **Service Account Usage Test**
  - [ ] Created a test GitHub workflow that uses a service account key
  - [ ] Ran the workflow and confirmed successful authentication to GCP
  - [ ] Verified the workflow was able to access appropriate GCP resources

## Security Verification

- [ ] **Least Privilege Assessment**

  - [ ] Reviewed all service account permissions
  - [ ] Identified any permissions that could be removed without affecting functionality
  - [ ] Created a plan for reducing permissions in production environments

- [ ] **Workload Identity Federation Readiness**
  - [ ] Assessed readiness for transitioning to Workload Identity Federation
  - [ ] Reviewed the `switch_to_wif_authentication.sh` script
  - [ ] Created a plan for migration if appropriate

## Documentation and Training

- [ ] **Documentation**

  - [ ] Verified all documentation is up-to-date and accurate
  - [ ] Confirmed team members know where to find documentation

- [ ] **Team Training**
  - [ ] Conducted training session for relevant team members
  - [ ] Ensured team understands how to use the tools and scripts
  - [ ] Designated responsible person(s) for maintaining the integration

## Maintenance Plan

- [ ] **Key Rotation Schedule**

  - [ ] Established schedule for rotating service account keys
  - [ ] Documented process for key rotation

- [ ] **Monitoring Setup**
  - [ ] Set up alerts for Cloud Function failures
  - [ ] Configured monitoring for Cloud Scheduler job execution
  - [ ] Established process for reviewing logs periodically

---

Completed by: **********\_\_\_\_**********

Date: **********\_\_\_\_**********

Notes:
