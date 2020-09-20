FROM ubuntu:bionic

# ENV PYTHONUNBUFFERED 1

RUN mkdir /app
WORKDIR /app
COPY . /app/

RUN apt-get update && \
	apt-get install -y --no-install-recommends \
		git \
		python3-pip \
		python3-dev \
		libpq-dev \
		build-essential \
		curl \
		unattended-upgrades && \
	curl -sL https://deb.nodesource.com/setup_12.x | bash - && \
	apt-get install -y --no-install-recommends nodejs && \
	npm install -g eslint eslint-config-standard eslint-plugin-import eslint-plugin-node eslint-plugin-promise eslint-plugin-standard && \
	rm -r /var/lib/apt/lists/*

RUN pip3 install --upgrade setuptools pip
RUN pip3 install -r requirements.txt

WORKDIR /app
