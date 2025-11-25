from flask import Flask, redirect, request, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import requests
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///food_logs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# New food items to track
FOOD_ITEMS = {
    "RegBurger": "regburger",
    "AndrewRegBurger": "andrewregburger",
    "NickRegBurger": "nickregburger",
    "EricRegBurger": "ericregburger",
    "GeoffRegBurger": "geoffregburger",
    "Gavin": "gavin"
}

class FoodLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    food_name = db.Column(db.String(100))
    log_date = db.Column(db.Date)

with app.app_context():
    db.create_all()

CLIENT_ID = os.getenv("FITBIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("FITBIT_CLIENT_SECRET")
REDIRECT_URI = os.getenv("FITBIT_REDIRECT_URI")
AUTH_HEADER = os.getenv("FITBIT_AUTH_HEADER")
ACCESS_TOKEN = os.getenv("FITBIT_ACCESS_TOKEN")

@app.route("/authorize")
def authorize():
    scope = "nutrition"
    return redirect(
        f"https://www.fitbit.com/oauth2/authorize?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}&scope={scope}&expires_in=604800"
    )

@app.route("/callback")
def callback():
    code = request.args.get("code")
    token_url = "https://api.fitbit.com/oauth2/token"
    headers = {
        "Authorization": f"Basic {AUTH_HEADER}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "client_id": CLIENT_ID,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": code
    }
    response = requests.post(token_url, headers=headers, data=data)
    return response.json()

@app.route("/update")
def update_logs():
    if not ACCESS_TOKEN:
        return "Missing access token", 400

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    today = datetime.utcnow().date()
    start_date = datetime(today.year - 1 if today.month < 9 else today.year, 9, 1).date()
    end_date = today

    current = start_date
    while current <= end_date:
        date_str = current.strftime("%Y-%m-%d")
        url = f"https://api.fitbit.com/1/user/-/foods/log/date/{date_str}.json"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            logs = response.json().get("foods", [])
            for item in logs:
                name = item.get("loggedFood", {}).get("name", "").lower()
                for label, keyword in FOOD_ITEMS.items():
                    if keyword in name:
                        exists = FoodLog.query.filter_by(food_name=label, log_date=current).first()
                        if not exists:
                            db.session.add(FoodLog(food_name=label, log_date=current))
            db.session.commit()
        current += timedelta(days=1)

    return "Food logs updated"

@app.route("/iframe")
def iframe():
    today = datetime.utcnow().date()
    start_date = datetime(today.year - 1 if today.month < 9 else today.year, 9, 1).date()
    counts = {}
    for label in FOOD_ITEMS:
        count = FoodLog.query.filter(
            FoodLog.food_name == label,
            FoodLog.log_date >= start_date,
            FoodLog.log_date <= today
        ).count()
        counts[label] = count
    return render_template("iframe.html", counts=counts)

@app.route("/")
def home():
    return redirect("/iframe")

if __name__ == "__main__":
    app.run()
