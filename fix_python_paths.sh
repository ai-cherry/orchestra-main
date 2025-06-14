#!/bin/bash
# Fix Python path issues across all scripts

echo "🔧 Fixing Python paths across all scripts..."

# Find all shell scripts and Python files that use 'python' command
files_to_fix=(
    "orchestra_service_manager.sh"
    "start_mcp_memory.py"
    "start_api.sh"
    "start_mcp_memory_server.sh"
    "start_mcp_servers_working.sh"
    "start_orchestra.sh"
    "start_orchestra_complete.sh"
    "start_orchestra_simple.sh"
    "orchestra_autostart"
)

# Fix Python commands in shell scripts
for file in "${files_to_fix[@]}"; do
    if [ -f "$file" ]; then
        echo "Fixing $file..."
        # Replace 'python ' with 'python3 ' (with space to avoid replacing pythonic)
        sed -i.bak 's/python /python3 /g' "$file"
        # Replace 'python$' with 'python3' (at end of line)
        sed -i.bak 's/python$/python3/g' "$file"
        rm -f "$file.bak"
    fi
done

# Create Python symlink in virtual environment
if [ -d "venv" ]; then
    echo "Creating python symlink in venv..."
    if [ -f "venv/bin/python3" ] && [ ! -f "venv/bin/python" ]; then
        ln -s python3 venv/bin/python
    fi
fi

echo "✅ Python paths fixed!" 