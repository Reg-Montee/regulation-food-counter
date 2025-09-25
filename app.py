import os
import json
from flask import Flask, render_template, request, redirect
from datetime import datetime
import logging

app = Flask(__name__)
CACHE_FILE = 'food_counts.json'
FOOD_ITEMS = ['Regulation Hotdog', 'Regulation Burger', 'Regulation Apple']

def load_counts():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {item: 0 for item in FOOD_ITEMS}

@app.route('/')
def index():
    counts = load_counts()
    return render_template('index.html', counts=counts)

@app.route('/refresh', methods=['POST'])
def refresh():
    try:
        from update_counts import update_food_counts
        update_food_counts()
    except Exception as e:
        logging.error(f"Manual refresh failed: {e}")
    return redirect('/')
