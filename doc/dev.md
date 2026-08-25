# tCF Developer Guide

## Prerequisites

Install:

- [Git](https://git-scm.com/book/en/Getting-Started-Installing-Git)
- [Docker Desktop](https://docs.docker.com/get-docker/) with Docker Compose v2
- [uv](https://docs.astral.sh/uv/) for host-side Python checks
- Node.js and npm for the JavaScript checks

## Initial setup

Clone the repository and create the local environment file:

```bash
git clone https://github.com/thecourseforum/theCourseForum2.git
cd theCourseForum2
cp .env.example .env
```

`.env` is local-only and is intentionally ignored by Docker builds. Do not put
production credentials in it.

## Compose architecture

The Compose project is named `tcf`. Services without a profile are always
available:

| Service | Purpose | Local address |
| --- | --- | --- |
| `db` | PostgreSQL 18.1 | internal only |
| `valkey` | Cache, sessions, and Cachalot | internal only |
| `minio` | S3-compatible media/static storage | API `localhost:9000`, console `localhost:9001` |
| `minio-init` | Creates the MinIO buckets, then exits | none |
| `cdn` | Serves the MinIO static bucket through Caddy | `http://localhost:8081` |

The `full` profile adds the production-shaped application services:

| Service | Purpose |
| --- | --- |
| `release` | Runs migrations, collects static files, invalidates Cachalot, and clears sessions |
| `web` | Runs Django with Gunicorn |

The profile name describes the deployment shape, not the Django settings
module. Local Compose uses `TCF_ENV=local` by default, so debug tools remain
enabled. Production ECS tasks set `TCF_ENV=prod` and use AWS services instead
of the local Postgres, Valkey, and MinIO services.

## Start the local site

The plain command starts only the infrastructure and CDN:

```bash
docker compose up
```

To start Django as well, activate the production-shaped profile:

```bash
docker compose --profile full up --build
```

The `release` task runs first. The `web` service starts only after `release`
finishes successfully.

Once the stack is running:

- Website: <http://localhost:8000>
- Static CDN: <http://localhost:8081>
- MinIO console: <http://localhost:9001>

Stop the stack while preserving database and object-storage volumes:

```bash
docker compose --profile full down
```

To remove all local data as well:

```bash
docker compose --profile full down -v
```

## Restore the local database

Download the latest database backup manually from the [database backup
folder](https://drive.google.com/drive/u/0/folders/1a7OkHkepOBWKiDou8nEhpAG41IzLi7mh)
and save it as `db/latest.dump`.

Reset the local database and restore the dump with:

```bash
./scripts/reset-db.sh
```

The script stops the Compose services, clears the public database schema,
restores the custom-format dump through `docker compose exec`, and preserves
the named volumes for other services. Start the application again afterward:

```bash
docker compose --profile full up --build
```

To create a custom-format backup of the local database:

```bash
./scripts/local_dump.sh [filename.dump]
```

## Run Django management commands

With the `web` service running, use `exec`:

```bash
docker compose --profile full exec web python manage.py shell
docker compose --profile full exec web python manage.py fetch_clubs
docker compose --profile full exec web python manage.py load_grades ALL_DANGEROUS
```

For a one-off command, use `run`:

```bash
docker compose --profile full run --rm web python manage.py <command>
```

Enter the application container with:

```bash
docker compose --profile full exec web bash
```

## Environment modes

`TCF_ENV` selects the Django runtime mode:

- `local` (default for local Compose): debug tools enabled; uses local Postgres, Valkey, and MinIO
- `ci`: debug disabled; uses the same Compose-backed services in GitHub Actions
- `prod`: production settings; uses AWS RDS, ElastiCache, and S3; ECS tasks must set this explicitly

The Compose `full` profile does not automatically set `TCF_ENV=prod`.

## Local quality checks

Install the locked development dependencies and run the same checks used by CI:

```bash
uv sync --frozen --group dev --no-install-project
uv run ruff check .
uv run ruff format --check .
uv run djlint tcf_website/templates --check --lint
uv run ty check
npm ci
npx eslint -c .config/.eslintrc.yml tcf_website/static/
```

The Compose-backed Django test command is:

```bash
docker compose --profile full run --rm --build web python manage.py test
```

GitHub Actions additionally runs the tests with coverage against the same
Postgres, Valkey, and MinIO services.

## VS Code

When opening the project, VS Code may prompt you to install the recommended
extensions. The list is in `.vscode/extensions.json`.

## Authentication

Login, logout, and profile functionality requires additional Cognito
credentials. Consult the project maintainers if you need access.
