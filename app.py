import os
import requests
from flask import Flask, render_template
from datetime import datetime, timedelta
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Fitbit API credentials from environment variables
ACCESS_TOKEN = os.getenv("FITBIT_ACCESS_TOKEN")
CLIENT_ID = os.getenv("FITBIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("FITBIT_CLIENT_SECRET")
REDIRECT_URI = os.getenv("FITBIT_REDIRECT_URI")
REFRESH_TOKEN = os.getenv("FITBIT_REFRESH_TOKEN")

# Food items to track
FOOD_ITEMS = ["Regulation Hotdog", "Regulation Burger", "Regulation Apple"]

# Determine the 12-month period from September 1 to August 31
def get_date_range():
    today = datetime.today()
    if today.month >= 9:
        start_date = datetime(today.year, 9, 1)
        end_date = datetime(today.year + 1, 8, 31)
    else:
        start_date = datetime(today.year - 1, 9, 1)
        end_date = datetime(today.year, 8, 31)
    return start_date, end_date

# Fetch food logs from Fitbit API
def fetch_food_logs(start_date, end_date):
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    food_counts = {item: 0 for item in FOOD_ITEMS}
    current_date = start_date

    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        url = f"https://api.fitbit.com/1/user/-/foods/log/date/{date_str}.json"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            for entry in data.get("foods", []):
                name = entry.get("loggedFood", {}).get("name", "")
                for item in FOOD_ITEMS:
                    if item.lower() in name.lower():
                        food_counts[item] += 1
            logging.info(f"Processed {date_str}")
        except Exception as e:
            logging.error(f"Error fetching data for {date_str}: {e}")
        current_date += timedelta(days=1)

    return food_counts

@app.route("/")
def index():
    start_date, end_date = get_date_range()
    food_counts = fetch_food_logs(start_date, end_date)
    return render_template("index.html", food_counts=food_counts)
