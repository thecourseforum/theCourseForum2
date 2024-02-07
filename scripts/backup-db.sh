#!/bin/sh

# run like so: env $(cat .env | grep -v '^#' | xargs) sh scripts/backup-db.sh

if ! command -v gdrive &> /dev/null; then
  echo '"gdrive" is not installed.'
  exit
fi

if ! command -v pg_dump &> /dev/null; then
  echo '"pg_dump" is not installed.'
  exit
fi

if [ -z "$OCEAN_DB_NAME" ]; then
  echo 'Environment variable "OCEAN_DB_NAME" is not set.'
  echo 'Ensure the proper digital ocean environment variables are exposed.'
  exit
elif [ -z "$GDRIVE_FOLDER_ID" ]; then
  echo 'Environment variable "GDRIVE_FOLDER_ID" is not set.'
  exit
fi

conn="postgresql://$OCEAN_DB_USER:$OCEAN_DB_PASSWORD@$OCEAN_DB_HOST:$OCEAN_DB_PORT/$OCEAN_DB_NAME"
dump="digitalocean_dump_$(date '+%m-%Y').sql"

pg_dump "$conn" > "$dump"

gdrive upload --parent "$GDRIVE_FOLDER_ID" "$dump"
