#!/bin/bash
# Startup hook script to enforce standard mode at runtime

# Set environment variables
export USE_RECOVERY_MODE=false
export STANDARD_MODE=true

# Force standard mode via Python
python3 -c "
import os
os.environ['USE_RECOVERY_MODE'] = 'false'
os.environ['STANDARD_MODE'] = 'true'
print('STARTUP HOOK: Enforced standard mode through environment variables')
"

# Execute the original command
exec "$@"
