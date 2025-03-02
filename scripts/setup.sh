#!/bin/sh

if [ -z "$1" ]; then
  echo "Must specify location to clone and set up theCourseForum2 respository."
  exit
fi

cd "$1" || exit

exists() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Error: '$1' is not installed. Please install '$1'." >&2
    exit
  }
}

exists git

exists docker

exists gdown # check for gdown

git clone git@github.com:thecourseforum/theCourseForum2.git
if [ "$?" -ne 0 ]; then
  echo "Unable to clone thecourseforum/theCourseForum2 with SSH. Ensure you have an ssh key set up on your GitHub account."
  echo "See https://docs.github.com/en/authentication/connecting-to-github-with-ssh for more info."
  exit 1
fi

cd theCourseForum2 || exit

git switch dev

echo ""
echo "============================================"
echo "Please ensure that the '.env' file exists in the repository directory: $(eval echo "$1")"
echo "Once you have created the '.env' file, press Enter to continue."
echo "If the '.env' file does not exist, the script will exit."
echo "============================================"

printf "Press Enter to continue after verifying the '.env' file..."
read -r _ </dev/tty

[ ! -f ".env" ] && echo "Error: '.env' file does not exist in '$1'. Follow the installation instructions in doc/dev.md after creating a '.env' file." && exit 1

GDRIVE_FILE_ID="1TsSvhvWGA24537xNo_9CkULKzjugNrZH"
SQL_FILE_PATH="db/latest.sql"

echo "Downloading $SQL_FILE_PATH from Google Drive..."

# use gdown to download latest.sql
gdown "$GDRIVE_FILE_ID" --output "$SQL_FILE_PATH"
if [ "$?" -ne 0 ]; then
  echo "Failed to download $SQL_FILE_PATH from Google Drive."
  echo "Make sure the file is publicly accessible or you have proper permissions."
  exit 1
fi

docker compose build --no-cache
docker compose up &
(
  sleep 3 # 1 to 3 to ensure containers are up
  docker exec -i tcf_db psql tcf_db -U tcf_django -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
  docker exec -i tcf_db psql tcf_db -U tcf_django -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
  echo "Importing data from $SQL_FILE_PATH..."
  docker exec -i tcf_db psql tcf_db -U tcf_django < "$SQL_FILE_PATH"
) &
