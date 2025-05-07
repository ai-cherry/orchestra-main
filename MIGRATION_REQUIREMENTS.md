# GCP Organization Migration - Real Requirements

This document outlines the actual requirements and critical steps needed to migrate the AGI Baby Cherry project to the Cherry AI organization and set up the hybrid IDE environment.

## Table of Contents

1. [Essential Prerequisites](#essential-prerequisites)
2. [Required Permissions & Quota](#required-permissions--quota)
3. [Step-by-Step Migration Process](#step-by-step-migration-process)
4. [Critical Verification Points](#critical-verification-points)
5. [Common Issues & Solutions](#common-issues--solutions)
6. [Pre-Migration Checklist](#pre-migration-checklist)

## Essential Prerequisites

Before beginning the migration, ensure you have:

### Required Tools
- **Google Cloud SDK** (gcloud CLI) - For all GCP operations
  - Installation: https://cloud.google.com/sdk/docs/install
  - Minimum version: 392.0.0 or higher
  
- **Terraform** - For infrastructure provisioning
  - Installation: https://developer.hashicorp.com/terraform/downloads
  - Minimum version: 1.0.0 or higher
  
- **jq** - For JSON processing in scripts
  - Installation: Use your system's package manager (apt, yum, homebrew, etc.)

### Required Files
- **Service account key file** for `vertex-agent@cherry-ai-project.iam.gserviceaccount.com`
- **Terraform configuration files**:
  - `hybrid_workstation_config.tf` - Main Terraform configuration for Cloud Workstations
  - `terraform.tfvars` - Variables file with project-specific values

## Required Permissions & Quota

### IAM Permissions
- **Source Project (cherry-ai-project):**
  - Project Owner or Editor role
  - Service Account Admin role
  - Security Admin role
  - Network Admin role
  
- **Target Organization (cherry-ai):**
  - Organization Admin role
  - Folder Admin role (if using folders)

### Resource Quota Requirements
- **GPU Quota** in us-west4 region:
  - 2x NVIDIA Tesla T4 GPUs per workstation (total: 6 GPUs for 3 workstations)
  
- **Compute Engine Quota:**
  - n2d-standard-32 VMs (32 vCPUs per workstation)
  - Total: 96 vCPUs for 3 workstations
  
- **Storage Quota:**
  - 500GB SSD boot disk per workstation
  - 1TB persistent storage per workstation
  - Total: ~4.5TB of SSD storage

### Networking Requirements
- **VPC Network** with private service access configured
- **IP Range** allocated for private services (Redis, AlloyDB)
- **Firewall Rules** allowing necessary traffic to workstations

## Step-by-Step Migration Process

### 1. Authentication & Authorization
```bash
# Interactive authentication
gcloud auth login

# OR service account authentication
gcloud auth activate-service-account vertex-agent@cherry-ai-project.iam.gserviceaccount.com --key-file=/path/to/key.json

# Set current project
gcloud config set project cherry-ai-project
```

### 2. Enable Required APIs
```bash
gcloud services enable \
  cloudresourcemanager.googleapis.com \
  iam.googleapis.com \
  workstations.googleapis.com \
  compute.googleapis.com \
  aiplatform.googleapis.com \
  storage.googleapis.com \
  redis.googleapis.com \
  alloydb.googleapis.com \
  serviceusage.googleapis.com \
  bigquery.googleapis.com \
  monitoring.googleapis.com
```

### 3. Project Migration
```bash
# Verify current project details
gcloud projects describe cherry-ai-project --format=json

# Perform the migration
gcloud projects move cherry-ai-project --organization=8732-9111-4285
```

### 4. Memory Layer Setup
```bash
# Create Redis instance
gcloud redis instances create agent-memory \
  --size=10 \
  --region=us-west4 \
  --tier=standard \
  --redis-version=redis_6_x \
  --connect-mode=private-service-access \
  --network=default

# Create AlloyDB cluster
gcloud alloydb clusters create agi-baby-cluster \
  --password=SECURE_PASSWORD_HERE \
  --region=us-west4 \
  --network=default

# Create AlloyDB instance
gcloud alloydb instances create alloydb-instance \
  --instance-type=PRIMARY \
  --cpu-count=8 \
  --region=us-west4 \
  --cluster=agi-baby-cluster \
  --machine-config=n2-standard-8 \
  --database=agi_baby_cherry \
  --user=alloydb-user
```

### 5. Cloud Workstation Setup with Terraform
```bash
# Create terraform.tfvars file
cat > terraform.tfvars << EOF
project_id = "cherry-ai-project"
project_number = "104944497835"
region = "us-west4"
zone = "us-west4-a"
env = "prod"
service_account_email = "vertex-agent@cherry-ai-project.iam.gserviceaccount.com"
admin_email = "scoobyjava@cherry-ai.me"
gemini_api_key = "AIzaSyA0rewcfUHo87WMEz4a8Og1eAWTslxlgEE"
gcs_bucket = "gs://cherry-ai-project-bucket/repos"
EOF

# Initialize and apply Terraform configuration
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```

## Critical Verification Points

After each major step, verify success before moving forward:

### 1. Project Organization Verification
```bash
gcloud projects describe cherry-ai-project --format=json | grep -A 2 parent
```
Expected output should show: `"parent": { "type": "organization", "id": "8732-9111-4285" }`

### 2. Redis Instance Verification
```bash
gcloud redis instances describe agent-memory --region=us-west4 --format=json
```
Verify status is "READY" and the configured size is 10GB

### 3. AlloyDB Verification
```bash
gcloud alloydb instances list --cluster=agi-baby-cluster --region=us-west4 --format=json
```
Verify instance type is "PRIMARY" and state is "READY"

### 4. Cloud Workstation Verification
```bash
gcloud workstations clusters list --format=json
gcloud workstations list --format=json
```
Verify at least one workstation is created and running

## Common Issues & Solutions

### 1. Permission Errors
- **Issue**: "Permission denied" or "Not authorized" errors
- **Solution**: 
  - Verify the authenticated account has proper IAM roles
  - Check for organization policies that might restrict operations
  - Use `gcloud projects get-iam-policy` to check current permissions

### 2. Quota Exceeded
- **Issue**: "Quota exceeded" errors, especially for GPUs or CPUs
- **Solution**:
  - Request quota increases through Google Cloud Console
  - Consider using a different region with available quota
  - Reduce the number of workstations or their size

### 3. Network Configuration
- **Issue**: "Private service access not configured" errors
- **Solution**:
  - Set up private service access for your VPC:
    ```bash
    gcloud compute addresses create google-managed-services-default \
      --global \
      --purpose=VPC_PEERING \
      --prefix-length=16 \
      --network=default
    
    gcloud services vpc-peerings connect \
      --service=servicenetworking.googleapis.com \
      --ranges=google-managed-services-default \
      --network=default
    ```

### 4. Terraform State Issues
- **Issue**: Terraform fails with state or resource conflicts
- **Solution**:
  - Check for existing resources with the same names
  - Use `terraform import` to bring existing resources into state
  - In extreme cases, use `terraform state rm` to remove problematic resources

## Pre-Migration Checklist

Complete this checklist before attempting the migration:

- [ ] **Access Verification**
  - [ ] Confirmed Organization Admin access to cherry-ai (ID: 8732-9111-4285)
  - [ ] Confirmed Project Owner access to cherry-ai-project (ID: 104944497835)
  - [ ] Verified service account permissions
  
- [ ] **Resource Verification**
  - [ ] Checked and confirmed GPU quota in target region
  - [ ] Verified VPC network configuration
  - [ ] Confirmed billing account is active and linked
  
- [ ] **Backup & Safety**
  - [ ] Created backup of project IAM policy
  - [ ] Documented currently running services
  - [ ] Prepared rollback plan in case of issues
  
- [ ] **Tools & Configuration**
  - [ ] Installed and configured Google Cloud SDK
  - [ ] Installed Terraform and verified version
  - [ ] Prepared service account key file
  - [ ] Reviewed and updated Terraform configuration

Once this checklist is complete, you are ready to begin the migration using the `real_migration_steps.sh` script or by following the steps in this document manually.
