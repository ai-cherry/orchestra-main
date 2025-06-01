#!/bin/bash
# Script to protect and monitor .roomodes configuration

echo "🛡️ Protecting Roo modes configuration..."

# Create a hash of the current .roomodes file
ROOMODES_HASH=$(sha256sum .roomodes | cut -d' ' -f1)
echo "Current .roomodes hash: $ROOMODES_HASH"

# Create a protected backup
cp .roomodes .roomodes.protected
chmod 444 .roomodes.protected
echo "✅ Created protected backup at .roomodes.protected"

# Create a monitoring script
cat > .roo/scripts/check_roomodes.sh << 'EOF'
#!/bin/bash
ORIGINAL_HASH=$(sha256sum .roomodes.protected | cut -d' ' -f1)
CURRENT_HASH=$(sha256sum .roomodes | cut -d' ' -f1)

if [ "$ORIGINAL_HASH" != "$CURRENT_HASH" ]; then
    echo "⚠️  WARNING: .roomodes file has been modified!"
    echo "Original hash: $ORIGINAL_HASH"
    echo "Current hash: $CURRENT_HASH"
    echo ""
    echo "To restore the protected configuration:"
    echo "  cp .roomodes.protected .roomodes"
else
    echo "✅ .roomodes file is unchanged"
fi
EOF

chmod +x .roo/scripts/check_roomodes.sh

echo ""
echo "📋 Instructions:"
echo "1. The .roomodes file is now protected with a backup"
echo "2. Run '.roo/scripts/check_roomodes.sh' to verify if it's been changed"
echo "3. If modes disappear, restore with: cp .roomodes.protected .roomodes"
echo ""
echo "🔍 Checking for potential conflicts..."

# Check for any other mode configuration files
if [ -f "$HOME/.cursor/roomodes" ]; then
    echo "⚠️  Found global roomodes at: $HOME/.cursor/roomodes"
fi

if [ -f "$HOME/.config/cursor/roomodes" ]; then
    echo "⚠️  Found config roomodes at: $HOME/.config/cursor/roomodes"
fi

# Check if mcp_server/roo/modes.py exists
if [ -f "mcp_server/roo/modes.py" ]; then
    echo "⚠️  Found hardcoded modes.py (already backed up)"
fi

echo ""
echo "✅ Protection complete!" 