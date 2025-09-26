# Regulation Food Counter App

This Flask app tracks how many times a Fitbit user has logged eating:
- Regulation Hotdog
- Regulation Burger
- Regulation Apple

## Features
- Fitbit OAuth2 login
- User-specific food tracking
- Scheduled updates at 4am and 4pm GMT
- Manual refresh and API access

## Setup
1. Set Heroku config vars:
   - `FITBIT_CLIENT_ID`
   - `FITBIT_CLIENT_SECRET`
   - `FITBIT_REDIRECT_URI`
   - `FLASK_SECRET_KEY`

2. Deploy to Heroku via GitHub.

## Routes
- `/login`: Start Fitbit login
- `/callback`: Handle Fitbit redirect
- `/`: Show counters
- `/manual-refresh`: Trigger update
- `/api/counters`: Get counter data
