FROM python:3.11.0

ENV PYTHONUNBUFFERED=1
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

COPY . /app/
WORKDIR /app

RUN apt-get update && \
	curl -sL https://deb.nodesource.com/setup_12.x | bash - && \
	apt-get install -y --no-install-recommends \
		libpq-dev \
		build-essential \
		unattended-upgrades \
		nodejs && \
	rm -rf /var/lib/apt/lists/*
RUN curl -sSL https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh > /wait-for-it.sh && chmod +x /wait-for-it.sh
RUN npm install --no-fund --no-audit
RUN pip3 install -r requirements.txt --disable-pip-version-check --no-cache-dir
