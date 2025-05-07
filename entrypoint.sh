#!/bin/bash
# entrypoint.sh
# Entrypoint script for the AI Orchestra API Docker container

set -e

# Function to wait for a service to be available
wait_for_service() {
  local host=$1
  local port=$2
  local service=$3
  local timeout=${4:-30}
  local elapsed=0

  echo "Waiting for $service at $host:$port..."
  while ! nc -z "$host" "$port" > /dev/null 2>&1; do
    sleep 1
    elapsed=$((elapsed + 1))
    if [ "$elapsed" -ge "$timeout" ]; then
      echo "Timeout waiting for $service at $host:$port"
      exit 1
    fi
  done
  echo "$service is available at $host:$port"
}

# Check if we need to wait for any services
if [ -n "$WAIT_FOR_HOST" ] && [ -n "$WAIT_FOR_PORT" ]; then
  wait_for_service "$WAIT_FOR_HOST" "$WAIT_FOR_PORT" "service" "$WAIT_FOR_TIMEOUT"
fi

# Apply database migrations if needed
if [ "$APPLY_MIGRATIONS" = "true" ]; then
  echo "Applying database migrations..."
  # Add migration command here if needed
  # Example: alembic upgrade head
fi

# Run the command
echo "Running command: $*"
exec "$@"