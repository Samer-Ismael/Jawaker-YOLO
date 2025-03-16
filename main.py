import os
import time
import psutil
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


@app.route('/cards')
def get_cards():
    return jsonify(updating_list())


@app.route('/picture')
def get_picture():
    picture_path = os.path.join('frontend', 'live_view.png')
    if not os.path.exists(picture_path):
        return "Image not found", 404
    return send_file(picture_path, mimetype='image/png')


@app.route('/health')
def get_health():
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get application specific info
        frontend_img_exists = os.path.exists(os.path.join('frontend', 'live_view.png'))
        
        return jsonify({
            'status': 'healthy',
            'timestamp': time.time(),
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent
            },
            'app': {
                'frontend_image_exists': frontend_img_exists,
                'frontend_image_last_modified': os.path.getmtime(os.path.join('frontend', 'live_view.png')) if frontend_img_exists else None
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': time.time()
        }), 500


if __name__ == '__main__':
    # Ensure frontend directory exists
    os.makedirs('frontend', exist_ok=True)
    app.run(host='0.0.0.0', port=5001, debug=True)
