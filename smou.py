import argparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from collections import defaultdict
import time
import pandas as pd
import os
from dotenv import load_dotenv
import requests
import random
import json
import pdfplumber
import tempfile
from selenium.webdriver.common.action_chains import ActionChains
import glob

# Load environment variables from .env file
load_dotenv()

# Setup argument parser
parser = argparse.ArgumentParser(description="Scrape SMOU parking data")
parser.add_argument('--output', default='/app/smou_parking_data.json', 
                   help="Path to output JSON file")
args = parser.parse_args()

###############################
smou_moviments = os.getenv("SMOU_MOVEMENTS_URL")
type_of_service_checked = "Parquímetre"
specific_plates = os.getenv("LICENSE_PLATES", "").split(",")
if not specific_plates or specific_plates[0] == "":
    raise ValueError("No license plates found in environment variables. Please set LICENSE_PLATES")
blue_zone_regular_cost=3.25
blue_zone_eco_cost=2.50
blue_zone_0_cost=0
green_zone_regular_cost=3.5
green_zone_eco_cost=2.75
green_zone_0_cost=0.5

user_agents = [
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.864.41 Safari/537.36 Edg/91.0.864.41",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36 Edg/92.0.902.55",
    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36",
    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.15",
    # Firefox on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:90.0) Gecko/20100101 Firefox/90.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:91.0) Gecko/20100101 Firefox/91.0",
    # Mobile Chrome on Android
    "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G960U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.66 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Mobile Safari/537.36",
    # Mobile Safari on iOS
    "Mozilla/5.0 (iPhone; CPU iPhone OS 13_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 13_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0 Mobile/15E148 Safari/604.1",
    # Opera on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 OPR/77.0.4054.275",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36 OPR/78.0.4093.184",
    # Edge on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11.0; rv:91.0) Gecko/20100101 Firefox/91.0 Edg/92.0.902.62",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_3_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36 Edg/91.0.864.59",
]
#################################
# Account credentials from environment variables
accounts = []
i = 1
while True:
    email = os.getenv(f"ACCOUNT{i}_EMAIL")
    password = os.getenv(f"ACCOUNT{i}_PASSWORD")
    if not email or not password:
        break
    accounts.append({"username": email, "password": password})
    i += 1

if not accounts:
    raise ValueError("No valid accounts found in environment variables. Please ensure at least one account is configured (ACCOUNT1_EMAIL and ACCOUNT1_PASSWORD)")

# Home Assistant details from environment variables
home_assistant_url = os.getenv("HOME_ASSISTANT_URL")
access_token = os.getenv("ACCESS_TOKEN")
headers = {
    "Authorization": f"Bearer {access_token}",
    "content-type": "application/json",
}

# Set up Chrome options
options = Options()
#options.add_argument("--headless=new")  # Comment out to see the browser window
options.add_argument("--ignore-certificate-errors")
options.add_argument("--allow-insecure-localhost")
options.add_argument("window-size=1920,1080")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument(f"user-agent={random.choice(user_agents)}")
# Add these specific download preferences
options.add_experimental_option('prefs', {
    'download.default_directory': '/app/downloads',
    'download.prompt_for_download': False,
    'download.directory_upgrade': True,
    'safebrowsing.enabled': False,
    'download.default_directory_infobar_shown': False,
    'plugins.always_open_pdf_externally': True,
    'profile.default_content_settings.popups': 0,
    'profile.default_content_setting_values.automatic_downloads': 1
})
            json=data,
# Add this to prevent the "multiple files" warning
options.add_experimental_option('excludeSwitches', ['enable-automation', 'safebrowsing-disable-download-protection'])


def update_home_assistant_sensors(sensor_data):
    """
    Update sensor values in Home Assistant
    Args:
        sensor_data (dict): Dictionary of sensor_id: value pairs to update
    """
    for entity_id, state in sensor_data.items():
        data = {
            "state": state,
            "attributes": {"unit_of_measurement": "€"}
        }
        response = requests.post(
            f"{home_assistant_url}{entity_id}",
            headers=headers,
            json=data,
            verify=False
        )

        if response.status_code == 200:
            print(f"Successfully updated {entity_id} in Home Assistant")
        else:
            print(f"Failed to update {entity_id} in Home Assistant: {response.content}")

def collect_parking_data():
    try:
        # Try to load existing data first
        try:
            with open(args.output, 'r', encoding='utf-8') as f:
                all_parsed_data = json.load(f)
                existing_ids = {entry["ID"] for entry in all_parsed_data}
                print(f"Loaded {len(all_parsed_data)} existing entries")
        except FileNotFoundError:
            all_parsed_data = []
            existing_ids = set()
            print("No existing data found, starting fresh collection")

        # Loop through each account
        for account in accounts:
            print(f"\nProcessing account: {account['username']}")
            
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.set_window_size(1920, 1080)
            driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
            driver.execute("send_command", {
                'cmd': 'Page.setDownloadBehavior',
                'params': {
                    'behavior': 'allow',
                    'downloadPath': '/app/downloads'
                }
            })

            try:
                # Login process
                driver.get(smou_moviments)
                email_field = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder=' Correu electrònic ']")))
                email_field.send_keys(account["username"])
                password_field = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//input[@name='password']")))
                password_field.send_keys(account["password"])
                submit_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and text()='Iniciar sessió']")))
                submit_button.click()
                time.sleep(2)
                driver.set_page_load_timeout(180)
                driver.get(smou_moviments)

                # Add after successful login
                print("Successfully logged in")
                print(f"Current URL: {driver.current_url}")

                # Select custom range and input dates
                mat_select = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "mat-select-0")))
                mat_select.click()
                rang_personalitzat_option = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//mat-option/span[contains(text(), 'Rang personalitzat')]")))
                rang_personalitzat_option.click()
                input_field = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "mat-input-0")))
                input_field.send_keys("01/05/2023")
                today_date = datetime.today().strftime('%d/%m/%Y')
                input_field = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "mat-input-1")))
                input_field.send_keys(today_date)
                submit_button = driver.find_element(By.XPATH, "//button[@type='submit']//span[text()=' Cercar ']")
                submit_button.click()

                # Wait for the table to load
                time.sleep(2)

                try:
                    # Get all elements that contain 'de '
                    total_pages_elements = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.XPATH, "//span[contains(text(), 'de ')]"))
                    )
                    # Select the text of the last element in the list
                    total_pages_text = total_pages_elements[-1].text if total_pages_elements else ""
                    # Extract the total pages number from the last element's text
                    total_pages = int(total_pages_text.split()[-1])  # Extract the last word (number of pages)
                except Exception as e:
                    print(f"Error extracting total number of pages for account {account['username']}:", e)
                    driver.quit()
                    continue

                print(f"Total pages found for account {account['username']}: {total_pages}")
                total_pages = int(total_pages_text.split()[-1])  # Extracts the last number (total pages)

                # Initialize data storage for new entries from this account
                new_entries = []

                # Loop through each page and extract data
                for page in range(total_pages):
                    print(f"Processing page {page + 1} of {total_pages} for account {account['username']}")

                    # Extract rows from the table
                    table = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html/body/app-root/div/div[2]/app-moviements/div/div/div[3]/div/div/div/div[1]/table")))
                    rows = table.find_elements(By.TAG_NAME, "tr")

                    # Extract data for each row
                    for row in rows[1:]:  # Skip header
                        cells = row.find_elements(By.TAG_NAME, "td")
                        
                        if cells and type_of_service_checked in cells[5].text.strip() and cells[4].text.strip() in specific_plates:
                            entry_id = cells[1].text.strip()
                            
                            # Skip if we already have this entry
                            if entry_id in existing_ids:
                                continue
                            
                            print(f"Processing row with cells count: {len(cells)}")
                            print(f"Row content: {[cell.text for cell in cells]}")
                            
                            try:
                                # Get the last cell (Accions column)
                                actions_cell = cells[-1]
                                print(f"Found actions cell with text: {actions_cell.text}")
                                
                                # Click the button inside the actions cell
                                actions_button = actions_cell.find_element(By.TAG_NAME, "button")
                                driver.execute_script("arguments[0].click();", actions_button)
                                time.sleep(1)  # Small wait after click
                                
                                # Wait for the dropdown menu and find the PDF download option
                                pdf_button = WebDriverWait(driver, 10).until(
                                    EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'actionText') and contains(text(), 'Descarregar PDF')]"))
                                )
                                driver.execute_script("arguments[0].click();", pdf_button)
                                time.sleep(2)  # Wait for download to start
                                
                                # Wait for the file to download and check if it exists
                                download_dir = "/app/downloads"
                                timeout = time.time() + 10  # 10 seconds timeout
                                while time.time() < timeout:
                                    pdf_files = glob.glob(f"{download_dir}/*.pdf")
                                    if pdf_files:
                                        latest_file = max(pdf_files, key=os.path.getctime)
                                        print(f"Found downloaded PDF: {latest_file}")
                                        
                                        # Parse the PDF
                                        try:
                                            with pdfplumber.open(latest_file) as pdf:
                                                first_page = pdf.pages[0]
                                                text = first_page.extract_text()
                                                print(f"PDF content for entry {entry_id}:")
                                                print(text)
                                                
                                            # Clean up - delete the PDF after processing
                                            os.remove(latest_file)
                                        except Exception as e:
                                            print(f"Error processing PDF for entry {entry_id}: {e}")
                                        break
                                    time.sleep(0.5)
                                else:
                                    print(f"Timeout waiting for PDF download for entry {entry_id}")
                                
                            except Exception as e:
                                print(f"Error clicking buttons for entry {entry_id}: {str(e)}")
                                continue
                            
                            # Continue with existing record creation
                            record = {
                                "ID": entry_id,
                                "Start date": cells[2].text.strip(),
                                "End date": cells[3].text.strip(),
                                "Number of hours and minutes": cells[9].text.strip(),
                                "Type of parking": cells[7].text.strip(),
                                "Cost": cells[10].text.strip(),
                                "Mail": account["username"]
                            }
                            new_entries.append(record)
                            existing_ids.add(entry_id)

                    # Check if this is the last page; if so, break out of the loop
                    if page == total_pages - 1:
                        break

                    # Click the "Next" button to move to the next page
                    next_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//i[contains(@class, 'fas fa-angle-right')]")))
                    next_button.click()

                    # Wait for the next page to load
                    time.sleep(2)

                # Add new entries to all_parsed_data
                if new_entries:
                    print(f"Found {len(new_entries)} new entries for account {account['username']}")
                    all_parsed_data.extend(new_entries)
                    
                    # Save after each account's new entries
                    with open(args.output, 'w', encoding='utf-8') as f:
                        json.dump(all_parsed_data, f, ensure_ascii=False, indent=4)
                    print(f"Updated data saved to {args.output}")
                else:
                    print(f"No new entries found for account {account['username']}")

            except Exception as e:
                print(f"Error processing account {account['username']}: {str(e)}")
            finally:
                driver.quit()

        print(f"\nCollection completed. Total entries: {len(all_parsed_data)}")

    except Exception as e:
        print(f"Error collecting data: {e}")

if __name__ == "__main__":
    collect_parking_data()