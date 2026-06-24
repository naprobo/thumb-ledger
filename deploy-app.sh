#!/usr/bin/env bash
set -Eeuo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
BRANCH="${BRANCH:-}"
BUILD_SERVICES=(backend)
APP_SERVICES=(backend frontend)
export DOCKER_BUILDKIT=1

cd "$(dirname "$0")"

echo "==> Updating source code"
if [[ -n "$BRANCH" ]]; then
  git pull --ff-only origin "$BRANCH"
else
  git pull --ff-only
fi

if [[ ! -f frontend/dist/index.html ]]; then
  echo "ERROR: frontend/dist/index.html not found."
  echo "Build frontend before publishing this branch, then commit frontend/dist."
  exit 1
fi

echo "==> Building app images only: ${BUILD_SERVICES[*]}"
docker compose -f "$COMPOSE_FILE" build "${BUILD_SERVICES[@]}"

echo "==> Recreating app containers only, without dependencies"
docker compose -f "$COMPOSE_FILE" up -d --no-deps "${APP_SERVICES[@]}"

echo "==> Current app container status"
docker compose -f "$COMPOSE_FILE" ps "${APP_SERVICES[@]}"

echo "==> Done. Frontend is served from ./frontend/dist without building on this server."
echo "==> Unchanged services: db, nginx, cloudflared, objstore"
