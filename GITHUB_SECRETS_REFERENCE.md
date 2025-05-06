# GitHub Secrets Reference

A quick reference guide for all GitHub secrets required for GCP integration, Workload Identity Federation, Vertex AI, and Gemini services.

## GitHub Organization Level Secrets

### Workload Identity Federation Secrets
| Secret Name | Value | Source |
|-------------|-------|--------|
| `WIF_PROVIDER_ID` | `projects/525398941159/locations/global/workloadIdentityPools/github-pool/providers/github-provider` | Terraform output |
| `WIF_SERVICE_ACCOUNT` | `github-actions-deployer@cherry-ai-project.iam.gserviceaccount.com` | Terraform output |
| `GCP_PROJECT_ID` | `cherry-ai-project` | Project configuration |
| `GCP_PROJECT_NUMBER` | `525398941159` | Project configuration |

### Administrative Service Account Keys
| Secret Name | Description | Source |
|-------------|-------------|--------|
| `GCP_ADMIN_SA_KEY_JSON` | Admin service account key for initial setup | JSON key file |
| `GCP_PROJECT_ADMIN_KEY` | Project admin key for creating service accounts | JSON key file |
| `GCP_SECRET_MANAGEMENT_KEY` | Key for secret management operations | JSON key file |

### GitHub Authentication
| Secret Name | Value | Purpose |
|-------------|-------|---------|
| `GH_PAT` | `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` | GitHub Personal Access Token |

### General Service Account Keys 
| Secret Name | Description | Created By |
|-------------|-------------|------------|
| `VERTEX_AI_SERVICE_ACCOUNT_KEY` | Admin level access to Vertex AI | create_service_accounts_and_update_secrets.sh |
| `GEMINI_API_SERVICE_ACCOUNT_KEY` | Admin level access to Gemini API | create_service_accounts_and_update_secrets.sh |
| `GEMINI_CODE_ASSIST_SERVICE_ACCOUNT_KEY` | Admin level access to Gemini Code Assist | create_service_accounts_and_update_secrets.sh |
| `GEMINI_CLOUD_ASSIST_SERVICE_ACCOUNT_KEY` | Admin level access to Gemini Cloud Assist | create_service_accounts_and_update_secrets.sh |
| `SECRET_MANAGER_SERVICE_ACCOUNT_KEY` | Admin level access to Secret Manager | create_service_accounts_and_update_secrets.sh |

### Focused Service Account Keys
| Secret Name | Description | Created By |
|-------------|-------------|------------|
| `VERTEX_AI_FULL_ACCESS_KEY` | Focused access to Vertex AI | create_vertex_gemini_keys.sh |
| `GEMINI_API_FULL_ACCESS_KEY` | Focused access to Gemini API | create_vertex_gemini_keys.sh |
| `GEMINI_CODE_ASSIST_FULL_ACCESS_KEY` | Focused access to Gemini Code Assist | create_vertex_gemini_keys.sh |
| `GEMINI_CLOUD_ASSIST_FULL_ACCESS_KEY` | Focused access to Gemini Cloud Assist | create_vertex_gemini_keys.sh |

## GitHub Codespaces Secrets/Variables

The same secrets should be available in both GitHub Actions and GitHub Codespaces environments. The `update_codespaces_secrets.sh` script handles mirroring these values.

## Usage in GitHub Actions Workflows

### Using Workload Identity Federation (Preferred)
```yaml
- name: Authenticate to Google Cloud
  uses: google-github-actions/auth@v1
  with:
    workload_identity_provider: ${{ secrets.WIF_PROVIDER_ID }}
    service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}
```

### Using Service Account Keys
```yaml
- name: Authenticate to Google Cloud for Vertex AI
  uses: google-github-actions/auth@v1
  with:
    credentials_json: ${{ secrets.VERTEX_AI_FULL_ACCESS_KEY }}
