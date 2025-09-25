from flask import Flask, jsonify, send_from_directory
import os
import requests
from datetime import datetime, timedelta

app = Flask(__name__, static_folder='public')

# Load environment variables
CLIENT_ID = os.getenv("FITBIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("FITBIT_CLIENT_SECRET")
ACCESS_TOKEN = os.getenv("FITBIT_ACCESS_TOKEN")
REFRESH_TOKEN = os.getenv("FITBIT_REFRESH_TOKEN")

# Helper function to refresh token
def refresh_access_token():
    global ACCESS_TOKEN, REFRESH_TOKEN
    token_url = "https://api.fitbit.com/oauth2/token"
    auth_header = f"{CLIENT_ID}:{CLIENT_SECRET}"
    headers = {
        "Authorization": "Basic " + auth_header.encode("ascii").hex(),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID
    }
    response = requests.post(token_url, headers=headers, data=data)
    if response.status_code == 200:
        tokens = response.json()
        ACCESS_TOKEN = tokens["access_token"]
        REFRESH_TOKEN = tokens["refresh_token"]
        return True
    return False

# Route to fetch food counts
@app.route('/food-count')
def food_count():
    global ACCESS_TOKEN
    hotdogs = burgers = apples = 0
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    today = datetime.utcnow()
    start_year = today.year if today.month >= 9 else today.year - 1
    start_date = datetime(start_year, 9, 1)
    end_date = start_date + timedelta(days=365)

    current_date = start_date
    while current_date < end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        url = f"https://api.fitbit.com/1/user/-/foods/log/date/{date_str}.json"
        response = requests.get(url, headers=headers)

        if response.status_code == 401:
            if refresh_access_token():
                headers["Authorization"] = f"Bearer {ACCESS_TOKEN}"
                response = requests.get(url, headers=headers)

        if response.status_code == 200:
            foods = response.json().get("foods", [])
            for food in foods:
                name = food["loggedFood"]["name"]
                if name == "Regulation Hotdog":
                    hotdogs += 1
                elif name == "Regulation Burger":
                    burgers += 1
                elif name == "Regulation Apple":
                    apples += 1

        current_date += timedelta(days=1)

    return jsonify({"hotdogs": hotdogs, "burgers": burgers, "apples": apples})

# Serve iframe.html
@app.route('/')
def root():
    return send_from_directory('public', 'iframe.html')

@app.route('/public/<path:filename>')
def serve_public(filename):
    return send_from_directory('public', filename)

# Run the app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)