# Keamanan API Key di Database

## 📋 Status Saat Ini

### ✅ Yang Sudah Aman:
1. **Database Access Control**
   - Hanya admin yang bisa menambah/edit API key via Settings page
   - Authentication required untuk semua API endpoints
   - Session token validation

2. **API Key Masking**
   - API key tidak pernah ditampilkan full di frontend
   - Hanya ditampilkan masked: `AIzaSyA3mU...YSU`
   - Full API key hanya ada di backend

3. **Database Connection**
   - Menggunakan parameterized queries (prevent SQL injection)
   - Connection menggunakan credentials dari environment variable

### ⚠️ Yang Perlu Diperhatikan:
1. **API Key Disimpan Plain Text**
   - Saat ini API key disimpan langsung (tidak di-encrypt) di database
   - Ini **NORMAL** untuk API keys (tidak seperti password)
   - API key perlu bisa dibaca langsung untuk digunakan

2. **Database File Access**
   - Jika database file bisa diakses langsung, API key bisa dibaca
   - Pastikan file permission database aman
   - Gunakan MySQL user dengan minimal privileges

## 🔄 Alur Penggunaan API Key

```
1. Admin Input API Key
   ↓
2. Simpan ke Database (table: api_keys)
   ↓
3. Sistem Ambil API Key (dengan rotation)
   ↓
4. Gunakan untuk Google CSE API Call
   ↓
5. Jika Error 429 (Quota Exceeded):
   - Mark API key sebagai 'quota_exceeded'
   - Ambil API key berikutnya (rotation)
   - Retry dengan API key baru
   ↓
6. Jika Berhasil:
   - Update usage_count
   - Update last_used timestamp
```

## 🔒 Rekomendasi Keamanan

### Level 1: Basic Security (Saat Ini)
- ✅ Database access control
- ✅ Admin-only access
- ✅ API key masking di frontend
- ✅ Parameterized queries

### Level 2: Enhanced Security (Opsional)
- 🔐 Encrypt API key di database
- 🔐 Database-level encryption
- 🔐 Audit logging untuk API key access
- 🔐 IP whitelist untuk database access

### Level 3: Maximum Security (Production)
- 🔐 Encrypt API key dengan AES-256
- 🔐 Key rotation policy
- 🔐 API key expiration
- 🔐 Separate encryption key storage
- 🔐 Database backup encryption

## 📊 Perbandingan: Password vs API Key

| Aspek | Password | API Key |
|-------|----------|---------|
| **Storage** | Hashed (SHA-256 + Salt) | Plain Text (bisa di-encrypt) |
| **Usage** | Verify only | Read & Use directly |
| **Reason** | User input, bisa di-hash | System needs actual value |
| **Security** | One-way hash | Two-way encryption (if needed) |

## 🛡️ Best Practices

1. **Database Security**
   ```sql
   -- Pastikan user database hanya punya privileges yang diperlukan
   GRANT SELECT, INSERT, UPDATE ON clearance_facesearch.api_keys TO 'app_user'@'localhost';
   -- JANGAN berikan DROP atau DELETE privileges
   ```

2. **File Permissions**
   ```bash
   # Pastikan database file tidak readable oleh public
   chmod 600 /var/lib/mysql/clearance_facesearch/api_keys.ibd
   ```

3. **Network Security**
   - Gunakan SSL/TLS untuk database connection
   - Restrict database access ke localhost saja
   - Gunakan firewall rules

4. **Backup Security**
   - Encrypt database backups
   - Jangan simpan backup di public location
   - Rotate backup encryption keys

## 🔐 Opsi Enkripsi (Jika Diperlukan)

Jika Anda ingin menambahkan enkripsi untuk API key, bisa menggunakan:

1. **Application-level encryption** (recommended)
   - Encrypt sebelum save ke database
   - Decrypt saat retrieve
   - Gunakan library seperti `cryptography`

2. **Database-level encryption**
   - MySQL Transparent Data Encryption (TDE)
   - Column-level encryption
   - Requires MySQL Enterprise

## 📝 Kesimpulan

**Status Saat Ini: AMAN untuk Development/Internal Use**

- API key disimpan plain text adalah **NORMAL** untuk API keys
- Keamanan utama dari:
  - Database access control
  - Admin-only access
  - Network security
  - File permissions

**Untuk Production:**
- Pertimbangkan encrypt API key jika:
  - Database bisa diakses oleh multiple users
  - Database backup disimpan di cloud
  - Compliance requirements (PCI-DSS, etc.)

**Rekomendasi:**
- Untuk internal use: Current setup sudah cukup
- Untuk production: Tambahkan application-level encryption

