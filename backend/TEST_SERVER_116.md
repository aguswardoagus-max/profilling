# Testing Server 116 Fallback

## Cara Testing

1. **Pastikan server 224 tidak tersedia** (atau sudah ditandai tidak tersedia)
2. **Jalankan aplikasi Flask**
3. **Lakukan pencarian dengan NIK** (contoh: `1505041107830002`)
4. **Cek console/log untuk melihat debug output**

## Debug Output yang Akan Muncul

### Jika Server 116 Dipanggil:
```
INFO: Server 224 tidak tersedia, langsung menggunakan server 116 untuk pencarian
DEBUG: call_search - Parameter yang akan dikirim ke server 116: {'nik': '1505041107830002', ...}
INFO: Server 116 - Mencari dengan NIK menggunakan parameter ktp_number: 1505041107830002
INFO: Server 116 - Melakukan pencarian dengan parameter: {'ktp_number': '1505041107830002'}
INFO: Server 116 - URL lengkap: http://10.1.54.116/toolkit/api/identity/search?ktp_number=1505041107830002
INFO: Server 116 - Response status code: 200
INFO: Server 116 - Response keys: ['error', 'person', 'success']
INFO: Server 116 - Ditemukan X hasil
INFO: Server 116 - Contoh hasil pertama - NIK: 1505041107830002, Nama: MARGUTIN
DEBUG: perform_regular_search - Response dari call_search: type=<class 'dict'>, keys=['person', '_server_116_fallback', ...]
DEBUG: perform_regular_search - Hasil parse: X people ditemukan
```

### Jika Ada Masalah:
- **Tidak ada log "Server 116"** → Server 116 tidak dipanggil, cek logic fallback
- **Status code bukan 200** → Cek koneksi ke server 116
- **Response kosong** → Cek parameter yang dikirim
- **Parse error** → Cek format response dari server 116

## Manual Test Script

Jalankan script test:
```bash
python backend/test_server_116.py
```

Script ini akan:
1. Test login ke server 116
2. Test pencarian dengan NIK
3. Test pencarian dengan nama
4. Menampilkan hasil detail

## Troubleshooting

### Masalah: Server 116 tidak dipanggil
- **Solusi**: Pastikan `FALLBACK_MODE = True` di `clearance_face_search.py`
- **Solusi**: Pastikan server 224 benar-benar tidak tersedia atau sudah ditandai tidak tersedia

### Masalah: Response kosong dari server 116
- **Cek**: Apakah parameter `ktp_number` benar?
- **Cek**: Apakah session login masih valid?
- **Cek**: Apakah server 116 benar-benar mengembalikan data?

### Masalah: Parse error
- **Cek**: Format response dari server 116 (`{"error":"","person":[...],"success":true}`)
- **Cek**: Apakah field `person` ada dan berupa array?

