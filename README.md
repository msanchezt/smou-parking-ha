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
    docker run -d --name smou-scraper --restart unless-stopped -v /path/to/data:/app smou-scraper
    ```
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

### 4. Suggested Lovelace Dashboard

You can use the following YAML configuration to create a dashboard that displays your parking data:

```yaml
type: vertical-stack
cards:
  - type: grid
    columns: 2
    square: false
    cards:
      - type: entities
        title: Blue Zone
        card_mod:
          style: |
            ha-card {
              --ha-card-header-color: #4473FF;
            }
        entities:
          - entity: sensor.blue_zone_paid
            name: Paid
            icon: mdi:cash
          - entity: sensor.blue_zone_regular_tariff
            name: Regular rate
            icon: mdi:cash-multiple
          - entity: sensor.blue_zone_savings
            name: Blue zone savings
            icon: mdi:cash-check
          - entity: sensor.blue_zone_entries
            name: Times parked
            icon: mdi:counter
      - type: entities
        title: Green Zone
        card_mod:
          style: |
            ha-card {
              --ha-card-header-color: #45A72D;
            }
        entities:
          - entity: sensor.green_zone_paid
            name: Paid
            icon: mdi:cash
          - entity: sensor.green_zone_regular_tariff
            name: Regular rate
            icon: mdi:cash-multiple
          - entity: sensor.green_zone_savings
            name: Green zone savings
            icon: mdi:cash-check
          - entity: sensor.green_zone_entries
            name: Times parked
            icon: mdi:counter
  - type: grid
    columns: 2
    square: false
    cards:
      - type: entity
        entity: sensor.total_savings
        name: Total Savings
        icon: mdi:currency-eur
        state_color: false
      - type: entity
        entity: sensor.total_entries
        name: Times parked
        icon: mdi:counter
      - type: entity
        entity: sensor.newest_entry
        name: Newest entry
        icon: mdi:counter
      - type: entity
        entity: sensor.oldest_entry
        name: Oldest entry
        icon: mdi:counter
  - type: history-graph
    title: 💶 Payment History
    hours_to_show: 500
    entities:
      - entity: sensor.blue_zone_savings
        name: Blue
      - entity: sensor.green_zone_savings
        name: Green
      - entity: sensor.total_savings
        name: Savings

```

This dashboard includes:
- Separate cards for Blue and Green zone statistics
- Total savings and parking entries counters
- A historical graph showing payment trends over time

Note: This configuration requires the `card-mod` custom card to be installed via HACS for the colored headers.

## Support My Work

If you find this integration helpful, you can buy me a coffee to show your support:

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/msanchezt)

