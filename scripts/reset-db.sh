#!/bin/bash

# Make sure to set the DB_FILE environment variable to the name of your SQL dump
DB_FILE="${DB_FILE:-db/latest.sql}"

if [ ! -f "$DB_FILE" ]; then 
  echo "Database file '$DB_FILE' not found."
  echo "Ensure the latest db file is downloaded and located in '$DB_FILE'."
  echo 'The latest backup can be found in the Google Drive at "tCF/Engineering/DB/latest.sql".'
  exit 1
fi

docker exec -i tcf_db psql tcf_db -U tcf_django -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker exec -i tcf_db psql tcf_db -U tcf_django < "$DB_FILE"
