# Useful Commands

Choose one local application workflow first:

- Devcontainer: run commands directly with `uv run`.
- Bundled web service: use `docker compose --profile full exec web`.

Start the bundled service with:

```bash
docker compose --profile full up --build
```

## Local Django commands

With the bundled `web` service running:

```bash
docker compose --profile full exec web python manage.py shell
docker compose --profile full exec web python manage.py fetch_clubs
docker compose --profile full exec web python manage.py load_clubs
docker compose --profile full exec web python manage.py load_grades ALL_DANGEROUS
```

From the devcontainer:

```bash
uv run python manage.py shell
uv run python manage.py fetch_clubs
uv run python manage.py load_clubs
uv run python manage.py load_grades ALL_DANGEROUS
```

For a one-off bundled-container command:

```bash
docker compose --profile full run --rm web python manage.py <command>
```

## Review Drive

Enable the review drive banner by reverting [this commit](https://github.com/thecourseforum/theCourseForum2/commit/c16383ff2b987dbfde127da97f5a280cb6e0a210) to include the HTML banner template.

## Picking Review Drive Winners

Use the Django shell and select relevant reviews:

```python
from tcf_website.models import Review

# For example, the review drive tag for the Fall 2023 semester is `tCFF23`.
reviews = list(Review.objects.filter(text__icontains="<review drive tag>"))
total_winners = 3
winners = reviews.order_by("?")[:total_winners]
```

Consult marketing for the correct semester tag and number of winners. Send the
selected winners to the marketing team.

## Production operations

Production commands run in ECS rather than the local Compose containers. Use
`scripts/ecs-run-command.sh` for one-off commands after authenticating with AWS
CLI:

```bash
./scripts/ecs-run-command.sh python manage.py <command>
```

The moderation helper uses the production ECS task by default. To use it with
the local bundled web service instead:

```bash
USE_DOCKER=1 ./scripts/hide_review.sh
```

## Database dumps

Create a custom-format dump of the local Compose database:

```bash
./scripts/local_dump.sh [filename.dump]
```

Restore `db/latest.dump` or another custom-format dump into the local database:

```bash
./scripts/reset-db.sh [filename.dump]
```

Create a production dump through the configured EC2 jump host:

```bash
./scripts/prod_dump.sh [filename.dump]
```

The production script reads `EC2_HOST`, `EC2_USER`, `PEM_KEY`, `PROD_DB_HOST`,
`PROD_DB_USER`, and `PROD_DB_PASSWORD` from `.env`. Never commit production
credentials.

## Data workflows

- [Semester data](semester-data.md)
- [Grade data](grade-data.md)

Fetched club data is saved in
`tcf_website/management/commands/club_data/csv`.

## Automation scripts

These scripts are used by CI/deployment automation and generally are not run
manually:

- `container-startup.sh` — ECS/Gunicorn entrypoint
- `notify-checks-result.sh` — CI result notification
- `notify-deployment-result.sh` — deployment result notification
