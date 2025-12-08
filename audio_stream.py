import pyaudio
import threading
import queue
import time
import logging
from datetime import datetime

class AudioStream:
    def __init__(self, config):
        self.config = config
        self.audio = None
        self.stream = None
        self.is_streaming = False
        self.audio_queue = queue.Queue(maxsize=100)

        self.initialize_audio()
        self.start_streaming()

    def initialize_audio(self):
        """Initialize audio capture"""
        print("🔊 Initializing audio")
        try:
            self.audio = pyaudio.PyAudio()

            # List all audio devices for debugging
            print("\n📱 Available INPUT devices:")
            device_index = self.config.AUDIO_DEVICE_INDEX

            for i in range(self.audio.get_device_count()):
                info = self.audio.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    print(f"  [{i}] {info['name']}")
                    print(f"      Input Channels: {info['maxInputChannels']}")
                    print(f"      Sample Rate: {info['defaultSampleRate']}")

                    # USB mikrofonunu otomatik bul
                    if device_index is None and 'USB' in info['name'].upper():
                        device_index = i
                        print(f"      ✅ USB mikrofon bulundu, kullanılacak!")

            print()

            if device_index is not None:
                print(f"🎤 Using device index: {device_index}")
            else:
                print(f"🎤 Using default device (None)")

            # Open audio stream
            self.stream = self.audio.open(
                format=self.config.AUDIO_FORMAT,
                channels=self.config.AUDIO_CHANNELS,
                rate=self.config.AUDIO_RATE,
                input=True,
                frames_per_buffer=self.config.AUDIO_CHUNK,
                input_device_index=device_index
            )

            print(f"✅ Audio initialized: {self.config.AUDIO_RATE}Hz, {self.config.AUDIO_CHANNELS} channel(s)\n")

        except Exception as e:
            print(f"❌ Audio error: {e}")
            self.audio = None
            self.stream = None

    def start_streaming(self):
        """Start audio streaming thread"""
        print("🔊 Starting audio stream")
        if self.stream:
            self.is_streaming = True
            self.stream_thread = threading.Thread(target=self._stream_loop, daemon=True)
            self.stream_thread.start()

    def _stream_loop(self):
        """Main audio streaming loop"""
        print("🎤 Audio stream loop started")
        chunk_count = 0

        while self.is_streaming and self.stream:
            try:
                # Read audio data
                audio_data = self.stream.read(self.config.AUDIO_CHUNK, exception_on_overflow=False)
                chunk_count += 1

                # Debug: Her 100 chunk'ta bir bilgi ver
                if chunk_count % 100 == 0:
                    import audioop
                    rms = audioop.rms(audio_data, 2)
                    print(f"🎤 Audio chunk #{chunk_count}, RMS level: {rms}, Queue size: {self.audio_queue.qsize()}")

                # Add to queue for streaming
                if not self.audio_queue.full():
                    self.audio_queue.put(audio_data)
                else:
                    # Remove oldest item if queue is full
                    try:
                        self.audio_queue.get_nowait()
                        self.audio_queue.put(audio_data)
                    except queue.Empty:
                        pass

            except Exception as e:
                print(f"⚠️  Audio read error: {e}")
                time.sleep(0.1)

    def generate_audio(self):
        """Generator for audio streaming to Flask"""
        import struct

        # Send WAV header first for browser compatibility
        wav_header = self._create_wav_header()
        yield wav_header

        print("🎤 Audio feed started, sending to browser...")

        while self.is_streaming:
            try:
                # Get audio data from queue with timeout
                audio_data = self.audio_queue.get(timeout=1.0)
                yield audio_data
            except queue.Empty:
                # If no data available, yield silence
                silence = b'\x00' * self.config.AUDIO_CHUNK * self.config.AUDIO_CHANNELS * 2
                yield silence

    def _create_wav_header(self):
        """Create a WAV file header for streaming"""
        import struct

        # WAV header for infinite streaming
        # Using a large file size (0xFFFFFFFF) to indicate streaming
        sample_rate = self.config.AUDIO_RATE
        num_channels = self.config.AUDIO_CHANNELS
        bits_per_sample = 16
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8

        header = struct.pack('<4sI4s', b'RIFF', 0xFFFFFFFF, b'WAVE')
        header += struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, num_channels, sample_rate, byte_rate, block_align, bits_per_sample)
        header += struct.pack('<4sI', b'data', 0xFFFFFFFF)

        return header

    def is_active(self):
        """Check if audio is active"""
        return self.stream is not None and self.is_streaming

    def get_volume_level(self):
        """Get current volume level (for monitoring)"""
        if self.stream and self.is_streaming:
            try:
                # Read a small sample
                data = self.stream.read(self.config.AUDIO_CHUNK, exception_on_overflow=False)
                # Calculate RMS (Root Mean Square) for volume level
                import audioop
                rms = audioop.rms(data, 2)
                # Convert to percentage (0-100)
                volume = min(100, int(rms / 327.67))  # 32767 max for 16-bit audio
                return volume
            except:
                return 0
        return 0

    def stop(self):
        """Stop audio streaming"""
        print("🔊 Stopping audio stream")
        self.is_streaming = False

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        if self.audio:
            self.audio.terminate()
