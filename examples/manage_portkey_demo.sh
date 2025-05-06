#!/bin/bash
# This script demonstrates the usage of the Portkey virtual keys management CLI tool

# Ensure MASTER_PORTKEY_ADMIN_KEY is set
if [ -z "$MASTER_PORTKEY_ADMIN_KEY" ]; then
    echo "Error: MASTER_PORTKEY_ADMIN_KEY environment variable is not set"
    echo "Please set it first: export MASTER_PORTKEY_ADMIN_KEY=your_portkey_admin_key"
    exit 1
fi

echo "=== Portkey Virtual Keys Management Demo ==="
echo ""

# List all existing keys
echo "Listing all existing virtual keys..."
python scripts/manage_portkey_keys.py list-keys

# Create a virtual key for OpenAI (uncomment and set your actual key to use)
echo ""
echo "Creating a virtual key for OpenAI..."
echo "# python scripts/manage_portkey_keys.py create-key --name \"OpenAI-Demo\" --provider openai --key \"sk-...\" --budget-limit 50"

# Create a virtual key for Anthropic (uncomment and set your actual key to use)
echo ""
echo "Creating a virtual key for Anthropic..."
echo "# python scripts/manage_portkey_keys.py create-key --name \"Anthropic-Demo\" --provider anthropic --key \"sk-...\" --budget-limit 50"

# Get details about a specific key (uncomment and set your actual key ID to use)
echo ""
echo "Getting details for a specific virtual key..."
echo "# python scripts/manage_portkey_keys.py get-key --id \"vk_...\" --format json"

# Update a key (uncomment and set your actual key ID to use)
echo ""
echo "Updating a virtual key..."
echo "# python scripts/manage_portkey_keys.py update-key --id \"vk_...\" --name \"OpenAI-Prod\" --budget-limit 100"

# Rotate a key (uncomment and set your actual key ID and new key to use)
echo ""
echo "Rotating a virtual key..."
echo "# python scripts/manage_portkey_keys.py rotate-key --id \"vk_...\" --new-key \"sk-...\""

# Create a gateway configuration for fallback (uncomment and set your actual virtual keys to use)
echo ""
echo "Creating a fallback gateway configuration..."
echo "# python scripts/manage_portkey_keys.py create-config --name \"Fallback-Demo\" --strategy fallback --providers '[
#   {\"virtual_key\": \"vk_openai_...\", \"models\": [\"gpt-4\", \"gpt-3.5-turbo\"]},
#   {\"virtual_key\": \"vk_anthropic_...\", \"models\": [\"claude-3-opus\", \"claude-3-sonnet\"]}
# ]'"

# List gateway configurations
echo ""
echo "Listing gateway configurations..."
echo "# python scripts/manage_portkey_keys.py list-configs"

# Get usage statistics (uncomment to use)
echo ""
echo "Getting usage statistics..."
echo "# python scripts/manage_portkey_keys.py get-usage --start-date 2025-01-01 --end-date 2025-04-23"

echo ""
echo "Demo complete. Uncomment the lines above to actually execute the commands."
echo "Make sure to replace the placeholder values with your actual API keys and virtual key IDs."
