#!/bin/bash
# Pulumi wrapper script that automatically handles passphrase
# This prevents passphrase prompts and warnings

# Set the passphrase
export PULUMI_CONFIG_PASSPHRASE="cherry_ai-dev-123"

# Disable update checks to avoid warnings
export PULUMI_SKIP_UPDATE_CHECK=true

# Run pulumi with all arguments passed to this script
exec pulumi "$@"
