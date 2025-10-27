# Dokumentasi Filter Lokasi untuk Pencarian Identity

## Overview
Fitur ini menambahkan kemampuan untuk memfilter pencarian identity berdasarkan lokasi geografis (provinsi, kabupaten/kota, kecamatan, dan desa) tanpa mengubah logic yang sudah ada.

## Parameter yang Ditambahkan

### 1. API Endpoint `/api/search`
- `no_prop`: Kode provinsi (contoh: "12" untuk Jambi)
- `no_kab`: Kode kabupaten/kota
- `no_kec`: Kode kecamatan  
- `no_desa`: Kode desa
- `family_cert_number`: Nomor kartu keluarga
- `tempat_lahir`: Tempat lahir
- `tanggal_lahir`: Tanggal lahir

### 2. Command Line Tool `clearance_face_search.py`
- `--no_prop`: Filter provinsi
- `--no_kab`: Filter kabupaten/kota
- `--no_kec`: Filter kecamatan
- `--no_desa`: Filter desa
- `--family_cert_number`: Filter nomor kartu keluarga
- `--tempat_lahir`: Filter tempat lahir
- `--tanggal_lahir`: Filter tanggal lahir

## Contoh Penggunaan

### 1. API Endpoint
```bash
curl -X POST http://127.0.0.1:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123",
    "search_type": "identity",
    "name": "agus saputra",
    "no_prop": "12",
    "no_kab": "1201",
    "no_kec": "120101",
    "no_desa": "1201012001",
    "page": "1"
  }'
```

### 2. Command Line Tool
```bash
python backend/clearance_face_search.py \
  --username admin \
  --password admin123 \
  --name "agus saputra" \
  --no_prop 12 \
  --no_kab 1201 \
  --no_kec 120101 \
  --no_desa 1201012001 \
  --page 1 \
  --pretty
```

### 3. URL dengan Query Parameters
```
http://10.1.54.224:8000/clearance/ktp/search?name=agus%20saputra&nik=&family_cert_number=&tempat_lahir=&tanggal_lahir=&no_prop=12&no_kab=1201&no_kec=120101&no_desa=1201012001&page=1
```

## Validasi
- Minimal satu parameter harus diisi untuk membatasi hasil pencarian
- Parameter yang valid: `name`, `nik`, `family_cert_number`, `tempat_lahir`, `tanggal_lahir`, `no_prop`, `no_kab`, `no_kec`, `no_desa`
- Jika tidak ada parameter yang diisi, akan mengembalikan error 400

## Kode Wilayah
- `no_prop`: Kode provinsi (2 digit)
- `no_kab`: Kode kabupaten/kota (4 digit)
- `no_kec`: Kode kecamatan (6 digit)
- `no_desa`: Kode desa (10 digit)

Contoh untuk Jambi:
- Provinsi: 12
- Kabupaten/Kota: 1201 (Kota Jambi), 1202 (Kabupaten Kerinci), dll.
- Kecamatan: 120101 (Kecamatan Jambi Selatan), dll.
- Desa: 1201012001 (Desa tertentu), dll.

## Backward Compatibility
- Semua parameter bersifat opsional
- Logic yang sudah ada tidak diubah
- Hanya menambahkan kemampuan filter tambahan
- Default value untuk semua parameter adalah string kosong

## Testing
Gunakan file `test_location_search.py` untuk menguji implementasi:

```bash
python test_location_search.py
```

## Catatan
- Fitur ini memerlukan server eksternal yang mendukung parameter lokasi
- Pastikan server eksternal dapat menangani parameter `no_prop`, `no_kab`, `no_kec`, `no_desa`
- Jika server eksternal tidak tersedia, akan menggunakan fallback mode
