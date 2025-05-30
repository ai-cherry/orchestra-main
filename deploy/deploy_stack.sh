#!/bin/bash
set -e

cd "$(dirname "$0")"

docker compose -f docker-compose.vultr.yml pull
DOCKER_BUILDKIT=1 docker compose -f docker-compose.vultr.yml up -d
