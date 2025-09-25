from flask import Flask, render_template
import requests
import os
from datetime import datetime, timedelta

app = Flask(__name__)

FOOD_ITEMS = ["Regulation Hotdog", "Regulation Burger", "Regulation Apple"]

def get_fitbit_food_logs(start_date, end_date):
    access_token = os.getenv("FITBIT_ACCESS_TOKEN")
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    food_counts = {item: 0 for item in FOOD_ITEMS}
    current_date = start_date
    while current_date <= end_date:
        url = f"https://api.fitbit.com/1/user/-/foods/log/date/{current_date.strftime('%Y-%m-%d')}.json"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            for log in data.get("foods", []):
                name = log.get("name", "")
                for item in FOOD_ITEMS:
                    if item.lower() in name.lower():
                        food_counts[item] += 1
        current_date += timedelta(days=1)
    return food_counts

def get_date_range():
    today = datetime.today()
    if today.month >= 9:
        start_date = datetime(today.year, 9, 1)
        end_date = datetime(today.year + 1, 8, 31)
    else:
        start_date = datetime(today.year - 1, 9, 1)
        end_date = datetime(today.year, 8, 31)
    return start_date, end_date

@app.route("/")
def index():
    start_date, end_date = get_date_range()
    food_counts = get_fitbit_food_logs(start_date, end_date)
    return render_template("index.html", food_counts=food_counts)

if __name__ == "__main__":
    app.run(debug=True)
