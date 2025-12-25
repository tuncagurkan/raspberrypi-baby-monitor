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

    # Audio settings - Optimized for better quality
    AUDIO_FORMAT = pyaudio.paInt16  # 16-bit audio
    AUDIO_CHANNELS = 1  # Mono (daha az gürültü, daha stabil)
    AUDIO_RATE = 44100  # 44.1kHz sample rate (daha evrensel ve stabil)
    AUDIO_CHUNK = 2048  # Frames per buffer (daha büyük buffer = daha az cızırtı)
    AUDIO_DEVICE_INDEX = None  # None = default device (USB mikrofon otomatik bulunuyor)

    # Audio processing settings
    AUDIO_NOISE_GATE = 100  # Gürültü eşiği (0-32767, altındaki sesler kesilir)
    AUDIO_NORMALIZE = True  # Ses normalizasyonu (cızırtıyı azaltır)

    # Hareket tespiti
    MOTION_THRESHOLD = 0.5  # %0.5 hareket threshold - El ve kafa hareketleri için hassas
    MOTION_DETECTION_ENABLED = True  # Hareket algılama AÇIK
    MOTION_CHECK_INTERVAL = 10  # Her 10 frame'de bir (çok daha az CPU)

    # Gece görüşü - Arducam Motorized IR-CUT
    NIGHT_VISION_AUTO = True  # Otomatik gece/gündüz geçişi
    NIGHT_VISION_BRIGHTNESS_THRESHOLD = 50  # Gece moduna geçiş eşiği (0-100, düşük = karanlık)

    # Arducam IR-CUT GPIO Pins
    IR_CUT_DAY_PIN = 4      # IR-CUT filtre gündüz modu (IR kapanır)
    IR_CUT_NIGHT_PIN = 17   # IR-CUT filtre gece modu (IR açılır)
    IR_LED_PIN = 5          # IR LED kontrolü

    # GPIO Pin Control
    GPIO_ENABLED = True     # GPIO kontrolü aktif mi?
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