# 🔒 Panduan Keamanan Folder Aplikasi

## 🎯 Overview
Panduan ini menjelaskan cara mengunci folder aplikasi agar tidak bisa dibuka sembarang orang, tapi tetap bisa diakses oleh program Python.

## 🛡️ Opsi Keamanan Folder

### 1. **Folder Tersembunyi + Permissions (Recommended)**
- Folder aplikasi dipindahkan ke folder tersembunyi (dimulai dengan titik)
- Set permissions agar hanya owner yang bisa akses
- Program Python tetap bisa berjalan normal

### 2. **File Permissions Only**
- Set permissions folder agar hanya owner yang bisa akses
- Folder tetap terlihat tapi tidak bisa dibuka

### 3. **Environment Variables**
- Simpan path aplikasi di environment variables
- Folder bisa disembunyikan di lokasi yang tidak biasa

## 🚀 Cara Menggunakan

### **Windows:**

#### Setup Folder Aman:
```cmd
# Jalankan script setup
secure_folder_setup.bat

# Atau manual
mkdir .clearance_app
# Pindahkan semua file ke folder tersebut
```

#### Menjalankan Aplikasi:
```cmd
# Setelah setup
launcher.bat

# Atau manual
cd .clearance_app
python app.py
```

#### Mengembalikan Struktur Semula:
```cmd
restore.bat
```

### **Linux/Mac:**

#### Setup Folder Aman:
```bash
# Buat script executable
chmod +x secure_folder_setup.sh

# Jalankan script setup
./secure_folder_setup.sh

# Atau manual
mkdir .clearance_app
chmod 700 .clearance_app
# Pindahkan semua file ke folder tersebut
```

#### Menjalankan Aplikasi:
```bash
# Setelah setup
./launcher.sh

# Atau manual
cd .clearance_app
python3 app.py
```

#### Mengembalikan Struktur Semula:
```bash
# Buat script executable
chmod +x restore.sh

# Jalankan restore
./restore.sh
```

### **Cross-Platform (Python):**

#### Setup Folder Aman:
```bash
python secure_folder_setup.py setup
```

#### Menjalankan Aplikasi:
```bash
python launcher.py
```

#### Mengembalikan Struktur Semula:
```bash
python secure_folder_setup.py restore
```

#### Lihat Status:
```bash
python secure_folder_setup.py status
```

## 📁 Struktur Folder Setelah Setup

### **Sebelum Setup:**
```
project_folder/
├── app.py
├── database.py
├── cekplat.py
├── requirements.txt
├── static/
├── uploads/
└── ...
```

### **Setelah Setup:**
```
project_folder/
├── .clearance_app/          # Folder tersembunyi dan aman
│   ├── app.py
│   ├── database.py
│   ├── cekplat.py
│   ├── requirements.txt
│   ├── static/
│   ├── uploads/
│   └── ...
├── launcher.py              # Script untuk menjalankan aplikasi
├── .app_config              # Konfigurasi aplikasi
└── secure_folder_setup.py   # Script setup
```

## 🔐 Level Keamanan

### **Level 1: Folder Tersembunyi**
- ✅ Folder tidak terlihat di file explorer biasa
- ✅ Tidak bisa dibuka dengan double-click
- ✅ Program Python tetap bisa akses

### **Level 2: Permissions (Linux/Mac)**
- ✅ Hanya owner yang bisa read/write/execute
- ✅ Group dan others tidak bisa akses
- ✅ Permissions: 700 (folder), 600 (file)

### **Level 3: Script Launcher**
- ✅ Aplikasi hanya bisa dijalankan via script launcher
- ✅ Script launcher bisa dipassword protect
- ✅ Logging akses ke aplikasi

## 🛠️ Konfigurasi Lanjutan

### **Password Protect Launcher:**

#### Windows (launcher.bat):
```batch
@echo off
set /p password="Masukkan password: "
if "%password%"=="your_password" (
    cd .clearance_app
    python app.py
) else (
    echo Password salah!
    pause
)
```

#### Linux/Mac (launcher.sh):
```bash
#!/bin/bash
read -s -p "Masukkan password: " password
echo
if [ "$password" = "your_password" ]; then
    cd .clearance_app
    python3 app.py
else
    echo "Password salah!"
    exit 1
fi
```

### **Environment Variables:**
```bash
# Set di .bashrc atau .zshrc
export CLEARANCE_APP_PATH="/path/to/.clearance_app"
export CLEARANCE_APP_PASSWORD="your_password"

# Gunakan di script
cd $CLEARANCE_APP_PATH
python3 app.py
```

## 🔍 Troubleshooting

### **Masalah Umum:**

#### 1. **Folder tidak bisa diakses:**
```bash
# Linux/Mac: Cek permissions
ls -la .clearance_app

# Fix permissions
chmod 700 .clearance_app
chmod 600 .clearance_app/*
```

#### 2. **Script launcher tidak berfungsi:**
```bash
# Cek apakah script executable
ls -la launcher.sh

# Fix permissions
chmod +x launcher.sh
```

#### 3. **Python tidak bisa import module:**
```python
# Pastikan path benar di launcher
import sys
sys.path.insert(0, '.clearance_app')
```

#### 4. **File tidak ditemukan:**
```bash
# Cek apakah file ada di folder aman
ls -la .clearance_app/

# Restore jika perlu
python secure_folder_setup.py restore
```

## 📊 Monitoring & Logging

### **Log Akses:**
```python
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    filename='.clearance_app/access.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Log setiap akses
logging.info(f"Application started by user: {os.getenv('USER')}")
```

### **Check Status:**
```bash
# Lihat status keamanan
python secure_folder_setup.py status

# Output:
# 📊 Status Keamanan Folder:
# ========================================
# ✅ Folder aman: .clearance_app
# 🔐 Permissions: 700
# 📁 Jumlah file/folder: 15
# ✅ Script launcher tersedia
```

## 🚨 Security Best Practices

### **1. Regular Backup:**
```bash
# Backup folder aman
tar -czf clearance_backup_$(date +%Y%m%d).tar.gz .clearance_app
```

### **2. Monitor Access:**
```bash
# Monitor akses ke folder
inotifywait -m -r .clearance_app
```

### **3. Update Permissions:**
```bash
# Refresh permissions secara berkala
find .clearance_app -type d -exec chmod 700 {} \;
find .clearance_app -type f -exec chmod 600 {} \;
```

### **4. Secure Deletion:**
```bash
# Hapus file dengan aman
shred -vfz -n 3 .clearance_app/sensitive_file.txt
```

## 📞 Support

Jika mengalami masalah:
1. Cek log file di `.clearance_app/access.log`
2. Jalankan `python secure_folder_setup.py status`
3. Restore struktur semula jika perlu
4. Hubungi administrator sistem

---

**🔒 Folder aplikasi Anda sekarang aman dan terlindungi!**


