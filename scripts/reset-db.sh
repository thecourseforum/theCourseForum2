#!/bin/sh

DB_FILE="${DB_FILE:-db/latest.sql}"

if [ ! -f "$DB_FILE" ]; then 
  echo 'Database file db/latest.sql not found.'
  echo 'Ensure the latest db file is downloaded and located in "db/latest.sql".'
  echo 'The latest backup can be found in the Google Drive at "tCF/Engineering/DB/latest.sql".'
  exit 1
fi

docker exec -i tcf_db psql tcf_db -U tcf_django -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker exec -i tcf_db bash -c "psql tcf_db -U tcf_django < $DB_FILE"
