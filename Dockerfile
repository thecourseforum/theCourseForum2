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

FROM base AS dev

ENV UV_PYTHON_DOWNLOADS=never

# Node 20 from the official image (Debian ships an older major).
COPY --from=node:20-bookworm-slim /usr/local/bin/node /usr/local/bin/node
COPY --from=node:20-bookworm-slim /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm && \
    ln -s ../lib/node_modules/corepack/dist/corepack.js /usr/local/bin/corepack 2>/dev/null; \
    ln -sf ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/* && \
    uv sync --frozen --no-install-project --group dev

# Docker CLI (no daemon here; talks to the host daemon over the mounted socket).
COPY --from=docker:cli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=docker:cli /usr/local/libexec/docker/cli-plugins /usr/local/libexec/docker/cli-plugins

COPY .devcontainer/bashrc /root/tcf-dev-bashrc
RUN grep -q 'tcf-dev-bashrc' /root/.bashrc || echo '. /root/tcf-dev-bashrc' >> /root/.bashrc

# Source code comes from the devcontainer.json bind mount, not baked in.

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
