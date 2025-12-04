# Konfigurasi Ngrok untuk Server 116

## Masalah
Ketika aplikasi di-hosting di ngrok, server 116 tidak bisa diakses karena menggunakan IP private `10.1.54.116` yang hanya bisa diakses dari jaringan lokal.

## Solusi

### Opsi 1: Setup Ngrok Tunnel untuk Server 116 (Recommended)

1. **Setup ngrok tunnel untuk server 116:**
   ```bash
   ngrok http 10.1.54.116:80
   ```

2. **Copy URL ngrok yang diberikan** (contoh: `https://abc123.ngrok.io`)

3. **Set environment variable di server backend:**
   ```bash
   export SERVER_116_BASE=https://abc123.ngrok.io
   ```

   Atau tambahkan ke file `.env`:
   ```
   SERVER_116_BASE=https://abc123.ngrok.io
   ```

4. **Restart aplikasi backend**

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

## Verifikasi

Setelah mengkonfigurasi, cek log aplikasi untuk memastikan:
- ✅ Login ke server 116 berhasil
- ❌ Tidak ada error "Tidak dapat terhubung ke server 116"

Jika masih ada error connection, pastikan:
1. Ngrok tunnel aktif dan running
2. URL ngrok benar (tanpa trailing slash)
3. Server 116 bisa diakses dari ngrok tunnel
4. Environment variable sudah di-set dengan benar

## Catatan Penting

- **Default**: `SERVER_116_BASE=http://10.1.54.116` (hanya untuk jaringan lokal)
- **Ngrok**: Set ke URL ngrok tunnel (contoh: `https://abc123.ngrok.io`)
- **Kredensial**: Server 116 selalu menggunakan `jambi/@ab526d` (tidak bisa diubah dari frontend)

