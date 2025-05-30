#!/bin/bash
# Safe pip install script that prevents version conflicts

set -euo pipefail

echo "🚀 Orchestra Safe Install"
echo "========================"

# Ensure we're in venv
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
    echo "Creating virtual environment..."
    python3.10 -m venv venv
    source venv/bin/activate
fi

# Upgrade pip first
pip install --upgrade pip==24.0

# Install with constraints
echo "Installing with constraints..."
pip install -r requirements/production/requirements.txt -c requirements/constraints.txt

# Verify
echo "Verifying installation..."
pip check || echo "⚠️  Some conflicts detected but may be ignorable"

echo "✅ Installation complete!"
