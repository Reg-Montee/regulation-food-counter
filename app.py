import os
import datetime
import requests
from flask import Flask, render_template
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# Fitbit API credentials from environment variables
ACCESS_TOKEN = os.getenv("FITBIT_ACCESS_TOKEN")
REFRESH_TOKEN = os.getenv("FITBIT_REFRESH_TOKEN")
CLIENT_ID = os.getenv("FITBIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("FITBIT_CLIENT_SECRET")

# Food items to track
FOOD_ITEMS = ["Regulation Hotdog", "Regulation Burger", "Regulation Apple"]
counters = {item: 0 for item in FOOD_ITEMS}

def get_food_logs():
    global counters
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    today = datetime.date.today()
    start_year = today.year if today.month >= 9 else today.year - 1
    start_date = datetime.date(start_year, 9, 1)
    end_date = datetime.date(start_year + 1, 8, 31)

    counters = {item: 0 for item in FOOD_ITEMS}

    date = start_date
    while date <= end_date:
        url = f"https://api.fitbit.com/1/user/-/foods/log/date/{date.isoformat()}.json"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            for entry in data.get("foods", []):
                name = entry.get("loggedFood", {}).get("name", "")
                for item in FOOD_ITEMS:
                    if item.lower() in name.lower():
                        counters[item] += 1
        date += datetime.timedelta(days=1)

scheduler = BackgroundScheduler()
scheduler.add_job(get_food_logs, 'cron', hour=4)
scheduler.start()

@app.route("/")
def index():
    return render_template("index.html", counters=counters)

if __name__ == "__main__":
    get_food_logs()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
