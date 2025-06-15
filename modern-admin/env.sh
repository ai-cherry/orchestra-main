#!/bin/sh
# env.sh - Inject environment variables into React build

# Replace environment variables in built files
find /usr/share/nginx/html -name "*.js" -exec sed -i "s|VITE_API_URL_PLACEHOLDER|${VITE_API_URL:-http://localhost:8000}|g" {} \;
find /usr/share/nginx/html -name "*.js" -exec sed -i "s|VITE_APP_NAME_PLACEHOLDER|${VITE_APP_NAME:-Orchestra AI}|g" {} \;

echo "Environment variables injected successfully"

