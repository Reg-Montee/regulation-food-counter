# Regulation Food Counter

This Flask app tracks the number of times a preauthorized Fitbit user logs Regulation Hotdog, Regulation Burger, and Regulation Apple. It displays counters in a styled iframe and updates data twice daily.

## Features

- OAuth2 authorization with Fitbit API
- Persistent food log storage in SQLite
- Daily updates at 4am and 4pm GMT via Heroku Scheduler
- Styled iframe display of counters

## Deployment

1. Set up a Heroku app and connect this GitHub repo.
2. Add Config Vars:
   - `FITBIT_CLIENT_ID`
   - `FITBIT_CLIENT_SECRET`
   - `FITBIT_REDIRECT_URI`
   - `FITBIT_AUTH_HEADER`
   - `FITBIT_ACCESS_TOKEN`
3. Use Heroku Scheduler to hit `/update` twice daily.

## Styling

- Font: Helvetica Bold
- Background: #FEFEFE
- Container: #000000 with rounded corners
- Counter Circles: #FEFEFE
- Title Text: #FEFEFE
- Counter Text: #000000
