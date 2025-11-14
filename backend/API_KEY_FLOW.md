# Alur API Key - Dari Input Hingga Penggunaan

## 🔄 Diagram Alur Lengkap

```
┌─────────────────────────────────────────────────────────────┐
│ 1. ADMIN INPUT API KEY                                      │
│    - Via Settings Page (http://127.0.0.1:5000/settings)    │
│    - Hanya admin yang bisa akses                            │
│    - Input field type="password" (tidak terlihat saat ketik)│
└────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. VALIDASI & ENKRIPSI (OPSIONAL)                          │
│    - Validasi format (harus mulai dengan "AIza")           │
│    - Jika encryption enabled: encrypt sebelum save          │
│    - Log activity: "Admin updated API key"                 │
└────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. SIMPAN KE DATABASE                                       │
│    Table: api_keys                                          │
│    - api_key: "AIzaSyA3mUw3gtWxajpBPqB4VpFPZMf6lbnRYSU"    │
│    - status: "active"                                       │
│    - priority: 0 (default)                                 │
│    - usage_count: 0                                        │
│    - created_at: timestamp                                 │
└────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. SISTEM AMBIL API KEY (SAAT DIPERLUKAN)                  │
│    Function: get_google_cse_api_key()                      │
│    - Query: SELECT api_key FROM api_keys                   │
│             WHERE status='active'                           │
│             ORDER BY priority DESC, last_used ASC           │
│    - Update: usage_count++, last_used = NOW()              │
└────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. GUNAKAN UNTUK GOOGLE CSE API CALL                       │
│    - Request ke: https://www.googleapis.com/customsearch/v1│
│    - Parameter: key=API_KEY, cx=CSE_ID, q=query            │
└────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
         ┌────────────┴────────────┐
         │                         │
         ▼                         ▼
┌──────────────────┐    ┌──────────────────────────────┐
│ 6A. BERHASIL     │    │ 6B. ERROR 429 (QUOTA EXCEEDED)│
│ - Return results │    │ - Mark API key:               │
│ - Update stats   │    │   status = 'quota_exceeded'   │
│                  │    │   quota_exceeded_at = NOW()   │
└──────────────────┘    └────────────┬─────────────────┘
                                       │
                                       ▼
                      ┌────────────────────────────────┐
                      │ 7. AUTO ROTATION              │
                      │ - Ambil API key berikutnya     │
                      │ - Retry dengan API key baru    │
                      │ - Max 5 retries               │
                      └────────────────────────────────┘
```

## 🔐 Keamanan di Setiap Langkah

### Langkah 1: Input
- ✅ **Authentication**: Hanya admin yang bisa input
- ✅ **Authorization**: Check role='admin' di backend
- ✅ **Input Masking**: Type password, tidak terlihat saat ketik
- ✅ **Validation**: Format check (harus "AIza...")

### Langkah 2: Transmisi
- ✅ **HTTPS**: Jika menggunakan HTTPS, data encrypted in transit
- ✅ **Session Token**: Validasi session untuk setiap request
- ✅ **CSRF Protection**: Session cookie dengan SameSite

### Langkah 3: Storage
- ⚠️ **Plain Text**: API key disimpan langsung (tidak di-hash)
- ✅ **Database Access**: Hanya aplikasi yang bisa akses
- ✅ **Parameterized Queries**: Prevent SQL injection
- ✅ **File Permissions**: Database file tidak readable public

### Langkah 4: Retrieval
- ✅ **Query Filter**: Hanya ambil status='active'
- ✅ **No Logging**: API key tidak di-log full (hanya masked)
- ✅ **Memory**: API key hanya di memory saat digunakan

### Langkah 5: Usage
- ✅ **Direct Use**: Langsung ke Google API, tidak melalui proxy
- ✅ **Error Handling**: Tidak expose error details ke frontend
- ✅ **Rate Limiting**: Auto-rotation jika quota exceeded

## 📊 Data Flow Security

```
Frontend (Settings Page)
    │
    │ HTTPS (if enabled)
    │ Session Token
    │
    ▼
Backend API (/api/settings/api-key)
    │
    │ Validate Session
    │ Check Admin Role
    │
    ▼
Database (api_keys table)
    │
    │ Encrypted Connection (if SSL enabled)
    │ Parameterized Query
    │
    ▼
Storage (MySQL)
    │
    │ File Permissions: 600
    │ User Privileges: Limited
    │
    ▼
Retrieval (get_active_api_key)
    │
    │ Query with WHERE status='active'
    │ Update usage stats
    │
    ▼
Google CSE API
    │
    │ HTTPS
    │ API Key in request
    │
    ▼
Response
```

## 🛡️ Security Layers

### Layer 1: Application Security
- ✅ Authentication & Authorization
- ✅ Input Validation
- ✅ Error Handling
- ✅ Activity Logging

### Layer 2: Database Security
- ✅ Access Control (MySQL users)
- ✅ Parameterized Queries
- ✅ Connection Encryption (optional)
- ✅ Backup Encryption (recommended)

### Layer 3: Network Security
- ✅ HTTPS (recommended for production)
- ✅ Firewall Rules
- ✅ IP Whitelisting (optional)

### Layer 4: File System Security
- ✅ File Permissions
- ✅ Database File Location
- ✅ Backup Location Security

## ⚠️ Risiko & Mitigasi

| Risiko | Kemungkinan | Dampak | Mitigasi |
|--------|------------|--------|----------|
| Database di-hack | Rendah | Tinggi | Access control, encryption |
| API key di-log | Sedang | Sedang | Masking, no full logging |
| SQL Injection | Rendah | Tinggi | Parameterized queries ✅ |
| Unauthorized Access | Sedang | Tinggi | Authentication ✅ |
| Database Backup Leak | Rendah | Tinggi | Encrypt backups |
| API Key di Memory | Rendah | Sedang | Clear after use |

## ✅ Checklist Keamanan

- [x] Authentication required
- [x] Admin-only access
- [x] Input validation
- [x] Parameterized queries
- [x] API key masking di frontend
- [x] Activity logging
- [x] Error handling
- [ ] Encryption (optional)
- [ ] Database SSL (optional)
- [ ] Backup encryption (recommended)

## 🎯 Kesimpulan

**Status Keamanan: BAIK untuk Development/Internal Use**

Sistem sudah memiliki:
- ✅ Multiple security layers
- ✅ Access control
- ✅ Input validation
- ✅ Safe database practices

**Untuk Production:**
- Pertimbangkan encryption jika ada compliance requirements
- Gunakan HTTPS
- Encrypt database backups
- Monitor access logs

