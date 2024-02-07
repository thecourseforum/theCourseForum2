#!/bin/sh

filename="$1"
filename="${filename:-db/prod.sql}"

if [ ! -d "$(dirname "$filename")" ]; then
  echo "Database destination '$filename' invalid."
  echo "Ensure the directory $(dirname "$filename") exists."
  exit 1
fi

PGPASSWORD="$DB_PASSWORD" pg_dump -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" >"$filename"
