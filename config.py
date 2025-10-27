import pyaudio

class Config:
    # Web Server
    WEB_PORT = 8080

    # API Server Configuration
    API_BASE_URL = 'http://35.158.190.252:8000'
    DEVICE_ID = 'baby-monitor-pi'
    DEVICE_AUTH_KEY = 'e6a1d40a42f6dd017cdc7735176f65294ff7230a93d4e21597c7e5b0f26075ae'

    # Kamera ayarları
    CAMERA_WIDTH = 320  # Düşük çözünürlük (performans için)
    CAMERA_HEIGHT = 240
    CAMERA_FPS = 30

    # Audio settings
    AUDIO_FORMAT = pyaudio.paInt16  # 16-bit audio
    AUDIO_CHANNELS = 1  # Mono
    AUDIO_RATE = 16000  # 16kHz sample rate (good for voice)
    AUDIO_CHUNK = 1024  # Frames per buffer
    AUDIO_DEVICE_INDEX = None  # None = default device

    # Hareket tespiti
    MOTION_THRESHOLD = 0.5  # %0.5 hareket threshold - El ve kafa hareketleri için hassas
    MOTION_DETECTION_ENABLED = False  # PERFORMANS İÇİN KAPALI - Gerekirse açabilirsiniz
    MOTION_CHECK_INTERVAL = 10  # Her 10 frame'de bir (çok daha az CPU)
    # 
    # # Sensör ayarları
    # DHT_PIN = 4  # DHT22 sensör pini
    # 
    # # Ses ayarları
    # SOUND_THRESHOLD = 60  # dB alarm seviyesi
    # 
    # # Uyarı limitleri
    # TEMP_MIN = 18  # °C
    # TEMP_MAX = 26  # °C
    # HUMIDITY_MAX = 70  # %