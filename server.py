from flask import Flask, jsonify, send_from_directory
import os
import requests
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='public')

client_id = os.getenv("FITBIT_CLIENT_ID")
client_secret = os.getenv("FITBIT_CLIENT_SECRET")
access_token = os.getenv("FITBIT_ACCESS_TOKEN")
refresh_token = os.getenv("FITBIT_REFRESH_TOKEN")

food_counts = {"hotdogs": 0, "burgers": 0, "apples": 0}

def refresh_tokens():
    global access_token, refresh_token
    url = "https://api.fitbit.com/oauth2/token"
    auth_header = f"{client_id}:{client_secret}"
    headers = {
        "Authorization": "Basic " + auth_header.encode("ascii").hex(),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        tokens = response.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

def fetch_food_counts():
    global food_counts
    food_counts = {"hotdogs": 0, "burgers": 0, "apples": 0}
    headers = {"Authorization": f"Bearer {access_token}"}
    today = datetime.utcnow()
    start_year = today.year if today.month >= 9 else today.year - 1
    start_date = datetime(start_year, 9, 1)
    end_date = start_date + timedelta(days=365)

    current_date = start_date
    while current_date < end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        url = f"https://api.fitbit.com/1/user/-/foods/log/date/{date_str}.json"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            foods = response.json().get("foods", [])
            for food in foods:
                name = food["loggedFood"]["name"]
                if name == "Regulation Hotdog":
                    food_counts["hotdogs"] += 1
                elif name == "Regulation Burger":
                    food_counts["burgers"] += 1
                elif name == "Regulation Apple":
                    food_counts["apples"] += 1
        current_date += timedelta(days=1)

@app.route('/food-count')
def get_food_count():
    return jsonify(food_counts)

@app.route('/refresh-count')
def manual_refresh():
    fetch_food_counts()
    return jsonify({"status": "refreshed", "counts": food_counts})

@app.route('/')
def root():
    return send_from_directory('public', 'iframe.html')

scheduler = BackgroundScheduler()
scheduler.add_job(fetch_food_counts, 'cron', hour=4, minute=0)
scheduler.start()

fetch_food_counts()

if __name__ == '__main__':
    app.run()
