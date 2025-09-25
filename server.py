from flask import Flask, send_from_directory, redirect
from apscheduler.schedulers.background import BackgroundScheduler
import datetime

app = Flask(__name__, static_folder='public')

# Route to serve iframe.html
@app.route('/')
def home():
    return redirect('/public/iframe.html')

@app.route('/public/<path:filename>')
def serve_public(filename):
    return send_from_directory(app.static_folder, filename)

# Dummy refresh route
@app.route('/refresh-count')
def refresh_count():
    # Placeholder for actual refresh logic
    return "Counters refreshed at " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Schedule daily refresh at 4am GMT
def scheduled_refresh():
    print("Scheduled refresh triggered at", datetime.datetime.utcnow())

scheduler = BackgroundScheduler(timezone="UTC")
scheduler.add_job(scheduled_refresh, 'cron', hour=4, minute=0)
scheduler.start()

if __name__ == '__main__':
    app.run()
