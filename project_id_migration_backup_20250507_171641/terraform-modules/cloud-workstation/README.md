# GCP Cloud Workstation Terraform Module

This Terraform module provisions a Google Cloud Workstation configured for AI/ML development with:

- n2d-standard-32 machine type (32 vCPUs)
- 2x NVIDIA T4 GPUs for accelerated computing
- 1TB persistent SSD storage
- Preinstalled JupyterLab and IntelliJ
- IAM bindings for vertex-agent@ service account
- Security-focused configuration with shielded VMs

## Usage

```hcl
module "ai_workstation" {
  source = "path/to/cloud-workstation"

  project_id = "agi-baby-cherry"
  region     = "us-central1"
}
```

See the [example](./example) directory for a complete usage example.

## Requirements

- Google Cloud SDK 438.0.0+
- Terraform 1.5.0+
- Google Beta provider for some Cloud Workstation features

## Resources Created

- Cloud Workstation Cluster
- Cloud Workstation Configuration
- Cloud Workstation Instance
- IAM bindings for service account
- API service enablement

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| project_id | GCP project ID | string | "agi-baby-cherry" | yes |
| region | GCP region | string | "us-central1" | no |
| cluster_name | Workstation cluster name | string | "ai-development" | no |
| config_name | Workstation configuration name | string | "ai-dev-config" | no |
| workstation_name | Workstation instance name | string | "ai-workstation" | no |
| network_name | VPC network name | string | "default" | no |
| subnetwork_name | VPC subnetwork name | string | "default" | no |
| machine_type | Machine type | string | "n2d-standard-32" | no |
| gpu_type | GPU type | string | "nvidia-tesla-t4" | no |
| gpu_count | Number of GPUs | number | 2 | no |
| persistent_disk_size_gb | Persistent disk size (GB) | number | 1024 | no |
| environment_variables | Container environment variables | map(string) | {...} | no |
| disable_public_ip | Disable public IP | bool | false | no |

## Outputs

| Name | Description |
|------|-------------|
| workstation_url | URL to access the workstation |
| workstation_ip | External IP address (if enabled) |
| workstation_connection_command | Command to start and connect to the workstation |
| jupyter_connection_command | Command to connect to JupyterLab |
| machine_specs | Machine specifications |
| iam_bindings | IAM bindings created |

## Connecting to the Workstation

### Web Interface

Access the workstation through the web interface:

```
https://[REGION].workstations.cloud.google.com/[PROJECT_ID]/[REGION]/[CLUSTER_NAME]/[CONFIG_NAME]/[WORKSTATION_NAME]
```

### Command Line

Start and connect to the workstation:

```bash
gcloud workstations start [WORKSTATION_NAME] \
  --cluster=[CLUSTER_NAME] \
  --config=[CONFIG_NAME] \
  --region=[REGION] \
  --project=[PROJECT_ID]
```

### JupyterLab Access

Connect to JupyterLab via SSH tunnel:

```bash
gcloud compute ssh workstation-[CLUSTER_NAME]-[CONFIG_NAME]-[WORKSTATION_NAME] \
  --project=[PROJECT_ID] \
  --zone=[REGION]-a \
  -- -L 8888:localhost:8888
```

Then access JupyterLab at: http://localhost:8888

## Features

### Development Tools

The workstation comes preinstalled with:

- IntelliJ IDEA Ultimate (official Google Cloud Workstation image)
- JupyterLab with common data science packages
- Python 3 with numpy, pandas, tensorflow, scikit-learn, and matplotlib

### GPU Support

The workstation includes 2x NVIDIA T4 GPUs with CUDA and cuDNN for accelerated machine learning.

### Persistent Storage

A 1TB persistent SSD is mounted at `/home/user/persistent-data` for reliable storage of your work.

## IAM Configuration

The module grants the vertex-agent service account:

- `roles/workstations.user` - For workstation access
- `roles/aiplatform.user` - For Vertex AI access

## License

MIT
