#!/usr/bin/env bash
set -Eeuo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
BRANCH="${BRANCH:-}"
SERVICES=(backend frontend)
export DOCKER_BUILDKIT=1

cd "$(dirname "$0")"

echo "==> Updating source code"
if [[ -n "$BRANCH" ]]; then
  git pull --ff-only origin "$BRANCH"
else
  git pull --ff-only
fi

echo "==> Building app images only: ${SERVICES[*]}"
docker compose -f "$COMPOSE_FILE" build "${SERVICES[@]}"

echo "==> Recreating app containers only, without dependencies"
docker compose -f "$COMPOSE_FILE" up -d --no-deps "${SERVICES[@]}"

echo "==> Current app container status"
docker compose -f "$COMPOSE_FILE" ps "${SERVICES[@]}"

echo "==> Done. Unchanged services: db, nginx, cloudflared, objstore"
