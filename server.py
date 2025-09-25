from flask import Flask, send_from_directory, redirect
from apscheduler.schedulers.background import BackgroundScheduler
import datetime

app = Flask(__name__, static_folder='public')

@app.route('/')
def home():
    return redirect('/public/iframe.html')

@app.route('/public/<path:filename>')
def serve_public(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/refresh-count')
def refresh_count():
    # Placeholder for manual refresh logic
    return "Counters refreshed manually."

def scheduled_refresh():
    # Placeholder for scheduled refresh logic
    print("Scheduled refresh at", datetime.datetime.utcnow())

# Schedule daily refresh at 4am GMT
scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_refresh, 'cron', hour=4, minute=0)
scheduler.start()

if __name__ == '__main__':
    app.run()
