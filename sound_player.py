import numpy as np
import pyaudio
import threading
import time

class SoundPlayer:
    def __init__(self, config):
        self.config = config
        self.audio = None
        self.stream = None
        self.is_playing = False
        self.current_sound = None
        self.volume = 0.5
        self.play_thread = None

        self.initialize_audio()

    def initialize_audio(self):
        """Initialize audio output"""
        print("🔊 Initializing sound player")
        try:
            self.audio = pyaudio.PyAudio()
            print("✅ Sound player initialized")
        except Exception as e:
            print(f"❌ Sound player error: {e}")
            self.audio = None

    def generate_white_noise(self, duration=1.0):
        """Beyaz gürültü üret"""
        sample_rate = 44100
        samples = int(sample_rate * duration)
        noise = np.random.uniform(-1, 1, samples)
        return (noise * 32767 * self.volume).astype(np.int16)

    def generate_pink_noise(self, duration=1.0):
        """Pembe gürültü üret"""
        sample_rate = 44100
        samples = int(sample_rate * duration)

        # Pink noise filter
        white = np.random.uniform(-1, 1, samples)
        b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
        a = [1, -2.494956002, 2.017265875, -0.522189400]

        # Simple approximation
        pink = np.zeros(samples)
        for i in range(len(b)):
            if i < len(white):
                pink += b[i] * np.roll(white, i)

        pink = pink / np.max(np.abs(pink))
        return (pink * 32767 * self.volume).astype(np.int16)

    def generate_shush(self, duration=1.0):
        """Pış pış sesi üret"""
        sample_rate = 44100
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples)

        # Modulated noise
        carrier = 2000 + 200 * np.sin(2 * np.pi * 3 * t)
        noise = np.random.uniform(-1, 1, samples)

        # Apply envelope
        envelope = 0.5 + 0.5 * np.sin(2 * np.pi * 3 * t)
        shush = noise * envelope * 0.3

        return (shush * 32767 * self.volume).astype(np.int16)

    def generate_heartbeat(self, duration=1.0):
        """Kalp atışı üret"""
        sample_rate = 44100
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples)

        bpm = 70
        beat_freq = bpm / 60.0

        # Two beats (lub-dub)
        beat1 = np.sin(2 * np.pi * 80 * t) * np.exp(-10 * t)
        beat2 = np.sin(2 * np.pi * 60 * (t - 0.15)) * np.exp(-10 * (t - 0.15))
        beat2[t < 0.15] = 0

        heartbeat = beat1 + beat2
        heartbeat = np.tile(heartbeat[:int(sample_rate/beat_freq)], int(beat_freq * duration) + 1)[:samples]

        return (heartbeat * 32767 * self.volume * 0.5).astype(np.int16)

    def generate_rain(self, duration=1.0):
        """Yağmur sesi üret"""
        sample_rate = 44100
        samples = int(sample_rate * duration)

        # Filtered white noise for rain
        noise = np.random.uniform(-1, 1, samples)

        # Low-pass filter approximation
        filtered = np.convolve(noise, np.ones(20)/20, mode='same')
        filtered = filtered / np.max(np.abs(filtered))

        return (filtered * 32767 * self.volume * 0.7).astype(np.int16)

    def generate_ocean(self, duration=1.0):
        """Okyanus dalgası üret"""
        sample_rate = 44100
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples)

        # Low frequency oscillation with noise
        wave = np.sin(2 * np.pi * 0.3 * t) * 0.5
        noise = np.random.uniform(-0.2, 0.2, samples)

        ocean = wave + noise
        ocean = ocean / np.max(np.abs(ocean))

        return (ocean * 32767 * self.volume * 0.6).astype(np.int16)

    def _play_loop(self, sound_type):
        """Ses çalma döngüsü"""
        if not self.audio:
            print("❌ Audio not initialized")
            return

        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                output=True
            )

            print(f"🎵 Playing: {sound_type}")

            while self.is_playing and self.current_sound == sound_type:
                # Generate 1 second of audio
                if sound_type == 'whitenoise':
                    audio_data = self.generate_white_noise(1.0)
                elif sound_type == 'pinknoise':
                    audio_data = self.generate_pink_noise(1.0)
                elif sound_type == 'shush':
                    audio_data = self.generate_shush(1.0)
                elif sound_type == 'heartbeat':
                    audio_data = self.generate_heartbeat(1.0)
                elif sound_type == 'rain':
                    audio_data = self.generate_rain(1.0)
                elif sound_type == 'ocean':
                    audio_data = self.generate_ocean(1.0)
                else:
                    break

                # Play audio
                if self.is_playing:
                    self.stream.write(audio_data.tobytes())

            # Temiz kapatma
            if self.stream:
                if self.stream.is_active():
                    self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            print("⏹️ Sound loop ended")

        except Exception as e:
            print(f"❌ Playback error: {e}")
            self.is_playing = False
            if self.stream:
                try:
                    self.stream.close()
                except:
                    pass
                self.stream = None

    def play(self, sound_type):
        """Ses çalmaya başla"""
        # Önceki sesi temizce durdur
        if self.is_playing:
            print(f"Stopping previous sound...")
            self.stop()
            time.sleep(0.5)  # ALSA'nın temizlenmesini bekle

        self.current_sound = sound_type
        self.is_playing = True
        self.play_thread = threading.Thread(target=self._play_loop, args=(sound_type,), daemon=True)
        self.play_thread.start()

    def stop(self):
        """Sesi durdur"""
        self.is_playing = False

        # Thread'in bitmesini bekle
        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join(timeout=1.0)

        # Stream'i temizle
        if self.stream:
            try:
                if self.stream.is_active():
                    self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                print(f"Stream close error: {e}")
            finally:
                self.stream = None

        self.current_sound = None
        print("⏹️ Sound stopped cleanly")

    def set_volume(self, volume):
        """Ses seviyesini ayarla (0.0 - 1.0)"""
        self.volume = max(0.0, min(1.0, volume))

    def get_status(self):
        """Mevcut durumu al"""
        return {
            'is_playing': self.is_playing,
            'current_sound': self.current_sound,
            'volume': int(self.volume * 100)
        }

    def cleanup(self):
        """Temizlik"""
        self.stop()
        if self.audio:
            self.audio.terminate()
