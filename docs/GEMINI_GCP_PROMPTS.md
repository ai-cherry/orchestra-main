# Gemini GCP Prompts for AI Orchestra Setup

This document provides a series of prompts to use with Gemini in the GCP Cloud Shell to review, setup, and configure all the tools for the AI Orchestra project.

## Project Information

- Project name: cherry-ai-project
- Project number: 525398941159
- Project ID: cherry-ai-project
- GCP organization: cherry-ai.me

## Table of Contents

1. [Project Setup and API Enablement](#1-project-setup-and-api-enablement)
2. [Workload Identity Federation Setup](#2-workload-identity-federation-setup)
3. [Vertex AI Setup](#3-vertex-ai-setup)
4. [Cloud Workstations (Hybrid IDE) Setup](#4-cloud-workstations-hybrid-ide-setup)
5. [Kubernetes (GKE) Setup](#5-kubernetes-gke-setup)
6. [Database Setup (Firestore)](#6-database-setup-firestore)
7. [Secret Management](#7-secret-management)
8. [CI/CD Pipeline Setup](#8-cicd-pipeline-setup)
9. [Monitoring and Logging](#9-monitoring-and-logging)
10. [Cost Optimization](#10-cost-optimization)

## 1. Project Setup and API Enablement

### Prompt 1.1: Review and Enable Required APIs

```
I need to set up the AI Orchestra project in GCP. Please help me review which APIs need to be enabled and provide the gcloud commands to enable them. The project requires:

- Vertex AI
- Cloud Run
- Cloud Workstations
- Firestore
- Secret Manager
- Container Registry
- Artifact Registry
- Cloud Build
- IAM
- Cloud Storage
- Pub/Sub
- Cloud Scheduler

Please provide a script that checks which APIs are already enabled and enables any that are missing.
```

### Prompt 1.2: Project Configuration Check

```
Please analyze my current GCP project configuration and provide a report on:

1. Project ID and number
2. Default region and zone
3. Currently enabled APIs
4. Service accounts and their roles
5. IAM permissions
6. Networking setup (VPC, subnets, firewall rules)

For any missing or misconfigured components needed for the AI Orchestra project, provide the gcloud commands to fix them.
```

## 2. Workload Identity Federation Setup

### Prompt 2.1: GitHub to GCP Workload Identity Federation

```
I need to set up Workload Identity Federation between GitHub Actions and GCP for the AI Orchestra project. Please provide step-by-step instructions and gcloud commands to:

1. Create a Workload Identity Pool
2. Create a Workload Identity Provider for GitHub
3. Configure the necessary IAM permissions
4. Set up the GitHub Actions workflow to use Workload Identity Federation
5. Test the configuration

The GitHub organization is "ai-cherry" and the repository is "orchestra-main". The GCP project ID is "cherry-ai-project" and the GCP organization is "cherry-ai.me".
```

### Prompt 2.2: Verify Workload Identity Federation Setup

```
I've set up Workload Identity Federation for my GitHub Actions workflows. Please help me verify the setup by:

1. Checking the Workload Identity Pool configuration
2. Verifying the Workload Identity Provider settings
3. Testing the IAM permissions
4. Providing a sample GitHub Actions workflow that uses the Workload Identity Federation

If there are any issues, please provide the gcloud commands to fix them.
```

## 3. Vertex AI Setup

### Prompt 3.1: Vertex AI Service Account Setup

```
I need to create a service account for Vertex AI with the appropriate permissions for the AI Orchestra project. Please provide the gcloud commands to:

1. Create a service account named "vertex-power-user"
2. Assign the necessary roles for Vertex AI operations
3. Create and download a key for the service account
4. Store the key in Secret Manager
5. Configure the AI Orchestra application to use this service account

The service account should have permissions to:
- Create and manage Vertex AI endpoints
- Deploy models
- Run predictions
- Access necessary storage buckets
```

### Prompt 3.2: Vertex AI Model Deployment

```
I need to deploy a model to Vertex AI for the AI Orchestra project. Please provide the gcloud commands and steps to:

1. Upload a model to Vertex AI Model Registry
2. Create a Vertex AI endpoint
3. Deploy the model to the endpoint
4. Test the endpoint with a sample request
5. Set up monitoring for the endpoint

The model is a text generation model that will be used for the AI Orchestra application.
```

### Prompt 3.3: Vertex AI API Key Setup

```
I need to create and configure API keys for Vertex AI to be used by the AI Orchestra application. Please provide the gcloud commands and steps to:

1. Create an API key for Vertex AI
2. Restrict the API key to only the necessary APIs
3. Store the API key securely in Secret Manager
4. Configure the AI Orchestra application to use this API key
5. Set up key rotation

Please also include best practices for API key management in GCP.
```

## 4. Cloud Workstations (Hybrid IDE) Setup

### Prompt 4.1: Cloud Workstations Configuration

```
I need to set up Cloud Workstations for the AI Orchestra project to create a hybrid IDE environment. Please provide the gcloud commands and steps to:

1. Create a Cloud Workstations configuration
2. Set up a custom container image with the necessary development tools
3. Configure networking for the workstation
4. Set up persistent storage
5. Configure authentication and access control

The workstation should include:
- Python 3.11+
- Poetry
- Docker
- Terraform
- gcloud CLI
- GitHub CLI
- VS Code Server
```

### Prompt 4.2: Cloud Workstations Networking

```
I need to configure networking for Cloud Workstations in the AI Orchestra project. Please provide the gcloud commands and steps to:

1. Create a VPC for the workstations
2. Configure private IP addressing
3. Set up IAP for secure access
4. Configure firewall rules
5. Set up DNS configuration

The workstations should be able to access:
- GitHub repositories
- GCP services (Vertex AI, Firestore, etc.)
- Container registries
```

### Prompt 4.3: Cloud Workstations Integration with GitHub

```
I need to integrate Cloud Workstations with GitHub for the AI Orchestra project. Please provide the gcloud commands and steps to:

1. Configure Git credentials in the workstation
2. Set up GitHub authentication
3. Configure GitHub CLI
4. Set up pre-commit hooks
5. Configure VS Code extensions for GitHub integration

The GitHub organization is "ai-cherry" and the repository is "orchestra-main". The GCP project ID is "cherry-ai-project" and the GCP organization is "cherry-ai.me".
```

### Prompt 4.4: Cloud Workstations Persistent Configuration

```
I need to ensure that my Cloud Workstations configuration persists across sessions for the AI Orchestra project. Please provide the gcloud commands and steps to:

1. Configure persistent home directories
2. Set up dotfiles repository
3. Configure persistent VS Code settings
4. Set up persistent credentials
5. Configure automatic startup scripts

Please also include best practices for managing persistent configurations in Cloud Workstations.
```

## 5. Kubernetes (GKE) Setup

### Prompt 5.1: GKE Cluster Creation

```
I need to create a GKE cluster for the AI Orchestra project. Please provide the gcloud commands and steps to:

1. Create a GKE cluster with the appropriate size and configuration
2. Configure node pools
3. Set up Workload Identity for the cluster
4. Configure networking
5. Set up cluster monitoring

The cluster should be optimized for running AI workloads and should be cost-effective.
```

### Prompt 5.2: Kubernetes Deployment Configuration

```
I need to deploy the AI Orchestra application to GKE. Please provide the Kubernetes manifests and steps to:

1. Create deployments for the application components
2. Configure services and ingress
3. Set up ConfigMaps and Secrets
4. Configure resource requests and limits
5. Set up horizontal pod autoscaling

The application consists of:
- API service
- UI service
- Worker service
- Redis for caching
```

### Prompt 5.3: GKE Monitoring and Logging

```
I need to set up monitoring and logging for my GKE cluster in the AI Orchestra project. Please provide the gcloud commands and steps to:

1. Configure Cloud Monitoring for the cluster
2. Set up Cloud Logging
3. Create custom dashboards
4. Configure alerts
5. Set up log-based metrics

Please also include best practices for monitoring and logging in GKE.
```

## 6. Database Setup (Firestore)

### Prompt 6.1: Firestore Configuration

```
I need to set up Firestore for the AI Orchestra project. Please provide the gcloud commands and steps to:

1. Create a Firestore database in Native mode
2. Configure database location and settings
3. Set up collections and documents structure
4. Configure indexes
5. Set up backup and restore

The database will store:
- User data
- Agent configurations
- Conversation history
- System settings
```

### Prompt 6.2: Firestore Security Rules

```
I need to configure security rules for Firestore in the AI Orchestra project. Please provide the security rules and steps to:

1. Create security rules for collections
2. Configure authentication and authorization
3. Set up data validation
4. Configure access patterns
5. Test the security rules

The security rules should follow the principle of least privilege and ensure data is properly protected.
```

### Prompt 6.3: Firestore Indexes and Query Optimization

```
I need to optimize Firestore queries for the AI Orchestra project. Please provide the gcloud commands and steps to:

1. Analyze current query patterns
2. Create composite indexes for complex queries
3. Optimize data structure for query performance
4. Configure caching
5. Monitor query performance

Please also include best practices for Firestore query optimization.
```

## 7. Secret Management

### Prompt 7.1: Secret Manager Setup

```
I need to set up Secret Manager for the AI Orchestra project. Please provide the gcloud commands and steps to:

1. Create secrets for API keys, credentials, and configuration
2. Configure access control for secrets
3. Set up secret versioning
4. Configure secret rotation
5. Integrate secrets with Cloud Run, GKE, and other services

The secrets will include:
- API keys for Vertex AI, Gemini, and other services
- Database credentials
- GitHub tokens
- Service account keys
```

### Prompt 7.2: Secret Rotation Automation

```
I need to automate secret rotation for the AI Orchestra project. Please provide the gcloud commands and steps to:

1. Create a Cloud Function or Cloud Run service for secret rotation
2. Configure Cloud Scheduler to trigger rotation
3. Set up notifications for rotation events
4. Configure service account for rotation
5. Test the rotation process

The rotation should be applied to:
- API keys
- Service account keys
- Database credentials
```

## 8. CI/CD Pipeline Setup

### Prompt 8.1: GitHub Actions Workflow

```
I need to set up GitHub Actions workflows for the AI Orchestra project. Please provide the YAML configuration and steps to:

1. Create a workflow for CI (linting, testing, building)
2. Create a workflow for CD (deployment to Cloud Run or GKE)
3. Configure Workload Identity Federation for the workflows
4. Set up environment-specific deployments (dev, staging, prod)
5. Configure notifications for workflow events

The workflows should use Workload Identity Federation for authentication with GCP.
```

### Prompt 8.2: Cloud Build Configuration

```
I need to set up Cloud Build for the AI Orchestra project. Please provide the gcloud commands and YAML configuration to:

1. Create a Cloud Build trigger for GitHub repository
2. Configure build steps for testing, building, and deploying
3. Set up artifact storage
4. Configure service account permissions
5. Set up notifications for build events

The build process should include:
- Running tests
- Building Docker images
- Pushing images to Artifact Registry
- Deploying to Cloud Run or GKE
```

## 9. Monitoring and Logging

### Prompt 9.1: Cloud Monitoring Setup

```
I need to set up Cloud Monitoring for the AI Orchestra project. Please provide the gcloud commands and steps to:

1. Create custom dashboards for application metrics
2. Configure uptime checks
3. Set up alerting policies
4. Create service level objectives (SLOs)
5. Configure notification channels

The monitoring should cover:
- Cloud Run services
- GKE clusters
- Firestore
- Vertex AI endpoints
```

### Prompt 9.2: Cloud Logging Configuration

```
I need to configure Cloud Logging for the AI Orchestra project. Please provide the gcloud commands and steps to:

1. Configure log sinks
2. Create log-based metrics
3. Set up log exports to BigQuery
4. Configure log exclusions
5. Set up log-based alerts

The logging should capture:
- Application logs
- System logs
- Audit logs
- Error logs
```

## 10. Cost Optimization

### Prompt 10.1: Cost Analysis and Optimization

```
I need to analyze and optimize costs for the AI Orchestra project in GCP. Please provide the gcloud commands and steps to:

1. Analyze current resource usage and costs
2. Identify cost optimization opportunities
3. Configure budget alerts
4. Implement cost-saving measures
5. Monitor cost trends

Please focus on optimizing costs for:
- Vertex AI usage
- GKE clusters
- Cloud Run services
- Cloud Storage
- Firestore
```

### Prompt 10.2: Resource Quotas and Limits

```
I need to configure resource quotas and limits for the AI Orchestra project in GCP. Please provide the gcloud commands and steps to:

1. Review current quotas and limits
2. Request quota increases where needed
3. Configure resource limits for services
4. Set up monitoring for quota usage
5. Configure alerts for approaching limits

Please focus on quotas and limits for:
- Vertex AI API requests
- GKE resources
- Cloud Run instances
- Firestore operations
- API requests
```

## Comprehensive Setup Script

### Prompt: Generate Complete Setup Script

```
I need a comprehensive script to set up the entire AI Orchestra infrastructure in GCP. Please generate a bash script that:

1. Enables all required APIs
2. Sets up Workload Identity Federation with GitHub
3. Creates and configures Vertex AI resources
4. Sets up Cloud Workstations for hybrid IDE
5. Creates a GKE cluster (if needed)
6. Configures Firestore database
7. Sets up Secret Manager with all required secrets
8. Configures monitoring and logging
9. Sets up CI/CD pipelines
10. Implements cost optimization measures

The script should be idempotent, include error handling, and provide detailed logging of each step.

Project details:
- Project name: cherry-ai-project
- Project number: 525398941159
- Project ID: cherry-ai-project
- GCP organization: cherry-ai.me
- GitHub organization: ai-cherry
- GitHub repository: orchestra-main
```

## Hybrid IDE Specific Setup

### Prompt: Complete Hybrid IDE Setup

```
I need to complete the setup of the hybrid IDE environment for the AI Orchestra project using Cloud Workstations. Please provide a detailed script that:

1. Creates a Cloud Workstations configuration with the following:
   - Base image: Ubuntu 22.04
   - Pre-installed tools: Python 3.11, Poetry, Docker, Terraform, gcloud CLI, GitHub CLI
   - VS Code Server with extensions for Python, Docker, Terraform, and GitHub
   - Persistent storage configuration

2. Sets up the necessary networking:
   - VPC configuration
   - Private IP addressing
   - IAP for secure access
   - Firewall rules

3. Configures authentication and access:
   - Service account with necessary permissions
   - GitHub authentication
   - GCP authentication

4. Sets up persistent configuration:
   - Dotfiles repository
   - VS Code settings
   - Git configuration
   - Shell configuration

5. Configures integration with other GCP services:
   - Vertex AI
   - Firestore
   - Secret Manager
   - Cloud Storage

Project details:
- Project name: cherry-ai-project
- Project number: 525398941159
- Project ID: cherry-ai-project
- GCP organization: cherry-ai.me
- GitHub organization: ai-cherry
- GitHub repository: orchestra-main

Please include all necessary gcloud commands and configuration files.
```

### Prompt: Verify and Troubleshoot Hybrid IDE Setup

```
I've set up the hybrid IDE environment using Cloud Workstations, but I need to verify and troubleshoot the setup. Please provide a script that:

1. Verifies the Cloud Workstations configuration:
   - Checks if the workstation is running
   - Verifies installed tools and versions
   - Tests connectivity to GitHub and GCP services

2. Troubleshoots common issues:
   - Authentication problems
   - Networking issues
   - Permission errors
   - Storage problems

3. Provides fixes for identified issues:
   - gcloud commands to fix configuration
   - Configuration file updates
   - Permission adjustments

4. Sets up monitoring for the workstation:
   - Resource usage monitoring
   - Uptime checks
   - Log analysis

Please include detailed explanations for each check and fix.
```

## Vertex AI Integration

### Prompt: Complete Vertex AI Integration

```
I need to fully integrate Vertex AI with the AI Orchestra project. Please provide a comprehensive script that:

1. Sets up the necessary service accounts and permissions:
   - Creates a service account for Vertex AI
   - Assigns appropriate roles
   - Creates and securely stores keys

2. Configures Vertex AI resources:
   - Creates endpoints
   - Deploys models
   - Sets up prediction services

3. Integrates with the AI Orchestra application:
   - Configures environment variables
   - Sets up authentication
   - Implements API calls

4. Sets up monitoring and logging:
   - Creates custom dashboards
   - Configures alerts
   - Sets up log analysis

5. Implements cost optimization:
   - Configures auto-scaling
   - Sets up budget alerts
   - Optimizes resource usage

Project details:
- Project name: cherry-ai-project
- Project number: 525398941159
- Project ID: cherry-ai-project
- GCP organization: cherry-ai.me
- GitHub organization: ai-cherry
- GitHub repository: orchestra-main

Please include all necessary gcloud commands, API calls, and configuration files.
```

## End-to-End Testing

### Prompt: Create End-to-End Testing Script
```
I need to create an end-to-end testing script for the AI Orchestra infrastructure in GCP. Please provide a script that:

1. Tests connectivity and authentication:
   - GitHub to GCP via Workload Identity Federation
   - Cloud Workstations to GCP services
   - Application to Vertex AI
   - Application to Firestore

2. Tests deployment pipelines:
   - GitHub Actions workflows
   - Cloud Build triggers
   - Deployment to Cloud Run or GKE

3. Tests application functionality:
   - API endpoints
   - UI functionality
   - Integration with Vertex AI
   - Data storage in Firestore

4. Tests monitoring and alerting:
   - Simulates errors to trigger alerts
   - Verifies log collection
   - Checks dashboard functionality

5. Tests disaster recovery:
   - Simulates service outages
   - Tests backup and restore procedures
   - Verifies high availability configurations

Project details:
- Project name: cherry-ai-project
- Project number: 525398941159
- Project ID: cherry-ai-project
- GCP organization: cherry-ai.me
- GitHub organization: ai-cherry
- GitHub repository: orchestra-main

Please include detailed steps, expected results, and troubleshooting guidance for each test.
```