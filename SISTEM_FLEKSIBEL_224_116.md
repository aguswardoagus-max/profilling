# Sistem Fleksibel dan Cerdas: Server 224 ↔ Server 116

## Ringkasan
Sistem profiling yang OTOMATIS dan CERDAS dalam memilih server:
- **Server 224 HIDUP** → Gunakan server 224 (semua fitur lengkap)
- **Server 224 MATI** → Otomatis switch ke server 116 (cepat, tanpa delay)

## Kredensial Berbeda untuk Setiap Server

### Server 224 (Server Utama)
- **URL**: `http://10.1.54.224:8000`
- **Kredensial**: `rezarios` / `12345678`
- **Fitur**: Identity search, phone data, family data (lengkap)

### Server 116 (Server Alternatif)
- **URL**: `http://10.1.54.116`
- **Kredensial**: `jambi` / `@ab526d`
- **Fitur**: Identity search, family data (terbatas)
- **Tidak ada**: Phone data

## Alur Kerja Sistem Cerdas

### Scenario 1: Server 224 HIDUP ✅

```
1. User search dengan NIK
   ↓
2. Backend cek server 224 (0.5 detik)
   ↓
3. Server 224 HIDUP
   ↓
4. Login ke server 224 dengan kredensial rezarios
   ↓
5. Search identity di server 224
   ↓
6. Get phone data dari server 224
   ↓
7. Get family data dari server 224
   ↓
8. Hasil lengkap ditampilkan
```

**Kecepatan**: Normal (semua fitur lengkap)

### Scenario 2: Server 224 MATI ❌

```
1. User search dengan NIK
   ↓
2. Backend cek server 224 (0.5 detik)
   ↓
3. Server 224 MATI
   ↓
4. LANGSUNG skip ke server 116 (TANPA retry!)
   ↓
5. Login ke server 116 dengan kredensial jambi
   ↓
6. Search identity di server 116
   ↓
7. SKIP phone data (tidak tersedia di 116)
   ↓
8. Get family data langsung dari server 116 (family_cert_number)
   ↓
9. Hasil ditampilkan dengan notifikasi "Menggunakan Server Alternatif (116)"
```

**Kecepatan**: SANGAT CEPAT (1-2 detik per NIK, tanpa timeout)

### Scenario 3: Server 224 Hidup Kembali 🔄

```
1. Server 224 mati → sistem gunakan server 116
   ↓
2. Setelah 30 detik, sistem check lagi
   ↓
3. Server 224 hidup kembali
   ↓
4. Request berikutnya OTOMATIS gunakan server 224 lagi
   ↓
5. Semua fitur lengkap kembali (phone, family, dll)
```

**Recovery otomatis**: Tidak perlu restart atau manual intervention

## Fitur Cerdas

### 1. Cache Server Status
```python
_server_224_status = {
    'available': True,
    'last_check': 0,
    'check_interval': 30,  # Check setiap 30 detik
    'consecutive_failures': 0,
    'max_failures': 1  # Langsung mark unavailable setelah 1 kegagalan
}
```

### 2. Quick Check (0.5 detik)
- Timeout sangat pendek untuk deteksi cepat
- Menggunakan cache untuk menghindari check berulang
- Jika server sudah ditandai mati, langsung return False (0 delay)

### 3. Optimasi Kecepatan untuk Server 116
- **Phone data**: Skip (tidak tersedia di 116)
- **Family data**: Langsung query ke server 116 dengan `family_cert_number`
- **Refetch**: Skip (tidak perlu double query)
- **Timeout**: Dikurangi dari 15 detik ke 5 detik

### 4. Fallback Otomatis
- Jika server 224 mati → langsung server 116 tanpa retry
- Jika server 224 hidup → otomatis kembali ke server 224
- Tidak ada manual intervention

## Perbandingan Kecepatan

### Server 224 Mati (Menggunakan Server 116)

**SEBELUM (LAMBAT):**
- Per NIK: 5 detik (phone timeout) + 15 detik (family timeout) + 5 detik (refetch) = **25 detik**
- 6 NIK = **150 detik** (2.5 menit) ❌

**SESUDAH (CEPAT):**
- Per NIK: 0 detik (skip phone) + 0 detik (skip family timeout) + 0 detik (skip refetch) = **~1 detik**
- 6 NIK = **~6 detik** ✅

**Peningkatan**: 25x lebih cepat! ⚡

## Logging yang Jelas

### Server 224 Hidup:
```
INFO: [API_SEARCH] ✅ Server 224 HIDUP - Menggunakan server 224
INFO: [API_SEARCH] ✅ Kredensial rezarios digunakan untuk server 224
```

### Server 224 Mati:
```
INFO: [API_SEARCH] ✅ Server 224 MATI - Menggunakan server 116
INFO: [API_SEARCH] ✅ Kredensial rezarios akan digunakan untuk LOGIN ke server 116
INFO: [FLEKSIBEL] ❌ Server 224 MATI - LANGSUNG ke server 116 TANPA RETRY
INFO: [SERVER_116] Mencoba login dengan kredensial hardcoded: jambi
INFO: [SERVER_116] ✅ Login berhasil dengan username: jambi
INFO: [INFO] ✅ CERDAS: Server 224 mati, langsung gunakan server 116 untuk family data
INFO: [INFO] Server 116 mengembalikan X anggota keluarga untuk NKK: XXXX
```

## Fitur yang Dipertahankan

✅ Semua logic server 224 tetap ada (tidak dihilangkan)
✅ Semua fitur server 224 tetap berfungsi saat server hidup
✅ Phone data tetap berfungsi saat server 224 hidup
✅ Family data tetap berfungsi di kedua server

## Status
✅ Sistem CERDAS dan FLEKSIBEL
✅ Otomatis switch antara server 224 dan 116
✅ CEPAT seperti di server aslinya
✅ Family data muncul otomatis dari server 116
✅ Recovery otomatis setiap 30 detik
✅ Tidak ada logic yang dihilangkan

