FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev \
        build-essential \
        ca-certificates \
        curl \
        && \
    rm -rf /var/lib/apt/lists/* && \
    curl -sSL https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh > /wait-for-it.sh && \
    chmod +x /wait-for-it.sh

WORKDIR /app

# Copy requirements and install
ARG REQUIREMENTS=requirements/prod.txt
COPY requirements/ /app/requirements/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/${REQUIREMENTS}

# Copy application code
COPY . /app/

# Make startup script executable
RUN chmod +x /app/scripts/container-startup.sh

# Expose port
EXPOSE 8000

# Run startup script
ENTRYPOINT ["/app/scripts/container-startup.sh"]
