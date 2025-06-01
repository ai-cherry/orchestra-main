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
