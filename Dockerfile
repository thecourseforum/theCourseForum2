# =================
#  1. Builder Stage
# =================
# Use the slim image as a base for our builder
FROM python:3.11-slim AS builder

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV NODE_MAJOR=20
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install ONLY the build-time dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        # For building python packages
        build-essential libpq-dev

COPY requirements.txt ./
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --disable-pip-version-check --no-cache-dir -r requirements.txt
    

# =================
#  2. Final Stage
# =================
# Use the slim image as a base for our runtime
FROM python:3.11-slim as runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV NODE_MAJOR=20
ENV PATH="/opt/venv/bin:$PATH"
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install ONLY the runtime dependencies
# Note: libpq5 is the runtime library, libpq-dev was the build-time one.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        # libpq5 nodejs ca-certificates curl gnupg && \
        curl && \
    # Clean up
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy wait-for-it script
RUN curl -sSL https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh > /wait-for-it.sh && \
    chmod +x /wait-for-it.sh

# Copy the installed dependencies from the builder stage
COPY --from=builder /opt/venv /opt/venv
# Node modules are irrelevant in production for this app except for format.sh which is an artifact

# Copy application code
COPY . /app/
RUN chmod +x /app/scripts/container-startup.sh
