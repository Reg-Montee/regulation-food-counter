import os
import logging
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console (Heroku logs)
        logging.FileHandler("scheduler.log")  # Local file (optional)
    ]
)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///food_counter.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

FOOD_ITEMS = ['Regulation Hotdog', 'Regulation Burger', 'Regulation Apple']

class FoodCounter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    food_item = db.Column(db.String(50), unique=True, nullable=False)
    count = db.Column(db.Integer, default=0)

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
