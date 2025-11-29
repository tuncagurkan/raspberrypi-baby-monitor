import numpy as np
import pyaudio
import threading
import time
import wave
import os

class SoundPlayer:
    def __init__(self, config):
        self.config = config
        self.audio = None
        self.stream = None
        self.is_playing = False
        self.current_sound = None
        self.volume = 0.5
        self.play_thread = None
        self.start_time = None

        self.initialize_audio()

    def initialize_audio(self):
        """Initialize audio output"""
        print("🔊 Initializing sound player")
        try:
            self.audio = pyaudio.PyAudio()

            # Debug: List all audio devices
            print("\n📱 Available audio devices:")
            for i in range(self.audio.get_device_count()):
                info = self.audio.get_device_info_by_index(i)
                print(f"  [{i}] {info['name']} - Output channels: {info['maxOutputChannels']}")
            print()

            print("✅ Sound player initialized")
        except Exception as e:
            print(f"❌ Sound player error: {e}")
            self.audio = None

    def generate_white_noise(self, duration=1.0):
        """Bebek için optimize edilmiş beyaz gürültü (<500Hz ağırlıklı)"""
        sample_rate = 44100
        samples = int(sample_rate * duration)

        # Beyaz gürültü üret
        noise = np.random.uniform(-1, 1, samples)

        # Düşük frekans vurgusu için basit low-pass filter (bebek için)
        # FFT kullanmadan basit moving average
        window_size = int(sample_rate / 500)  # 500Hz kesim
        filtered = np.convolve(noise, np.ones(window_size)/window_size, mode='same')

        # Normalize et ve ses seviyesini düşür (50dB için)
        filtered = filtered / np.max(np.abs(filtered)) * 0.4
        return (filtered * 32767 * self.volume).astype(np.int16)

    def generate_pink_noise(self, duration=1.0):
        """Bebek için pembe gürültü (yağmur/okyanus gibi doğal sesler)"""
        sample_rate = 44100
        samples = int(sample_rate * duration)

        # Pink noise - bass-heavy
        white = np.random.uniform(-1, 1, samples)

        # Pink noise filter (1/f spectrum)
        b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
        a = [1, -2.494956002, 2.017265875, -0.522189400]

        pink = np.zeros(samples)
        for i in range(len(b)):
            if i < len(white):
                pink += b[i] * np.roll(white, i)

        # Normalize ve yumuşat
        pink = pink / np.max(np.abs(pink)) * 0.35
        return (pink * 32767 * self.volume).astype(np.int16)

    def generate_shush(self, duration=1.0):
        """Bebek sakinleştirici pış pış sesi (500-2000Hz, ritmik)"""
        sample_rate = 44100
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples)

        # Band-limited noise (500-2000Hz) - anne/baba sesi taklidi
        noise = np.random.uniform(-1, 1, samples)

        # Low-pass filter (~2000Hz)
        window_size = int(sample_rate / 2000)
        filtered_noise = np.convolve(noise, np.ones(window_size)/window_size, mode='same')

        # Ritmik pulsing (delta frequency ~3Hz - derin uyku frekansı)
        # Yumuşak pulsing
        envelope = 0.6 + 0.4 * np.sin(2 * np.pi * 3 * t)

        shush = filtered_noise * envelope * 0.25  # Daha yumuşak

        return (shush * 32767 * self.volume).astype(np.int16)

    def generate_heartbeat(self, duration=1.0):
        """Anne karnındaki kalp atışı (70 BPM, <250Hz, rahim sesi)"""
        sample_rate = 44100
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples)

        bpm = 70  # Anne kalp atışı
        beat_period = 60.0 / bpm  # 0.857 saniye
        beat_samples = int(sample_rate * beat_period)

        # Tek bir kalp atışı oluştur (lub-dub)
        single_beat_t = np.linspace(0, beat_period, beat_samples)

        # Lub (düşük frekans ~60Hz, kuvvetli)
        lub = np.sin(2 * np.pi * 60 * single_beat_t) * np.exp(-15 * single_beat_t)

        # Dub (daha yüksek ~100Hz, hafif, 0.2 saniye sonra)
        dub_t = single_beat_t - 0.2
        dub = np.sin(2 * np.pi * 100 * dub_t) * np.exp(-20 * dub_t) * 0.6
        dub[dub_t < 0] = 0

        # Combine
        single_beat = lub + dub

        # Rahim yankısı ekle (düşük frekanslı reverb)
        reverb = np.convolve(single_beat, np.exp(-np.linspace(0, 5, 1000)), mode='same') * 0.1
        single_beat = single_beat + reverb

        # Tüm duration için tekrarla
        num_beats = int(duration / beat_period) + 1
        heartbeat = np.tile(single_beat, num_beats)[:samples]

        # Yumuşak ses seviyesi
        return (heartbeat * 32767 * self.volume * 0.35).astype(np.int16)

    def generate_rain(self, duration=1.0):
        """Yumuşak yağmur sesi (doğal pembe gürültü, rahatlatıcı)"""
        sample_rate = 44100
        samples = int(sample_rate * duration)

        # Pembe gürültü benzeri (yağmur için uygun)
        noise = np.random.uniform(-1, 1, samples)

        # Gentle low-pass filter (yağmur damlaları efekti)
        window_size = int(sample_rate / 800)
        filtered = np.convolve(noise, np.ones(window_size)/window_size, mode='same')

        # Random intensity variations (doğal yağmur)
        t = np.linspace(0, duration, samples)
        intensity = 0.7 + 0.3 * np.sin(2 * np.pi * 0.2 * t)  # Yavaş değişim

        rain = filtered * intensity
        rain = rain / np.max(np.abs(rain)) * 0.3

        return (rain * 32767 * self.volume).astype(np.int16)

    def generate_ocean(self, duration=1.0):
        """Yumuşak okyanus dalgaları (düşük frekans, derin uyku)"""
        sample_rate = 44100
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples)

        # Çok yavaş dalga hareketi (0.2Hz - rahim içi sıvı hareketi benzeri)
        wave1 = np.sin(2 * np.pi * 0.2 * t) * 0.4
        wave2 = np.sin(2 * np.pi * 0.15 * t + np.pi/3) * 0.3  # Harmonik

        # Yumuşak arka plan gürültüsü (köpük/su sesi)
        noise = np.random.uniform(-0.15, 0.15, samples)

        # Low-pass filter noise
        window_size = int(sample_rate / 300)
        filtered_noise = np.convolve(noise, np.ones(window_size)/window_size, mode='same')

        # Combine
        ocean = wave1 + wave2 + filtered_noise * 0.5
        ocean = ocean / np.max(np.abs(ocean)) * 0.28

        return (ocean * 32767 * self.volume).astype(np.int16)

    def generate_lullaby(self, duration=1.0):
        """Yumuşak ninni melodisi (basit, tekrarlayan, rahatlatıcı)"""
        sample_rate = 44100
        samples = int(sample_rate * duration)

        # Ninni notaları (Hz) - basit bir melodi: C4-E4-G4-E4-C4-D4-E4-D4
        # Düşük oktav, yumuşak
        notes = [
            261.63,  # C4 (Do)
            329.63,  # E4 (Mi)
            392.00,  # G4 (Sol)
            329.63,  # E4 (Mi)
            261.63,  # C4 (Do)
            293.66,  # D4 (Re)
            329.63,  # E4 (Mi)
            293.66,  # D4 (Re)
        ]

        note_duration = duration / len(notes)  # Her notanın süresi
        note_samples = int(sample_rate * note_duration)

        lullaby = np.zeros(samples)

        for i, freq in enumerate(notes):
            start = i * note_samples
            end = min(start + note_samples, samples)
            t = np.linspace(0, note_duration, end - start)

            # Yumuşak sine wave + hafif harmonik
            note = np.sin(2 * np.pi * freq * t)  # Ana nota
            note += 0.2 * np.sin(2 * np.pi * freq * 2 * t)  # Harmonik

            # ADSR envelope (yumuşak başlangıç ve bitiş)
            attack = int(note_samples * 0.1)
            release = int(note_samples * 0.2)
            envelope = np.ones(len(t))

            if len(t) > attack:
                envelope[:attack] = np.linspace(0, 1, attack)
            if len(t) > release:
                envelope[-release:] = np.linspace(1, 0, release)

            note = note * envelope
            lullaby[start:end] = note

        # Normalize ve yumuşak ses seviyesi
        lullaby = lullaby / np.max(np.abs(lullaby)) * 0.25

        return (lullaby * 32767 * self.volume).astype(np.int16)

    def _play_file_loop(self, sound_type, file_path):
        """Ses dosyasından çalma döngüsü"""
        print(f"🎬 Starting playback for {sound_type}")
        print(f"   File path: {file_path}")

        if not self.audio:
            print("❌ Audio not initialized")
            return

        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return

        print(f"✅ File exists, size: {os.path.getsize(file_path) / 1024 / 1024:.2f} MB")

        try:
            # Dosyayı aç
            wf = wave.open(file_path, 'rb')
            print(f"🎼 WAV file opened:")
            print(f"   Channels: {wf.getnchannels()}")
            print(f"   Sample width: {wf.getsampwidth()} bytes")
            print(f"   Frame rate: {wf.getframerate()} Hz")
            print(f"   Frames: {wf.getnframes()}")

            # Stream'i dosya parametreleriyle aç
            self.stream = self.audio.open(
                format=self.audio.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )

            print(f"🎵 Playing: {sound_type} from file")
            print(f"   Volume: {int(self.volume * 100)}%")

            # Chunk size (0.5 saniye)
            chunk_size = int(wf.getframerate() * 0.5)

            while self.is_playing and self.current_sound == sound_type:
                # Dosyayı baştan başlat (loop için)
                wf.rewind()

                # Dosyayı chunk'lar halinde oku ve çal
                while self.is_playing and self.current_sound == sound_type:
                    data = wf.readframes(chunk_size)
                    if not data:
                        break  # Dosya bitti, başa dön

                    # Ses seviyesini ayarla
                    if self.volume != 1.0:
                        audio_array = np.frombuffer(data, dtype=np.int16)
                        audio_array = (audio_array * self.volume).astype(np.int16)
                        data = audio_array.tobytes()

                    if self.is_playing:
                        self.stream.write(data)

            # Temizlik
            wf.close()
            if self.stream:
                if self.stream.is_active():
                    self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            print("⏹️ Sound loop ended")

        except Exception as e:
            print(f"❌ File playback error: {e}")
            self.is_playing = False
            if self.stream:
                try:
                    self.stream.close()
                except:
                    pass
                self.stream = None

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
        print(f"\n{'='*60}")
        print(f"🎮 PLAY REQUEST: {sound_type}")
        print(f"{'='*60}")

        # Önceki sesi temizce durdur
        if self.is_playing:
            print(f"⏸️  Stopping previous sound: {self.current_sound}")
            self.stop()
            time.sleep(0.5)  # ALSA'nın temizlenmesini bekle

        self.current_sound = sound_type
        self.is_playing = True
        self.start_time = time.time()  # Başlangıç zamanını kaydet

        # Ninni için dosyadan çal
        if sound_type == 'lullaby':
            lullaby_file = os.path.join(os.path.dirname(__file__), 'sounds', 'dandini.wav')
            print(f"🎵 Selected: Dandini Dandini Dastana")
            self.play_thread = threading.Thread(target=self._play_file_loop, args=(sound_type, lullaby_file), daemon=True)
        elif sound_type == 'lullaby2':
            lullaby_file = os.path.join(os.path.dirname(__file__), 'sounds', 'beyaz_gurultu.wav')
            print(f"🎵 Selected: Beyaz Gürültü Ninni")
            self.play_thread = threading.Thread(target=self._play_file_loop, args=(sound_type, lullaby_file), daemon=True)
        else:
            print(f"🎵 Selected: Generated sound ({sound_type})")
            self.play_thread = threading.Thread(target=self._play_loop, args=(sound_type,), daemon=True)

        print(f"🚀 Starting playback thread...")
        self.play_thread.start()
        print(f"✅ Thread started successfully\n")

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
        self.start_time = None
        print("⏹️ Sound stopped cleanly")

    def set_volume(self, volume):
        """Ses seviyesini ayarla (0.0 - 1.0)"""
        self.volume = max(0.0, min(1.0, volume))

    def get_status(self):
        """Mevcut durumu al"""
        elapsed_seconds = 0
        if self.is_playing and self.start_time:
            elapsed_seconds = int(time.time() - self.start_time)

        # Süreyi dakika:saniye formatına çevir
        minutes = elapsed_seconds // 60
        seconds = elapsed_seconds % 60
        elapsed_str = f"{minutes}:{seconds:02d}"

        return {
            'is_playing': self.is_playing,
            'current_sound': self.current_sound,
            'volume': int(self.volume * 100),
            'elapsed_seconds': elapsed_seconds,
            'elapsed_time': elapsed_str
        }

    def cleanup(self):
        """Temizlik"""
        self.stop()
        if self.audio:
            self.audio.terminate()
