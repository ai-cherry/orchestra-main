#!/bin/bash
set -euo pipefail

# --- CONFIG ---
API_URL="https://cherry-ai.me"
API_KEY="4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd"
ADMIN_UI_DIR="$(dirname "$0")/../admin-ui"
WEB_ROOT="/var/www/orchestra-admin"
BACKEND_PORT=8001

# --- 1. Write .env for Admin UI ---
echo "VITE_API_URL=$API_URL" > "$ADMIN_UI_DIR/.env"
echo "VITE_API_KEY=$API_KEY" >> "$ADMIN_UI_DIR/.env"

# --- 2. Build Admin UI ---
cd "$ADMIN_UI_DIR"
pnpm install
pnpm build

# --- 3. Deploy dist/ to web root ---
sudo mkdir -p "$WEB_ROOT"
sudo rsync -a --delete dist/ "$WEB_ROOT/"

# --- 4. Restart backend and nginx ---
sudo systemctl restart orchestra-real || true
sudo systemctl restart orchestra-api || true
sudo systemctl reload nginx

# --- 5. Verify /api/agents returns real data ---
RESPONSE=$(curl -s -H "X-API-Key: $API_KEY" "$API_URL/api/agents")
if echo "$RESPONSE" | grep -q 'sys-001' && echo "$RESPONSE" | grep -q 'analyze-001'; then
  echo "✅ Real agent data detected."
else
  echo "❌ ERROR: Real agent data NOT detected. Response: $RESPONSE"
  exit 1
fi

echo "✅ Deployment complete. Admin UI and backend are now in sync."
