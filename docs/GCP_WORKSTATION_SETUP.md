#
This guide provides instructions for setting up
## Overview

The `setup_
1. A Cloud Workstation cluster
2. A Cloud Workstation configuration with 3. A Cloud Workstation instance with JupyterLab and IntelliJ Ultimate
4. Service account with appropriate permissions

This setup provides a powerful development environment for AI Orchestra with:

- n2d-standard-16 machine (16 vCPUs, AMD Milan optimized)
- 200GB SSD boot disk
- NVIDIA Tesla T4 GPU for AI workloads
- JupyterLab for data science and ML development
- IntelliJ Ultimate for code development
- - Gemini SDK pre-installed
- Poetry for dependency management

## Prerequisites

Before running the script, ensure you have:

1. 2. Authenticated with gcloud (`gcloud auth login`)
3. Access to the `cherry-ai-project` 4. Permissions to create service accounts and assign IAM roles

## Usage

To set up the
```bash
# Make the script executable (if not already)
chmod +x setup_
# Run the script
./setup_```

The script will:

1. Check gcloud installation and authentication
2. Enable required APIs
3. Create a service account with appropriate permissions
4. Create a Cloud Workstation cluster
5. Create a Cloud Workstation configuration
6. Create a Cloud Workstation instance
7. Display the URL to access the workstation

## Configuration

The script uses the following default configuration:

- Project ID: `cherry-ai-project`
- Region: `us-west4`
- Cluster name: `ai-orchestra-cluster`
- Configuration name: `ai-orchestra-config`
- Workstation name: `ai-orchestra-workstation`
- Service account name: `vertex-ai-admin`
- Machine type: `n2d-standard-16`
- Boot disk size: `200GB`

You can modify these values in the script if needed.

## Accessing the Workstation

After the script completes successfully, it will display the URL to access the workstation. You can also access it through the
1. Go to the [Cloud Workstations page](https://console.cloud.google.com/workstations) in the 2. Select the `cherry-ai-project` project
3. Click on the `ai-orchestra-workstation` workstation
4. Click "Start" if the workstation is not already running
5. Click "Launch" to open the workstation in your browser

## Development Environment

The workstation comes pre-configured with:

### JupyterLab

- Access JupyterLab by running `/home/user/start_jupyter.sh` in the terminal
- JupyterLab will be available on port 8888
- Pre-installed packages include:
  - pandas
  - matplotlib
  - scikit-learn
  - tensorflow
  - ipywidgets

###
- Pre-installed and configured for the `cherry-ai-project` project
- Access through the `google.cloud.aiplatform` Python package

### Gemini SDK

- Pre-installed and ready to use
- Access through the `google.generativeai` Python package

### Poetry

- Pre-installed for Python dependency management
- Use for managing project dependencies

## Troubleshooting

If you encounter issues:

1. **Authentication errors**: Run `gcloud auth login` to authenticate
2. **Permission errors**: Ensure you have the necessary permissions in the 3. **API not enabled**: The script attempts to enable required APIs, but if it fails, enable them manually in the 4. **Resource already exists**: The script checks for existing resources and skips creation if they exist

## Security Considerations

The workstation is configured with security best practices:

- Private cluster with no public IP addresses
- Shielded VM with secure boot, vTPM, and integrity monitoring
- Service account with least privilege permissions

## Next Steps

After setting up the workstation:

1. Clone the AI Orchestra repository
2. Set up your development environment
3. Configure 4. Start developing with the pre-installed tools

## Cleanup

To delete the resources when no longer needed:

```bash
gcloud workstations delete ai-orchestra-workstation \
  --config=ai-orchestra-config \
  --cluster=ai-orchestra-cluster \
  --project=cherry-ai-project \
  --location=us-west4 \
  --quiet

gcloud workstations configs delete ai-orchestra-config \
  --cluster=ai-orchestra-cluster \
  --project=cherry-ai-project \
  --location=us-west4 \
  --quiet

gcloud workstations clusters delete ai-orchestra-cluster \
  --project=cherry-ai-project \
  --location=us-west4 \
  --quiet
```
