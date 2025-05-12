# Google Cloud Workstation Migration Checklist

## Pre-Migration Tasks
- [ ] Verify GCP project access and permissions
- [ ] Install Google Cloud SDK and authenticate
- [ ] Install Terraform
- [ ] Document all GitHub secrets and environment variables
- [ ] Take inventory of required VS Code extensions

## Infrastructure Setup
- [ ] Run the migration script: `./gcp_workstation_migrate.sh`
- [ ] Create Terraform variables file
- [ ] Apply Terraform configuration
- [ ] Verify Cloud Workstation cluster is created
- [ ] Check service account permissions

## Secret Migration
- [ ] Run the secret migration script: `./migrate_secrets.sh`
- [ ] Verify all secrets are in Google Secret Manager
- [ ] Set up Secret Manager access for service accounts

## Development Environment Setup
- [ ] Launch Cloud Workstation from GCP Console
- [ ] Clone GitHub repository
- [ ] Run AI assistance setup script: `./setup_ai_assistance.sh`
- [ ] Configure VS Code settings and extensions
- [ ] Verify Gemini Code Assist integration

## CI/CD Pipeline Migration
- [ ] Set up Cloud Build triggers
- [ ] Convert GitHub Actions workflows to Cloud Build configs
- [ ] Set up proper service account permissions
- [ ] Test deployment pipeline
- [ ] Update documentation with new deployment instructions

## Post-Migration Verification
- [ ] Verify AI coding assistance works (Gemini, Roo, Cline)
- [ ] Test MCP memory integration
- [ ] Confirm Vertex AI access and integration
- [ ] Verify deployments work correctly
- [ ] Check that all extensions function as expected

## Runtime Cost Controls
- [ ] Set up budget alerts
- [ ] Configure auto-shutdown policies for workstations
- [ ] Implement cost monitoring dashboard

## Additional Considerations
- Both Roo and Cline will continue to work in the GCP environment
- MCP memory is fully compatible and enhanced in the GCP environment
- Direct integration with Vertex AI provides significantly improved performance
- GitHub remains your code repository but execution environment moves to GCP
