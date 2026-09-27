#!/usr/bin/env bash
# Create a custom-format dump of the local Compose database.

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [[ ! -f .env ]]; then
  echo "Missing .env. Copy .env.example to .env first." >&2
  exit 1
fi

# shellcheck disable=SC1091
source .env

filename="${1:-local.dump}"
dump_path="db/$filename"

if [[ ! -d "$(dirname "$dump_path")" ]]; then
  echo "Database destination '$dump_path' invalid." >&2
  echo "Ensure the directory db exists, and provide just the filename." >&2
  exit 1
fi

echo "--- Creating '$dump_path'..."
docker compose exec -T db pg_dump \
  -U "$DB_USER" -d "$DB_NAME" --format=custom --clean > "$dump_path"

echo "--- Database dump written to '$dump_path'."
