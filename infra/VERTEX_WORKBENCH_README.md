# Vertex AI Workbench Infrastructure

This Terraform configuration provisions a complete environment for AI/ML workloads on Google Cloud Platform, including Vertex AI Workbench, Firestore, Redis, and Secret Manager resources.

## Resources Provisioned

1. **Vertex AI Workbench**
   - 4 vCPUs, 16GB RAM (n1-standard-4 with T4 GPU acceleration)
   - TensorFlow 2.10 with CUDA 11.3 pre-installed
   - 100GB SSD boot disk
   - Shielded VM with secure boot enabled

2. **Firestore Database**
   - Native mode database
   - Optimistic concurrency
   - Daily automated backups (2:00 AM UTC)
   - 30-day backup retention

3. **Memorystore Redis**
   - 3GB memory capacity
   - High-availability configuration
   - Transit encryption enabled
   - Authentication enabled
   - Automatic weekly maintenance (Sundays 2:00 AM)

4. **Secret Manager**
   - Vertex AI API key secret
   - Redis authentication secret
   - Firestore backup credentials

5. **Additional Resources**
   - Service account with appropriate IAM permissions
   - Required GCP API services enabled
   - Backup storage bucket with uniform access control
   - Pub/Sub topic and Cloud Scheduler for backup automation

## Prerequisites

1. Google Cloud Platform account with billing enabled
2. Owner or Editor role on the target GCP project
3. Terraform v1.0.0+ installed
4. Google Cloud SDK installed and configured

## Usage

1. **Initialize Terraform**
   ```bash
   cd infra
   terraform init
   ```

2. **Customize Variables (Optional)**
   Edit `vertex_workbench.tfvars` to customize:
   - `project_id`: Your GCP project ID
   - `region`: Deployment region
   - `env`: Environment name (dev, stage, prod)
   - Other resource names and configurations

3. **Review the Execution Plan**
   ```bash
   terraform plan -var-file=vertex_workbench.tfvars
   ```

4. **Apply the Configuration**
   ```bash
   terraform apply -var-file=vertex_workbench.tfvars
   ```

5. **Access Connection Details**
   After successful deployment, connection details will be:
   - Printed to the console as output
   - Written to `infra/connection_details.json`

## Connection Details

The configuration outputs a JSON document containing all connection information:

```json
{
  "vertex_workbench": {
    "name": "vertex-workbench-dev",
    "url": "https://us-central1.notebooks.cloud.google.com/view/your-project-id/us-central1/vertex-workbench-dev",
    "machine_type": "n1-standard-4",
    "location": "us-central1"
  },
  "firestore": {
    "name": "orchestrator-db",
    "type": "FIRESTORE_NATIVE",
    "location": "us-central1",
    "backup_bucket": "your-project-id-firestore-backups",
    "backup_schedule": "Daily at 2:00 AM UTC"
  },
  "redis": {
    "host": "10.0.0.1",
    "port": "6379",
    "memory_size": "3 GB",
    "auth_enabled": true,
    "auth_secret": "projects/your-project-id/secrets/redis-auth/versions/latest"
  },
  "secrets": {
    "vertex_api_key": "projects/your-project-id/secrets/vertex-api-key/versions/latest",
    "redis_auth": "projects/your-project-id/secrets/redis-auth/versions/latest",
    "firestore_backup_credentials": "projects/your-project-id/secrets/firestore-backup-credentials/versions/latest"
  },
  "service_account": {
    "email": "orchestrator-service-account@your-project-id.iam.gserviceaccount.com",
    "roles": [
      "roles/datastore.user",
      "roles/redis.editor",
      "roles/secretmanager.secretAccessor",
      "roles/aiplatform.user"
    ]
  }
}
```

## Security Notes

1. The Vertex AI API key is stored in Secret Manager, but its value is included in the Terraform state. For production use, consider:
   - Using Terraform's sensitive data handling
   - Managing the secret outside of Terraform
   - Using a key management service

2. By default, the configuration uses Google's service account for the Workbench instance. For production, consider creating a custom service account with minimal permissions.

## Cleanup

To destroy all resources created by this configuration:

```bash
terraform destroy -var-file=vertex_workbench.tfvars
```

**Important**: This will permanently delete all resources, including the Firestore database and its data. Make sure to back up important data before running this command.
