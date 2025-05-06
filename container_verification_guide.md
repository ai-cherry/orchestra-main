# Container Verification Guide

## Project Information
- Project ID: cherry-ai.me
- Project Number: 525398941159
- Region: us-central1
- Registry: us-central1-docker.pkg.dev/cherry-ai.me/orchestra

## Container Image Verification Steps

1. **Verify Registry Access**
   ```bash
   gcloud auth configure-docker us-central1-docker.pkg.dev
   docker pull us-central1-docker.pkg.dev/cherry-ai.me/orchestra/api:latest
   ```

2. **Check Container Scan Results**
   ```bash
   gcloud artifacts docker images scan us-central1-docker.pkg.dev/cherry-ai.me/orchestra/api:latest
   ```

3. **Verify Container Signatures**
   ```bash
   cosign verify us-central1-docker.pkg.dev/cherry-ai.me/orchestra/api:latest
   ```

4. **Test Container Locally**
   ```bash
   docker run -p 8000:8000 \
     -e PROJECT_ID=cherry-ai.me \
     -e GOOGLE_CLOUD_PROJECT=cherry-ai.me \
     us-central1-docker.pkg.dev/cherry-ai.me/orchestra/api:latest
   ```

## Service Account Verification
- Service Account: vertex-agent@cherry-ai.me.iam.gserviceaccount.com
- Required Roles:
  - roles/artifactregistry.reader
  - roles/run.admin
  - roles/aiplatform.user

## Container Health Checks
- API Endpoint: http://localhost:8000/health
- Expected Response: {"status": "healthy"}
- Timeout: 5 seconds
- Period: 30 seconds

## Security Requirements
1. No privileged containers
2. Read-only root filesystem
3. Non-root user execution
4. Resource limits enforced
5. Network policies applied

## Verification Script

The `verify_container.sh` script will check for the following:

1. **Python version** - Should be version 3.11
2. **Poetry version**
3. **Docker version**
4. **Terraform version** - Should be version 1.5.x
5. It will also install all project dependencies using `poetry install --with dev`

## How to Use

After rebuilding your container, run the verification script:

```bash
./verify_container.sh
```

### Expected Output

The script will show the versions of all installed tools and report if any are missing from your PATH. You should see output similar to:

```
==== Environment Information ====
Date: [current date and time]
User: [your username]
Current directory: [working directory]

==== Python Version ====
Python 3.11.x

==== Poetry Version ====
Poetry (version x.x.x)

==== Docker Version ====
Docker version x.x.x, build xxxxxxx

==== Terraform Version ====
Terraform vx.x.x

==== Installing Poetry Dependencies ====
[output from poetry install --with dev]

==== Verification Complete ====
All required tools have been checked and dependencies installed.
```

## Manual Commands

If you prefer to run the verification commands individually:

```bash
# Check Python version
python --version

# Check Poetry version
poetry --version

# Check Docker version
docker --version

# Check Terraform version
terraform --version

# Install dependencies
poetry install --with dev
```

## Troubleshooting

If any tool is reported as not installed or not available in PATH:

1. Check that your `.devcontainer/devcontainer.json` file includes all required features
2. Ensure the container was rebuilt after making changes to the configuration
3. Try restarting the container
4. Check that the postCreateCommand completed successfully
