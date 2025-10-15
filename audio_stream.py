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

            # Open audio stream
            self.stream = self.audio.open(
                format=self.config.AUDIO_FORMAT,
                channels=self.config.AUDIO_CHANNELS,
                rate=self.config.AUDIO_RATE,
                input=True,
                frames_per_buffer=self.config.AUDIO_CHUNK,
                input_device_index=self.config.AUDIO_DEVICE_INDEX
            )

            print(f"✅ Audio initialized: {self.config.AUDIO_RATE}Hz, {self.config.AUDIO_CHANNELS} channel(s)")

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
        while self.is_streaming and self.stream:
            try:
                # Read audio data
                audio_data = self.stream.read(self.config.AUDIO_CHUNK, exception_on_overflow=False)

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
        while self.is_streaming:
            try:
                # Get audio data from queue with timeout
                audio_data = self.audio_queue.get(timeout=1.0)
                yield audio_data
            except queue.Empty:
                # If no data available, yield silence
                silence = b'\x00' * self.config.AUDIO_CHUNK * self.config.AUDIO_CHANNELS * 2
                yield silence

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
