#!/usr/bin/env python3
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import json
from datetime import datetime

class WebRTCBabyMonitor:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'baby_monitor_webrtc'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        self.active_connections = {}
        self.setup_routes()
        self.setup_webrtc_signaling()
    
    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('webrtc_index.html')
        
        @self.app.route('/test')
        def test():
            return "WebRTC Server çalışıyor! ✅"
    
    def setup_webrtc_signaling(self):
        @self.socketio.on('connect')
        def on_connect():
            print(f"✅ İstemci bağlandı: {request.sid}")
            emit('connected', {'status': 'connected'})
        
        @self.socketio.on('disconnect')
        def on_disconnect():
            print(f"❌ İstemci ayrıldı: {request.sid}")
        
        @self.socketio.on('offer')
        def handle_offer(data):
            print("📤 WebRTC Offer alındı")
            emit('offer', data, broadcast=True, include_self=False)
        
        @self.socketio.on('answer')
        def handle_answer(data):
            print("📥 WebRTC Answer alındı") 
            emit('answer', data, broadcast=True, include_self=False)
        
        @self.socketio.on('ice_candidate')
        def handle_ice_candidate(data):
            print("🧊 ICE Candidate alındı")
            emit('ice_candidate', data, broadcast=True, include_self=False)
    
    def run(self):
        print("🍼 WebRTC Baby Monitor başlatılıyor...")
        print(f"🌐 Test için: http://0.0.0.0:5000/test")
        print(f"📹 WebRTC için: http://0.0.0.0:5000")
        self.socketio.run(
            self.app,
            host='0.0.0.0', 
            port=5000,
            debug=True
        )

if __name__ == '__main__':
    monitor = WebRTCBabyMonitor()
    monitor.run()