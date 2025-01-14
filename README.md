# SMOU Parking Integration for Home Assistant

This integration allows you to track your SMOU parking expenses in Barcelona through Home Assistant by scraping data from the SMOU website.

## Architecture Overview

This integration consists of two main components:

1. **Home Assistant Custom Component** (HACS Integration)
   - Reads and processes parking data from a JSON file
   - Creates and updates sensors in Home Assistant
   - Tracks expenses, savings, and parking statistics

2. **Data Collection Service** (Docker Container)
   - Runs a Python script using Selenium to scrape SMOU website
   - Handles authentication and data extraction
   - Stores parking data in a JSON file
   - Runs as a scheduled task outside Home Assistant

This two-component approach is necessary because web scraping with Selenium is not easily achievable within Home Assistant, and running it externally provides better reliability and performance.

## Features
- Tracks paid amounts for Zona Blava and Zona Verda parking
- Supports multiple SMOU accounts
- Maintains historical parking data
- Updates automatically via scheduled data collection
- Supports multiple vehicle license plates and different environmental labels (regular, eco, zero emissions)
- Calculates potential savings based on the environmental labels

## Prerequisites
- Home Assistant instance
- Docker environment for running the data collection service
- SMOU account credentials
- Shared storage location accessible by both Home Assistant and Docker

## Installation

### 1. Data Collection Service Setup

1. Clone this repository on a path of your choice
2. Create a `.env` file with your credentials and data (check .env.example)
3. Build and run the Docker container:

    ```
    docker build -t smou-scraper .
    docker run -d \
        --name smou-scraper \
        --restart unless-stopped \
        -v /path/to/data:/app/data \
        --env-file .env \
        smou-scraper
    ```

The file structure should look like this:

    /path/to/data/
    └── automations-running-in-docker/
    ├── smou.py
    └── smou_parking_data.json (will be created automatically)

4. On your Home Assistant docker mount this extra volume and re-deploy:
    
    ```
    volumes:
      # Existing volumes
      - /path/to/data/automations:/automations
    ```
### 3. Home Assistant Integration Setup
1. Install the integration through HACS (add this repository)
2. Configure the integration in Home Assistant:
   - Go to Configuration > Integrations
   - Click the + button and search for "SMOU Parking"
   - Enter the path to the JSON file (must match the mounted volume in Docker). It's recommended to keep the default value.

