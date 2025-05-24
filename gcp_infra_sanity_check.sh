#!/bin/bash
# gcp_infra_sanity_check.sh
# One-command sanity check for solo GCP devs: authentication, account, project, IAM, org policy, Cloud Run, and secrets.

set -e

echo "=============================="
echo "GCP Infra Sanity Check (Solo Dev Edition)"
echo "=============================="
echo

# 1. Check gcloud authentication and active account
echo "1. Checking gcloud authentication and active account..."
gcloud info --format="value(config.account)" || true
ACTIVE_ACCOUNT=$(gcloud config get-value account 2>/dev/null)
if [[ -z "$ACTIVE_ACCOUNT" ]]; then
  echo "❌ No active gcloud account. Run: gcloud auth login"
  exit 1
else
  echo "✅ Active account: $ACTIVE_ACCOUNT"
fi

# 2. Check if using a Google (gmail/workspace) account, not a service account
if [[ "$ACTIVE_ACCOUNT" == *"gserviceaccount.com"* ]]; then
  echo "❌ You are using a service account. Run: gcloud auth login and select your Google account."
  exit 1
else
  echo "✅ Using a Google user account."
fi

# 3. Check active project
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [[ -z "$PROJECT_ID" ]]; then
  echo "❌ No active project set. Run: gcloud config set project YOUR_PROJECT_ID"
  exit 1
else
  echo "✅ Active project: $PROJECT_ID"
fi

# 4. Check org policy constraints that block public Cloud Run
echo
echo "2. Checking org policy for public Cloud Run access..."
gcloud org-policies list --project="$PROJECT_ID" | grep allowedPolicyMemberDomains || echo "No domain restriction policy found."
gcloud org-policies list --project="$PROJECT_ID" | grep run.allowedIngress || echo "No ingress restriction policy found."
echo "If you see nothing above, there are no org policies blocking public access at the project level."

# 5. Check Cloud Run IAM for orchestra-api
echo
echo "3. Checking Cloud Run IAM policy for orchestra-api..."
gcloud run services get-iam-policy orchestra-api --region=us-west4 --format=json | grep allUsers && echo "✅ allUsers has Cloud Run Invoker." || echo "❌ allUsers does NOT have Cloud Run Invoker."

# 6. Check Cloud Run service status
echo
echo "4. Checking Cloud Run service status..."
gcloud run services describe orchestra-api --region=us-west4 --format="value(status.url,status.conditions)"

# 7. Check for secrets in Secret Manager
echo
echo "5. Checking for secrets in Secret Manager..."
gcloud secrets list --format="table(name,replication.policy,createTime)"

echo
echo "=============================="
echo "Sanity check complete."
echo "If you see ❌ above, follow the suggested fix. If you see all ✅, your GCP infra is ready for solo dev sanity."
echo "=============================="
