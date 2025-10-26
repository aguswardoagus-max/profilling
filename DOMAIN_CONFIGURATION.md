# Domain Configuration Guide

Aplikasi ini sekarang mendukung konfigurasi yang fleksibel untuk berbagai domain dan environment.

## 🚀 Cara Menjalankan

### 1. Localhost (Default)
```bash
python run.py
```
Aplikasi akan berjalan di `http://localhost:5000`

### 2. Domain Kustom
```bash
# HTTP
python run_domain.py --domain yourdomain.com --port 5000

# HTTPS
python run_domain.py --domain yourdomain.com --port 5000 --https
```

### 3. IP Address
```bash
python run_domain.py --domain 192.168.1.100 --port 5000
```

## ⚙️ Konfigurasi Environment

### File .env
Buat file `.env` di root directory:

```env
# Environment
FLASK_ENV=development
HTTPS=false
BASE_URL=http://yourdomain.com:5000

# Allowed Origins (comma-separated)
ALLOWED_ORIGINS=http://yourdomain.com:5000,https://yourdomain.com:5000,http://localhost:5000

# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=clearance_facesearch
```

## 🔧 Fitur Konfigurasi Dinamis

### 1. CORS Support
- Otomatis mendukung localhost dan domain kustom
- Mendukung HTTP dan HTTPS
- Konfigurasi melalui environment variables

### 2. Session Management
- Session cookie aman untuk HTTPS
- Domain-agnostic session handling
- Proper cookie configuration

### 3. Frontend Configuration
- API endpoint `/api/frontend-config` untuk konfigurasi dinamis
- Base URL otomatis terdeteksi
- Support untuk multiple domains

## 🌐 Contoh Konfigurasi

### Development
```bash
python run.py
# http://localhost:5000
```

### Production dengan Domain
```bash
python run_domain.py --domain myapp.com --port 80 --https
# https://myapp.com
```

### Internal Network
```bash
python run_domain.py --domain 192.168.1.100 --port 5000
# http://192.168.1.100:5000
```

## 🔒 Keamanan

### HTTPS Configuration
Untuk production dengan HTTPS:

1. Set environment variable:
```bash
export HTTPS=true
export BASE_URL=https://yourdomain.com
```

2. Atau gunakan script:
```bash
python run_domain.py --domain yourdomain.com --https
```

### CORS Security
- Hanya domain yang diizinkan yang bisa mengakses API
- Konfigurasi melalui `ALLOWED_ORIGINS`
- Support untuk credentials

## 🐛 Troubleshooting

### CORS Error
Jika ada CORS error, pastikan domain ditambahkan ke `ALLOWED_ORIGINS`:
```env
ALLOWED_ORIGINS=http://yourdomain.com:5000,https://yourdomain.com:5000
```

### Session Issues
Jika ada masalah session, cek konfigurasi cookie:
- `SESSION_COOKIE_SECURE=true` untuk HTTPS
- `SESSION_COOKIE_DOMAIN` untuk domain tertentu

### Port Issues
Pastikan port tidak digunakan aplikasi lain:
```bash
netstat -an | findstr :5000
```

## 📝 Notes

- Aplikasi otomatis mendeteksi protocol (HTTP/HTTPS)
- Base URL otomatis terdeteksi dari request
- Konfigurasi frontend di-load secara dinamis
- Support untuk multiple environments
