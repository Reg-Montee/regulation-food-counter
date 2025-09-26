import os
import logging
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import requests

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///food_counter.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

FOOD_ITEMS = ['Regulation Hotdog', 'Regulation Burger', 'Regulation Apple']

class FoodCounter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    food_item = db.Column(db.String(50), unique=True, nullable=False)
    count = db.Column(db.Integer, default=0)

def init_db():
    with app.app_context():
        db.create_all()
        for item in FOOD_ITEMS:
            if not FoodCounter.query.filter_by(food_item=item).first():
                db.session.add(FoodCounter(food_item=item, count=0))
        db.session.commit()

def refresh_access_token():
    logging.info("Refreshing Fitbit access token...")
    url = "https://api.fitbit.com/oauth2/token"
    headers = {
        "Authorization": f"Basic {requests.auth._basic_auth_str(os.getenv('FITBIT_CLIENT_ID'), os.getenv('FITBIT_CLIENT_SECRET'))}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": os.getenv('FITBIT_REFRESH_TOKEN')
    }
    try:
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            tokens = response.json()
            os.environ['FITBIT_ACCESS_TOKEN'] = tokens['access_token']
            os.environ['FITBIT_REFRESH_TOKEN'] = tokens['refresh_token']
            logging.info("Access token refreshed successfully.")
            return tokens['access_token']
        else:
            logging.error(f"Failed to refresh token: {response.status_code} {response.text}")
    except Exception as e:
        logging.exception("Exception occurred while refreshing access token.")
    return os.getenv('FITBIT_ACCESS_TOKEN')

def fetch_food_logs():
    logging.info("Starting fetch_food_logs job...")
    try:
        access_token = refresh_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}
        today = datetime.utcnow().date()
        start_date = datetime(today.year if today.month >= 9 else today.year - 1, 9, 1).date()
        current_date = start_date
        food_counts = {item: 0 for item in FOOD_ITEMS}

        while current_date <= today:
            url = f"https://api.fitbit.com/1/user/-/foods/log/date/{current_date}.json"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                logs = response.json().get('foods', [])
                for log in logs:
                    name = log.get('name', '')
                    for item in FOOD_ITEMS:
                        if item.lower() in name.lower():
                            food_counts[item] += 1
            else:
                logging.warning(f"Failed to fetch logs for {current_date}: {response.status_code}")
            current_date += timedelta(days=1)

        with app.app_context():
            for item, count in food_counts.items():
                record = FoodCounter.query.filter_by(food_item=item).first()
                if record:
                    record.count = count
            db.session.commit()
        logging.info("fetch_food_logs job completed successfully.")
    except Exception as e:
        logging.exception("Exception occurred during fetch_food_logs job.")

@app.route('/')
def index():
    counters = FoodCounter.query.all()
    return render_template('index.html', counters=counters)

@app.route('/api/counters')
def api_counters():
    counters = FoodCounter.query.all()
    return jsonify({counter.food_item: counter.count for counter in counters})

# Scheduler setup
def start_scheduler():
    scheduler = BackgroundScheduler(timezone='UTC')
    scheduler.add_job(fetch_food_logs, CronTrigger(hour='4,16', minute=0))
    scheduler.start()
    logging.info("Scheduler started with jobs at 4am and 4pm GMT.")

# Initialize everything
init_db()
start_scheduler()