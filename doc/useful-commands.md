# Useful Commands

All local application commands run through the production-shaped Compose
profile. Start the stack first:

```bash
docker compose --profile full up --build
```

Use `exec` for commands in the running web container:

```bash
docker compose --profile full exec web python manage.py shell
docker compose --profile full exec web python manage.py fetch_clubs
docker compose --profile full exec web python manage.py load_clubs
docker compose --profile full exec web python manage.py load_grades ALL_DANGEROUS
```

Use `run --rm` for a one-off command when the web container does not need to
remain running:

```bash
docker compose --profile full run --rm web python manage.py <command>
```

## Review Drive

Enable the review drive banner by reverting [this commit](https://github.com/thecourseforum/theCourseForum2/commit/c16383ff2b987dbfde127da97f5a280cb6e0a210) to include the HTML banner template.

## Picking Review Drive Winners

Use the Django shell:

```bash
docker compose --profile full exec web python manage.py shell
```

Then select relevant reviews:

```python
from tcf_website.models import Review

# For example, the review drive tag for the Fall 2023 semester is `tCFF23`.
reviews = list(Review.objects.filter(text__icontains="<review drive tag>"))
total_winners = 3
winners = reviews.order_by("?")[:total_winners]
```

Consult marketing for the correct semester tag and number of winners. Send the
selected winners to the marketing team.

## Inspecting production

Production commands run in ECS rather than the local Compose `web` container.
Use `scripts/ecs-run-command.sh` for one-off commands after authenticating with
AWS CLI:

```bash
./scripts/ecs-run-command.sh python manage.py <command>
```

The moderation helper supports the production ECS task by default. To run it
against the local Compose stack instead:

```bash
USE_DOCKER=1 ./scripts/hide_review.sh
```

## Database dumps

Create a custom-format dump of the local Compose database:

```bash
./scripts/local_dump.sh [filename.dump]
```

Create a dump of the production database through the configured EC2 jump host:

```bash
./scripts/prod_dump.sh [filename.dump]
```

The production script reads `EC2_HOST`, `EC2_USER`, `PEM_KEY`, `PROD_DB_HOST`,
`PROD_DB_USER`, and `PROD_DB_PASSWORD` from `.env`. Handle production database
credentials carefully and never commit them.

## Updating grades

See [grade-data.md](grade-data.md).

## Fetching and loading semester data

See [semester-data.md](semester-data.md).

## Fetching and loading club data

See the `fetch_clubs` and `load_clubs` commands above. Fetched data is saved in
`tcf_website/management/commands/club_data/csv`.

## CI and deployment helpers

These scripts are used by automation and generally do not need to be run
manually:

- `notify-checks-result.sh` posts CI results.
- `notify-deployment-result.sh` posts deployment results.
- `container-startup.sh` is the ECS/Gunicorn entrypoint.
