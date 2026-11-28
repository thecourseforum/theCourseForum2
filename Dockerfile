# syntax=docker/dockerfile:1@sha256:572cebbc2b15e6f84c077742952674889cb63cd5e9b80abdffcbe587b6f19183

FROM python:3.12-slim-bookworm@sha256:44cf1793efa7c7a476bb0f2cff81443f4a072c90c1cb127e2924933daa3e8c64 AS base

ENV PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_CACHE_DIR=/root/.cache/uv \
    PATH="/opt/venv/bin:$PATH"

COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

FROM base AS dev

ENV UV_PYTHON_DOWNLOADS=never

# Node 24 from the official image (Debian ships an older major).
COPY --from=node:24.22.3-bookworm-slim@sha256:873f586f3794f52281bd039bf02c048a0be08fde619338f9941bad1eb6b34530 /usr/local/bin/node /usr/local/bin/node
COPY --from=node:24.22.3-bookworm-slim@sha256:873f586f3794f52281bd039bf02c048a0be08fde619338f9941bad1eb6b34530 /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm && \
    ln -s ../lib/node_modules/corepack/dist/corepack.js /usr/local/bin/corepack 2>/dev/null; \
    ln -sf ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/* && \
    uv sync --frozen --no-install-project --group dev

# Docker CLI (no daemon here; talks to the host daemon over the mounted socket).
COPY --from=docker:cli@sha256:4e60c31615e83523afbb59773b25d055c0da9edcd5f80a4c6a6eebad49de1a25 /usr/local/bin/docker /usr/local/bin/docker
COPY --from=docker:cli@sha256:4e60c31615e83523afbb59773b25d055c0da9edcd5f80a4c6a6eebad49de1a25 /usr/local/libexec/docker/cli-plugins /usr/local/libexec/docker/cli-plugins

COPY --from=amazon/aws-cli:2.42.3@sha256:271de464e935f765aa2afb6ec69881e9f4a9afd3e978214a2b5f5ddcbbc161b5 /usr/local/aws-cli /usr/local/aws-cli
RUN ln -s /usr/local/aws-cli/v2/current/bin/aws /usr/local/bin/aws && \
    ln -s /usr/local/aws-cli/v2/current/bin/aws_completer /usr/local/bin/aws_completer

COPY .devcontainer/bashrc /root/tcf-dev-bashrc
RUN grep -q 'tcf-dev-bashrc' /root/.bashrc || echo '. /root/tcf-dev-bashrc' >> /root/.bashrc

# Source code comes from the devcontainer.json bind mount, not baked in.

FROM base AS static-build

COPY manage.py ./
COPY tcf_core ./tcf_core
COPY tcf_website ./tcf_website
RUN DJANGO_SETTINGS_MODULE=tcf_core.settings.dev TCF_ENV=ci STATIC_MANIFEST=true \
    SECRET_KEY=collectstatic DB_NAME=x DB_USER=x DB_PASSWORD=x DB_HOST=x DB_PORT=5432 \
    python manage.py collectstatic --noinput

FROM scratch AS static-files

COPY --from=static-build /app/staticfiles/ /

FROM caddy:2-alpine@sha256:003a97808e781aa9f7e75cc2f43d34d461099031faf5e20faefb9f61126836f0 AS cdn

COPY Caddyfile /etc/caddy/Caddyfile
COPY --from=static-build /app/staticfiles/ /srv/

# Shipped to ECS by the deploy workflow.
FROM base AS prod

RUN addgroup --system app && \
    adduser --system --ingroup app --home /home/app app && \
    mkdir -p /home/app/.cache/uv && \
    chown -R app:app /opt/venv /home/app && \
    chown app:app /app

COPY --chown=app:app --exclude=tcf_website/static . /app/
COPY --chown=app:app --from=static-build /app/staticfiles/staticfiles.json /app/staticfiles/

ENV HOME=/home/app \
    UV_CACHE_DIR=/home/app/.cache/uv
USER app

EXPOSE 8000

CMD ["/app/scripts/container-startup.sh"]
