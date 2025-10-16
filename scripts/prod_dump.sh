#!/bin/bash
# This script dumps a remote database by connecting through an EC2 instance.
source .env

filename="$1"
filename="${filename:-prod.dump}"

if [ ! -d "$(dirname "db/$filename")" ]; then
  echo "Database destination 'db/$filename' invalid."
  echo "Ensure the directory db exists, and provide just the filename."
  exit 1
fi

# Ensure EC2 instance is active!

set -e

echo "--- Connecting to EC2 instance '$EC2_HOST' to dump database from '$PROD_DB_HOST' with key at '$PEM_KEY'..."

chmod 400 $PEM_KEY

ssh -i "$PEM_KEY" "$EC2_USER@$EC2_HOST" "PGPASSWORD='$PROD_DB_PASSWORD' pg_dump --host='$PROD_DB_HOST' --username=$PROD_DB_USER --format=custom --clean $PROD_DB_USER" > "db/$filename"

echo "--- ✅ Successfully created remote database dump at: db/$filename"