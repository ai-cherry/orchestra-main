#!/bin/bash
# Script to format Terraform files and validate configurations

# Set -e to exit on errors
set -e

echo "============================================="
echo "Running terraform fmt -recursive on ./infra"
echo "============================================="
terraform fmt -recursive ./infra

# Common environment
echo ""
echo "============================================="
echo "Initializing and validating common environment"
echo "============================================="
cd /workspaces/orchestra-main/infra/terraform/gcp/environments/common && terraform init && terraform validate

# Dev environment
echo ""
echo "============================================="
echo "Initializing and validating dev environment"
echo "============================================="
cd /workspaces/orchestra-main/infra/terraform/gcp/environments/dev && terraform init && terraform validate

# Prod environment
echo ""
echo "============================================="
echo "Initializing and validating prod environment"
echo "============================================="
cd /workspaces/orchestra-main/infra/terraform/gcp/environments/prod && terraform init && terraform validate

echo ""
echo "============================================="
echo "All environments formatted, initialized, and validated"
echo "============================================="
