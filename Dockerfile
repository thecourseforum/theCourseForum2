FROM python:3.9.2
COPY . /app/
WORKDIR /app
ENV PYTHONUNBUFFERED=1
RUN apt-get update && \
	curl -sL https://deb.nodesource.com/setup_12.x | bash - && \
	apt-get install -y --no-install-recommends \
		libpq-dev \
		build-essential \
		unattended-upgrades \
		nodejs && \
	npm install && \
	pip3 install -r requirements.txt --disable-pip-version-check && \
	rm -rf /var/lib/apt/lists/*
