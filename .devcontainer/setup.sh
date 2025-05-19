#!/usr/bin/env bash
set -euo pipefail
echo "🔑  Fetching SA creds"
gcloud secrets versions access latest --secret=platform-admin-key > /workspace/credentials.json
gcloud auth activate-service-account --key-file=/workspace/credentials.json --quiet
pip install --upgrade pip
pip install -r requirements.txt || true
echo "✅  Dev container ready" 