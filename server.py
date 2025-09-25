from flask import Flask, send_from_directory, redirect
import os

app = Flask(__name__, static_folder='public')

@app.route('/')
def home():
    return redirect('/public/iframe.html')

@app.route('/public/<path:filename>')
def serve_public(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
