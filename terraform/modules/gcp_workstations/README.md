# Google Cloud Workstations Module for AI Orchestra

This Terraform module deploys Google Cloud Workstations for the AI Orchestra project, providing a fully managed development environment in the cloud. The workstations are pre-configured with all the necessary tools and permissions to work with the AI Orchestra system.

## Overview

The module creates:
- A Cloud Workstations cluster
- A workstation configuration with custom container image
- A default workstation instance
- Service account with appropriate permissions
- Persistent disk storage for user data
- Cloud Storage bucket for data persistence
- Artifact Registry for container images
- Necessary IAM bindings and firewall rules

## Prerequisites

- Google Cloud project with billing enabled
- Required APIs enabled (this module will attempt to enable them)
- Terraform 1.0+
- Google provider 4.0+

## Required IAM Permissions

The account running Terraform needs the following permissions:
- `roles/workstations.admin`
- `roles/iam.serviceAccountAdmin`
- `roles/artifactregistry.admin`
- `roles/storage.admin`
- `roles/compute.admin`
- `roles/serviceusage.serviceUsageAdmin`

## Usage

```hcl
module "workstations" {
  source = "./terraform/modules/gcp_workstations"

  project_id         = var.project_id
  environment        = "dev"
  location           = "us-central1"
  network            = "default"
  subnetwork         = "default"
  machine_type       = "e2-standard-4"
  boot_disk_size_gb  = 50
  data_disk_size_gb  = 100
  cache_disk_size_gb = 20
  
  workstation_users = [
    "user:user@example.com",
    "group:developers@example.com"
  ]
}
```

## Input Variables

| Name | Description | Type | Default |
|------|-------------|------|---------|
| project_id | The GCP project ID | string | required |
| environment | Environment (dev, staging, prod) | string | "dev" |
| location | The GCP region where resources will be created | string | "us-central1" |
| network | The VPC network to use for workstations | string | "default" |
| subnetwork | The VPC subnetwork to use for workstations | string | "default" |
| machine_type | Machine type for workstation VMs | string | "e2-standard-4" |
| boot_disk_size_gb | Size of the boot disk in GB | number | 50 |
| data_disk_size_gb | Size of the data disk in GB | number | 100 |
| cache_disk_size_gb | Size of the cache disk in GB | number | 20 |
| workstation_image_version | Version of the workstation container image | string | "latest" |
| idle_timeout | Idle timeout for workstations in seconds | string | "3600s" (1 hour) |
| running_timeout | Maximum running time for workstations in seconds | string | "86400s" (24 hours) |
| workstation_users | List of users who can access workstations (emails in format 'user:user@example.com') | list(string) | [] |

## Outputs

| Name | Description |
|------|-------------|
| workstation_cluster_id | ID of the workstation cluster |
| workstation_config_id | ID of the workstation configuration |
| workstation_id | ID of the default workstation |
| workstation_service_account_email | Email of the service account used by workstations |
| workstation_bucket_name | Name of the GCS bucket for workstation data |
| workstation_cluster_endpoint | Endpoint URL for the workstation cluster |
| container_registry_id | ID of the Artifact Registry for container images |
| container_registry_location | Location of the Artifact Registry |

## Customization

### Custom Container Image

To use a custom container image for workstations, build and push your image to the Artifact Registry:

```bash
# Build the container image
docker build -t us-docker.pkg.dev/${PROJECT_ID}/orchestra-container-registry/orchestra-workstation:latest .

# Push the image to Artifact Registry
docker push us-docker.pkg.dev/${PROJECT_ID}/orchestra-container-registry/orchestra-workstation:latest
```

Then specify the version in the `workstation_image_version` variable.

### Custom Network Configuration

For enhanced security, you can deploy workstations in a custom VPC network:

```hcl
module "workstations" {
  source = "./terraform/modules/gcp_workstations"

  project_id = var.project_id
  network    = module.vpc.network_name
  subnetwork = module.vpc.subnet_name
  
  # ... other variables
}
```

## Deployment

1. Create a new directory for your workstation configuration:
   ```bash
   mkdir -p terraform/environments/dev/workstations
   ```

2. Create a `main.tf` file with the module configuration:
   ```hcl
   module "workstations" {
     source = "../../../modules/gcp_workstations"
     
     project_id = var.project_id
     environment = "dev"
     
     # ... other variables
   }
   ```

3. Initialize and apply Terraform:
   ```bash
   terraform init
   terraform apply
   ```

4. Access the workstation through the console or using the URL from the outputs:
   ```bash
   echo "Workstation URL: $(terraform output -raw workstation_cluster_endpoint)"
   ```

## Troubleshooting

### API Enablement Issues

If you encounter errors related to disabled APIs, manually enable the required APIs:

```bash
gcloud services enable workstations.googleapis.com \
    artifactregistry.googleapis.com \
    compute.googleapis.com \
    cloudresourcemanager.googleapis.com \
    secretmanager.googleapis.com \
    aiplatform.googleapis.com
```

### Permission Issues

Ensure the service account has the necessary permissions. You may need to grant additional roles:

```bash
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member serviceAccount:WORKSTATION_SA_EMAIL \
    --role roles/ROLE_NAME
```

### Container Image Access

If the workstation can't pull the container image, verify the service account has the `artifactregistry.reader` role:

```bash
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member serviceAccount:WORKSTATION_SA_EMAIL \
    --role roles/artifactregistry.reader
```

## License

This module is licensed under the MIT License - see the LICENSE file for details.