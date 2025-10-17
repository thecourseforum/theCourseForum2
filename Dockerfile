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
        build-essential libpq-dev \
        # For adding nodejs repo
        ca-certificates curl gnupg && \
    # Add Node.js repository
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
    # Install Node.js
    apt-get update && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY package.json /app

RUN npm install --no-fund --no-audit

# Install Python dependencies into a virtual environment
COPY requirements.txt ./
RUN sed -i '...' requirements.txt && \
    python -m venv /opt/venv && \
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
        libpq5 nodejs ca-certificates curl gnupg && \
    # Clean up
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy wait-for-it script
RUN curl -sSL https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh > /wait-for-it.sh && \
    chmod +x /wait-for-it.sh

# Copy the installed dependencies from the builder stage
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app/node_modules ./node_modules

# Copy application code
COPY . /app/
RUN chmod +x /app/scripts/container-startup.sh
