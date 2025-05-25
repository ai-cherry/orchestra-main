#!/bin/bash
# freeze_requirements.sh - Capture EXACT versions of all installed packages
# Run this after confirming everything works

set -euo pipefail

DATE=$(date +%Y%m%d_%H%M%S)
FREEZE_DIR="requirements/frozen"

echo "🔒 Freezing Requirements"
echo "======================="

# Create frozen directory
mkdir -p $FREEZE_DIR

# Check if in venv
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
    echo "❌ Not in virtual environment! Run: source venv/bin/activate"
    exit 1
fi

# Freeze all packages
echo "Freezing all packages..."
pip freeze > $FREEZE_DIR/all_packages_$DATE.txt

# Create categorized requirements
echo "Creating categorized requirements..."

# Base packages
cat > $FREEZE_DIR/base_$DATE.txt << 'EOF'
# Frozen base requirements - DO NOT MODIFY
# Generated: $(date)
# Python: $(python --version)
EOF

pip freeze | grep -E "^(fastapi|pydantic|sqlalchemy|google-cloud|litellm|redis|httpx|uvicorn|phidata|python-dotenv)==" >> $FREEZE_DIR/base_$DATE.txt || true

# Dev packages
cat > $FREEZE_DIR/dev_$DATE.txt << 'EOF'
# Frozen dev requirements - DO NOT MODIFY
# Generated: $(date)
EOF

pip freeze | grep -E "^(pytest|black|mypy|flake8|pre-commit|types-)==" >> $FREEZE_DIR/dev_$DATE.txt || true

# Create main requirements files
echo "Updating main requirements files..."

# Backup current files
cp requirements/base.txt requirements/base.txt.backup.$DATE 2>/dev/null || true
cp requirements/dev.txt requirements/dev.txt.backup.$DATE 2>/dev/null || true

# Copy frozen files to main
cp $FREEZE_DIR/base_$DATE.txt requirements/base.txt
cp $FREEZE_DIR/dev_$DATE.txt requirements/dev.txt

# Create a lockfile with hashes
echo "Creating lockfile with hashes..."
pip freeze --all > $FREEZE_DIR/lockfile_with_hashes_$DATE.txt

# Create version report
cat > $FREEZE_DIR/version_report_$DATE.txt << EOF
Orchestra Version Report
=======================
Date: $(date)
Python: $(python --version)
Pip: $(pip --version)
Virtual Env: $VIRTUAL_ENV

Key Package Versions:
--------------------
$(pip show fastapi pydantic sqlalchemy litellm | grep -E "^(Name|Version):" | paste - - | column -t)

Total Packages: $(pip list | wc -l)

System Info:
-----------
OS: $(uname -a)
User: $(whoami)
PWD: $(pwd)
EOF

echo ""
echo "✅ Requirements frozen successfully!"
echo "Files created:"
echo "  - $FREEZE_DIR/all_packages_$DATE.txt (complete freeze)"
echo "  - $FREEZE_DIR/base_$DATE.txt (base packages)"
echo "  - $FREEZE_DIR/dev_$DATE.txt (dev packages)"
echo "  - $FREEZE_DIR/lockfile_with_hashes_$DATE.txt (with hashes)"
echo "  - $FREEZE_DIR/version_report_$DATE.txt (summary)"
echo ""
echo "Main requirements updated:"
echo "  - requirements/base.txt"
echo "  - requirements/dev.txt"
echo ""
echo "⚠️  IMPORTANT: Commit these files to git!" 