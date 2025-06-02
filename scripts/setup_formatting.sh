#!/bin/bash
# Simple formatting setup - no over-engineering!

echo "🎨 Setting up simple code formatting..."

# Add format commands to Makefile if not already there
if ! grep -q "^format:" Makefile; then
    cat >> Makefile << 'EOF'

# Code formatting commands
format:
	@echo "🎨 Formatting code with Black and isort..."
	@black . --quiet
	@isort . --quiet

lint:
	@echo "🔍 Running linters..."
	@flake8 .
	@echo "✅ Linting complete"

clean-code: format lint
	@echo "✨ Code is clean and formatted!"
EOF
    echo "✅ Added format, lint, and clean-code commands to Makefile"
else
    echo "📌 Format commands already in Makefile"
fi

# Update VSCode settings for auto-formatting
mkdir -p .vscode
cat > .vscode/settings.json << 'EOF'
{
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "editor.formatOnSave": true,
    "[python]": {
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        }
    },
    "python.linting.flake8Args": [
        "--config=.flake8"
    ],
    "roo-cline.rooCodeCloudEnabled": true
}
EOF
echo "✅ Updated VSCode/Cursor settings for auto-formatting"

# Check if formatting tools are installed
echo ""
echo "📦 Checking required tools..."
for tool in black isort flake8; do
    if pip show $tool >/dev/null 2>&1; then
        echo "✅ $tool is installed"
    else
        echo "❌ $tool is NOT installed - run: pip install $tool"
    fi
done

echo ""
echo "🎯 Simple formatting setup complete!"
echo ""
echo "Usage:"
echo "  make format     - Format all Python files"
echo "  make lint       - Run linters"
echo "  make clean-code - Format and lint"
echo ""
echo "VSCode/Cursor will now auto-format on save! 🚀" 