@echo off

docker exec tcf_django black --line-length 80 .
docker exec tcf_django isort --profile black --line-length 80 .
docker exec tcf_django npx prettier --write "**/*.{css,js,md}"
docker exec tcf_django npx eslint --fix -c .config/.eslintrc.yml tcf_website/static/
