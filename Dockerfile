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
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
	echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list && \
	apt-get update && apt-get -y install google-chrome-stable && \
	curl https://chromedriver.storage.googleapis.com/2.31/chromedriver_linux64.zip -o /usr/local/bin/chromedriver && \
	chmod +x /usr/local/bin/chromedriver
