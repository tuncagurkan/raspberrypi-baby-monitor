# raspberrypi-baby-monitor

# Hardware
- Raspiberry Pi B+ 3
- Raspiberry Pi Camera Module

# Gerekli sistem kütüphaneleri
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv git -y
sudo apt install libatlas-base-dev libhdf5-dev
sudo apt install libopencv-dev python3-opencv

mkdir baby_monitor_live
cd baby_monitor_live

# Sanal ortam oluştur
python3 -m venv venv
source venv/bin/activate

# Gerekli paketleri yükle
pip install flask flask-socketio opencv-python numpy
sudo raspi-config
- Interface Options > Camera > Enable
- Interface Options > SSH > Enable
sudo reboot

# Run!
bashcd baby_monitor_live
source venv/bin/activate
python3 app.py
->
http://localhost:5000
http://[PI_IP_ADRESI]:5000


✅ Özellikler
- HD kalitede canlı video stream (640x480 @ 25fps)
- Gerçek zamanlı FPS gösterimi
- Timestamp overlay - Video üzerinde tarih/saat
- Çoklu kullanıcı desteği - Aynı anda birden fazla kişi izleyebilir
- Responsive tasarım - Mobil uyumlu
- Tam ekran modu - Video'yu tam ekranda izleme
- Otomatik yeniden bağlanma - Bağlantı koptuğunda otomatik yeniler
- WebSocket ile gerçek zamanlı iletişim