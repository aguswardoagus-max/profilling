# Panduan Reports / Profiling

## Overview
Fitur Reports / Profiling memungkinkan pengguna untuk mengelola, memfilter, dan mengekspor data profiling dalam format dokumen Word (DOCX) dan PDF sesuai dengan template yang telah ditentukan.

## Fitur Utama

### 1. Panel Filter & Controls
- **Provinsi**: Filter berdasarkan provinsi
- **Kabupaten/Kota**: Filter berdasarkan kabupaten/kota (dependent dari provinsi)
- **Kecamatan**: Filter berdasarkan kecamatan (optional)
- **Kategori Profiling**: Multi-select untuk kategori seperti "Perkebunan", "Aktor Kunci", "Keuangan", "Logistik", "Keamanan"
- **Subkategori/Tag**: Multi-select untuk subkategori seperti "Sawit Ilegal", "Pemilik Lahan", "Tenaga Kerja", "Supplier"
- **Rentang Tanggal**: Filter berdasarkan tanggal input/investigasi
- **Status Verifikasi**: Filter berdasarkan status (draft, verified, published)
- **Kata Kunci**: Search berdasarkan nama, NIK, atau alamat
- **Sorting**: Urutkan berdasarkan tanggal, nama, kabupaten, atau kategori

### 2. Panel Results
- **Grid Layout**: Menampilkan data dalam bentuk card dengan thumbnail foto
- **Multi-Select**: Pilih multiple records dengan checkbox
- **Auto-Select**: Tombol "Select All" dan "Clear Selection"
- **Card Information**: 
  - Foto profil (thumbnail 80x80px)
  - Nama lengkap
  - NIK
  - Lokasi (Kabupaten/Kota)
  - Tanggal input
  - Kategori

### 3. Panel Preview
- **Collapsible**: Panel dapat di-collapse untuk menghemat ruang
- **Document Preview**: Preview dokumen dalam format HTML sebelum export
- **WYSIWYG**: Tampilan sesuai dengan template final

### 4. Multi-Select Toolbar
Muncul ketika ada record yang dipilih:
- **Auto-link**: Mencari record terkait berdasarkan NIK, alamat, atau relasi keluarga
- **Group as Single Report**: Menggabungkan multiple records dalam satu dokumen
- **Preview Document**: Generate preview dokumen
- **Export**: Export ke DOCX atau PDF

## Template Dokumen

### Layout Halaman 1
```
PROFILING
Perkebunan Sawit Ilegal PT. Mitra Prima Gitabadi
di Kabupaten [KABUPATEN]

[NAMA TARGET]

[FOTO] 180x180px    | 1. Data Diri:
                    | a. Nama Ayah : [NAMA_AYAH]
                    | b. NIK : [NIK]
                    | c. TTL : [TTL]
                    | d. Alamat : [ALAMAT]
                    | e. Nomor HP : [HP]
                    | f. Nama Ibu : [NAMA_IBU]
                    | g. Istri : [NAMA_ISTRI]
                    | h. Anak : [ANAK]
```

### Layout Halaman 2
```
2. Hasil Pendalaman:

Target Prioritas.
[Target Prioritas text]

Simpul Pengolahan.
[Simpul Pengolahan text]

Aktor Pendukung.
[Aktor Pendukung text]

Jaringan Lokal.
[Jaringan Lokal text]

Koordinasi.
[Koordinasi text]

Demikian untuk menjadikan periksa.
Otentikasi
```

## API Endpoints

### GET /api/profiling/reports
Mengambil data profiling dengan filter
**Parameters:**
- `prov`: Provinsi
- `kab_kota`: Kabupaten/Kota
- `kec`: Kecamatan
- `kategori`: Kategori
- `subkategori`: Subkategori
- `status_verifikasi`: Status verifikasi
- `start_date`: Tanggal mulai
- `end_date`: Tanggal akhir
- `q`: Kata kunci search
- `page`: Halaman
- `limit`: Limit per halaman
- `sort_by`: Field untuk sorting
- `sort_order`: ASC/DESC

### GET /api/profiling/reports/{id}
Mengambil detail profiling report

### GET /api/profiling/reports/{id}/related
Mencari record terkait berdasarkan NIK, alamat, atau relasi keluarga

### POST /api/profiling/preview
Generate preview dokumen
**Body:**
```json
{
  "ids": [1, 2, 3],
  "template": "default"
}
```

### POST /api/profiling/export
Export dokumen ke DOCX/PDF
**Body:**
```json
{
  "ids": [1, 2, 3],
  "type": "docx",
  "combine": true,
  "filename": "custom_filename.docx"
}
```

### GET /api/profiling/download/{filename}
Download file yang telah di-export

### GET /api/profiling/stats
Mengambil statistik profiling reports

## Database Schema

### Tabel: profiling_reports
```sql
CREATE TABLE profiling_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    nama VARCHAR(255) NOT NULL,
    nik VARCHAR(20),
    ttl VARCHAR(100),
    jk ENUM('L', 'P'),
    alamat TEXT,
    kel VARCHAR(100),
    kec VARCHAR(100),
    kab_kota VARCHAR(100),
    prov VARCHAR(100),
    hp VARCHAR(20),
    nama_ayah VARCHAR(255),
    nama_ibu VARCHAR(255),
    nama_istri VARCHAR(255),
    anak TEXT,
    pekerjaan VARCHAR(255),
    jabatan VARCHAR(255),
    foto_url VARCHAR(500),
    kategori VARCHAR(100),
    subkategori VARCHAR(100),
    hasil_pendalaman TEXT,
    target_prioritas TEXT,
    simpul_pengolahan TEXT,
    aktor_pendukung TEXT,
    jaringan_lokal TEXT,
    koordinasi TEXT,
    tanggal_input TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status_verifikasi ENUM('draft', 'verified', 'published') DEFAULT 'draft',
    related_ids TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    -- Indexes and Foreign Keys
);
```

### Tabel: export_audit
```sql
CREATE TABLE export_audit (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    export_type ENUM('docx', 'pdf') NOT NULL,
    record_ids TEXT NOT NULL,
    filename VARCHAR(255),
    file_path VARCHAR(500),
    export_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT
);
```

## Cara Penggunaan

### 1. Akses Menu
- Login ke aplikasi
- Klik menu "Reports" → "Reports / Profiling"

### 2. Filter Data
- Gunakan panel filter di sebelah kiri
- Pilih provinsi, kabupaten, kategori, dll.
- Klik tombol "Filter" untuk menerapkan filter

### 3. Pilih Records
- Centang checkbox pada record yang ingin dipilih
- Atau gunakan tombol "Select All" untuk memilih semua
- Gunakan "Auto-link" untuk mencari record terkait

### 4. Preview Dokumen
- Klik tombol "Preview Document" pada toolbar
- Panel preview akan menampilkan dokumen dalam format HTML

### 5. Export Dokumen
- Klik tombol "Export" pada toolbar
- Pilih format: DOCX atau PDF
- Pilih apakah ingin menggabungkan dalam satu dokumen atau terpisah
- File akan otomatis didownload

## Nama File Export
Format nama file otomatis:
- Single record: `PROFILING_[NAMA]_[KABUPATEN]_[YYYY-MM-DD].[ext]`
- Multiple records: `PROFILING_MULTIPLE_[YYYY-MM-DD].[ext]`

## Keamanan & Audit
- Semua export activity dicatat dalam tabel `export_audit`
- Hanya user dengan role "report_viewer" atau lebih tinggi yang dapat akses export
- File export disimpan di folder `exports/` dengan nama yang aman
- Session validation untuk semua API endpoints

## Dependencies
- `python-docx`: Untuk generate DOCX
- `reportlab`: Untuk generate PDF
- `mysql-connector-python`: Untuk database connection
- `flask`: Web framework

## Troubleshooting

### Error: "No valid reports found"
- Pastikan ada data profiling di database
- Jalankan script `add_sample_profiling_data.py` untuk menambahkan data sample

### Error: "Failed to generate document"
- Pastikan folder `exports/` dapat diakses
- Check permission untuk menulis file

### Error: "Unauthorized"
- Pastikan user sudah login
- Check session token di localStorage

## Sample Data
Script `add_sample_profiling_data.py` menyediakan 5 sample data:
1. BUDIMAN SUTRISNO - Manager Perkebunan (verified)
2. SITI RAHAYU - Istri (draft)
3. AHMAD SUTRISNO - Anak (draft)
4. HARTO WIJAYA - Pemilik Lahan (verified)
5. BAMBANG SUTRISNO - Mandor (verified)

Semua data sample menggunakan lokasi "Tanjung Jabung Timur" dan kategori "Perkebunan".
