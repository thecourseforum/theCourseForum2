FROM python:3.12

ENV PYTHONUNBUFFERED=1

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev build-essential ca-certificates \
        curl gnupg unattended-upgrades && \
    rm -rf /var/lib/apt/lists/* && \
    curl -sSL https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh > /wait-for-it.sh && \
    chmod +x /wait-for-it.sh

WORKDIR /app

COPY requirements.txt /app

RUN pip3 install -r requirements.txt --disable-pip-version-check --no-cache-dir

COPY . /app/

RUN chmod +x /app/scripts/container-startup.sh

# Container-level health check for ECS/Docker
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
  CMD curl -fsS http://localhost:80/healthz || exit 1
