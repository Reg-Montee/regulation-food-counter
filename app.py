import os
import json
import logging
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO)

# Fitbit API credentials from environment variables
ACCESS_TOKEN = os.getenv("FITBIT_ACCESS_TOKEN")
CLIENT_ID = os.getenv("FITBIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("FITBIT_CLIENT_SECRET")
REDIRECT_URI = os.getenv("FITBIT_REDIRECT_URI")
REFRESH_TOKEN = os.getenv("FITBIT_REFRESH_TOKEN")

# Food items to track
FOOD_ITEMS = ["Regulation Hotdog", "Regulation Burger", "Regulation Apple"]
CACHE_FILE = "food_counts.json"

# Determine the 12-month period from September 1 to August 31
def get_date_range():
    today = datetime.utcnow().date()
    if today.month >= 9:
        start = datetime(today.year, 9, 1).date()
        end = datetime(today.year + 1, 8, 31).date()
    else:
        start = datetime(today.year - 1, 9, 1).date()
        end = datetime(today.year, 8, 31).date()
    return start, end

# Fetch food logs from Fitbit API
def fetch_food_counts():
    start_date, end_date = get_date_range()
    counts = {item: 0 for item in FOOD_ITEMS}
    date = start_date
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    while date <= end_date:
        url = f"https://api.fitbit.com/1/user/-/foods/log/date/{date}.json"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            for entry in data.get("foods", []):
                name = entry.get("loggedFood", {}).get("name", "")
                for item in FOOD_ITEMS:
                    if item.lower() in name.lower():
                        counts[item] += 1
            logging.info(f"Fetched data for {date}")
        except Exception as e:
            logging.error(f"Error fetching data for {date}: {e}")
        date += timedelta(days=1)

    with open(CACHE_FILE, "w") as f:
        json.dump(counts, f)
    return counts

# Load cached counts
def load_cached_counts():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return fetch_food_counts()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        counts = fetch_food_counts()
        return redirect("/")
    counts = load_cached_counts()
    return render_template("index.html", counts=counts)

if __name__ == "__main__":
    app.run(debug=True)
