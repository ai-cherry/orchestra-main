#!/bin/bash
# Create a snapshot of the /data volume using Vultr CLI
set -euo pipefail
VOLUME_ID="${VULTR_VOLUME_ID:-}"
if [[ -z "$VOLUME_ID" ]]; then
  echo "VULTR_VOLUME_ID is not set" >&2
  exit 1
fi
SNAP_ID=$(vultr-cli snapshot create "$VOLUME_ID" | awk '{print $NF}')
echo "Created snapshot $SNAP_ID"
