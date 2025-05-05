# Container Verification Guide

This guide helps you verify that your development container has been set up correctly with all the required tools and dependencies.

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
