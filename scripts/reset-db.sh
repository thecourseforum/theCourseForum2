#!/usr/bin/env bash
# Reset the local Compose database and restore a custom-format dump.

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [[ ! -f .env ]]; then
  echo "Missing .env. Copy .env.example to .env first." >&2
  exit 1
fi

# shellcheck disable=SC1091
source .env

DB_FILE="${1:-latest.dump}"
DUMP_PATH="db/$DB_FILE"

if [[ ! -f "$DUMP_PATH" ]]; then
  echo "Database file '$DUMP_PATH' not found." >&2
  echo "Download the backup and place it in db/, or provide its filename." >&2
  exit 1
fi

echo "--- Stopping Compose services (keeping named volumes)..."
docker compose --profile full down --remove-orphans

echo "--- Starting PostgreSQL..."
docker compose up -d db

echo "--- Waiting for PostgreSQL..."
until docker compose exec -T db pg_isready -U "$DB_USER" -d "$DB_NAME" -q; do
  sleep 1
done

echo "--- Clearing the public schema..."
docker compose exec -T db psql \
  -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 <<'SQL'
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
SQL

echo "--- Restoring '$DUMP_PATH'..."
docker compose exec -T db pg_restore \
  -U "$DB_USER" -d "$DB_NAME" --no-owner < "$DUMP_PATH"

echo "--- Database restore complete."
