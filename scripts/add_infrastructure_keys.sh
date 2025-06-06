#!/bin/bash
# Add infrastructure keys to your .env file - RUN THIS ONCE when you have the keys!

echo "=== Infrastructure Keys Setup ==="
echo "This will add infrastructure keys to your .env file PERMANENTLY"
echo "You only need to run this ONCE when you get the keys!"
echo

# Function to add a key to .env if provided
add_to_env() {
    local key_name=$1
    local key_value=$2
    
    if [ -n "$key_value" ]; then
        # Remove existing key if present
        sed -i "/^$key_name=/d" .env 2>/dev/null
        # Add new key
        echo "$key_name=$key_value" >> .env
        echo "✅ Added $key_name to .env"
    fi
}

# Check if user wants to add keys
echo "Do you have infrastructure keys to add? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo
    echo "Enter your keys (press Enter to skip any key you don't have):"
    echo
    
    # Lambda API Key
    echo -n "LAMBDA_API_KEY (for cloud deployment): "
    read -r Lambda_KEY
    add_to_env "LAMBDA_API_KEY" "$Lambda_KEY"
    
    # Pulumi Passphrase
    echo -n "PULUMI_CONFIG_PASSPHRASE (optional, for state encryption): "
    read -r PULUMI_PASS
    add_to_env "PULUMI_CONFIG_PASSPHRASE" "$PULUMI_PASS"
    
    # AWS Keys (for S3 state backend)
    echo -n "AWS_ACCESS_KEY_ID (optional, for S3 state): "
    read -r AWS_KEY
    add_to_env "AWS_ACCESS_KEY_ID" "$AWS_KEY"
    
    if [ -n "$AWS_KEY" ]; then
        echo -n "AWS_SECRET_ACCESS_KEY: "
        read -r AWS_SECRET
        add_to_env "AWS_SECRET_ACCESS_KEY" "$AWS_SECRET"
    fi
    
    # Airbyte (probably not needed)
    echo
    echo "Airbyte keys (press Enter to skip - not needed for AI coordination):"
    echo -n "AIRBYTE_API_KEY: "
    read -r AIRBYTE_KEY
    add_to_env "AIRBYTE_API_KEY" "$AIRBYTE_KEY"
    
    if [ -n "$AIRBYTE_KEY" ]; then
        echo -n "AIRBYTE_API_URL: "
        read -r AIRBYTE_URL
        add_to_env "AIRBYTE_API_URL" "$AIRBYTE_URL"
        
        echo -n "AIRBYTE_WORKSPACE_ID: "
        read -r AIRBYTE_WS
        add_to_env "AIRBYTE_WORKSPACE_ID" "$AIRBYTE_WS"
    fi
    
    echo
    echo "✅ Infrastructure keys saved to .env!"
    echo "✅ They will be loaded automatically - you NEVER need to enter them again!"
else
    echo
    echo "No problem! Your AI coordination works perfectly without these keys."
    echo "Run this script later when you get infrastructure keys."
fi

echo
echo "Current status:"
./scripts/deployment_readiness_check.sh | grep -A20 "📊 SUMMARY"