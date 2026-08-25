# tCF Developer Guide

## Prerequisites

Install:

- [Git](https://git-scm.com/book/en/Getting-Started-Installing-Git)
- [Docker Desktop](https://docs.docker.com/get-docker/) with Docker Compose v2
- [VS Code](https://code.visualstudio.com/) with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
- [uv](https://docs.astral.sh/uv/) for host-side Python checks
- Node.js and npm for JavaScript checks

You also need access to the [tCF Google Drive](https://drive.google.com/drive/u/0/folders/1a7OkHkepOBWKiDou8nEhpAG41IzLi7mh) if you need a database dump.

## Initial setup

Clone the repository and create the local environment file:

```bash
git clone https://github.com/thecourseforum/theCourseForum2.git
cd theCourseForum2
cp .env.example .env
```

PostgreSQL reads the values in `.env` when its data directory is initialized.
`.env` is local-only and is excluded from Docker build contexts. Never put
production credentials in it.

## Compose architecture

The Compose project is named `tcf`.

Services without a profile provide the shared local infrastructure:

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
| `release` | Migrations, static collection, Cachalot invalidation, and session cleanup |
| `web` | Bundled Django application served by Gunicorn on `localhost:8000` |

The `dev` profile adds the VS Code development container:

| Service | Purpose |
| --- | --- |
| `devcontainer` | Development tools, Node.js, uv, and Docker-outside-of-Docker access |

The Compose profile controls which containers run; it does not select Django
settings. Local containers use `TCF_ENV=local` by default. ECS production tasks
set `TCF_ENV=prod` and use AWS RDS, ElastiCache, and S3.

## Choose a local workflow

### VS Code devcontainer (recommended for development)

Open the repository in VS Code and run **Dev Containers: Reopen in Container**.
The devcontainer uses the `dev` profile, bind-mounts the repository at `/app`,
installs the development dependencies, and forwards port 8000.

Inside the devcontainer terminal:

```bash
# Start the CDN if it is not already running
docker compose up -d cdn

# Apply migrations and collect static files
docker compose --profile full run --rm release

# Start Django with automatic reload
uv run python manage.py runserver 0.0.0.0:8000
```

The devcontainer controls sibling Compose services through the mounted Docker
socket. Do not run a full `docker compose down` from inside the devcontainer;
run destructive lifecycle commands from a host terminal instead.

### Bundled production-shaped web service

To run the complete local stack with Gunicorn:

```bash
docker compose --profile full up --build
```

The `release` task waits for PostgreSQL, Valkey, and MinIO bucket initialization,
then `web` starts only after `release` succeeds.

The plain command below starts infrastructure/CDN only and does not start
Django:

```bash
docker compose up
```

Once the full stack is running:

- Website: <http://localhost:8000>
- Static CDN: <http://localhost:8081>
- MinIO console: <http://localhost:9001>

Do not run the devcontainer server and bundled `web` service on port 8000 at
the same time.

## Database dumps

Download the latest custom-format backup manually from the [database backup
folder](https://drive.google.com/drive/u/0/folders/1a7OkHkepOBWKiDou8nEhpAG41IzLi7mh) and save
it as `db/latest.dump`.

From a host terminal, reset the local database and restore the dump with:

```bash
./scripts/reset-db.sh
```

The script stops Compose services without deleting named volumes, clears the
public schema, and restores the dump through `docker compose exec`. Start the
chosen local workflow again afterward.

Create a custom-format local backup with:

```bash
./scripts/local_dump.sh [filename.dump]
```

To remove all local database and object-storage data:

```bash
docker compose --profile full down -v
```

## Run Django management commands

In the running bundled web service:

```bash
docker compose --profile full exec web python manage.py shell
docker compose --profile full exec web python manage.py fetch_clubs
docker compose --profile full exec web python manage.py load_grades ALL_DANGEROUS
```

In the devcontainer:

```bash
uv run python manage.py shell
uv run python manage.py fetch_clubs
uv run python manage.py load_grades ALL_DANGEROUS
```

For a one-off bundled-container command:

```bash
docker compose --profile full run --rm web python manage.py <command>
```

## Environment modes

`TCF_ENV` selects the Django runtime mode:

- `local`: local development settings and debug tools; uses Postgres, Valkey, and MinIO
- `ci`: debug disabled; uses the same Compose-backed services in GitHub Actions
- `prod`: production settings; uses AWS RDS, ElastiCache, and S3; ECS must set this explicitly

The Compose `full` profile does not automatically set `TCF_ENV=prod`.

## Local quality checks

Run the same host-side checks used by CI:

```bash
uv sync --frozen --group dev --no-install-project
uv run ruff check .
uv run ruff format --check .
uv run djlint tcf_website/templates --check --lint
uv run ty check
npm ci
npx eslint -c .config/.eslintrc.yml tcf_website/static/
```

Run the Compose-backed Django tests with:

```bash
docker compose --profile full run --rm --build web python manage.py test
```

GitHub Actions runs these tests with coverage against the same PostgreSQL,
Valkey, and MinIO services.

## Useful documentation

- [Useful commands](useful-commands.md)
- [Semester data](semester-data.md)
- [Grade data](grade-data.md)

## Authentication

Login, logout, and profile functionality requires additional Cognito
credentials. Consult the project maintainers if you need access.
