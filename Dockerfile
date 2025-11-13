FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Compile bytecode for all uv commands
ENV UV_COMPILE_BYTECODE=1

# Change the working directory to the `app` directory
WORKDIR /app

# Install dependencies
COPY pyproject.toml /app/
COPY uv.lock /app/

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-install-project

# Copy the project into the image
COPY . /app/

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Allow ECS to start the container (prod-only)
RUN chmod +x /app/scripts/container-startup.sh
