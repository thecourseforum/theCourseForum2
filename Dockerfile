FROM python:3.9.2

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
RUN npm install
RUN pip3 install -r requirements.txt --disable-pip-version-check --no-cache-dir
RUN python3 manage.py migrate && \
    python3 manage.py collectstatic --noinput && \
    python3 manage.py invalidate_cachalot tcf_website
