#!/bin/bash
# This script creates a compressed dump of the local Docker database.

filename="$1"
filename="${filename:-local.dump}"

if [ ! -d "$(dirname "db/$filename")" ]; then
  echo "Database destination 'db/$filename' invalid."
  echo "Ensure the directory db exists, and provide just the filename."
  exit 1
fi

set -e

echo "--- Creating a dump of the '$DB_NAME' database from container 'tcf_db'..."


docker exec tcf_db pg_dump -U "$DB_USER" -d "$DB_NAME" --format=custom --clean > "db/$filename"

echo "--- ✅ Successfully created database dump at: db/$filename"