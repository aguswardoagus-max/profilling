# NGROK Setup Guide

Panduan untuk menjalankan aplikasi dengan ngrok untuk akses dari domain eksternal.

## 🚀 Quick Start

### 1. Install NGROK
```bash
# Download dari https://ngrok.com/download
# Atau install via package manager
```

### 2. Start NGROK
```bash
# Terminal 1: Start ngrok
ngrok http 5000

# Terminal 2: Start aplikasi dengan ngrok
python run_ngrok.py --ngrok-url https://your-ngrok-url.ngrok-free.dev
```

### 3. Atau Auto-detect NGROK
```bash
# Aplikasi akan auto-detect ngrok domain
python run_ngrok.py
```

## ⚙️ Konfigurasi

### Environment Variables
Buat file `.env`:
```env
# NGROK Configuration
NGROK_MODE=true
BASE_URL=https://your-ngrok-url.ngrok-free.dev
HTTPS=true
ALLOWED_ORIGINS=*,https://your-ngrok-url.ngrok-free.dev,http://localhost:5000
```

### Manual Configuration
```bash
# Set environment variables
export NGROK_MODE=true
export BASE_URL=https://asteroidal-isotactic-alexandra.ngrok-free.dev
export HTTPS=true
export ALLOWED_ORIGINS="*,https://asteroidal-isotactic-alexandra.ngrok-free.dev,http://localhost:5000"

# Run aplikasi
python run.py
```

## 🔧 Troubleshooting

### CORS Issues
Jika ada CORS error:
1. Pastikan ngrok URL ditambahkan ke `ALLOWED_ORIGINS`
2. Gunakan `python run_ngrok.py` untuk auto-configuration
3. Check console untuk "Added ngrok domain to allowed origins"

### Session Issues
Jika ada masalah session:
1. Pastikan `SESSION_COOKIE_SAMESITE=None` untuk ngrok
2. Pastikan `SESSION_COOKIE_SECURE=true` untuk HTTPS
3. Clear browser cookies dan coba lagi

### Authentication Loop
Jika stuck di "Memverifikasi autentikasi...":
1. Clear browser storage (localStorage, sessionStorage, cookies)
2. Restart aplikasi
3. Cek console untuk error messages

## 📋 Testing

### 1. Test Local
```bash
python run.py
# http://localhost:5000
```

### 2. Test NGROK
```bash
python run_ngrok.py --ngrok-url https://your-url.ngrok-free.dev
# https://your-url.ngrok-free.dev
```

### 3. Test Auto-detect
```bash
python run_ngrok.py
# Aplikasi akan auto-detect ngrok domain
```

## 🌐 NGROK Domain Examples

- `https://abc123.ngrok.io`
- `https://def456.ngrok-free.app`
- `https://asteroidal-isotactic-alexandra.ngrok-free.dev`

## 🔍 Debug Information

### Console Logs
Aplikasi akan menampilkan:
```
Allowed CORS origins: ['http://localhost:5000', 'https://your-url.ngrok-free.dev', '*']
Added ngrok domain to allowed origins: https://your-url.ngrok-free.dev
Frontend config loaded: {baseUrl: 'https://your-url.ngrok-free.dev', ...}
```

### API Endpoints
- `/api/frontend-config` - Konfigurasi frontend
- `/api/auth-status` - Status authentication
- `/api/check-auth` - Check authentication

## ⚠️ Security Notes

- NGROK mode mengaktifkan CORS untuk semua domain (`*`)
- Hanya untuk development/testing
- Jangan gunakan untuk production
- Session cookies dikonfigurasi untuk ngrok HTTPS

## 🆘 Common Issues

### 1. "Memverifikasi autentikasi..." stuck
**Solution:**
```bash
# Clear browser data
# Restart aplikasi
python run_ngrok.py --ngrok-url https://your-url.ngrok-free.dev
```

### 2. CORS Error
**Solution:**
```bash
# Check allowed origins
curl https://your-url.ngrok-free.dev/api/frontend-config
```

### 3. Session not working
**Solution:**
```bash
# Check cookie settings
# Clear browser cookies
# Restart aplikasi
```
