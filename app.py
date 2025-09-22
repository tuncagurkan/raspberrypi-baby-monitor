#!/usr/bin/env python3
from flask import Flask, render_template, Response, jsonify, request
from flask_socketio import SocketIO, emit
import threading
import time
import json
from datetime import datetime

from camera_stream import CameraStream
from config import Config

class BabyMonitorApp:
    def __init__(self):
        print("🍼 Baby Monitor starting")
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'baby_monitor_secret'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        print("🍼 before config")
        self.config = Config()
        self.camera = CameraStream(self.config)
        
        print("🍼 before setups")
        self.connected_clients = 0
        self.setup_routes()
        self.setup_socketio()
        self.start_background_tasks()
        print("🍼 setup done")
    
    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('index.html')
        
        @self.app.route('/video_feed')
        def video_feed():
            print("Video feed requested")
            return Response(
                self.camera.generate_frames(),
                mimetype='multipart/x-mixed-replace; boundary=frame'
            )
        
        @self.app.route('/api/status')
        def get_status():
            print("Status requested")
            return jsonify({
                'camera_active': self.camera.is_active(),
                'connected_clients': self.connected_clients,
                'camera_fps': self.camera.get_fps(),
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/camera/settings', methods=['POST'])
        def update_camera_settings():
            print("Camera settings update requested")
            data = request.get_json()
            self.camera.update_settings(data)
            return jsonify({'status': 'success'})
    
    def setup_socketio(self):
        @self.socketio.on('connect')
        def on_connect():
            self.connected_clients += 1
            emit('status', {'connected_clients': self.connected_clients}, broadcast=True)
            print(f"İstemci bağlandı. Toplam: {self.connected_clients}")
        
        @self.socketio.on('disconnect')
        def on_disconnect():
            self.connected_clients -= 1
            emit('status', {'connected_clients': self.connected_clients}, broadcast=True)
            print(f"İstemci ayrıldı. Toplam: {self.connected_clients}")
        
        @self.socketio.on('request_status')
        def handle_status_request():
            status = self.get_current_status()
            emit('status_update', status)
    
    def start_background_tasks(self):
        # Durum güncellemelerini broadcast et
        def broadcast_status():
            while True:
                if self.connected_clients > 0:
                    status = self.get_current_status()
                    self.socketio.emit('status_update', status)
                time.sleep(2)  # Her 2 saniyede bir güncelle
        
        status_thread = threading.Thread(target=broadcast_status, daemon=True)
        status_thread.start()
    
    def get_current_status(self):
        return {
            'camera_fps': self.camera.get_fps(),
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
    
    def run(self):
        print("🍼 Baby Monitor başlatılıyor...")
        print(f"Web arayüzü: http://localhost:{self.config.WEB_PORT}")
        self.socketio.run(
            self.app, 
            host='localhost', 
            port=self.config.WEB_PORT,
            debug=False,
            allow_unsafe_werkzeug=True
        )

if __name__ == '__main__':
    monitor = BabyMonitorApp()
    monitor.run()