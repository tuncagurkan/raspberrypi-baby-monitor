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

        # Hareket algılama (basit frame difference)
        self.motion_detected = False
        self.motion_callback = None  # Hareket algılandığında çağrılacak callback
        self.motion_frame_counter = 0  # Performans için frame atlama sayacı
        self.motion_boxes = []  # Hareket algılanan bölgelerin koordinatları
        self.prev_frame = None  # Önceki frame (frame difference için)
        
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
        # Gece görüşü işleme
        if self.config.NIGHT_VISION_ENABLED:
            frame = self._apply_night_vision(frame)

        # Hareket tespiti (performans için her N frame'de bir)
        if self.config.MOTION_DETECTION_ENABLED:
            self.motion_frame_counter += 1
            if self.motion_frame_counter >= self.config.MOTION_CHECK_INTERVAL:
                self._detect_motion(frame)
                self.motion_frame_counter = 0

        # Frame üzerinde bilgileri göster
        frame_with_info = self._add_overlay_info(frame)

        return frame_with_info
    
    def _apply_night_vision(self, frame):
        """Gece görüşü efekti uygula (yazılımsal)"""
        # Histogram eşitleme (CLAHE - Contrast Limited Adaptive Histogram Equalization)
        # Gri tonlamaya çevir
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # CLAHE uygula (performanslı)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Parlaklık ve kontrast ayarla
        alpha = 1.0 + (self.config.NIGHT_VISION_CONTRAST / 100.0)  # Kontrast
        beta = self.config.NIGHT_VISION_BRIGHTNESS  # Parlaklık
        enhanced = cv2.convertScaleAbs(enhanced, alpha=alpha, beta=beta)

        # Tekrar BGR'ye çevir (gece görüşü yeşil efekt için)
        night_vision_frame = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

        # Yeşil ton ekle (opsiyonel - klasik gece görüşü görünümü)
        night_vision_frame[:, :, 0] = night_vision_frame[:, :, 0] * 0.3  # Mavi azalt
        night_vision_frame[:, :, 2] = night_vision_frame[:, :, 2] * 0.3  # Kırmızı azalt
        night_vision_frame[:, :, 1] = night_vision_frame[:, :, 1] * 1.2  # Yeşil artır

        return night_vision_frame

    def _detect_motion(self, frame):
        """Hareket tespiti - ULTRA BASIT (frame difference only)"""
        # Çok küçük frame (performans)
        small_frame = cv2.resize(frame, (160, 120))

        # Gri tonlama
        gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)

        # Basit blur
        gray = cv2.GaussianBlur(gray, (5, 5), 0)

        # İlk frame ise kaydet ve çık
        if self.prev_frame is None:
            self.prev_frame = gray
            return

        # Frame farkı (en basit yöntem)
        frame_diff = cv2.absdiff(self.prev_frame, gray)

        # Threshold
        _, thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)

        # Hareket yüzdesi
        motion_pixels = cv2.countNonZero(thresh)
        total_pixels = thresh.shape[0] * thresh.shape[1]
        motion_percentage = (motion_pixels / total_pixels) * 100

        # Hareket tespit
        was_detected = self.motion_detected
        self.motion_detected = motion_percentage > self.config.MOTION_THRESHOLD

        # Bounding box yok (çok yavaş - atla)
        self.motion_boxes = []

        # Önceki frame'i güncelle
        self.prev_frame = gray

        # Callback
        if self.motion_detected and not was_detected and self.motion_callback:
            self.motion_callback(motion_percentage)
    
    def _add_overlay_info(self, frame):
        """Frame üzerine bilgi overlay'i ekle (minimal - performans)"""
        # Frame kopyalama bile CPU yer - direkt üzerine yaz

        # Sadece FPS (küçük font - performans)
        cv2.putText(frame, f"FPS:{self.fps}", (5, 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Hareket durumu (sadece aktifse)
        if self.config.MOTION_DETECTION_ENABLED and self.motion_detected:
            # Basit "M" harfi (performans)
            cv2.putText(frame, "M", (5, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

            # Hareket bölgeleri (varsa)
            for (x, y, w, h) in self.motion_boxes:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 1)

        return frame
    
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
                # JPEG encode (düşük kalite - performans)
                ret, buffer = cv2.imencode('.jpg', self.current_frame,
                                         [cv2.IMWRITE_JPEG_QUALITY, 60])  # 85 -> 60 (daha hızlı)
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.01)  # Minimal delay
    
    def update_settings(self, settings):
        """Kamera ayarlarını güncelle"""
        if 'brightness' in settings and self.camera:
            self.camera.set(cv2.CAP_PROP_BRIGHTNESS, settings['brightness'])
        if 'contrast' in settings and self.camera:
            self.camera.set(cv2.CAP_PROP_CONTRAST, settings['contrast'])

    def is_active(self):
        """Kamera aktif mi?"""
        return self.camera is not None and self.is_streaming

    def get_fps(self):
        """Mevcut FPS değerini al"""
        return self.fps

    def set_motion_callback(self, callback):
        """Hareket algılandığında çağrılacak callback fonksiyonunu ayarla"""
        self.motion_callback = callback

    def is_motion_detected(self):
        """Hareket algılandı mı?"""
        return self.motion_detected if self.config.MOTION_DETECTION_ENABLED else False
    
    def stop(self):
        """Streaming'i durdur"""
        self.is_streaming = False
        if self.camera:
            self.camera.release()