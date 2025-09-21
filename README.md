# raspberrypi-baby-monitor

# Hardware
- Raspiberry Pi B+ 3
- Raspiberry Pi Camera Module

1. Gerekli sistem paketlerini yükleyin


# Gerekli sistem kütüphaneleri
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv git -y
sudo apt install libatlas-base-dev libhdf5-dev
sudo apt install libopencv-dev python3-opencv

2. Python sanal ortamı oluşturun
mkdir baby_monitor_live
cd baby_monitor_live

# Sanal ortam oluştur
python3 -m venv venv
source venv/bin/activate

# Gerekli paketleri yükle
pip install flask flask-socketio opencv-python numpy
3. Raspberry Pi ayarlarını yapın
bash# Kamera ve SSH'ı aktifleştir
sudo raspi-config
# Interface Options > Camera > Enable
# Interface Options > SSH > Enable

# Reboot gerekebilir
sudo reboot

4. Dosyaları oluşturun
Yukarıdaki kodları ilgili dosyalara kopyalayın:

app.py
camera_stream.py
config.py
templates/index.html
requirements.txt

5. Uygulamayı çalıştırın
bashcd baby_monitor_live
source venv/bin/activate
python3 app.py

6. Web arayüzüne erişin

Yerel erişim: http://localhost:5000
Ağ erişimi: http://[PI_IP_ADRESI]:5000
Mobil erişim: Telefon tarayıcısından aynı adres

✅ Özellikler

- HD kalitede canlı video stream (640x480 @ 25fps)
- Gerçek zamanlı FPS gösterimi
- Timestamp overlay - Video üzerinde tarih/saat
- Çoklu kullanıcı desteği - Aynı anda birden fazla kişi izleyebilir
- Responsive tasarım - Mobil uyumlu
- Tam ekran modu - Video'yu tam ekranda izleme
- Otomatik yeniden bağlanma - Bağlantı koptuğunda otomatik yeniler
- WebSocket ile gerçek zamanlı iletişim