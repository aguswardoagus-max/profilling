# AI Inpainting Guide - LaMa Cleaner Integration

## Overview
Backend Flask telah disempurnakan dengan fitur AI inpainting menggunakan LaMa Cleaner untuk menghapus watermark dari foto profil secara otomatis.

## Fitur Baru

### 1. AI Watermark Removal
- **Fungsi**: `clean_watermark(image_bytes)`
- **Teknologi**: OpenCV inpainting dengan deteksi watermark otomatis
- **Input**: Bytes gambar dengan watermark
- **Output**: Bytes gambar bersih tanpa watermark

### 2. Foto Download & Processing
- **Fungsi**: `download_foto(url_foto, timeout=30)`
- **Fungsi**: `process_and_save_clean_photo(nik, url_foto)`
- **Fitur**: Download otomatis dari URL, proses AI inpainting, dan cache system

### 3. Cache System
- **Lokasi**: `/static/clean_photos/`
- **Format**: `{NIK}.jpg`
- **Benefit**: Tidak perlu proses ulang untuk foto yang sudah diproses

### 4. Enhanced API Response
- **Field Baru**: `foto_bersih_url`
- **Format**: `/static/clean_photos/{NIK}.jpg`
- **Contoh**: `/static/clean_photos/3174xxxxx.jpg`

## Dependencies Baru

```bash
pip install opencv-python==4.8.1.78
pip install lama-cleaner==1.2.0
pip install torch==2.0.1
pip install torchvision==0.15.2
```

## Cara Kerja

### 1. Pencarian Data Profil
```json
POST /api/search
{
  "search_type": "identity",
  "name": "John Doe",
  "nik": "3174xxxxx",
  "username": "user",
  "password": "pass"
}
```

### 2. Response dengan Foto Bersih
```json
{
  "results": [
    {
      "person": {
        "full_name": "John Doe",
        "ktp_number": "3174xxxxx",
        "face": "data:image/jpeg;base64,...",
        "foto_bersih_url": "/static/clean_photos/3174xxxxx.jpg",
        "family_data": {...},
        "phone_data": [...]
      }
    }
  ]
}
```

### 3. Akses Foto Bersih
```
GET /static/clean_photos/3174xxxxx.jpg
```

## Logging

Semua proses AI inpainting dicatat dalam log:
- Download foto dari URL
- Proses watermark removal
- Cache hit/miss
- Error handling

## Konfigurasi

### Folder Structure
```
project/
├── static/
│   └── clean_photos/     # Foto bersih hasil AI inpainting
├── app.py               # Backend dengan fitur AI inpainting
└── requirements.txt     # Dependencies terbaru
```

### Environment Variables
Tidak ada konfigurasi tambahan yang diperlukan. Semua proses dilakukan offline di server.

## Error Handling

1. **Download Gagal**: Log warning, skip AI inpainting
2. **Watermark Removal Gagal**: Log error, return original photo
3. **Cache Error**: Log error, continue dengan foto asli
4. **Invalid URL**: Skip processing, set `foto_bersih_url` ke `null`

## Performance

- **Cache Hit**: Instant response (file sudah ada)
- **Cache Miss**: ~2-5 detik untuk proses AI inpainting
- **Storage**: ~50-200KB per foto bersih (tergantung resolusi)

## Testing

### Test Endpoint
```bash
# Test dengan NIK yang sudah ada
GET /api/debug/search/1505041107830002

# Response akan include foto_bersih_url jika berhasil
```

### Manual Test
1. Jalankan pencarian dengan NIK yang valid
2. Periksa response untuk field `foto_bersih_url`
3. Akses URL foto bersih untuk memverifikasi hasil

## Troubleshooting

### Common Issues

1. **Import Error**: Pastikan semua dependencies terinstall
2. **Permission Error**: Pastikan folder `static/clean_photos/` writable
3. **Memory Error**: Untuk foto besar, pertimbangkan resize sebelum processing
4. **Timeout**: Adjust timeout di `download_foto()` jika URL lambat

### Log Monitoring
```bash
tail -f app.log | grep "AI inpainting\|watermark\|clean_photo"
```

## Security Notes

- Semua proses dilakukan offline di server
- Tidak ada data yang dikirim ke API eksternal pihak ketiga
- Foto bersih disimpan lokal dengan nama NIK
- Access control melalui authentication system yang sudah ada

