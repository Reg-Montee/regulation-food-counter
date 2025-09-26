import os
import logging
from flask import Flask, redirect, request, session, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import requests

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default_secret_key")

db_url = os.environ.get('DATABASE_URL', 'sqlite:///food_counter.db')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

FOOD_ITEMS = ['Regulation Hotdog', 'Regulation Burger', 'Regulation Apple']

class UserToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), unique=True, nullable=False)
    access_token = db.Column(db.String(500))
    refresh_token = db.Column(db.String(500))

class FoodCounter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    food_item = db.Column(db.String(50), nullable=False)
    count = db.Column(db.Integer, default=0)

with app.app_context():
    db.create_all()

def refresh_access_token(user_token):
    url = "https://api.fitbit.com/oauth2/token"
    headers = {
        "Authorization": f"Basic {requests.auth._basic_auth_str(os.getenv('FITBIT_CLIENT_ID'), os.getenv('FITBIT_CLIENT_SECRET'))}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": user_token.refresh_token
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        tokens = response.json()
        user_token.access_token = tokens['access_token']
        user_token.refresh_token = tokens['refresh_token']
        db.session.commit()
        return tokens['access_token']
    return user_token.access_token

def fetch_food_logs(user_token):
    access_token = refresh_access_token(user_token)
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
        current_date += timedelta(days=1)

    for item, count in food_counts.items():
        record = FoodCounter.query.filter_by(user_id=user_token.user_id, food_item=item).first()
        if record:
            record.count = count
        else:
            db.session.add(FoodCounter(user_id=user_token.user_id, food_item=item, count=count))
    db.session.commit()

def scheduled_job():
    with app.app_context():
        users = UserToken.query.all()
        for user in users:
            fetch_food_logs(user)

scheduler = BackgroundScheduler(timezone='UTC')
scheduler.add_job(scheduled_job, CronTrigger(hour='4,16', minute=0))
scheduler.start()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')
    counters = FoodCounter.query.filter_by(user_id=session['user_id']).all()
    return render_template('index.html', counters=counters)

@app.route('/login')
def login():
    client_id = os.getenv('FITBIT_CLIENT_ID')
    redirect_uri = os.getenv('FITBIT_REDIRECT_URI')
    scope = 'nutrition'
    return redirect(f"https://www.fitbit.com/oauth2/authorize?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&expires_in=604800")

@app.route('/callback')
def callback():
    code = request.args.get('code')
    redirect_uri = os.getenv('FITBIT_REDIRECT_URI')
    client_id = os.getenv('FITBIT_CLIENT_ID')
    client_secret = os.getenv('FITBIT_CLIENT_SECRET')

    headers = {
        "Authorization": f"Basic {requests.auth._basic_auth_str(client_id, client_secret)}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "client_id": client_id,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
        "code": code
    }

    response = requests.post("https://api.fitbit.com/oauth2/token", headers=headers, data=data)

    if response.status_code == 200:
        tokens = response.json()
        user_id = tokens['user_id']
        session['user_id'] = user_id

        # Save tokens to database
        user_token = UserToken.query.filter_by(user_id=user_id).first()
        if user_token:
            user_token.access_token = tokens['access_token']
            user_token.refresh_token = tokens['refresh_token']
        else:
            db.session.add(UserToken(user_id=user_id, access_token=tokens['access_token'], refresh_token=tokens['refresh_token']))
        db.session.commit()

        fetch_food_logs(UserToken.query.filter_by(user_id=user_id).first())
        return redirect('/')
    else:
        logging.error(f"Fitbit token exchange failed: {response.status_code} - {response.text}")
        return f"Authorization failed: {response.status_code} - {response.text}", 400

@app.route('/manual-refresh')
def manual_refresh():
    if 'user_id' not in session:
        return redirect('/login')
    user_token = UserToken.query.filter_by(user_id=session['user_id']).first()
    fetch_food_logs(user_token)
    return "Manual refresh triggered.", 200

@app.route('/api/counters')
def api_counters():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    counters = FoodCounter.query.filter_by(user_id=session['user_id']).all()
    return jsonify({counter.food_item: counter.count for counter in counters})

if __name__ == '__main__':
    app.run()
