#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/inventory-api}"
BRANCH="${BRANCH:-main}"
COMPOSE_FILE="docker-compose.production.yml"
ENV_FILE=".env.production"

cd "${APP_DIR}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ${APP_DIR}/${ENV_FILE}." >&2
  echo "Copy .env.production.example and replace the example password." >&2
  exit 1
fi

git fetch origin "${BRANCH}"
git checkout "${BRANCH}"
git pull --ff-only origin "${BRANCH}"

docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" config --quiet
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up --build -d
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" ps

echo
echo "Deployment complete."
echo "Load demo data once with:"
echo "docker compose --env-file ${ENV_FILE} -f ${COMPOSE_FILE} exec api uv run python -m scripts.seed_demo_data"
