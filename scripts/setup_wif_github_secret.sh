#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# setup_wif_github_secret.sh
# -----------------------------------------------------------------------------
# Convenience helper for adding / updating the WIF_PROVIDER_ID GitHub secret
# required by the CI/CD workflow in `.github/workflows/main.yml`.
#
# USAGE:
#   ./scripts/setup_wif_github_secret.sh <provider-resource-name>
#
# EXAMPLE:
#   ./scripts/setup_wif_github_secret.sh \
#     "projects/123456789012/locations/global/workloadIdentityPools/pool-id/providers/provider-id"
# -----------------------------------------------------------------------------
set -euo pipefail

if ! command -v gh &>/dev/null; then
  echo "❌  GitHub CLI (gh) not found. Install from https://cli.github.com and retry." >&2
  exit 1
fi

if [ $# -ne 1 ]; then
  echo "Usage: $0 <WIF_PROVIDER_RESOURCE_NAME>" >&2
  exit 1
fi

WIF_PROVIDER_ID="$1"
REPO="$(git config --get remote.origin.url | sed -E 's#(git@github.com:|https://github.com/)##;s/\.git$//')"

if [[ -z "$REPO" ]]; then
  echo "❌  Could not determine repository (remote.origin.url)." >&2
  exit 1
fi

echo "🔑 Setting secret WIF_PROVIDER_ID for repo $REPO …"

gh secret set WIF_PROVIDER_ID --repo "$REPO" --body "$WIF_PROVIDER_ID"

echo "✅  Secret WIF_PROVIDER_ID set successfully." 