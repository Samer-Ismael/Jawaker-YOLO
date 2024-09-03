import os
import threading
import time

from flask import Flask, jsonify, send_from_directory, send_file
from flask_cors import CORS

from detecting import updating_list

app = Flask(__name__)
CORS(app)
frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')

detected_cards = []

def background_update():
    global detected_cards
    while True:
        detected_cards = updating_list()
        time.sleep(2)

@app.route('/')
def index():
    return send_file(os.path.join(frontend_dir, 'index.html'))

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(frontend_dir, filename)

@app.route('/cards', methods=['GET'])
def get_detected_cards():
    global detected_cards
    return jsonify({'detected_cards': detected_cards})

@app.route('/picture')
def get_picture():
    picture_path = "cropped_screenshot.png"
    return send_file(picture_path, mimetype='image/png')

if __name__ == '__main__':
    update_thread = threading.Thread(target=background_update, daemon=True)
    update_thread.start()
    app.run(debug=True, port=5001, host='0.0.0.0')
