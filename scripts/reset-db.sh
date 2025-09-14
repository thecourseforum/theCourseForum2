#!/bin/bash
#
# This script resets the local database by destroying the container and volume,
# starting a new one, and restoring it from a dump file.
source .env

DB_FILE="${1:-latest.dump}"

if [ ! -f "db/$DB_FILE" ]; then 
  echo "Database file '$DB_FILE' not found."
  echo "Ensure the latest dump file is downloaded and located in db/, and provide just the filename."
  echo 'The latest backup can be found in the Google Drive at "tCF/Engineering/DB/RDS/latest.dump".'
  exit 1
fi

set -e

echo "--- Tearing down existing containers and volumes..."
docker-compose down -v

echo "--- Starting new PostgreSQL container..."
docker-compose up -d db

echo "--- Waiting for database to be ready..."
until docker exec tcf_db pg_isready -U "$DB_USER" -d "$DB_NAME" -q; do
  echo "Database is unavailable - sleeping"
  sleep 1
done

echo "--- Database is ready! Restoring from dump file..."
docker exec -i tcf_db pg_restore -U "$DB_USER" -d "$DB_NAME" --no-owner "/app/$DB_FILE"

echo "--- Database restore complete!"