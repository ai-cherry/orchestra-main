#!/bin/bash
# gcp_auth_cleanup_and_reset.sh
# Script to reset gcloud authentication to your real user account (scoobyjava@cherry-ai.me), remove service account creds, and set project context.

set -e

echo "=============================="
echo "GCP Auth Cleanup & Reset"
echo "=============================="

# 1. List all current gcloud accounts
echo
echo "Current gcloud accounts:"
gcloud auth list

# 2. Remove all service account credentials
echo
echo "Removing all service account credentials..."
gcloud auth revoke --all || true

# 3. Login with your real user account
echo
echo "Logging in as scoobyjava@cherry-ai.me..."
gcloud auth login scoobyjava@cherry-ai.me

# 4. Set the correct project
echo
echo "Setting project to cherry-ai-project..."
gcloud config set project cherry-ai-project

# 5. Set your user account as the active account
echo
echo "Setting active account to scoobyjava@cherry-ai.me..."
gcloud config set account scoobyjava@cherry-ai.me

# 6. Confirm everything
echo
echo "Active account and project after reset:"
gcloud config list account
gcloud config list project

echo
echo "If you see scoobyjava@cherry-ai.me as the active account and cherry-ai-project as the project, your gcloud is now clean and ready for admin work."
echo "=============================="
