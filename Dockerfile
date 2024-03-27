FROM python:3.11.0

ENV PYTHONUNBUFFERED=1
ENV NODE_MAJOR=20

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

COPY . /app/
WORKDIR /app

RUN apt-get update && \
	apt-get install -y --no-install-recommends \
		libpq-dev build-essential ca-certificates \
		curl gnupg unattended-upgrades && \
	mkdir -p /etc/apt/keyrings && \
	curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
	echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
	apt-get update && \
	apt-get install -y --no-install-recommends nodejs && \
	rm -rf /var/lib/apt/lists/*
RUN curl -sSL https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh > /wait-for-it.sh && chmod +x /wait-for-it.sh
RUN npm install --no-fund --no-audit
RUN pip3 install -r requirements.txt --disable-pip-version-check --no-cache-dir
