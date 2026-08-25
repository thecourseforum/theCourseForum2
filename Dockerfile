# syntax=docker/dockerfile:1

FROM python:3.12-slim-bookworm AS base

ENV PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_CACHE_DIR=/root/.cache/uv \
    PATH="/opt/venv/bin:$PATH"

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Shipped to ECS by the deploy workflow.
FROM base AS prod

RUN addgroup --system app && \
    adduser --system --ingroup app --home /home/app app && \
    mkdir -p /home/app/.cache/uv && \
    chown -R app:app /opt/venv /home/app

COPY --chown=app:app . /app/
RUN chown -R app:app /app && \
    chmod +x /app/scripts/container-startup.sh

ENV HOME=/home/app \
    UV_CACHE_DIR=/home/app/.cache/uv
USER app

EXPOSE 80

CMD ["/app/scripts/container-startup.sh"]
