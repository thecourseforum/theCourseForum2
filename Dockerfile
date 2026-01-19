FROM python:3.12-slim-bookworm

ARG INSTALL_DEV=false

ENV PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev build-essential && \
    if [ "$INSTALL_DEV" = "true" ]; then \
        apt-get install -y --no-install-recommends nodejs npm; \
    fi && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN if [ "$INSTALL_DEV" = "true" ]; then \
        uv sync --frozen --no-install-project --group dev; \
    else \
        uv sync --frozen --no-install-project --no-dev; \
    fi

COPY . /app/

RUN chmod +x /app/scripts/container-startup.sh

ENTRYPOINT ["/app/scripts/container-startup.sh"]
