#!/usr/bin/env python3
from flask import Flask, render_template, Response, jsonify, request
from flask_socketio import SocketIO, emit
import threading
import time
import json
from datetime import datetime

from camera_stream import CameraStream
from audio_stream import AudioStream
from sound_player import SoundPlayer
from config import Config
from ip_registration_service import IPRegistrationService

class BabyMonitorApp:
    def __init__(self):
        print("🍼 Baby Monitor starting")
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'baby_monitor_secret'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        print("🍼 before config")
        self.config = Config()

        # Initialize IP registration
#        print("🍼 Initializing IP registration...")
#        self.ip_service = IPRegistrationService(self.config)
#        self.ip_service.initialize()

        self.camera = CameraStream(self.config)
        self.audio = AudioStream(self.config)
        self.sound_player = SoundPlayer(self.config)

        # Hareket algılama callback'i ayarla
        self.camera.set_motion_callback(self.on_motion_detected)

        # Ses algılama callback'i (mikrofon yoksa atlanır)
        if hasattr(self.audio, 'set_sound_callback'):
            self.audio.set_sound_callback(self.on_sound_detected)

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

        @self.app.route('/audio_feed')
        def audio_feed():
            print("Audio feed requested")
            return Response(
                self.audio.generate_audio(),
                mimetype='audio/x-raw'
            )
        
        @self.app.route('/api/status')
        def get_status():
            print("Status requested")
            return jsonify({
                'camera_active': self.camera.is_active(),
                'audio_active': self.audio.is_active(),
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

        @self.app.route('/api/motion/toggle', methods=['POST'])
        def toggle_motion_detection():
            """Hareket algılamayı aç/kapa"""
            current_state = self.config.MOTION_DETECTION_ENABLED
            self.config.MOTION_DETECTION_ENABLED = not current_state
            return jsonify({
                'status': 'success',
                'motion_enabled': self.config.MOTION_DETECTION_ENABLED
            })

        @self.app.route('/api/motion/status', methods=['GET'])
        def get_motion_status():
            """Hareket algılama durumunu al"""
            return jsonify({
                'motion_enabled': self.config.MOTION_DETECTION_ENABLED
            })

        @self.app.route('/api/nightvision/toggle', methods=['POST'])
        def toggle_night_vision():
            """Gece görüşünü aç/kapa"""
            current_state = self.config.NIGHT_VISION_ENABLED
            self.config.NIGHT_VISION_ENABLED = not current_state
            return jsonify({
                'status': 'success',
                'night_vision_enabled': self.config.NIGHT_VISION_ENABLED
            })

        @self.app.route('/api/nightvision/status', methods=['GET'])
        def get_night_vision_status():
            """Gece görüşü durumunu al"""
            return jsonify({
                'night_vision_enabled': self.config.NIGHT_VISION_ENABLED
            })

        @self.app.route('/api/sound/play', methods=['POST'])
        def play_sound():
            """Sakinleştirici ses çal (Raspberry Pi hoparlöründen)"""
            data = request.get_json()
            sound_type = data.get('sound_type')

            if not sound_type:
                return jsonify({'status': 'error', 'message': 'sound_type required'}), 400

            self.sound_player.play(sound_type)
            return jsonify({
                'status': 'success',
                'sound_type': sound_type
            })

        @self.app.route('/api/sound/stop', methods=['POST'])
        def stop_sound():
            """Sesi durdur"""
            self.sound_player.stop()
            return jsonify({'status': 'success'})

        @self.app.route('/api/sound/volume', methods=['POST'])
        def set_volume():
            """Ses seviyesini ayarla"""
            data = request.get_json()
            volume = data.get('volume', 50) / 100.0
            self.sound_player.set_volume(volume)
            return jsonify({
                'status': 'success',
                'volume': int(volume * 100)
            })

        @self.app.route('/api/sound/status', methods=['GET'])
        def get_sound_status():
            """Ses durumunu al"""
            return jsonify(self.sound_player.get_status())
    
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
            'audio_active': self.audio.is_active(),
            'motion_detected': self.camera.is_motion_detected(),
            'motion_enabled': self.config.MOTION_DETECTION_ENABLED,
            'night_vision_enabled': self.config.NIGHT_VISION_ENABLED,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }

    def on_motion_detected(self, motion_percentage):
        """Hareket algılandığında çağrılır"""
        print(f"🚨 Hareket bildirimi gönderiliyor! (%{motion_percentage:.2f})")
        self.socketio.emit('motion_alert', {
            'motion_percentage': round(motion_percentage, 2),
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })
    
    def run(self):
        print("🍼 Baby Monitor başlatılıyor...")
        print(f"Web arayüzü: http://0.0.0.0:{self.config.WEB_PORT}")
        self.socketio.run(
            self.app, 
            host='0.0.0.0', 
            port=self.config.WEB_PORT,
            debug=False,
            allow_unsafe_werkzeug=True
        )

if __name__ == '__main__':
    monitor = BabyMonitorApp()
    monitor.run()