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
            print("🎤 Audio feed requested")
            return Response(
                self.audio.generate_audio(),
                mimetype='audio/wav'
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

        # ==================== IR-CUT Gece Görüşü API ====================

        @self.app.route('/api/nightvision/status', methods=['GET'])
        def get_night_vision_status():
            """Gece görüşü durumunu al"""
            return jsonify({
                'status': 'success',
                'control_mode': 'auto' if self.config.NIGHT_VISION_AUTO else 'manual',
                'current_mode': self.camera.ir_control.get_current_mode()
            })

        @self.app.route('/api/nightvision/auto', methods=['POST'])
        def set_auto_mode():
            """Otomatik moda geç"""
            self.config.NIGHT_VISION_AUTO = True
            return jsonify({
                'status': 'success',
                'current_mode': self.camera.ir_control.get_current_mode()
            })

        @self.app.route('/api/nightvision/manual', methods=['POST'])
        def set_manual_mode():
            """Manuel moda geç"""
            print("🔧 API /api/nightvision/manual çağrıldı")
            print(f"   NIGHT_VISION_AUTO: {self.config.NIGHT_VISION_AUTO} -> False")
            self.config.NIGHT_VISION_AUTO = False
            print("   ✅ Manuel mod aktif")
            return jsonify({
                'status': 'success',
                'current_mode': self.camera.ir_control.get_current_mode()
            })

        @self.app.route('/api/nightvision/day', methods=['POST'])
        def set_day_mode():
            """Manuel gündüz modu"""
            print(f"🔧 API /api/nightvision/day çağrıldı")
            print(f"   NIGHT_VISION_AUTO: {self.config.NIGHT_VISION_AUTO}")

            if not self.config.NIGHT_VISION_AUTO:
                print("   ☀️ Gündüz moduna geçiliyor...")
                try:
                    self.camera.ir_control.manual_day_mode()
                    print("   ✅ Gündüz modu başarılı")
                    return jsonify({'status': 'success'})
                except Exception as e:
                    print(f"   ❌ Hata: {e}")
                    return jsonify({'status': 'error', 'message': str(e)}), 500
            else:
                print("   ⚠️ Otomatik mod aktif, önce manuel moda geç")
                return jsonify({'status': 'error', 'message': 'Önce manuel moda geçin'}), 400

        @self.app.route('/api/nightvision/night', methods=['POST'])
        def set_night_mode():
            """Manuel gece modu"""
            print(f"🔧 API /api/nightvision/night çağrıldı")
            print(f"   NIGHT_VISION_AUTO: {self.config.NIGHT_VISION_AUTO}")

            if not self.config.NIGHT_VISION_AUTO:
                print("   🌙 Gece moduna geçiliyor...")
                try:
                    self.camera.ir_control.manual_night_mode()
                    print("   ✅ Gece modu başarılı")
                    return jsonify({'status': 'success'})
                except Exception as e:
                    print(f"   ❌ Hata: {e}")
                    return jsonify({'status': 'error', 'message': str(e)}), 500
            else:
                print("   ⚠️ Otomatik mod aktif, önce manuel moda geç")
                return jsonify({'status': 'error', 'message': 'Önce manuel moda geçin'}), 400

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

        @self.app.route('/api/system/shutdown', methods=['POST'])
        def shutdown_system():
            """Sistemi kapat"""
            import subprocess
            try:
                # Raspberry Pi'yi kapat
                subprocess.Popen(['sudo', 'shutdown', 'now'])
                return jsonify({'status': 'success', 'message': 'Sistem kapatılıyor...'})
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @self.app.route('/api/wifi/networks', methods=['GET'])
        def get_wifi_networks():
            """Kayıtlı WiFi ağlarını listele"""
            import subprocess
            try:
                print("\n📶 WiFi ağları sorgulanıyor...")

                # Kayıtlı bağlantıları listele
                result = subprocess.run(
                    ['nmcli', '-t', '-f', 'NAME,TYPE,DEVICE,STATE', 'connection', 'show'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                print(f"🔍 nmcli return code: {result.returncode}")
                print(f"📋 nmcli stdout:\n{result.stdout}")
                print(f"❌ nmcli stderr:\n{result.stderr}")

                networks = []
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    print(f"  Processing line: {line}")
                    parts = line.split(':')
                    print(f"  Parts: {parts}")

                    if len(parts) >= 4 and parts[1] == '802-11-wireless':
                        name = parts[0]
                        device = parts[2]
                        is_active = parts[3] == 'activated'

                        print(f"  ✅ Found WiFi network: {name} (active: {is_active})")

                        # Aktif ağ için sinyal gücü al
                        signal_strength = 0
                        if is_active and device:
                            try:
                                signal_result = subprocess.run(
                                    ['nmcli', '-t', '-f', 'SIGNAL', 'device', 'wifi', 'list', 'ifname', device, '--rescan', 'no'],
                                    capture_output=True,
                                    text=True,
                                    timeout=3
                                )
                                # İlk satırı al (aktif ağ)
                                if signal_result.stdout.strip():
                                    first_line = signal_result.stdout.strip().split('\n')[0]
                                    try:
                                        signal_strength = int(first_line)
                                        print(f"  📡 Signal strength: {signal_strength}%")
                                    except:
                                        print(f"  ⚠️ Could not parse signal: {first_line}")
                            except Exception as sig_err:
                                print(f"  ⚠️ Signal check error: {sig_err}")

                        networks.append({
                            'name': name,
                            'active': is_active,
                            'signal': signal_strength
                        })

                print(f"\n✅ Toplam {len(networks)} WiFi ağı bulundu\n")
                return jsonify({'status': 'success', 'networks': networks})
            except Exception as e:
                print(f"❌ WiFi networks error: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @self.app.route('/api/wifi/connect', methods=['POST'])
        def connect_wifi():
            """Seçilen WiFi ağına bağlan"""
            import subprocess
            data = request.get_json()
            network_name = data.get('network_name')

            if not network_name:
                return jsonify({'status': 'error', 'message': 'network_name required'}), 400

            try:
                # Ağa bağlan
                result = subprocess.run(
                    ['nmcli', 'connection', 'up', network_name],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    return jsonify({'status': 'success', 'message': f'{network_name} ağına bağlanıldı'})
                else:
                    return jsonify({'status': 'error', 'message': result.stderr}), 500
            except subprocess.TimeoutExpired:
                return jsonify({'status': 'error', 'message': 'Bağlantı zaman aşımına uğradı'}), 500
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500
    
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

                    # Ses durumunu ayrıca gönder
                    sound_status = self.sound_player.get_status()
                    self.socketio.emit('sound_status', sound_status)
                time.sleep(1)  # Her 1 saniyede bir güncelle (ses için daha sık)

        status_thread = threading.Thread(target=broadcast_status, daemon=True)
        status_thread.start()
    
    def get_current_status(self):
        return {
            'camera_fps': self.camera.get_fps(),
            'audio_active': self.audio.is_active(),
            'motion_detected': self.camera.is_motion_detected(),
            'motion_enabled': self.config.MOTION_DETECTION_ENABLED,
            'night_vision_auto': self.config.NIGHT_VISION_AUTO,
            'night_vision_mode': self.camera.ir_control.get_current_mode(),
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