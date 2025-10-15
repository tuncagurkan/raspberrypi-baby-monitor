import pyaudio

class Config:
    # Web Server
    WEB_PORT = 5000

    # API Server Configuration
    API_BASE_URL = 'http://localhost:8080'
    DEVICE_ID = 'baby-monitor-pi'
    DEVICE_AUTH_KEY = 'e6a1d40a42f6dd017cdc7735176f65294ff7230a93d4e21597c7e5b0f26075ae'

    # Kamera ayarları
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    CAMERA_FPS = 25

    # Audio settings
    AUDIO_FORMAT = pyaudio.paInt16  # 16-bit audio
    AUDIO_CHANNELS = 1  # Mono
    AUDIO_RATE = 16000  # 16kHz sample rate (good for voice)
    AUDIO_CHUNK = 1024  # Frames per buffer
    AUDIO_DEVICE_INDEX = None  # None = default device
    
    # İleride kullanılabilir (şimdilik comment)
    # # Hareket tespiti
    # MOTION_THRESHOLD = 1.0  # %1 hareket threshold
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