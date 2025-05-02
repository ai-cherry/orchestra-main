# Deprecated Kubernetes Manifests

This directory contains Kubernetes manifest files that were part of an earlier deployment strategy for Orchestra that used Google Kubernetes Engine (GKE).

## Why These Files Are Archived

The project has standardized on Google Cloud Run as the primary deployment target due to:

- Simplicity of deployment and management
- Cost efficiency with pay-per-use and scaling to zero
- Reduced operational overhead
- Good fit for Orchestra's stateless architecture

## Contents

- `production-deployment.yaml`: Kubernetes Deployment for production environment
- `production-service.yaml`: Kubernetes Service for production environment
- `staging-deployment.yaml`: Kubernetes Deployment for staging environment
- `staging-service.yaml`: Kubernetes Service for staging environment

## Reference

For more information on the current deployment strategy, see the [DEPLOYMENT_STRATEGY.md](../../DEPLOYMENT_STRATEGY.md) document at the root of the repository.

## Future Use

If requirements change and Orchestra needs to move to GKE in the future, these files may serve as a starting point but would need to be updated to match the current application architecture.
