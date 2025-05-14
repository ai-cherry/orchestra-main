# AI Orchestra GCP Migration - Quick Start Guide

This guide provides step-by-step instructions for executing the AI Orchestra migration to Google Cloud Platform.

## Prerequisites

- Google Cloud SDK installed and configured
- Terraform installed (v1.0.0+)
- Python 3.11+ installed
- Docker installed
- Access to the AI Orchestra GitHub repository
- GCP Project with Owner or Editor permissions

## Setup Process

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/ai-orchestra.git
cd ai-orchestra
```

### 2. Configure Environment Variables

```bash
cd gcp_migration
cp .env.template .env
```

Edit the `.env` file with your specific configuration:
- `GCP_PROJECT_ID`: Your Google Cloud project ID
- `GCP_REGION`: The GCP region to deploy to
- `ENVIRONMENT`: Deployment environment (dev, staging, prod)
- `SERVICE_ACCOUNT`: Service account for the deployment
- Database credentials

### 3. Run the Migration Script

Execute the migration script with:

```bash
./execute_migration_now.sh
```

The script will:
1. Install all required dependencies
2. Authenticate with GCP
3. Set up Terraform state management
4. Deploy infrastructure (VPC, AlloyDB)
5. Configure and optimize the database
6. Deploy services to Cloud Run
7. Deploy AI models to Vertex AI
8. Set up monitoring and alerting
9. Verify the deployment

## Monitoring the Migration

The migration process generates comprehensive logs in the `migration_logs` directory.

You can monitor the progress in real-time through the terminal output, which shows:
- Step-by-step progress
- Success/failure indicators
- Time taken for each step

## Post-Migration Tasks

After the migration is complete:

1. Review the migration report at `migration_logs/migration_summary.md`
2. Verify that all services are running correctly
3. Update DNS records (if needed)
4. Set up additional monitoring alerts
5. Run a full test of the application

## Rollback Procedure

If you need to roll back the migration:

1. Run the following command to revert to the previous state:
   ```bash
   ./execute_migration_now.sh --rollback
   ```

2. This will:
   - Restore the previous configuration
   - Remove newly created GCP resources
   - Revert to the original state

## Troubleshooting

### Common Issues

1. **Authentication Failures**  
   Ensure you're logged in with `gcloud auth login` and have proper permissions.

2. **API Not Enabled**  
   The script enables required APIs, but if you encounter errors, enable them manually:
   ```bash
   gcloud services enable cloudresourcemanager.googleapis.com compute.googleapis.com containerregistry.googleapis.com run.googleapis.com secretmanager.googleapis.com aiplatform.googleapis.com alloydb.googleapis.com
   ```

3. **Terraform State Issues**  
   If Terraform state is corrupted, reset the state:
   ```bash
   terraform init -reconfigure
   ```

### Support

For additional support, contact the AI Orchestra migration team or open an issue in the GitHub repository.

## Next Steps

- Set up automated backup procedures
- Configure advanced monitoring
- Optimize resource usage based on performance metrics
- Train team members on the new GCP infrastructure

---

For a comprehensive understanding of the migration architecture, refer to the `MIGRATION_STRATEGY.md` document.