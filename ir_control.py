"""
Arducam Motorized IR-CUT Camera GPIO Control
IR-CUT filter ve IR LED kontrolü
"""

import time

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("⚠️ RPi.GPIO kütüphanesi bulunamadı - GPIO kontrolü devre dışı")


class IRControl:
    """Arducam IR-CUT ve IR LED kontrolü"""

    def __init__(self, config):
        self.config = config
        self.is_night_mode = False
        self.gpio_initialized = False

        if config.GPIO_ENABLED and GPIO_AVAILABLE:
            self._initialize_gpio()
        else:
            print("ℹ️ GPIO kontrolü devre dışı")

    def _initialize_gpio(self):
        """GPIO pinlerini başlat"""
        try:
            # GPIO mod ayarla (BCM numaralandırma)
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)

            # IR-CUT motor pinleri (OUTPUT)
            GPIO.setup(self.config.IR_CUT_DAY_PIN, GPIO.OUT)
            GPIO.setup(self.config.IR_CUT_NIGHT_PIN, GPIO.OUT)

            # IR LED pini (OUTPUT)
            GPIO.setup(self.config.IR_LED_PIN, GPIO.OUT)

            # Başlangıçta gündüz moduna al
            self._set_day_mode()

            self.gpio_initialized = True
            print(f"✅ GPIO başlatıldı - IR-CUT Day:{self.config.IR_CUT_DAY_PIN}, Night:{self.config.IR_CUT_NIGHT_PIN}, LED:{self.config.IR_LED_PIN}")

        except Exception as e:
            print(f"❌ GPIO başlatma hatası: {e}")
            self.gpio_initialized = False

    def _set_day_mode(self):
        """Gündüz modu - IR filtre aktif, IR LED kapalı"""
        print(f"🔧 _set_day_mode çağrıldı (GPIO initialized: {self.gpio_initialized})")

        if not self.gpio_initialized:
            print("⚠️ GPIO başlatılmamış, gündüz modu atlanıyor")
            # GPIO olmasa bile modu değiştir (test için)
            self.is_night_mode = False
            return

        try:
            print(f"   📌 GPIO pinleri:")
            print(f"      IR_CUT_DAY_PIN: {self.config.IR_CUT_DAY_PIN}")
            print(f"      IR_CUT_NIGHT_PIN: {self.config.IR_CUT_NIGHT_PIN}")
            print(f"      IR_LED_PIN: {self.config.IR_LED_PIN}")

            # IR-CUT motoru gündüz pozisyonuna getir
            print("   🔄 IR-CUT DAY -> HIGH, NIGHT -> LOW")
            GPIO.output(self.config.IR_CUT_DAY_PIN, GPIO.HIGH)
            GPIO.output(self.config.IR_CUT_NIGHT_PIN, GPIO.LOW)
            time.sleep(0.5)  # Motor hareket süresi

            # Motor pinlerini kapat (motor sadece anlık sinyal gerektirir)
            print("   🔄 Motor pinleri kapatılıyor")
            GPIO.output(self.config.IR_CUT_DAY_PIN, GPIO.LOW)
            GPIO.output(self.config.IR_CUT_NIGHT_PIN, GPIO.LOW)

            # IR LED'i kapat
            print("   💡 IR LED -> LOW (kapalı)")
            GPIO.output(self.config.IR_LED_PIN, GPIO.LOW)

            self.is_night_mode = False
            print("☀️ Gündüz modu aktif - IR filtre AÇIK, LED KAPALI")

        except Exception as e:
            print(f"❌ Gündüz modu hatası: {e}")
            import traceback
            traceback.print_exc()

    def _set_night_mode(self):
        """Gece modu - IR filtre kapalı, IR LED açık"""
        print(f"🔧 _set_night_mode çağrıldı (GPIO initialized: {self.gpio_initialized})")

        if not self.gpio_initialized:
            print("⚠️ GPIO başlatılmamış, gece modu atlanıyor")
            # GPIO olmasa bile modu değiştir (test için)
            self.is_night_mode = True
            return

        try:
            print(f"   📌 GPIO pinleri:")
            print(f"      IR_CUT_DAY_PIN: {self.config.IR_CUT_DAY_PIN}")
            print(f"      IR_CUT_NIGHT_PIN: {self.config.IR_CUT_NIGHT_PIN}")
            print(f"      IR_LED_PIN: {self.config.IR_LED_PIN}")

            # IR-CUT motoru gece pozisyonuna getir
            print("   🔄 IR-CUT DAY -> LOW, NIGHT -> HIGH")
            GPIO.output(self.config.IR_CUT_DAY_PIN, GPIO.LOW)
            GPIO.output(self.config.IR_CUT_NIGHT_PIN, GPIO.HIGH)
            time.sleep(0.5)  # Motor hareket süresi

            # Motor pinlerini kapat
            print("   🔄 Motor pinleri kapatılıyor")
            GPIO.output(self.config.IR_CUT_DAY_PIN, GPIO.LOW)
            GPIO.output(self.config.IR_CUT_NIGHT_PIN, GPIO.LOW)

            # IR LED'i aç
            print("   💡 IR LED -> HIGH (açık)")
            GPIO.output(self.config.IR_LED_PIN, GPIO.HIGH)

            self.is_night_mode = True
            print("🌙 Gece modu aktif - IR filtre KAPALI, LED AÇIK")

        except Exception as e:
            print(f"❌ Gece modu hatası: {e}")
            import traceback
            traceback.print_exc()

    def auto_switch_mode(self, brightness_level):
        """
        Parlaklığa göre otomatik mod değiştir

        Args:
            brightness_level (float): Görüntü parlaklık seviyesi (0-100)
        """
        if not self.config.NIGHT_VISION_AUTO or not self.gpio_initialized:
            return

        threshold = self.config.NIGHT_VISION_BRIGHTNESS_THRESHOLD

        # Karanlık -> Gece moduna geç
        if brightness_level < threshold and not self.is_night_mode:
            print(f"🔄 Karanlık algılandı (parlaklık: {brightness_level:.1f}%) - Gece moduna geçiliyor...")
            self._set_night_mode()

        # Aydınlık -> Gündüz moduna geç (hysteresis için +10 ekle)
        elif brightness_level > (threshold + 10) and self.is_night_mode:
            print(f"🔄 Aydınlık algılandı (parlaklık: {brightness_level:.1f}%) - Gündüz moduna geçiliyor...")
            self._set_day_mode()

    def manual_day_mode(self):
        """Manuel gündüz modu"""
        self._set_day_mode()

    def manual_night_mode(self):
        """Manuel gece modu"""
        self._set_night_mode()

    def get_current_mode(self):
        """Mevcut modu döndür"""
        return "night" if self.is_night_mode else "day"

    def cleanup(self):
        """GPIO temizle"""
        if self.gpio_initialized:
            try:
                GPIO.cleanup()
                print("🧹 GPIO temizlendi")
            except Exception as e:
                print(f"⚠️ GPIO temizleme hatası: {e}")
