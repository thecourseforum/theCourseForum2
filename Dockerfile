FROM python:3.6.5
COPY . /app/
WORKDIR /app
RUN apt-get update && \
	curl -sL https://deb.nodesource.com/setup_12.x | bash - && \
	apt-get install -y --no-install-recommends \
		libpq-dev \
		build-essential \
		unattended-upgrades \
		nodejs && \
	npm install eslint \
		eslint-config-standard \
		eslint-plugin-import \
		eslint-plugin-node \
		eslint-plugin-promise \
		eslint-plugin-standard && \
	pip3 install -r requirements.txt --disable-pip-version-check && \
	rm -rf /var/lib/apt/lists/*
