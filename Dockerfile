# Start with a base image
FROM python:3.10

# Install required dependencies
RUN apt-get update \
    && apt-get install -y wget unzip gnupg curl \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN wget -q "https://chromedriver.storage.googleapis.com/$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE)/chromedriver_linux64.zip" \
    -O /tmp/chromedriver.zip \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip

# Copy application code
COPY . /app
WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install cron
RUN apt-get update && apt-get install -y cron

# Copy the cron file into the container
COPY my_crontab /etc/cron.d/my_crontab
#COPY my_crontab_2 /etc/crontab

# Set permissions and apply the cron job
#RUN chmod 0644 /etc/crontab
RUN chmod 0644 /etc/cron.d/my_crontab \
    && crontab /etc/cron.d/my_crontab

# Command to start cron in the foreground to keep the container running
CMD ["cron", "-f"]
