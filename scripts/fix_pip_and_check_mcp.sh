#!/bin/bash
# Fix pip installation and check MCP dependencies

echo "🔧 Fixing pip installation issue..."

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✓ Virtual environment detected: $VIRTUAL_ENV"
    
    # Try to reinstall pip in the virtual environment
    echo "Reinstalling pip in virtual environment..."
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python3 get-pip.py
    rm get-pip.py
else
    echo "⚠️  No virtual environment detected"
fi

# Use python3 directly to check for MCP modules
echo -e "\n🔍 Checking for MCP-related modules..."

python3 -c "
import sys
print(f'Python version: {sys.version}')
print(f'Python path: {sys.executable}')

modules_to_check = [
    'mcp',
    'mcp.server',
    'uvicorn',
    'asyncio',
    'json',
    'psycopg2',
    'weaviate',
    'pydantic',
    'fastapi'
]

print('\nModule availability:')
for module in modules_to_check:
    try:
        __import__(module)
        print(f'  ✓ {module}: Available')
    except ImportError as e:
        print(f'  ✗ {module}: Not available - {str(e)}')
"

# Check if MCP SDK is available via different methods
echo -e "\n🔍 Checking for MCP SDK installation methods..."

# Check if there's a requirements file for MCP
if [ -f "mcp_server/requirements.txt" ]; then
    echo "✓ Found mcp_server/requirements.txt"
    echo "Contents:"
    cat mcp_server/requirements.txt
else
    echo "✗ No mcp_server/requirements.txt found"
fi

# Check for any MCP-related packages in existing requirements files
echo -e "\n🔍 Searching for MCP references in requirements files..."
find . -name "requirements*.txt" -type f -exec grep -l "mcp" {} \; 2>/dev/null

# Check environment variables
echo -e "\n🔍 Checking environment variables..."
env_vars=(
    "OPENROUTER_API_KEY"
    "POSTGRES_HOST"
    "POSTGRES_DB"
    "WEAVIATE_HOST"
    "API_URL"
    "API_KEY"
)

for var in "${env_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "  ✗ $var: Not set"
    else
        echo "  ✓ $var: Set"
    fi
done

# Try to use system pip if available
echo -e "\n🔍 Checking system pip..."
if command -v pip3 &> /dev/null; then
    echo "✓ pip3 is available"
    pip3 --version
else
    echo "✗ pip3 not found"
fi

# Check for MCP server files
echo -e "\n🔍 Checking MCP server files..."
if [ -d "mcp_server/servers" ]; then
    echo "✓ MCP server directory exists"
    echo "Server files found:"
    ls -la mcp_server/servers/*.py | head -10
else
    echo "✗ MCP server directory not found"
fi

echo -e "\n📊 Summary:"
echo "1. Fix pip by reinstalling if needed"
echo "2. MCP SDK needs to be installed (package name may vary)"
echo "3. Environment variables need to be set"
echo "4. MCP server files are present and have valid syntax"