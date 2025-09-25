from flask import Flask, render_template, request, redirect, url_for
import requests
import datetime
import json
import os
import time
import logging
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

FOOD_ITEMS = ["Regulation Hotdog", "Regulation Burger", "Regulation Apple"]
CACHE_FILE = "food_counts.json"

def get_date_range():
    today = datetime.date.today()
    if today.month >= 9:
        start_date = datetime.date(today.year, 9, 1)
        end_date = datetime.date(today.year + 1, 8, 31)
    else:
        start_date = datetime.date(today.year - 1, 9, 1)
        end_date = datetime.date(today.year, 8, 31)
    return start_date, end_date

def fetch_food_counts():
    access_token = os.getenv("FITBIT_ACCESS_TOKEN")
    headers = {"Authorization": f"Bearer {access_token}"}
    start_date, end_date = get_date_range()
    current_date = start_date
    counts = {item: 0 for item in FOOD_ITEMS}

    while current_date <= end_date:
        url = f"https://api.fitbit.com/1/user/-/foods/log/date/{current_date}.json"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            for log in data.get("foods", []):
                name = log.get("name", "")
                for item in FOOD_ITEMS:
                    if item.lower() in name.lower():
                        counts[item] += 1
        except Exception as e:
            logging.error(f"Error fetching data for {current_date}: {e}")
        time.sleep(1)
        current_date += datetime.timedelta(days=1)

    with open(CACHE_FILE, "w") as f:
        json.dump(counts, f)
    logging.info("Food counts updated.")
    return counts

def load_cached_counts():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return fetch_food_counts()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        counts = fetch_food_counts()
    else:
        counts = load_cached_counts()
    return render_template("index.html", counts=counts)

# Schedule daily update at 4am GMT
scheduler = BackgroundScheduler(timezone="UTC")
scheduler.add_job(fetch_food_counts, 'cron', hour=4, minute=0)
scheduler.start()

if __name__ == "__main__":
    app.run(debug=True)
