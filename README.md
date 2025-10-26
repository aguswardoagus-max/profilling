# Clearance Face Search Application

Aplikasi pencarian wajah dan profiling dengan fitur AI untuk sistem clearance.

## 📁 Struktur Project

```
profilling/
├── backend/                    # Backend Python files
│   ├── app.py                 # Main Flask application
│   ├── database.py            # Database operations
│   ├── cekplat.py            # License plate checking
│   ├── ai_config.py          # AI configuration
│   ├── ai_api_endpoints.py   # AI API endpoints
│   ├── requirements.txt      # Python dependencies
│   └── ...                   # Other backend files
├── frontend/                  # Frontend files
│   ├── pages/                # HTML pages
│   │   ├── dashboard.html    # Dashboard page
│   │   ├── profiling.html    # Profiling page
│   │   ├── ai_features.html  # AI Features page
│   │   └── ...               # Other HTML pages
│   ├── static/               # Static assets
│   │   ├── style.css         # Main stylesheet
│   │   ├── script.js         # Main JavaScript
│   │   ├── clean_photos/     # Clean photos
│   │   └── default-avatar.png
│   └── assets/               # Additional assets
├── config/                   # Configuration files
│   ├── ai_analytics.db       # AI Analytics database
│   └── clearance_facesearch.sql # Database schema
├── uploads/                  # Upload files
├── faces/                    # Face images
├── exports/                  # Export files
├── run.py                    # Application entry point
└── README.md                 # This file
```

## 🚀 Cara Menjalankan

### 1. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 2. Setup Database
```bash
python backend/setup_database.py
```

### 3. Run Application
```bash
python run.py
```

### 4. Akses Aplikasi
Buka browser dan akses: `http://127.0.0.1:5000`

## 🔧 Konfigurasi

### Environment Variables
Buat file `.env` di root directory:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=clearance_facesearch
```

### AI Configuration
Konfigurasi AI ada di `backend/ai_config.py`

## 📋 Fitur Utama

- ✅ **Authentication System** - Login/logout dengan session management
- ✅ **Face Recognition** - Pencarian wajah dengan AI
- ✅ **License Plate Check** - Pengecekan nomor plat kendaraan
- ✅ **Data Profiling** - Profiling data person
- ✅ **User Management** - Manajemen user dan role
- ✅ **Reports** - Laporan dan export data
- ✅ **AI Features** - Fitur AI untuk analisis
- ✅ **Security** - Keamanan tingkat enterprise

## 🛡️ Keamanan

- **Double Authentication** - Server-side + Client-side validation
- **Session Management** - Secure session tokens
- **Content Protection** - No content flash before authentication
- **Role-based Access** - Access control berdasarkan role

## 📝 API Endpoints

### Authentication
- `POST /api/login` - Login user
- `POST /api/logout` - Logout user
- `POST /api/validate-session` - Validate session

### Main Features
- `GET /dashboard` - Dashboard page
- `GET /profiling` - Profiling page
- `GET /ai-features` - AI Features page
- `GET /user-management` - User Management page

### Data APIs
- `GET /api/dashboard/stats` - Dashboard statistics
- `POST /api/profiling/search` - Search profiling data
- `POST /api/ai/face-analysis` - Face analysis

## 🔄 Development

### Backend Development
Semua file Python backend ada di folder `backend/`

### Frontend Development
Semua file HTML, CSS, JS ada di folder `frontend/`

### Database
Database MySQL dengan schema di `config/clearance_facesearch.sql`

## 📞 Support

Untuk pertanyaan atau masalah, silakan hubungi tim development.

---
**Clearance Face Search** - Professional Face Recognition System
