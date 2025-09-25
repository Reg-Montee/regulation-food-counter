import os
import requests
from flask import Flask, render_template
from datetime import datetime, timedelta

app = Flask(__name__)

# Fitbit API credentials from environment variables
ACCESS_TOKEN = os.getenv("FITBIT_ACCESS_TOKEN")
CLIENT_ID = os.getenv("FITBIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("FITBIT_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("FITBIT_REFRESH_TOKEN")

# Food items to track
FOOD_ITEMS = ["Regulation Hotdog", "Regulation Burger", "Regulation Apple"]
food_counts = {item: 0 for item in FOOD_ITEMS}

def refresh_access_token():
    url = "https://api.fitbit.com/oauth2/token"
    headers = {
        "Authorization": f"Basic {requests.auth._basic_auth_str(CLIENT_ID, CLIENT_SECRET)}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        tokens = response.json()
        os.environ["FITBIT_ACCESS_TOKEN"] = tokens["access_token"]
        os.environ["FITBIT_REFRESH_TOKEN"] = tokens["refresh_token"]
        return tokens["access_token"]
    return ACCESS_TOKEN

def get_food_logs():
    global food_counts
    food_counts = {item: 0 for item in FOOD_ITEMS}
    access_token = ACCESS_TOKEN
    headers = {"Authorization": f"Bearer {access_token}"}

    today = datetime.utcnow().date()
    start_year = today.year if today.month >= 9 else today.year - 1
    start_date = datetime(start_year, 9, 1).date()
    end_date = today

    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        url = f"https://api.fitbit.com/1/user/-/foods/log/date/{date_str}.json"
        response = requests.get(url, headers=headers)

        if response.status_code == 401:
            access_token = refresh_access_token()
            headers["Authorization"] = f"Bearer {access_token}"
            response = requests.get(url, headers=headers)

        if response.status_code == 200:
            logs = response.json().get("foods", [])
            for entry in logs:
                name = entry.get("loggedFood", {}).get("name", "")
                for item in FOOD_ITEMS:
                    if item.lower() in name.lower():
                        food_counts[item] += 1

        current_date += timedelta(days=1)

@app.route("/")
def index():
    return render_template("index.html", counters=food_counts)

if __name__ == "__main__":
    get_food_logs()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
