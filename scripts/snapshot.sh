#!/bin/bash
# Create a snapshot of the /data volume using Lambda CLI
set -euo pipefail
VOLUME_ID="${LAMBDA_VOLUME_ID:-}"
if [[ -z "$VOLUME_ID" ]]; then
  echo "LAMBDA_VOLUME_ID is not set" >&2
  exit 1
fi
SNAP_ID=$(Lambda-cli snapshot create "$VOLUME_ID" | awk '{print $NF}')
echo "Created snapshot $SNAP_ID"
