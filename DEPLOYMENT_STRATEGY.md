# Orchestra Deployment Strategy

## Cloud Run as Primary Deployment Target

Based on careful evaluation of Orchestra's deployment needs, **Cloud Run** has been selected as the primary deployment target over Google Kubernetes Engine (GKE). This document explains this decision and provides guidance for deployment.

## Why Cloud Run?

Cloud Run offers several advantages for Orchestra's current needs:

1. **Simplicity**: Reduced operational overhead compared to managing Kubernetes clusters
2. **Cost Effectiveness**: Pay-per-use billing model with scaling to zero when not in use
3. **Managed Infrastructure**: Google handles the underlying infrastructure, reducing maintenance burden
4. **Fast Deployment**: Quicker deployment process with fewer moving parts
5. **Suitable for Stateless Applications**: Well-aligned with Orchestra's stateless API architecture

## Existing Deployment Infrastructure

The deployment infrastructure is already configured for Cloud Run:

1. **Terraform Configuration**: `infra/orchestra-terraform/` defines Cloud Run services
2. **Deployment Scripts**: `deploy.sh` and `deploy_to_production.sh` target Cloud Run
3. **Cloud Build**: `cloudbuild.yaml` is configured for Cloud Run deployment

## Deployment Process

To deploy Orchestra to production:

```bash
# Deploy to development environment
./deploy.sh dev

# Deploy to production environment
./deploy.sh prod
# or use the legacy script (redirects to deploy.sh)
./deploy_to_production.sh
```

The deployment script handles:
- Infrastructure provisioning via Terraform
- Docker image building and pushing
- Cloud Run service deployment
- PostgreSQL schema setup (if needed)
- Phidata UI deployment (if configured)

## CI/CD Integration

Continuous deployment is configured using Cloud Build:

1. **Build Trigger**: Create a Cloud Build trigger that uses `cloudbuild.yaml`
2. **Environment Variables**: Configure necessary variables in the trigger settings
3. **Secret Management**: Secrets are managed through Google Secret Manager and accessed securely

## GKE Resources (Deprecated)

The project originally contained Kubernetes manifests for GKE deployment. These files have been moved to `archived_files/kubernetes/` and are no longer maintained:

- `production-deployment.yaml`
- `production-service.yaml`
- `staging-deployment.yaml`
- `staging-service.yaml`

## When to Consider GKE

While Cloud Run is the preferred deployment target, GKE might be considered in these scenarios:

1. **Complex Stateful Workloads**: If Orchestra evolves to include stateful components that require specific persistence guarantees
2. **Special Scheduling Requirements**: Workloads requiring specific node selection or advanced scheduling
3. **Extremely High Scale**: When reaching the upper limits of Cloud Run's scaling capabilities
4. **Custom Network Policies**: Need for advanced network security beyond what Cloud Run provides

## Migration to GKE (If Needed)

If future requirements necessitate a move to GKE:

1. Update the archived Kubernetes manifests
2. Create a new deployment script targeting GKE
3. Update CI/CD pipeline to deploy to GKE
4. Plan a phased migration approach

For now, all deployment efforts and improvements should focus on optimizing the Cloud Run deployment path.
