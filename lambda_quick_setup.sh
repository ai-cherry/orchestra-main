#!/bin/bash
# Quick Lambda Labs Setup Script
# This script handles the API-only setup for Lambda Labs

set -e

# Configuration - Set these environment variables before running
: ${LAMBDA_TOKEN:?"Error: LAMBDA_TOKEN environment variable not set"}
: ${SSH_KEY_NAME:="manus-ai-deployment"}
: ${GITHUB_PAT:?"Error: GITHUB_PAT environment variable not set"}

# Get SSH public key from environment or file
if [ -z "$SSH_PUBLIC_KEY" ]; then
    if [ -f "$HOME/.ssh/id_rsa.pub" ]; then
        export SSH_PUBLIC_KEY=$(cat "$HOME/.ssh/id_rsa.pub")
    else
        echo "Error: SSH_PUBLIC_KEY not set and no key found at ~/.ssh/id_rsa.pub"
        exit 1
    fi
fi

echo "🚀 Lambda Labs Quick Setup"
echo "=========================="

# Step 1: Check existing SSH keys
echo -e "\n📋 Step 1: Checking existing SSH keys..."
EXISTING_KEYS=$(curl -s -X GET \
  -H "Authorization: Bearer $LAMBDA_TOKEN" \
  https://cloud.lambdalabs.com/api/v1/ssh-keys)

echo "$EXISTING_KEYS" | jq '.data[] | {id, name}'

# Check if our key already exists
KEY_ID=$(echo "$EXISTING_KEYS" | jq -r '.data[] | select(.name == "'$SSH_KEY_NAME'") | .id')

if [ -z "$KEY_ID" ]; then
    # Step 2: Upload SSH key
    echo -e "\n🔑 Step 2: Uploading SSH key..."
    UPLOAD_RESPONSE=$(curl -s -X POST \
      -H "Authorization: Bearer $LAMBDA_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"name":"'"$SSH_KEY_NAME"'","public_key":"'"$SSH_PUBLIC_KEY"'"}' \
      https://cloud.lambdalabs.com/api/v1/ssh-keys)
    
    echo "$UPLOAD_RESPONSE" | jq .
    KEY_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.data.id')
    echo "✅ SSH key uploaded with ID: $KEY_ID"
else
    echo "✅ SSH key already exists with ID: $KEY_ID"
fi

# Step 3: Configure Pulumi
echo -e "\n⚙️  Step 3: Configuring Pulumi..."

# Initialize Pulumi if needed
if [ ! -d ".pulumi" ]; then
    pulumi stack init orchestra-dev --non-interactive || true
fi

# Set Pulumi configuration
pulumi config set lambda:api_key "$LAMBDA_TOKEN" --secret
pulumi config set lambda:ssh_key_id "$KEY_ID"
pulumi config set github:token "$GITHUB_PAT" --secret
pulumi config set lambda:instance_type "gpu_1x_a10"
pulumi config set lambda:region "us-west-1"

echo "✅ Pulumi configured"

# Step 4: Check available instance types
echo -e "\n📊 Step 4: Checking available instance types..."
INSTANCE_TYPES=$(curl -s -X GET \
  -H "Authorization: Bearer $LAMBDA_TOKEN" \
  https://cloud.lambdalabs.com/api/v1/instance-types)

echo "$INSTANCE_TYPES" | jq -r '.data[] | select(.regions_with_capacity | length > 0) | {name, price_per_hour: .price_cents_per_hour, regions: .regions_with_capacity}'

# Step 5: Create instance
echo -e "\n🚀 Step 5: Creating Lambda Labs instance..."
CREATE_RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer $LAMBDA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instance_type": "gpu_1x_a10",
    "region": "us-west-1",
    "ssh_key_ids": ['$KEY_ID'],
    "quantity": 1,
    "name": "orchestra-dev"
  }' \
  https://cloud.lambdalabs.com/api/v1/instances)

echo "$CREATE_RESPONSE" | jq .

# Extract instance details
INSTANCE_ID=$(echo "$CREATE_RESPONSE" | jq -r '.data.instances[0].id')
INSTANCE_IP=$(echo "$CREATE_RESPONSE" | jq -r '.data.instances[0].ip')

if [ "$INSTANCE_ID" != "null" ] && [ ! -z "$INSTANCE_ID" ]; then
    echo "✅ Instance created!"
    echo "   ID: $INSTANCE_ID"
    echo "   IP: $INSTANCE_IP"
    
    # Save instance details
    cat > lambda_instance_info.json << EOF
{
  "instance_id": "$INSTANCE_ID",
  "ip_address": "$INSTANCE_IP",
  "ssh_key_id": $KEY_ID,
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
    
    # Wait for instance to be ready
    echo -e "\n⏳ Waiting for instance to be ready..."
    for i in {1..30}; do
        STATUS=$(curl -s -X GET \
          -H "Authorization: Bearer $LAMBDA_TOKEN" \
          https://cloud.lambdalabs.com/api/v1/instances/$INSTANCE_ID | \
          jq -r '.data.status')
        
        if [ "$STATUS" = "active" ]; then
            echo "✅ Instance is active!"
            break
        fi
        
        echo "   Status: $STATUS (attempt $i/30)"
        sleep 10
    done
    
    # Step 6: Bootstrap instance
    echo -e "\n🔧 Step 6: Setting up SSH config..."
    
    # Add to SSH config
    SSH_CONFIG="
Host orchestra-dev
    HostName $INSTANCE_IP
    User ubuntu
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
"
    
    if ! grep -q "Host orchestra-dev" ~/.ssh/config 2>/dev/null; then
        echo "$SSH_CONFIG" >> ~/.ssh/config
        echo "✅ Added orchestra-dev to SSH config"
    fi
    
    echo -e "\n🎉 Setup complete!"
    echo "================================"
    echo "Instance IP: $INSTANCE_IP"
    echo "SSH: ssh ubuntu@$INSTANCE_IP"
    echo "VS Code: code --remote ssh-remote+orchestra-dev /home/ubuntu/orchestra-main"
    echo ""
    echo "Next steps:"
    echo "1. SSH into the instance: ssh orchestra-dev"
    echo "2. Clone your repo: git clone https://github.com/lynnmusil/orchestra-main.git"
    echo "3. Run setup: cd orchestra-main && ./setup_mcp_environment.sh"
    
else
    echo "❌ Failed to create instance. Response:"
    echo "$CREATE_RESPONSE" | jq .
fi

# Create helper script for destroying instance
cat > lambda_destroy.sh << 'EOF'
#!/bin/bash
# Destroy Lambda Labs instance

INSTANCE_ID=$(cat lambda_instance_info.json 2>/dev/null | jq -r '.instance_id')
if [ -z "$INSTANCE_ID" ] || [ "$INSTANCE_ID" = "null" ]; then
    echo "No instance ID found"
    exit 1
fi

echo "Terminating instance $INSTANCE_ID..."
curl -s -X POST \
  -H "Authorization: Bearer $LAMBDA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"instance_ids": ["'$INSTANCE_ID'"]}' \
  https://cloud.lambdalabs.com/api/v1/instances/terminate | jq .

rm -f lambda_instance_info.json
echo "✅ Instance terminated"
EOF

chmod +x lambda_destroy.sh
echo -e "\nTo destroy the instance later, run: ./lambda_destroy.sh"