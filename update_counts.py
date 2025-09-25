import os
import json
import time
import logging
import requests
from datetime import datetime, timedelta

FOOD_ITEMS = ['Regulation Hotdog', 'Regulation Burger', 'Regulation Apple']
CACHE_FILE = 'food_counts.json'

# Load Fitbit credentials from environment variables
ACCESS_TOKEN = os.getenv('FITBIT_ACCESS_TOKEN')

def get_date_range():
    today = datetime.utcnow()
    if today.month >= 9:
        start = datetime(today.year, 9, 1)
        end = datetime(today.year + 1, 8, 31)
    else:
        start = datetime(today.year - 1, 9, 1)
        end = datetime(today.year, 8, 31)
    return start, end

def fetch_food_logs(date):
    url = f"https://api.fitbit.com/1/user/-/foods/log/date/{date.strftime('%Y-%m-%d')}.json"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Error fetching data for {date.strftime('%Y-%m-%d')}: {e}")
        return {}

def update_food_counts():
    start_date, end_date = get_date_range()
    current_date = start_date
    counts = {item: 0 for item in FOOD_ITEMS}

    while current_date <= end_date:
        data = fetch_food_logs(current_date)
        for entry in data.get('foods', []):
            name = entry.get('name', '')
            for item in FOOD_ITEMS:
                if item.lower() in name.lower():
                    counts[item] += 1
        current_date += timedelta(days=1)
        time.sleep(1)

    with open(CACHE_FILE, 'w') as f:
        json.dump(counts, f)
