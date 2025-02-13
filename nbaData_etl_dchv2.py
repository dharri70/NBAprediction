import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import time
import os
import logging


# Set up logging
logging.basicConfig(filename='error_log.txt', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')


# Define labels mapping
labels = {
    "mp": "Minutes Played",
    "fg": "Field Goals",
    "fga": "Field Goals Attempted",
    "fg_pct": "Field Goal Percentage",
    "fg3": "Three-Point Field Goals",
    "fg3a": "Three-Point Field Goals Attempted",
    "fg3_pct": "Three-Point Field Goal Percentage",
    "ft": "Free Throws",
    "fta": "Free Throws Attempted",
    "ft_pct": "Free Throw Percentage",
    "orb": "Offensive Rebounds",
    "drb": "Defensive Rebounds",
    "trb": "Total Rebounds",
    "ast": "Assists",
    "stl": "Steals",
    "blk": "Blocks",
    "tov": "Turnovers",
    "pf": "Personal Fouls",
    "pts": "Points",
    "ts_pct": "True Shooting Percentage",
    "efg_pct": "Effective Field Goal Percentage",
    "fg3a_per_fga_pct": "Three-Point Attempt Rate",
    "fta_per_fga_pct": "Free Throw Attempt Rate",
    "orb_pct": "Offensive Rebound Percentage",
    "drb_pct": "Defensive Rebound Percentage",
    "trb_pct": "Total Rebound Percentage",
    "ast_pct": "Assist Percentage",
    "stl_pct": "Steal Percentage",
    "blk_pct": "Block Percentage",
    "tov_pct": "Turnover Percentage",
    "usg_pct": "Usage Percentage",
    "off_rtg": "Offensive Rating",
    "def_rtg": "Defensive Rating"
}

# Function to process a single URL and save CSV files
def process_url(url):
    try: 
        response = requests.get(url, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Find all td elements with class="right" and data-stat="mp"
        mp_td_list = soup.find_all('td', {'class': 'right', 'data-stat': 'mp'})

        # Arrays to store values
        first_32_values = []
        next_32_values = []

        # Iterate through all td elements and filter by text value '240'
        for td in mp_td_list:
            if td.get_text() == '240':
                # Get the parent tr tag
                tr_tag = td.find_parent('tr')

                # Find all td elements within the same tr tag with class="right" and data-stat attributes
                next_10_elements = tr_tag.find_all('td', {'class': 'right', 'data-stat': True})[1:20]

                # Extract and store desired data
                for element in next_10_elements:
                    data_stat = element['data-stat']
                    if data_stat in labels:
                        value = element.get_text()
                        if len(first_32_values) < 32:
                            first_32_values.append(value)
                        else:
                            next_32_values.append(value)

        # Generate unique filenames with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv1_filename = f"NBAdata14_24/csv1_{timestamp}.csv"
        csv2_filename = f"NBAdata14_24/csv2_{timestamp}.csv"

        # Write data to CSV files with labels as the first row
        with open(csv1_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([labels[data_stat] for data_stat in labels if data_stat != 'mp'])
            writer.writerow(first_32_values)

        with open(csv2_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([labels[data_stat] for data_stat in labels if data_stat != 'mp'])
            writer.writerow(next_32_values)

        print(f"CSV files '{csv1_filename}' and '{csv2_filename}' have been generated successfully.")

        # Log the successful URL visit
        with open('success_log.txt', 'a') as log_file:
            log_file.write(f"{url}\n")
    except requests.Timeout:
        logging.error(f"Timeout occured while accessing URL: {url}")
        print(f"Timeout occured while accessing URL: {url}")
    except requests.RequestException as e:
        logging.error(f"Error occured while accessing URL: {url} - {e}")
        print(f"Error occured while accessing URL: {url} - {e}")
    except Exception as e:
        logging.error(f"Unexpected error occured while accessing URL: {url} - {e}")
        print(f"Unexpected error occured while accessing URL: {url} - {e}")

# Create folder if it doesn't exist
os.makedirs("NBAdata14_24", exist_ok=True)

# Read URLs from file
with open('boxscore_urlsv2.txt', 'r') as file:
    urls = file.readlines()

# Process each URL with a download delay
for url in urls:
    url = url.strip()  # Remove leading/trailing whitespace
    process_url(url)
    time.sleep(60/15)  # Download delay of 60/15 seconds (4 seconds)
