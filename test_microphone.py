#!/usr/bin/env python3
"""
Mikrofon test scripti
USB mikrofonun çalışıp çalışmadığını test eder
"""
import pyaudio
import wave
import sys

def list_audio_devices():
    """Tüm ses cihazlarını listele"""
    p = pyaudio.PyAudio()
    print("\n" + "="*60)
    print("📱 SES CİHAZLARI LİSTESİ")
    print("="*60)

    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        print(f"\n[{i}] {info['name']}")
        print(f"    Max Input Channels:  {info['maxInputChannels']}")
        print(f"    Max Output Channels: {info['maxOutputChannels']}")
        print(f"    Default Sample Rate: {info['defaultSampleRate']}")

    p.terminate()
    print("\n" + "="*60)

def test_microphone(device_index=None, duration=5):
    """Mikrofondan ses kaydı yap"""
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100

    p = pyaudio.PyAudio()

    try:
        print(f"\n🎤 Mikrofon testi başlıyor...")
        print(f"⏱️  {duration} saniye kayıt yapılacak\n")

        # Stream aç
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=CHUNK
        )

        print("🔴 KAYIT BAŞLADI - Konuşun!")

        frames = []
        for i in range(0, int(RATE / CHUNK * duration)):
            data = stream.read(CHUNK)
            frames.append(data)

            # İlerleme göster
            if i % 10 == 0:
                print(".", end="", flush=True)

        print("\n\n✅ Kayıt tamamlandı!")

        # Stream'i kapat
        stream.stop_stream()
        stream.close()

        # Dosyaya kaydet
        filename = "test_microphone.wav"
        wf = wave.open(filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        print(f"💾 Kayıt '{filename}' dosyasına kaydedildi")
        print(f"\nDinlemek için: aplay {filename}")

    except Exception as e:
        print(f"\n❌ HATA: {e}")
    finally:
        p.terminate()

def main():
    print("\n🎤 MİKROFON TEST ARACI")

    # Önce cihazları listele
    list_audio_devices()

    # Kullanıcıdan cihaz seçmesini iste
    print("\nTest etmek istediğiniz cihazın numarasını girin")
    print("(Varsayılan mikrofon için Enter'a basın): ", end="")

    try:
        choice = input().strip()
        device_index = int(choice) if choice else None

        # Test yap
        test_microphone(device_index=device_index, duration=5)

    except KeyboardInterrupt:
        print("\n\nTest iptal edildi")
    except ValueError:
        print("\n❌ Geçersiz cihaz numarası")
    except Exception as e:
        print(f"\n❌ Hata: {e}")

if __name__ == "__main__":
    main()
