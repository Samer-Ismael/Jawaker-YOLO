import os
import time
from flask import Flask, jsonify, send_from_directory, send_file
from flask_cors import CORS
from detecting import updating_list

app = Flask(__name__)
CORS(app)
frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')


@app.route('/')
def index():
    return send_file(os.path.join(frontend_dir, 'index.html'))


@app.route('/<path:filename>')
def serve_static(filename):
    # Serve static files (CSS, JavaScript, etc.) from the frontend directory
    return send_from_directory(frontend_dir, filename)


@app.route('/cards', methods=['GET'])
def get_detected_cards():
    updated_list = updating_list()
    return jsonify({'detected_cards': updated_list})


@app.route('/picture')
def get_picture():
    # Set the path to the picture here
    picture_path = "cropped_screenshot.png"

    return send_file(picture_path, mimetype='image/png')


if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')