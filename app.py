import os
import requests
from flask import Flask, render_template
from datetime import datetime

app = Flask(__name__)

# Fitbit API credentials from config vars
ACCESS_TOKEN = os.getenv("FITBIT_ACCESS_TOKEN")
CLIENT_ID = os.getenv("FITBIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("FITBIT_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("FITBIT_REFRESH_TOKEN")

# Food items to track
FOOD_ITEMS = ["Regulation Hotdog", "Regulation Burger", "Regulation Apple"]

# Counter dictionary
food_counters = {item: 0 for item in FOOD_ITEMS}

def get_food_logs():
    global food_counters
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    # Determine date range: Sept 1 of previous year to Aug 31 of current year
    today = datetime.utcnow()
    year = today.year if today.month >= 9 else today.year - 1
    start_date = f"{year}-09-01"
    end_date = f"{year + 1}-08-31"

    # Reset counters
    food_counters = {item: 0 for item in FOOD_ITEMS}

    # Fetch logs month by month
    for month in range(9, 13):
        date_prefix = f"{year}-{month:02d}"
        fetch_month_logs(date_prefix, headers)
    for month in range(1, 9):
        date_prefix = f"{year + 1}-{month:02d}"
        fetch_month_logs(date_prefix, headers)

def fetch_month_logs(date_prefix, headers):
    url = f"https://api.fitbit.com/1/user/-/foods/log/date/{date_prefix}-01.json"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            for entry in data.get("foods", []):
                name = entry.get("loggedFood", {}).get("name", "")
                for item in FOOD_ITEMS:
                    if item.lower() in name.lower():
                        food_counters[item] += 1
    except Exception as e:
        print(f"Error fetching logs for {date_prefix}: {e}")

@app.route("/")
def index():
    return render_template("index.html", counters=food_counters)

if __name__ == "__main__":
    get_food_logs()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
