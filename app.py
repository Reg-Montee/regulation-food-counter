
from flask import Flask, render_template
import requests
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import os

app = Flask(__name__)

# Fitbit API credentials from environment variables
ACCESS_TOKEN = os.getenv("FITBIT_ACCESS_TOKEN")
REFRESH_TOKEN = os.getenv("FITBIT_REFRESH_TOKEN")
CLIENT_ID = os.getenv("FITBIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("FITBIT_CLIENT_SECRET")

# Food items to track
FOOD_ITEMS = ["Regulation Hotdog", "Regulation Burger", "Regulation Apple"]
COUNTS = {item: 0 for item in FOOD_ITEMS}

def get_food_logs():
    global COUNTS
    COUNTS = {item: 0 for item in FOOD_ITEMS}
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    today = datetime.utcnow().date()
    start = datetime(today.year if today.month >= 9 else today.year - 1, 9, 1).date()
    end = datetime(today.year + 1 if today.month >= 9 else today.year, 8, 31).date()

    date = start
    while date <= end and date <= today:
        url = f"https://api.fitbit.com/1/user/-/foods/log/date/{date}.json"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            for log in data.get("foods", []):
                name = log.get("loggedFood", {}).get("name", "")
                for item in FOOD_ITEMS:
                    if item.lower() in name.lower():
                        COUNTS[item] += 1
        date += timedelta(days=1)

# Schedule daily update at 4am GMT
scheduler = BackgroundScheduler(timezone="GMT")
scheduler.add_job(get_food_logs, 'cron', hour=4)
scheduler.start()

@app.route("/")
def index():
    return render_template("index.html", counts=COUNTS)

if __name__ == "__main__":
    get_food_logs()
    app.run(debug=True)
