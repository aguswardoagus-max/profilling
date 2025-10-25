# Clearance Face Search System

Sistem pencarian identitas profesional dengan fitur face recognition, data keluarga, dan nomor telepon.

## 🚀 Fitur Utama

- **Modern UI Design**: Tampilan startup yang profesional dan responsif
- **Face Recognition**: Pencarian berdasarkan foto wajah
- **Data Keluarga**: Informasi lengkap anggota keluarga
- **Nomor Telepon**: Data nomor HP terdaftar
- **PDF Export**: Cetak hasil pencarian dalam format PDF
- **Auto-Fill Credentials**: Username dan password otomatis dimuat dari `.env` (field tersembunyi)
- **Responsive Design**: Kompatibel dengan desktop dan mobile

## 📁 Struktur File

```
├── app.py                 # Flask web server utama
├── clearance_face_search.py # Core face recognition logic
├── index_modern.html      # UI modern (default)
├── index_simple.html      # UI sederhana
├── .env                  # Konfigurasi credentials
├── requirements.txt      # Dependencies Python
└── README.md            # Dokumentasi ini
```

## ⚙️ Instalasi

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Konfigurasi Credentials**:
   Edit file `.env`:
   ```env
   CLEARANCE_USERNAME=your_username
   CLEARANCE_PASSWORD=your_password
   ```

3. **Jalankan Server**:
   ```bash
   python app.py
   ```

4. **Akses Aplikasi**:
   - Modern UI: `http://localhost:5000`
   - Simple UI: `http://localhost:5000/simple`

## 🔧 Konfigurasi

### File .env

```env
# Credentials untuk API clearance
CLEARANCE_USERNAME=rezarios
CLEARANCE_PASSWORD=12345678

# API Endpoints
CLEARANCE_API_URL=http://10.1.54.224:4646
FAMILY_API_BASE=http://10.1.54.224:4646/json/clearance/dukcapil/family
FAMILY_API_ALT=http://10.1.54.116:27682/api/v1/ktp/internal
PHONE_API_BASE=http://10.1.54.224:4646/json/clearance/phones

# Application Settings
APP_NAME=Clearance Face Search
APP_VERSION=1.0.0
DEBUG_MODE=True
```

## 🎯 Cara Penggunaan

### 1. Pencarian dengan NIK
- Username dan password otomatis dimuat dari file `.env` (tidak perlu input manual)
- Masukkan NIK yang ingin dicari
- Klik "Search Identity"

### 2. Pencarian dengan Foto
- Upload foto wajah
- Sistem akan mencari kecocokan di database
- Hasil ditampilkan dengan tingkat kemiripan

### 3. Export PDF
- Setelah mendapat hasil pencarian
- Klik tombol "Print PDF"
- File PDF akan otomatis terdownload

## 📊 Data yang Ditampilkan

### Informasi Dasar
- Nama lengkap
- NIK
- Tanggal dan tempat lahir
- Jenis kelamin
- Agama
- Pekerjaan
- Alamat

### Data Keluarga
- Kepala keluarga
- NKK (Nomor Kartu Keluarga)
- Anggota keluarga lengkap dengan:
  - Nama dan hubungan
  - NIK masing-masing
  - Tanggal lahir
  - Pekerjaan
  - Status perkawinan

### Nomor Telepon
- Nomor HP terdaftar
- Operator
- Tanggal registrasi

### Foto Wajah
- Foto utama (jika tersedia)
- Avatar untuk anggota keluarga
- Fitur download foto

## 🔒 Keamanan

- Credentials disimpan di file `.env` (tidak di-commit ke git)
- API calls menggunakan authentication token
- Data sensitif tidak disimpan di frontend

## 🛠️ API Endpoints

- `GET /` - Halaman utama (modern UI)
- `GET /simple` - Halaman sederhana
- `GET /api/config` - Konfigurasi default
- `POST /api/search` - Pencarian identitas
- `GET /api/debug/*` - Debug endpoints

## 📱 Responsive Design

Aplikasi mendukung:
- Desktop (1200px+)
- Tablet (768px - 1199px)
- Mobile (< 768px)

## 🎨 UI Features

### Modern Design
- Gradient backgrounds
- Card-based layout
- Smooth animations
- Professional typography
- Icon integration (Font Awesome)

### Print Styles
- Optimized untuk PDF export
- Clean layout untuk printing
- Professional formatting

## 🔧 Troubleshooting

### Foto Tidak Muncul
- Cek console browser untuk error
- Pastikan data base64 valid
- Test dengan browser lain

### API Timeout
- Cek koneksi ke server API
- Pastikan credentials benar
- Cek firewall settings

### PDF Tidak Terdownload
- Pastikan browser support JavaScript
- Cek popup blocker
- Gunakan browser modern (Chrome, Firefox, Edge)

## 📞 Support

Untuk bantuan teknis atau bug report, silakan hubungi tim development.

---

**Clearance Face Search System v1.0.0**  
*Professional Identity Verification Platform*