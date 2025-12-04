# Konfigurasi Ngrok untuk Server 116

## 🚨 Masalah

Ketika aplikasi di-hosting di ngrok, server 116 tidak bisa diakses karena menggunakan IP private `10.1.54.116` yang hanya bisa diakses dari jaringan lokal.

**Error yang muncul:**
```
ERROR: [SERVER_116] Tidak dapat terhubung ke server 116
ERROR: [SERVER_116] URL: http://10.1.54.116
ERROR: [SERVER_116] IP http://10.1.54.116 adalah IP private dan tidak bisa diakses dari ngrok
```

## ✅ Solusi

### Opsi 1: Setup Ngrok Tunnel untuk Server 116 (Recommended)

#### Langkah 1: Install Ngrok (jika belum ada)
```bash
# Download dari https://ngrok.com/download
# Atau install via package manager
```

#### Langkah 2: Setup ngrok tunnel untuk server 116
Di komputer/server yang sama dengan server 116 (atau bisa mengakses `10.1.54.116`):

```bash
ngrok http 10.1.54.116:80
```

**Catatan:** Jika server 116 menggunakan port selain 80, sesuaikan:
```bash
ngrok http 10.1.54.116:PORT_NUMBER
```

#### Langkah 3: Copy URL ngrok yang diberikan
Contoh output ngrok:
```
Forwarding   https://abc123.ngrok-free.app -> http://localhost:80
```

Copy URL `https://abc123.ngrok-free.app` (atau URL yang diberikan ngrok).

#### Langkah 4: Set environment variable di server backend

**Opsi A: Set langsung di terminal (temporary)**
```bash
export SERVER_116_BASE=https://abc123.ngrok-free.app
```

**Opsi B: Tambahkan ke file `.env` (permanent)**
Edit file `.env` di folder backend:
```env
SERVER_116_BASE=https://abc123.ngrok-free.app
```

**Opsi C: Set saat menjalankan aplikasi**
```bash
SERVER_116_BASE=https://abc123.ngrok-free.app python backend/app.py
```

#### Langkah 5: Restart aplikasi backend
Jika aplikasi sudah running, restart agar environment variable diterapkan.

#### Langkah 6: Verifikasi
Setelah restart, coba lakukan pencarian lagi. Cek log untuk memastikan:
- ✅ `INFO: [SERVER_116] ✅ Login berhasil dengan username: jambi`
- ❌ Tidak ada error "Tidak dapat terhubung ke server 116"

### Opsi 2: Gunakan IP Publik (jika server 116 memiliki IP publik)

Jika server 116 memiliki IP publik atau domain yang bisa diakses dari internet:

```bash
export SERVER_116_BASE=http://your-server-116-domain.com
```

Atau di file `.env`:
```
SERVER_116_BASE=http://your-server-116-domain.com
```

### Opsi 3: VPN/Tunnel (jika menggunakan VPN)

Jika backend dan server 116 terhubung melalui VPN, pastikan:
- VPN aktif dan terhubung
- Backend bisa mengakses IP `10.1.54.116` melalui VPN
- Tidak perlu mengubah `SERVER_116_BASE` (biarkan default)

## 🔍 Troubleshooting

### Masalah: Ngrok URL berubah setiap restart

**Solusi:** Gunakan ngrok dengan domain tetap (ngrok plan berbayar) atau update environment variable setiap kali ngrok restart.

### Masalah: Masih error "Tidak dapat terhubung ke server 116"

**Cek:**
1. ✅ Ngrok tunnel aktif dan running
2. ✅ URL ngrok benar (tanpa trailing slash)
3. ✅ Server 116 bisa diakses dari ngrok tunnel (test di browser: `https://your-ngrok-url.ngrok.io`)
4. ✅ Environment variable sudah di-set dengan benar
5. ✅ Aplikasi backend sudah di-restart setelah set environment variable

### Masalah: Ngrok tunnel timeout

**Solusi:** 
- Pastikan ngrok tunnel tetap aktif selama aplikasi berjalan
- Gunakan ngrok dengan authtoken untuk menghindari timeout
- Pertimbangkan menggunakan ngrok plan berbayar untuk tunnel yang lebih stabil

## 📝 Catatan Penting

- **Default**: `SERVER_116_BASE=http://10.1.54.116` (hanya untuk jaringan lokal)
- **Ngrok**: Set ke URL ngrok tunnel (contoh: `https://abc123.ngrok-free.app`)
- **Kredensial**: Server 116 selalu menggunakan `jambi/@ab526d` (hardcoded, tidak bisa diubah dari frontend)
- **Port**: Pastikan port yang digunakan ngrok sesuai dengan port server 116 (default: 80)

## 🎯 Quick Setup Script

Buat file `setup_ngrok.sh`:
```bash
#!/bin/bash
# Setup ngrok untuk server 116

echo "Starting ngrok tunnel for server 116..."
ngrok http 10.1.54.116:80

# Setelah ngrok running, copy URL dan set environment variable:
# export SERVER_116_BASE=https://your-ngrok-url.ngrok.io
```

Jalankan:
```bash
chmod +x setup_ngrok.sh
./setup_ngrok.sh
```

