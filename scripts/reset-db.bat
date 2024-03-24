@echo off

IF "%DB_FILE%"=="" SET DB_FILE=db\latest.sql

if not exist "%DB_FILE%" (
    echo Database file '%DB_FILE%' not found.
    echo Ensure the latest db file is downloaded and located in '%DB_FILE%'.
    echo The latest backup can be found in the Google Drive at "tCF/Engineering/DB/latest.sql".
    exit /b 1
)

docker exec -i tcf_db psql tcf_db -U tcf_django -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker exec -i tcf_db bash -c "psql tcf_db -U tcf_django < %DB_FILE%"
