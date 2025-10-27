import cv2
import numpy as np
import threading
import time
from datetime import datetime
import logging

class CameraStream:
    def __init__(self, config):
        self.config = config
        self.camera = None
        self.current_frame = None
        self.is_streaming = False
        self.fps_counter = 0
        self.fps = 0

        # Hareket algılama
        self.motion_detected = False
        self.motion_callback = None  # Hareket algılandığında çağrılacak callback
        self.motion_frame_counter = 0  # Performans için frame atlama sayacı
        self.motion_boxes = []  # Hareket algılanan bölgelerin koordinatları
        if self.config.MOTION_DETECTION_ENABLED:
            self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
                detectShadows=False,  # Shadow detection kapalı (performans)
                varThreshold=25,  # Daha yüksek threshold (performans)
                history=200  # Daha az history (performans)
            )
        
        self.initialize_camera()
        self.start_streaming()
    
    def initialize_camera(self):
        """Kamerayı başlat"""
        print("🍼 Initializing camera")
        try:
            # Raspberry Pi Camera Module için
            self.camera = cv2.VideoCapture(0)
            
            if not self.camera.isOpened():
                raise Exception("Kamera açılamadı!")
            
            # Kamera ayarları
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.CAMERA_WIDTH)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.CAMERA_HEIGHT)
            self.camera.set(cv2.CAP_PROP_FPS, self.config.CAMERA_FPS)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Buffer'ı küçük tut
            
            print(f"✅ Kamera başlatıldı: {self.config.CAMERA_WIDTH}x{self.config.CAMERA_HEIGHT} @ {self.config.CAMERA_FPS}fps")
            
        except Exception as e:
            print(f"❌ Kamera hatası: {e}")
            self.camera = None
    
    def start_streaming(self):
        print("🍼 Starting camera stream")
        """Streaming thread'ini başlat"""
        if self.camera:
            self.is_streaming = True
            self.stream_thread = threading.Thread(target=self._stream_loop, daemon=True)
            self.fps_thread = threading.Thread(target=self._fps_counter, daemon=True)
            self.stream_thread.start()
            self.fps_thread.start()
    
    def _stream_loop(self):
        """Ana streaming döngüsü"""
        while self.is_streaming and self.camera:
            ret, frame = self.camera.read()
            if ret:
                # Frame'i işle
                processed_frame = self._process_frame(frame)
                self.current_frame = processed_frame
                self.fps_counter += 1
            else:
                print("⚠️  Kamera frame okuma hatası")
                time.sleep(0.1)
    
    def _process_frame(self, frame):
        """Frame işleme"""
        # Hareket tespiti (performans için her N frame'de bir)
        if self.config.MOTION_DETECTION_ENABLED:
            self.motion_frame_counter += 1
            if self.motion_frame_counter >= self.config.MOTION_CHECK_INTERVAL:
                self._detect_motion(frame)
                self.motion_frame_counter = 0

        # Frame üzerinde bilgileri göster
        frame_with_info = self._add_overlay_info(frame)

        return frame_with_info
    
    def _detect_motion(self, frame):
        """Hareket tespiti algoritması (optimize edilmiş)"""
        # Frame'i küçült (performans için)
        small_frame = cv2.resize(frame, (320, 240))

        # Ölçek oranını hesapla (bounding box için)
        scale_x = frame.shape[1] / 320
        scale_y = frame.shape[0] / 240

        # Gri tonlama
        gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)

        # Gaussian blur (daha küçük kernel - performans)
        gray = cv2.GaussianBlur(gray, (11, 11), 0)

        # Background subtraction
        fg_mask = self.bg_subtractor.apply(gray)

        # Basit threshold (morfolojik işlemler yavaş)
        _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)

        # Hareket alanını hesapla
        motion_pixels = cv2.countNonZero(fg_mask)
        total_pixels = gray.shape[0] * gray.shape[1]
        motion_percentage = (motion_pixels / total_pixels) * 100

        # Hareket threshold'u
        was_detected = self.motion_detected
        self.motion_detected = motion_percentage > self.config.MOTION_THRESHOLD

        # Hareket bölgelerini bul (sadece hareket varsa)
        self.motion_boxes = []
        if self.motion_detected:
            # Contour bul (küçük frame üzerinde - performans)
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Sadece büyük contour'ları al (gürültü filtreleme)
            for contour in contours:
                if cv2.contourArea(contour) > 500:  # Minimum alan (performans)
                    x, y, w, h = cv2.boundingRect(contour)
                    # Orijinal boyuta ölçeklendir
                    x_scaled = int(x * scale_x)
                    y_scaled = int(y * scale_y)
                    w_scaled = int(w * scale_x)
                    h_scaled = int(h * scale_y)
                    self.motion_boxes.append((x_scaled, y_scaled, w_scaled, h_scaled))

        # Yeni hareket algılandıysa callback'i çağır
        if self.motion_detected and not was_detected and self.motion_callback:
            self.motion_callback(motion_percentage)
            print(f"🔍 Hareket tespit edildi! (%{motion_percentage:.2f})")
    
    def _add_overlay_info(self, frame):
        """Frame üzerine bilgi overlay'i ekle"""
        overlay_frame = frame.copy()
        
        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(overlay_frame, timestamp, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # FPS bilgisi
        cv2.putText(overlay_frame, f"FPS: {self.fps}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Hareket durumu ve bounding box'lar
        if self.config.MOTION_DETECTION_ENABLED and self.motion_detected:
            cv2.putText(overlay_frame, "HAREKET!", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            # Hareket tespit edilen bölgeleri kareye al
            for (x, y, w, h) in self.motion_boxes:
                # Yeşil dikdörtgen çiz
                cv2.rectangle(overlay_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                # Üstüne "HAREKET" etiketi
                cv2.putText(overlay_frame, "HAREKET", (x, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return overlay_frame
    
    def _fps_counter(self):
        """FPS hesaplayıcısı"""
        while self.is_streaming:
            time.sleep(1)
            self.fps = self.fps_counter
            self.fps_counter = 0
    
    def generate_frames(self):
        """Flask streaming için frame generator"""
        while self.is_streaming:
            if self.current_frame is not None:
                # JPEG encode
                ret, buffer = cv2.imencode('.jpg', self.current_frame,
                                         [cv2.IMWRITE_JPEG_QUALITY, 85])
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(1/30)  # 30 FPS max
    
    def update_settings(self, settings):
        print("🍼 Camera settings update requested")
        """Kamera ayarlarını güncelle"""
        if 'brightness' in settings and self.camera:
            self.camera.set(cv2.CAP_PROP_BRIGHTNESS, settings['brightness'])
        if 'contrast' in settings and self.camera:
            self.camera.set(cv2.CAP_PROP_CONTRAST, settings['contrast'])
    
    def is_active(self):
        print("🍼 Checking if camera is active")
        """Kamera aktif mi?"""
        return self.camera is not None and self.is_streaming
    
    def get_fps(self):
        print("🍼 Getting current FPS")
        """Mevcut FPS değerini al"""
        return self.fps

    def set_motion_callback(self, callback):
        """Hareket algılandığında çağrılacak callback fonksiyonunu ayarla"""
        self.motion_callback = callback

    def is_motion_detected(self):
        """Hareket algılandı mı?"""
        return self.motion_detected if self.config.MOTION_DETECTION_ENABLED else False
    
    def stop(self):
        print("🍼 Stopping camera stream")
        """Streaming'i durdur"""
        self.is_streaming = False
        if self.camera:
            self.camera.release()